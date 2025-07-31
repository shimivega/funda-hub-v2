from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import json
from pathlib import Path

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///funda_app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['RESOURCES_FOLDER'] = 'resources'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create upload and resources directories
Path(app.config['UPLOAD_FOLDER']).mkdir(exist_ok=True)
Path(app.config['RESOURCES_FOLDER']).mkdir(exist_ok=True)

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    password_hash = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'admin', 'teacher', or 'learner'
    grade = db.Column(db.String(10), nullable=True)
    profile_picture = db.Column(db.String(200), nullable=True)
    status = db.Column(db.String(200), nullable=True)
    is_online = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Admin check helper method
    def is_admin(self):
        return self.role == 'admin' or self.email in ['admin@funda.com', 'solly@funda.com']
    
    # Teacher check helper method
    def is_teacher(self):
        return self.role in ['admin', 'teacher']
    
    # Can upload resources
    def can_upload(self):
        return self.role in ['admin', 'teacher']

class Classroom(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(50), nullable=False)
    grade = db.Column(db.String(10), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    join_code = db.Column(db.String(10), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class StudyGroup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    is_private = db.Column(db.Boolean, default=False)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Resource(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    grade = db.Column(db.String(20), nullable=False)
    subject = db.Column(db.String(50), nullable=False)
    resource_type = db.Column(db.String(50), nullable=False)
    source = db.Column(db.String(100), nullable=False)
    source_url = db.Column(db.String(500), nullable=True)
    file_size = db.Column(db.Integer, nullable=False)
    file_hash = db.Column(db.String(32), nullable=False)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    download_count = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    
    # New fields for enhanced functionality
    visibility = db.Column(db.String(20), default='all')  # 'all', 'teachers', 'admin'
    tags = db.Column(db.Text, nullable=True)  # JSON string of tags
    description = db.Column(db.Text, nullable=True)
    file_type = db.Column(db.String(10), nullable=False)  # 'pdf', 'video', etc.
    is_flagged = db.Column(db.Boolean, default=False)
    flag_reason = db.Column(db.String(500), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to get uploader info
    uploader = db.relationship('User', backref='uploaded_resources', lazy=True)
    
    def get_tags_list(self):
        """Convert tags JSON string to list"""
        if self.tags:
            try:
                return json.loads(self.tags)
            except:
                return []
        return []
    
    def set_tags_list(self, tags_list):
        """Convert tags list to JSON string"""
        self.tags = json.dumps(tags_list) if tags_list else None
    
    def can_view(self, user):
        """Check if user can view this resource"""
        if not self.is_active:
            return False
        
        if self.visibility == 'all':
            return True
        elif self.visibility == 'teachers' and user and user.is_teacher():
            return True
        elif self.visibility == 'admin' and user and user.is_admin():
            return True
        
        return False
    
    def get_structured_path(self):
        """Get structured file path: /resources/{grade}/{subject}/{type}/filename"""
        return f"/resources/{self.grade}/{self.subject}/{self.resource_type}/{self.filename}"

class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    grade = db.Column(db.String(20), nullable=False)
    subject = db.Column(db.String(50), nullable=False)
    language = db.Column(db.String(50), nullable=False)
    difficulty = db.Column(db.String(20), nullable=False)  # beginner, intermediate, advanced
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    visibility = db.Column(db.String(20), default='all')  # 'all', 'teachers', 'admin'
    time_limit = db.Column(db.Integer, nullable=True)  # in minutes
    randomize_questions = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    creator = db.relationship('User', backref='created_quizzes', lazy=True)
    questions = db.relationship('Question', backref='quiz', lazy=True, cascade='all, delete-orphan')

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    question_type = db.Column(db.String(20), nullable=False)  # multiple-choice, short-answer, essay, comprehension
    question_text = db.Column(db.Text, nullable=False)
    options = db.Column(db.Text, nullable=True)  # JSON string for multiple choice options
    correct_answer = db.Column(db.Text, nullable=True)
    explanation = db.Column(db.Text, nullable=True)
    points = db.Column(db.Integer, default=1)
    order_index = db.Column(db.Integer, nullable=False)
    
    # For comprehension questions
    passage = db.Column(db.Text, nullable=True)
    sub_questions = db.Column(db.Text, nullable=True)  # JSON string for comprehension sub-questions
    
    # For essay questions
    word_limit = db.Column(db.Integer, nullable=True)
    instruction = db.Column(db.Text, nullable=True)
    
    def get_options_list(self):
        """Convert options JSON string to list"""
        if self.options:
            try:
                return json.loads(self.options)
            except:
                return []
        return []
    
    def set_options_list(self, options_list):
        """Convert options list to JSON string"""
        self.options = json.dumps(options_list) if options_list else None

class TeacherChat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    resource_id = db.Column(db.Integer, db.ForeignKey('resource.id'), nullable=True)  # For sharing resources
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages', lazy=True)
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_messages', lazy=True)
    shared_resource = db.relationship('Resource', backref='shared_in_chats', lazy=True)

class ResourceFlag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    resource_id = db.Column(db.Integer, db.ForeignKey('resource.id'), nullable=False)
    flagged_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reason = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='pending')  # pending, reviewed, resolved
    reviewed_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    resource = db.relationship('Resource', backref='flags', lazy=True)
    flagger = db.relationship('User', foreign_keys=[flagged_by], backref='flagged_resources', lazy=True)
    reviewer = db.relationship('User', foreign_keys=[reviewed_by], backref='reviewed_flags', lazy=True)

class TeacherFriend(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    teacher1_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    teacher2_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, accepted, blocked
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    teacher1 = db.relationship('User', foreign_keys=[teacher1_id], backref='friend_requests_sent', lazy=True)
    teacher2 = db.relationship('User', foreign_keys=[teacher2_id], backref='friend_requests_received', lazy=True)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', user=current_user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            user.is_online = True
            db.session.commit()
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form['full_name']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']
        role = request.form['role']
        grade = request.form.get('grade', '')
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists')
            return render_template('register.html')
        
        user = User(
            full_name=full_name,
            email=email,
            phone=phone,
            password_hash=generate_password_hash(password),
            role=role,
            grade=grade
        )
        
        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        return redirect(url_for('dashboard'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    current_user.is_online = False
    db.session.commit()
    logout_user()
    return redirect(url_for('index'))

@app.route('/practice-zone')
@login_required
def practice_zone():
    return render_template('practice_zone.html')

@app.route('/study-groups')
@login_required
def study_groups():
    groups = StudyGroup.query.all()
    return render_template('study_groups.html', groups=groups)

@app.route('/textbooks')
@login_required
def textbooks():
    # Fetch all resources that are textbooks or exam papers
    resources = Resource.query.filter(
        (Resource.resource_type == 'textbook') | 
        (Resource.resource_type == 'exam_paper')
    ).all()
    
    # Group resources by grade and subject for better organization
    organized_resources = {}
    for resource in resources:
        if resource.grade not in organized_resources:
            organized_resources[resource.grade] = {}
        if resource.subject not in organized_resources[resource.grade]:
            organized_resources[resource.grade][resource.subject] = []
        organized_resources[resource.grade][resource.subject].append(resource)
    
    # Get unique grades and subjects for filters
    grades = sorted(list(set(r.grade for r in resources)))
    subjects = sorted(list(set(r.subject for r in resources)))
    
    return render_template(
        'textbooks.html',
        resources=organized_resources,
        grades=grades,
        subjects=subjects,
        current_grade=request.args.get('grade'),
        current_subject=request.args.get('subject')
    )

@app.route('/classrooms')
@login_required
def classrooms():
    if current_user.role == 'teacher':
        classrooms = Classroom.query.filter_by(teacher_id=current_user.id).all()
    else:
        # For learners, show joined classrooms (would need a join table)
        classrooms = []
    return render_template('classrooms.html', classrooms=classrooms)

@app.route('/chat')
@login_required
def chat():
    return render_template('chat.html')

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)

@app.route('/support-center')
@login_required
def support_center():
    return render_template('support_center.html')

# Resource Management Routes
@app.route('/resources')
@login_required
def resources():
    grade = request.args.get('grade', '')
    subject = request.args.get('subject', '')
    resource_type = request.args.get('type', '')
    
    query = Resource.query.filter_by(is_active=True)
    
    if grade:
        query = query.filter_by(grade=grade)
    if subject:
        query = query.filter_by(subject=subject)
    if resource_type:
        query = query.filter_by(resource_type=resource_type)
    
    resources = query.order_by(Resource.created_at.desc()).all()
    
    # Get available filters
    grades = db.session.query(Resource.grade).distinct().all()
    subjects = db.session.query(Resource.subject).distinct().all()
    types = db.session.query(Resource.resource_type).distinct().all()
    
    return render_template('resources.html', 
                         resources=resources,
                         grades=[g[0] for g in grades],
                         subjects=[s[0] for s in subjects],
                         types=[t[0] for t in types],
                         current_grade=grade,
                         current_subject=subject,
                         current_type=resource_type)

@app.route('/resources/download/<int:resource_id>')
@login_required
def download_resource(resource_id):
    resource = Resource.query.get_or_404(resource_id)
    
    # Increment download count
    resource.download_count += 1
    db.session.commit()
    
    # Serve the file
    return send_from_directory(os.path.dirname(resource.file_path), 
                             os.path.basename(resource.file_path),
                             as_attachment=True,
                             download_name=resource.original_filename)

@app.route('/admin/resources')
@login_required
def admin_resources():
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    resources = Resource.query.filter_by(is_active=True).order_by(Resource.upload_date.desc()).all()
    return render_template('admin_resources.html', resources=resources)

@app.route('/admin/upload')
@login_required
def admin_upload():
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
    return render_template('admin_upload.html')

@app.route('/create_quiz', methods=['GET', 'POST'])
@login_required
def create_quiz():
    if not current_user.can_upload():
        flash('Access denied. Teacher or admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        try:
            quiz = Quiz(
                title=request.form['title'],
                grade=request.form['grade'],
                subject=request.form['subject'],
                language=request.form['language'],
                difficulty=request.form['difficulty'],
                description=request.form.get('description', ''),
                time_limit=int(request.form['time_limit']) if request.form.get('time_limit') else None,
                visibility=request.form['visibility'],
                randomize_questions=bool(request.form.get('randomize_questions')),
                created_by=current_user.id
            )
            db.session.add(quiz)
            db.session.commit()
            
            flash('Quiz created successfully! You can now add questions.', 'success')
            return redirect(url_for('edit_quiz', quiz_id=quiz.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating quiz: {str(e)}', 'error')
    
    return render_template('create_quiz.html')

@app.route('/teacher/collaboration')
@login_required
def teacher_collaboration():
    if not current_user.is_teacher():
        flash('Access denied. Teacher privileges required.', 'error')
        return redirect(url_for('dashboard'))
    return render_template('teacher_collaboration.html')

@app.route('/quiz/<int:quiz_id>/edit')
@login_required
def edit_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    if quiz.created_by != current_user.id and not current_user.is_admin():
        flash('Access denied. You can only edit your own quizzes.', 'error')
        return redirect(url_for('practice_zone'))
    
    # For now, redirect to practice zone with success message
    # In a full implementation, this would show a quiz editing interface
    flash(f'Quiz "{quiz.title}" created successfully! Question editing interface coming soon.', 'success')
    return redirect(url_for('practice_zone'))

@app.route('/games')
@login_required
def games():
    return render_template('games.html')

@app.route('/games/geography')
@login_required
def geography_game():
    return render_template('geography_game.html')

@app.route('/games/language')
@login_required
def language_game():
    return render_template('language_game.html')

@app.route('/admin/resources/upload', methods=['POST'])
@login_required
def upload_resource():
    if not current_user.can_upload():
        return jsonify({'error': 'Access denied'}), 403
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file selected'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        # Get form data
        grade = request.form.get('grade')
        subject = request.form.get('subject')
        resource_type = request.form.get('resource_type')
        visibility = request.form.get('visibility', 'all')
        description = request.form.get('description', '')
        tags = request.form.getlist('tags')  # Get list of tags
        
        if not all([grade, subject, resource_type]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Validate visibility based on user role
        if visibility == 'admin' and not current_user.is_admin():
            visibility = 'teachers'  # Teachers can't set admin-only visibility
        
        # Secure filename
        filename = secure_filename(file.filename)
        
        # Detect file type
        file_extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        file_type = 'pdf' if file_extension == 'pdf' else 'video' if file_extension in ['mp4', 'avi', 'mov', 'wmv'] else 'other'
        
        # Create folder structure: /resources/{grade}/{subject}/{type}/
        folder_path = Path(app.config['RESOURCES_FOLDER']) / grade / subject / resource_type
        folder_path.mkdir(parents=True, exist_ok=True)
        
        # Save file
        file_path = folder_path / filename
        file.save(file_path)
        
        # Calculate file hash
        import hashlib
        with open(file_path, 'rb') as f:
            file_hash = hashlib.md5(f.read()).hexdigest()
        
        # Create resource record
        resource = Resource(
            filename=filename,
            original_filename=file.filename,
            file_path=str(file_path),
            grade=grade,
            subject=subject,
            resource_type=resource_type,
            source='Manual Upload',
            file_size=os.path.getsize(file_path),
            file_hash=file_hash,
            uploaded_by=current_user.id,
            visibility=visibility,
            description=description,
            file_type=file_type
        )
        
        # Set tags
        if tags:
            resource.set_tags_list(tags)
        
        db.session.add(resource)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Resource uploaded successfully', 'resource_id': resource.id})
    
    return jsonify({'error': 'Invalid file type'}), 400

# Enhanced resource routes with visibility filtering
@app.route('/resources')
@login_required
def resources():
    grade = request.args.get('grade', '')
    subject = request.args.get('subject', '')
    resource_type = request.args.get('type', '')
    
    # Base query with visibility filtering
    query = Resource.query.filter_by(is_active=True)
    
    # Apply visibility filtering based on user role
    if current_user.is_admin():
        # Admin can see all resources
        pass
    elif current_user.is_teacher():
        # Teachers can see all, teachers, and admin resources
        query = query.filter(Resource.visibility.in_(['all', 'teachers', 'admin']))
    else:
        # Learners can only see 'all' resources
        query = query.filter_by(visibility='all')
    
    # Apply filters
    if grade:
        query = query.filter_by(grade=grade)
    if subject:
        query = query.filter_by(subject=subject)
    if resource_type:
        query = query.filter_by(resource_type=resource_type)
    
    resources = query.order_by(Resource.created_at.desc()).all()
    
    # Filter resources that user can view
    viewable_resources = [r for r in resources if r.can_view(current_user)]
    
    # Get available filters
    grades = db.session.query(Resource.grade).distinct().all()
    subjects = db.session.query(Resource.subject).distinct().all()
    types = db.session.query(Resource.resource_type).distinct().all()
    
    return render_template('textbooks.html', 
                         resources=viewable_resources,
                         grades=[g[0] for g in grades],
                         subjects=[s[0] for s in subjects],
                         types=[t[0] for t in types],
                         current_grade=grade,
                         current_subject=subject,
                         current_type=resource_type)

# PDF Preview Route
@app.route('/resources/preview/<int:resource_id>')
@login_required
def preview_resource(resource_id):
    resource = Resource.query.get_or_404(resource_id)
    
    # Check if user can view this resource
    if not resource.can_view(current_user):
        flash('Access denied')
        return redirect(url_for('resources'))
    
    # For PDF files, serve directly for preview
    if resource.file_type == 'pdf':
        return send_from_directory(os.path.dirname(resource.file_path), 
                                 os.path.basename(resource.file_path),
                                 mimetype='application/pdf')
    else:
        # For other files, redirect to download
        return redirect(url_for('download_resource', resource_id=resource_id))

# Resource Flagging Routes
@app.route('/resources/flag/<int:resource_id>', methods=['POST'])
@login_required
def flag_resource(resource_id):
    resource = Resource.query.get_or_404(resource_id)
    
    reason = request.form.get('reason')
    description = request.form.get('description', '')
    
    if not reason:
        return jsonify({'error': 'Reason is required'}), 400
    
    # Check if user already flagged this resource
    existing_flag = ResourceFlag.query.filter_by(
        resource_id=resource_id,
        flagged_by=current_user.id
    ).first()
    
    if existing_flag:
        return jsonify({'error': 'You have already flagged this resource'}), 400
    
    # Create flag
    flag = ResourceFlag(
        resource_id=resource_id,
        flagged_by=current_user.id,
        reason=reason,
        description=description
    )
    
    db.session.add(flag)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Resource flagged successfully'})

# Quiz Management Routes
@app.route('/quizzes/create', methods=['GET', 'POST'])
@login_required
def create_quiz():
    if not current_user.can_upload():
        flash('Access denied')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description', '')
        grade = request.form.get('grade')
        subject = request.form.get('subject')
        language = request.form.get('language')
        difficulty = request.form.get('difficulty')
        visibility = request.form.get('visibility', 'all')
        time_limit = request.form.get('time_limit')
        randomize = request.form.get('randomize_questions') == 'on'
        
        if not all([title, grade, subject, language, difficulty]):
            flash('Please fill in all required fields')
            return render_template('create_quiz.html')
        
        # Validate visibility
        if visibility == 'admin' and not current_user.is_admin():
            visibility = 'teachers'
        
        quiz = Quiz(
            title=title,
            description=description,
            grade=grade,
            subject=subject,
            language=language,
            difficulty=difficulty,
            created_by=current_user.id,
            visibility=visibility,
            time_limit=int(time_limit) if time_limit else None,
            randomize_questions=randomize
        )
        
        db.session.add(quiz)
        db.session.commit()
        
        flash('Quiz created successfully!')
        return redirect(url_for('edit_quiz', quiz_id=quiz.id))
    
    return render_template('create_quiz.html')

@app.route('/quizzes/<int:quiz_id>/edit')
@login_required
def edit_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    
    # Check permissions
    if not current_user.can_upload() or (quiz.created_by != current_user.id and not current_user.is_admin()):
        flash('Access denied')
        return redirect(url_for('practice_zone'))
    
    return render_template('edit_quiz.html', quiz=quiz)

@app.route('/quizzes/<int:quiz_id>/questions', methods=['POST'])
@login_required
def add_question(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    
    # Check permissions
    if not current_user.can_upload() or (quiz.created_by != current_user.id and not current_user.is_admin()):
        return jsonify({'error': 'Access denied'}), 403
    
    question_type = request.form.get('question_type')
    question_text = request.form.get('question_text')
    correct_answer = request.form.get('correct_answer')
    explanation = request.form.get('explanation', '')
    points = int(request.form.get('points', 1))
    
    if not all([question_type, question_text]):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Get next order index
    max_order = db.session.query(db.func.max(Question.order_index)).filter_by(quiz_id=quiz_id).scalar() or 0
    
    question = Question(
        quiz_id=quiz_id,
        question_type=question_type,
        question_text=question_text,
        correct_answer=correct_answer,
        explanation=explanation,
        points=points,
        order_index=max_order + 1
    )
    
    # Handle multiple choice options
    if question_type == 'multiple-choice':
        options = request.form.getlist('options')
        if options:
            question.set_options_list(options)
    
    # Handle comprehension questions
    elif question_type == 'comprehension':
        passage = request.form.get('passage')
        question.passage = passage
        
        # Handle sub-questions (simplified for now)
        sub_questions = request.form.getlist('sub_questions')
        if sub_questions:
            question.sub_questions = json.dumps(sub_questions)
    
    # Handle essay questions
    elif question_type == 'essay':
        word_limit = request.form.get('word_limit')
        instruction = request.form.get('instruction')
        question.word_limit = int(word_limit) if word_limit else None
        question.instruction = instruction
    
    db.session.add(question)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Question added successfully', 'question_id': question.id})

# Teacher Collaboration Routes
@app.route('/teachers/chat/<int:teacher_id>')
@login_required
def teacher_chat(teacher_id):
    if not current_user.is_teacher():
        flash('Access denied')
        return redirect(url_for('dashboard'))
    
    teacher = User.query.get_or_404(teacher_id)
    if not teacher.is_teacher():
        flash('Invalid teacher')
        return redirect(url_for('dashboard'))
    
    # Get chat messages
    messages = TeacherChat.query.filter(
        ((TeacherChat.sender_id == current_user.id) & (TeacherChat.receiver_id == teacher_id)) |
        ((TeacherChat.sender_id == teacher_id) & (TeacherChat.receiver_id == current_user.id))
    ).order_by(TeacherChat.created_at.asc()).all()
    
    # Mark messages as read
    TeacherChat.query.filter_by(
        sender_id=teacher_id,
        receiver_id=current_user.id,
        is_read=False
    ).update({'is_read': True})
    db.session.commit()
    
    return render_template('teacher_chat.html', teacher=teacher, messages=messages)

@app.route('/teachers/send_message', methods=['POST'])
@login_required
def send_teacher_message():
    if not current_user.is_teacher():
        return jsonify({'error': 'Access denied'}), 403
    
    receiver_id = request.form.get('receiver_id')
    message = request.form.get('message')
    resource_id = request.form.get('resource_id')  # Optional resource sharing
    
    if not all([receiver_id, message]):
        return jsonify({'error': 'Missing required fields'}), 400
    
    receiver = User.query.get(receiver_id)
    if not receiver or not receiver.is_teacher():
        return jsonify({'error': 'Invalid receiver'}), 400
    
    chat_message = TeacherChat(
        sender_id=current_user.id,
        receiver_id=receiver_id,
        message=message,
        resource_id=int(resource_id) if resource_id else None
    )
    
    db.session.add(chat_message)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Message sent successfully'})

@app.route('/teachers/add_friend/<int:teacher_id>', methods=['POST'])
@login_required
def add_teacher_friend(teacher_id):
    if not current_user.is_teacher():
        return jsonify({'error': 'Access denied'}), 403
    
    teacher = User.query.get_or_404(teacher_id)
    if not teacher.is_teacher():
        return jsonify({'error': 'Invalid teacher'}), 400
    
    # Check if friendship already exists
    existing = TeacherFriend.query.filter(
        ((TeacherFriend.teacher1_id == current_user.id) & (TeacherFriend.teacher2_id == teacher_id)) |
        ((TeacherFriend.teacher1_id == teacher_id) & (TeacherFriend.teacher2_id == current_user.id))
    ).first()
    
    if existing:
        return jsonify({'error': 'Friend request already exists'}), 400
    
    friend_request = TeacherFriend(
        teacher1_id=current_user.id,
        teacher2_id=teacher_id
    )
    
    db.session.add(friend_request)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Friend request sent successfully'})

@app.route('/admin/resources/scrape', methods=['POST'])
@login_required
def trigger_scrape():
    if current_user.role != 'teacher':
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        # Import and run scraper
        from services.resource_scraper import EducationalResourceScraper
        scraper = EducationalResourceScraper(app.config['RESOURCES_FOLDER'])
        result = scraper.run_full_scrape()
        
        # Update database with scraped resources
        update_database_from_scraper(scraper)
        
        return jsonify({
            'success': True,
            'message': 'Scraping completed successfully',
            'result': result
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def allowed_file(filename):
    """Check if file extension is allowed"""
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'epub'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def update_database_from_scraper(scraper):
    """Update database with resources from scraper metadata"""
    metadata = scraper.metadata
    
    for file_key, file_info in metadata.get('downloads', {}).items():
        # Check if resource already exists
        existing = Resource.query.filter_by(
            filename=file_info['filename'],
            grade=file_info['grade'],
            subject=file_info['subject'],
            resource_type=file_info['resource_type']
        ).first()
        
        if not existing:
            resource = Resource(
                filename=file_info['filename'],
                original_filename=file_info['filename'],
                file_path=os.path.join(scraper.base_dir, file_key.replace('/', os.sep)),
                grade=file_info['grade'],
                subject=file_info['subject'],
                resource_type=file_info['resource_type'],
                source=file_info['source'],
                source_url=file_info.get('url'),
                file_size=file_info['file_size'],
                file_hash=file_info['hash']
            )
            db.session.add(resource)
    
    db.session.commit()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
