from app import app, db, User
from werkzeug.security import generate_password_hash
from datetime import datetime

def create_admin_user():
    with app.app_context():
        # Check if admin user already exists
        admin = User.query.filter_by(email='admin').first()
        
        if not admin:
            # Create admin user
            admin_user = User(
                full_name='Administrator',
                email='admin',
                phone='0000000000',
                password_hash=generate_password_hash('admin12345', method='pbkdf2:sha256'),
                role='admin',
                is_online=True,
                created_at=datetime.utcnow()
            )
            
            db.session.add(admin_user)
            db.session.commit()
            print("Admin user created successfully!")
            print("Username: admin")
            print("Password: admin12345")
        else:
            # Update admin password if user exists
            admin.password_hash = generate_password_hash('admin12345', method='pbkdf2:sha256')
            db.session.commit()
            print("Admin password has been reset!")
            print("Username: admin")
            print("Password: admin12345")

if __name__ == '__main__':
    create_admin_user()
