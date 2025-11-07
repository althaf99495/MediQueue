# MediQueue - Smart Hospital Queue Management System

## Overview
MediQueue is a comprehensive hospital queue and appointment management platform built with Flask, PostgreSQL, and Redis. The system digitizes patient-doctor interactions, reduces waiting times, and provides real-time updates through a modern web interface.

## Recent Changes
- **2025-11-07**: Initial project setup
  - Created Flask application with role-based authentication (Admin, Doctor, Patient)
  - Implemented database models for Users, Departments, Appointments, Queue Entries, Medical Records, and Prescriptions
  - Built Redis-powered queue service for real-time queue management
  - Created responsive UI with Bootstrap 5 and medical-themed CSS (teal/blue palette)
  - Implemented doctor dashboard with live queue display and consultation features
  - Built patient portal with appointment booking and queue position tracking
  - Created admin dashboard with statistics and management features
  - Added PDF prescription generation capability
  - Implemented QR code check-in system for patients

## Project Architecture

### Tech Stack
- **Backend**: Flask 3.0.0, SQLAlchemy, Flask-Login, Flask-SocketIO
- **Database**: PostgreSQL (via DATABASE_URL environment variable)
- **Queue System**: Redis (with fallback for offline testing)
- **Frontend**: Bootstrap 5, Chart.js, Socket.IO
- **PDF Generation**: ReportLab
- **QR Codes**: qrcode library

### Directory Structure
```
mediqueue/
├── models/            # Database models (User, Department, Appointment, etc.)
├── routes/            # Flask blueprints (auth, doctor, patient, admin)
├── services/          # Business logic (queue_service.py for Redis operations)
├── templates/         # Jinja2 HTML templates
│   ├── auth/         # Login, registration pages
│   ├── doctor/       # Doctor dashboard and features
│   ├── patient/      # Patient portal
│   └── admin/        # Admin management pages
├── static/
│   ├── css/          # Custom CSS with medical theme
│   ├── js/           # JavaScript files
│   └── img/          # Images
├── app.py            # Main application entry point
├── config.py         # Configuration settings
└── requirements.txt  # Python dependencies

```

### Database Models
1. **User** - Stores admin, doctor, and patient information with role-based fields
2. **Department** - Hospital departments (Cardiology, Neurology, etc.)
3. **Appointment** - Scheduled and walk-in appointments
4. **QueueEntry** - Real-time queue tracking per doctor
5. **MedicalRecord** - Visit history with symptoms, diagnosis, notes
6. **Prescription** - Medications and instructions linked to medical records
7. **DoctorAvailability** - Doctor working hours and scheduling

### User Roles

#### Admin
- Dashboard with system statistics
- CRUD operations for doctors, patients, departments
- Queue monitoring and manual prioritization
- Analytics with charts and export capabilities

#### Doctor
- Live queue display with patient information
- Patient consultation interface
- Digital prescription generation (PDF download)
- Medical history access
- Personal queue analytics

#### Patient
- Book appointments (scheduled) or join walk-in queues
- View current queue position and estimated wait time
- Real-time queue notifications
- Medical history and prescription access
- QR code check-in for hospital kiosks

### Key Features

#### Queue Management
- Redis-powered queue system with high-speed operations
- Functions: enqueue, dequeue, get_position, get_queue, reorder_queue
- Department-based queue separation
- Priority queue support for emergencies
- Estimated wait time calculations based on doctor consultation averages

#### Real-Time Updates
- Flask-SocketIO for WebSocket connections
- Live queue position updates
- Turn notifications for patients

#### Security
- Session-based authentication with Flask-Login
- Password hashing with Werkzeug
- CSRF protection with Flask-WTF
- Role-based access control

## User Preferences
- Clean, modern medical design with calming blue/teal color palette
- Bootstrap 5 for responsive layouts
- Card-based UI components with subtle shadows
- Real-time features for better user experience

## Initial Setup

### Creating the First Admin Account

**Option 1: Using the Web Interface (Recommended)**
1. Start the application
2. Visit `/setup` in your browser
3. Fill in the admin details (name, email, password)
4. Submit the form
5. Log in with your new admin account

**Option 2: Using Environment Variables**
Set the following environment variables before starting the app:
- `ADMIN_EMAIL` - Admin email address
- `ADMIN_PASSWORD` - Admin password (minimum 8 characters)

The admin account will be created automatically on first run.

**Security Note**: The `/setup` route is only accessible when no admin accounts exist. Once an admin is created, the route redirects to the home page.

## Environment Variables
- `DATABASE_URL` - PostgreSQL connection string
- `SESSION_SECRET` - Flask session secret key
- `REDIS_URL` - Redis connection URL (defaults to localhost:6379)

## Development Notes
- The application runs on port 5000 with SocketIO/eventlet
- Database tables are auto-created on first run
- Default admin account is created automatically
- Redis queue service has fallback handling for offline development

## Next Steps / Future Enhancements
- SMS/Email notifications for appointment reminders
- Public lobby display for queue status
- Patient feedback forms after visits
- Advanced analytics with exportable reports
- Multilingual support
- API endpoints for mobile app integration
