# KaziBuddy – Django Backend

**KaziBuddy** is a web-based platform that connects semi-skilled workers with potential employers. It allows users to register as either a worker or an employer, post jobs, apply for assignments, manage payments, track job progress, and build a reliable rating and review system.

---

## 📦 Project Structure

apps:
  accounts: Handles user authentication, registration, OTP, and core user model
  workers: Manages worker-specific profiles, skills, availability, and ID verification
  employers: Manages employer profiles, verification documents, and contact info
  jobs: Handles job creation, listing, and filtering by employers
  applications: Manages job applications submitted by workers
  assignments: Tracks the lifecycle of job assignments including progress and check-ins
  ratings: Manages post-job reviews and reputation scoring for users
  adminpanel: Provides admin features for approving/rejecting users and content
  analytics: Tracks usage, skills demand, and regional trends for admins
  utils: Shared utility functions like OTP generation, validation, and file uploads


## 🚀 Features

- User registration via phone/email with OTP verification
- Worker and employer profiles with document validation
- Job posting and worker application system
- Assignment lifecycle tracking (check-ins, updates, etc.)
- Secure in-app payment with escrow
- Ratings and review system post-completion
- Admin dashboard for vetting and analytics
- Optional: In-app messaging, learning modules, referrals

---

## 🔧 Tech Stack

- **Backend Framework:** Django & Django REST Framework  
- **Authentication:** Custom JWT (djangorestframework-simplejwt)  
- **Database:** PostgreSQL  
- **Messaging & Notifications:** Optional channels / Celery (future)  
- **Deployment:** Docker (optional), Render/Heroku/AWS  
- **CI/CD:** GitHub Actions (optional)

---

## 🛠️ Setup Instructions

project_setup:
  description: Setup guide for the KaziBuddy Django backend project

  prerequisites:
    - Python 3.8+
    - Git
    - PostgreSQL
    - pip

  steps:
    - step: Clone the project
      command: git clone https://github.com/yourusername/kazibuddy-backend.git

    - step: Navigate to the project directory
      command: cd kazibuddy-backend

    - step: Create a virtual environment
      command: python -m venv venv

    - step: Activate the virtual environment (Linux/macOS)
      command: source venv/bin/activate

    - step: Activate the virtual environment (Windows)
      command: venv\Scripts\activate

    - step: Upgrade pip
      command: pip install --upgrade pip

    - step: Install required packages
      command: pip install -r requirements.txt

    - step: Create .env file and set environment variables
      example:
        SECRET_KEY: your-django-secret-key
        DEBUG: "True"
        DATABASE_URL: postgres://user:password@localhost:5432/kazibuddy

    - step: Apply database migrations
      command: python manage.py migrate

    - step: Create superuser (optional)
      command: python manage.py createsuperuser

    - step: Run the development server
      command: python manage.py runserver

    - step: Access the application
      url: http://127.0.0.1:8000/

    - step: Access API documentation (if using drf-yasg)
      url: http://127.0.0.1:8000/docs/
