# KaziBuddy – Django Backend

**KaziBuddy** is a web-based platform that connects semi-skilled workers with potential employers. It allows users to register as either a worker or an employer, post jobs, apply for assignments, manage payments, track job progress, and build a reliable rating and review system.

---

## 📦 Project Structure

kazi_buddy/
├── accounts/ # User registration, authentication, OTP
├── workers/ # Worker profiles, availability, skills
├── employers/ # Employer profiles, verification
├── jobs/ # Job postings, filters, listings
├── applications/ # Job applications, statuses
├── assignments/ # Assignment lifecycle, tracking
├── payments/ # Escrow and transaction handling
├── ratings/ # Reviews and reputation scores
├── adminpanel/ # Admin-level controls and approval
├── notifications/ # Real-time updates & alerts
├── messaging/ # In-app chat (optional/future)
├── learning/ # Training and financial literacy (optional/future)
├── analytics/ # Usage analytics (optional/future)
├── utils/ # Shared services (OTP, validators, etc.)
├── manage.py
└── kazi_buddy/ # Core settings and routing


---

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

1. **Clone the repo:**
   ```bash
   git clone https://github.com/yourusername/kazibuddy-backend.git
   cd kazibuddy-backend
