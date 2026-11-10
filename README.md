# ConnectSphere

A Django-based social networking platform built as part of the CodeAlpha Full Stack Development Internship.

ConnectSphere allows users to create profiles, share posts, interact with other users, and communicate through private messaging — all within a premium dark-themed interface.

## Features

### User Authentication
- User registration and login
- Secure password-based authentication
- Custom Django User model
- Profile creation during registration

### User Profiles
- Customizable profile information
- Profile picture upload
- Bio and website fields
- Edit profile functionality
- Followers and following lists

### Social Feed
- Create posts with captions and images
- View posts from followed users
- Edit and delete your own posts
- Like and unlike posts
- Add comments to posts

### User Discovery
- Search users by username and name
- View discovered user profiles
- Follow and unfollow users

### Direct Messaging
- Private one-to-one conversations
- Text messages
- Image and video attachments
- Read status tracking
- Conversation inbox

### Security and Validation
- Django authentication and CSRF protection
- Access restrictions for private conversations
- Server-side form validation
- Image and attachment validation
- Upload size and format restrictions
- Protected post and profile operations

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Backend programming |
| Django | Web framework |
| HTML5 | Page structure |
| CSS3 | Styling and responsive interface |
| JavaScript | Frontend interactions |
| SQLite | Database |
| Pillow | Image processing and validation |
| Git & GitHub | Version control |

## Project Structure

```text
CodeAlpha_ConnectSphere/
│
├── accounts/
│   ├── migrations/
│   ├── admin.py
│   ├── forms.py
│   ├── models.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
│
├── config/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── messaging/
│   ├── migrations/
│   ├── admin.py
│   ├── forms.py
│   ├── models.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
│
├── social/
│   ├── migrations/
│   ├── admin.py
│   ├── forms.py
│   ├── models.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
│
├── static/
│   └── css/
│       └── style.css
│
├── templates/
│   ├── accounts/
│   ├── messaging/
│   └── social/
│
├── .gitignore
├── manage.py
├── requirements.txt
└── README.md
```

## Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/ritikchoudhary847/CodeAlpha_ConnectSphere.git
cd CodeAlpha_ConnectSphere
```

### 2. Create a virtual environment

Windows PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
pip install -r requirements.txt
```

### 4. Configure the Django secret key

Set a secret key in your environment. Do not commit the actual key to GitHub.

```powershell
$env:DJANGO_SECRET_KEY = "your-secret-key"
```

For a persistent Windows user environment variable, configure `DJANGO_SECRET_KEY` through Windows environment variables.

### 5. Apply database migrations

```powershell
python manage.py migrate
```

### 6. Create an administrator account

```powershell
python manage.py createsuperuser
```

### 7. Start the development server

```powershell
python manage.py runserver
```

Open the application at:

```text
http://127.0.0.1:8000/
```

Django administration:

```text
http://127.0.0.1:8000/admin/
```

## Running Tests

Run the application checks:

```powershell
python manage.py check
```

Run all application tests:

```powershell
python manage.py test accounts social messaging --verbosity 1
```

The current development test suite has successfully passed **49 automated tests**.

## Development Configuration

- Database: SQLite
- Email backend: Django console email backend
- Media files: Local development storage
- Static files: Django static files
- Time zone: Asia/Kolkata

These settings are intended for local development. Production deployment requires separate configuration for environment variables, allowed hosts, HTTPS, email delivery, static files, and media storage.

## Internship Project

**Program:** CodeAlpha Full Stack Development Internship
**Project:** ConnectSphere — Social Networking Platform
**Backend:** Python and Django
**Frontend:** HTML, CSS and JavaScript

## Author

**Ritik Choudhary**

GitHub: [ritikchoudhary847](https://github.com/ritikchoudhary847)

---

*Built with Django as a full-stack web development project.*
