# MediQueue - Clinic Management System

## Overview

MediQueue is a comprehensive web-based clinic management system built with Flask that handles patient registration, queue management, and medical workflows. The application serves different user roles (admin, doctor, receptionist) with specialized dashboards and functionalities. It includes features for patient management, appointment scheduling, prescription handling, payment processing, and AI-powered queue prediction. The system is designed for small to medium-sized medical clinics to streamline their operations and improve patient flow management.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Framework
- **Flask-based Architecture**: Uses Flask as the core web framework with a modular blueprint structure
- **Application Factory Pattern**: Centralized app creation in `app.py` with configuration management
- **Database Abstraction**: SQLAlchemy ORM for database operations with Flask-Migrate for schema management

### Database Design
- **SQLite Database**: Local file-based database (`mediqueue.db`) for simplicity and portability
- **Relational Schema**: Six main entities (User, Doctor, Patient, Queue, Payment, Prescription) with proper foreign key relationships
- **Connection Management**: Connection pooling and health checks configured for reliability

### Authentication & Authorization
- **Flask-Login**: Session-based authentication with user role management
- **Password Security**: Werkzeug password hashing for secure credential storage
- **Role-based Access Control**: Decorator-based authorization with three main roles (admin, doctor, receptionist)

### Application Structure
- **Blueprint Organization**: Modular route organization with separate blueprints for each user role
- **Form Handling**: Flask-WTF for form validation and CSRF protection
- **Template System**: Jinja2 templating with Bootstrap 5 for responsive UI

### AI Integration
- **Queue Prediction Module**: scikit-learn based linear regression model for wait time prediction
- **Data Analysis**: Pandas integration for processing queue and patient flow data
- **Model Persistence**: Pickle-based model storage for trained algorithms

### Reporting System
- **PDF Generation**: ReportLab integration for generating patient reports and receipts
- **Data Export**: Pandas-powered data analysis and export capabilities
- **Real-time Metrics**: Dashboard statistics with live queue monitoring

## External Dependencies

### Core Framework Dependencies
- **Flask**: Web framework with extensions (SQLAlchemy, Login, Migrate, WTF)
- **Werkzeug**: WSGI utilities and security features
- **Waitress**: Production WSGI server for deployment

### Database & ORM
- **SQLite**: Embedded database engine (no external server required)
- **SQLAlchemy**: Database ORM and query builder
- **Flask-Migrate**: Database schema migration management

### UI & Frontend
- **Bootstrap 5**: CSS framework via CDN for responsive design
- **Font Awesome**: Icon library via CDN for UI elements
- **Jinja2**: Template engine (included with Flask)

### Data Processing & AI
- **Pandas**: Data manipulation and analysis library
- **scikit-learn**: Machine learning library for queue prediction models
- **NumPy**: Numerical computing support (scikit-learn dependency)

### Document Generation
- **ReportLab**: PDF generation for reports and receipts

### Security & Forms
- **Flask-WTF**: Form handling with CSRF protection
- **Flask-Login**: User session management and authentication

### Production Deployment
- **ProxyFix**: Werkzeug middleware for handling reverse proxy headers
- **Waitress**: Production-ready WSGI server (alternative to development server)