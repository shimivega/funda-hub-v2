HEAD
# funda-hub
A full-featured educational platform for South African learners and teachers (Grades 1–12 + ABET), including textbooks, past exams, study tools, AI assistant, chat, quizzes, and multi-language support. Built with HTML, Tailwind CSS, and JavaScript.

# Funda App - South African Education Platform

A comprehensive education platform built for South African learners (Grades 1-12 + ABET) with automated resource management from trusted educational sources.

## 🌟 Features

### Core Features
- **User Authentication**: Role-based access for Teachers and Learners
- **Modern Dashboard**: Beautiful UI based on provided design template with light/dark mode
- **Interactive Quiz System**: Multi-subject quizzes (Math, Science, English) with scoring
- **AI Study Assistant**: Built-in chatbot for academic help and explanations
- **Support Center**: Comprehensive support for bullied learners with video call, messaging, and phone support
- **Educational Resources**: Automated scraping and management of textbooks, past exams, and study materials

### Resource Management System
- **Automated Scraping**: Weekly updates from trusted South African educational websites:
  - Siyavula (Open-source textbooks)
  - Department of Basic Education (Past exam papers)
  - WCED Portal (Western Cape resources)
  - Thutong Portal (National support materials)
- **Smart Categorization**: Automatic classification by Grade, Subject, and Resource Type
- **Admin Upload**: Manual resource upload with metadata management
- **Download Tracking**: Monitor resource usage and popularity

### Communication & Collaboration
- **Study Groups**: Create and join study groups with peers
- **WhatsApp-style Chat**: Real-time messaging with teachers and classmates
- **Virtual Classrooms**: Join online classes with video call integration
- **Profile Management**: Customizable profiles with study statistics

### Accessibility & Inclusivity
- **Multi-language Support**: English, isiZulu, Sesotho, Afrikaans
- **Accessibility Features**: Text-to-speech, high-contrast mode, adjustable font sizes
- **Mobile Responsive**: Works seamlessly on all devices

## 🛠️ Tech Stack

### Backend
- **Flask**: Python web framework
- **SQLAlchemy**: Database ORM
- **Flask-Login**: User session management
- **BeautifulSoup4**: Web scraping
- **Schedule**: Automated task scheduling

### Frontend
- **Tailwind CSS**: Modern utility-first CSS framework
- **Font Awesome**: Icon library
- **Vanilla JavaScript**: Interactive features and AJAX

### Database
- **SQLite**: Lightweight database for development
- **PostgreSQL**: Recommended for production

## 📁 Project Structure

```
funda-app/
├── app.py                      # Main Flask application
├── requirements.txt            # Python dependencies
├── init_services.py           # Initialization script
├── services/
│   ├── resource_scraper.py    # Educational resource scraper
│   └── scheduler.py           # Automated task scheduler
├── templates/                 # HTML templates
│   ├── base.html             # Base template
│   ├── dashboard.html        # Main dashboard
│   ├── login.html            # Login page
│   ├── register.html         # Registration page
│   ├── practice_zone.html    # Quiz system
│   ├── support_center.html   # Support center
│   ├── resources.html        # Resource browser
│   ├── admin_resources.html  # Admin resource management
│   ├── study_groups.html     # Study groups
│   ├── chat.html             # Messaging system
│   ├── classrooms.html       # Virtual classrooms
│   └── profile.html          # User profiles
├── resources/                # Downloaded educational resources
├── uploads/                  # User uploaded files
└── static/                   # Static assets (CSS, JS, images)
```

## 🚀 Installation & Setup

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

### Step 1: Install Python
If Python is not installed:
1. Download Python from [python.org](https://www.python.org/downloads/)
2. During installation, check "Add Python to PATH"
3. Verify installation: `python --version`

### Step 2: Install Dependencies
```bash
cd funda-app
pip install -r requirements.txt
```

### Step 3: Initialize the Application
```bash
python init_services.py
```

### Step 4: Run the Application
```bash
python app.py
```

### Step 5: Access the Application
Open your browser and navigate to: `http://localhost:5000`

## 📚 Usage Guide

### For Learners
1. **Register**: Create an account as a "Learner" and select your grade
2. **Dashboard**: Access all features from the main dashboard
3. **Practice Zone**: Take quizzes to test your knowledge
4. **Resources**: Browse and download textbooks, past exams, and study materials
5. **Study Groups**: Join or create study groups with classmates
6. **Support Center**: Get help if you're experiencing bullying or need support

### For Teachers
1. **Register**: Create an account as a "Teacher"
2. **Classrooms**: Create and manage virtual classrooms
3. **Resource Management**: Upload and manage educational resources
4. **Admin Panel**: Access `/admin/resources` for advanced resource management
5. **Update Resources**: Trigger manual scraping of educational websites

## 🔧 Admin Features

### Resource Management (`/admin/resources`)
- View all resources with statistics
- Upload new resources with metadata
- Trigger manual resource updates from external sources
- Monitor download statistics and usage

### Automated Resource Updates
- **Weekly Schedule**: Automatic scraping every Sunday at 2 AM
- **Daily Checks**: Quick checks for new exam papers every day at 6 AM
- **Manual Trigger**: Force immediate updates via admin panel

## 🛡️ Safety & Support Features

### Support Center
- **Emergency Contacts**: Direct links to emergency services and Childline
- **Video Call Support**: Connect with trained counselors
- **Live Chat**: Secure messaging with support staff
- **Anonymous Reporting**: Report bullying or abuse anonymously
- **Resource Library**: Self-help guides and inspirational content

### Privacy & Security
- All conversations are confidential
- Anonymous reporting protects user identity
- Secure file handling and download tracking
- Role-based access control

## 🌍 Educational Sources

The platform automatically pulls resources from:
- **Siyavula**: Open-source mathematics and science textbooks
- **Department of Basic Education**: Official curriculum and past exam papers
- **WCED Portal**: Western Cape Education Department resources
- **Thutong Portal**: National teacher and learner support materials

## 📱 Mobile Support

The application is fully responsive and works on:
- Desktop computers
- Tablets
- Smartphones
- All modern web browsers

## 🔮 Future Enhancements

- **Video Learning Library**: Embedded educational videos
- **AI-Powered Recommendations**: Personalized content suggestions
- **Offline Mode**: Download resources for offline study
- **Parent Portal**: Progress tracking for parents/guardians
- **Gamification**: Badges, leaderboards, and achievements
- **Career Guidance**: University and career path recommendations

## 🤝 Contributing

This is an open-source educational project. Contributions are welcome!

## 📄 License

This project is designed to support South African education and is freely available for educational use.

## 📞 Support

For technical support or educational partnerships, please contact the development team.

---

**Empowering South African Education Through Technology** 🇿🇦
>>>>>>> 9f6e0fc (Initial commit)
