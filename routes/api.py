from flask import request, jsonify, current_app
from flask_login import login_required, current_user
from flask_restx import Namespace, Resource, fields, reqparse
from functools import wraps
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
import os
import json
from datetime import datetime

from extensions import api
from models import (
    db, User, Appointment, QueueEntry, MedicalRecord, 
    Prescription, Department, DoctorAvailability, Report
)
from services import QueueService

# Initialize queue service
queue_service = QueueService()

# Create namespaces
auth_ns = Namespace('auth', description='Authentication operations')
doctor_ns = Namespace('doctors', description='Doctor operations')
patient_ns = Namespace('patients', description='Patient operations')
appointment_ns = Namespace('appointments', description='Appointment operations')
prescription_ns = Namespace('prescriptions', description='Prescription operations')
medical_record_ns = Namespace('medical-records', description='Medical records operations')
queue_ns = Namespace('queue', description='Queue management operations')

# Helper function for role-based access
def doctor_required_api(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_doctor():
            return {'message': 'Access denied. Doctor privileges required.'}, 403
        return f(*args, **kwargs)
    return decorated_function

def patient_required_api(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_patient():
            return {'message': 'Access denied. Patient privileges required.'}, 403
        return f(*args, **kwargs)
    return decorated_function

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

# Define models for API documentation
patient_model = api.model('Patient', {
    'id': fields.Integer(description='Patient ID'),
    'full_name': fields.String(description='Patient full name'),
    'email': fields.String(description='Patient email'),
    'phone': fields.String(description='Patient phone'),
    'age': fields.Integer(description='Patient age'),
    'gender': fields.String(description='Patient gender'),
    'blood_group': fields.String(description='Blood group'),
    'address': fields.String(description='Address'),
})

prescription_model = api.model('Prescription', {
    'id': fields.Integer(description='Prescription ID'),
    'patient_id': fields.Integer(description='Patient ID'),
    'doctor_id': fields.Integer(description='Doctor ID'),
    'medications': fields.Raw(description='Medications list (JSON)'),
    'instructions': fields.String(description='Instructions'),
    'created_at': fields.DateTime(description='Creation date'),
})

prescription_create_model = api.model('PrescriptionCreate', {
    'patient_id': fields.Integer(required=True, description='Patient ID'),
    'medications': fields.Raw(required=True, description='Medications list (JSON array)'),
    'instructions': fields.String(description='Instructions'),
    'symptoms': fields.String(required=True, description='Symptoms'),
    'diagnosis': fields.String(required=True, description='Diagnosis'),
    'notes': fields.String(description='Additional notes'),
})

medical_record_model = api.model('MedicalRecord', {
    'id': fields.Integer(description='Medical record ID'),
    'patient_id': fields.Integer(description='Patient ID'),
    'doctor_id': fields.Integer(description='Doctor ID'),
    'symptoms': fields.String(description='Symptoms'),
    'diagnosis': fields.String(description='Diagnosis'),
    'notes': fields.String(description='Notes'),
    'visit_date': fields.DateTime(description='Visit date'),
    'report_file': fields.String(description='Report file name'),
})

# Upload parser for file uploads
upload_parser = api.parser()
upload_parser.add_argument('report', location='files', type=FileStorage, required=False, help='Medical report file')
upload_parser.add_argument('symptoms', type=str, required=True, help='Symptoms')
upload_parser.add_argument('diagnosis', type=str, required=True, help='Diagnosis')
upload_parser.add_argument('notes', type=str, required=False, help='Additional notes')
upload_parser.add_argument('medications', type=str, required=False, help='Medications JSON array')
upload_parser.add_argument('instructions', type=str, required=False, help='Prescription instructions')

# ==================== AUTHENTICATION API ENDPOINTS ====================

@auth_ns.route('/login')
class Login(Resource):
    @api.doc(description='Login endpoint (Note: This is a placeholder. Use web login for now)')
    def post(self):
        """Login endpoint - Use web login interface"""
        return {
            'message': 'Please use the web login interface at /login',
            'note': 'API authentication will be implemented with token-based auth'
        }, 200

@auth_ns.route('/status')
class AuthStatus(Resource):
    @login_required
    @api.doc(security='Bearer')
    def get(self):
        """Get current user authentication status"""
        return {
            'success': True,
            'authenticated': True,
            'user': {
                'id': current_user.id,
                'email': current_user.email,
                'full_name': current_user.full_name,
                'role': current_user.role
            }
        }, 200

# ==================== DOCTOR API ENDPOINTS ====================

@doctor_ns.route('/select-patient')
class SelectPatient(Resource):
    @login_required
    @doctor_required_api
    @api.doc(security='Bearer')
    @api.param('search', 'Search by name, email, or phone')
    def get(self):
        """Search and select patients"""
        search = request.args.get('search', '')
        patients = []
        
        if search:
            patients = User.query.filter(
                User.role == 'patient',
                db.or_(
                    User.full_name.ilike(f'%{search}%'),
                    User.email.ilike(f'%{search}%'),
                    User.phone.ilike(f'%{search}%')
                )
            ).limit(50).all()
        else:
            # Show recent patients
            appointment_patient_ids = db.session.query(Appointment.patient_id).filter(
                Appointment.doctor_id == current_user.id
            ).distinct().all()
            
            record_patient_ids = db.session.query(MedicalRecord.patient_id).filter(
                MedicalRecord.doctor_id == current_user.id
            ).distinct().all()
            
            patient_ids = set()
            for pid_tuple in appointment_patient_ids:
                patient_ids.add(pid_tuple[0])
            for pid_tuple in record_patient_ids:
                patient_ids.add(pid_tuple[0])
            
            if patient_ids:
                patients = User.query.filter(
                    User.id.in_(list(patient_ids)),
                    User.role == 'patient'
                ).limit(20).all()
        
        return {
            'success': True,
            'patients': [{
                'id': p.id,
                'full_name': p.full_name,
                'email': p.email,
                'phone': p.phone or '',
                'age': p.age,
                'gender': p.gender or '',
                'blood_group': p.blood_group or ''
            } for p in patients]
        }, 200

@doctor_ns.route('/patient/<int:patient_id>')
class GetPatientDetails(Resource):
    @login_required
    @doctor_required_api
    @api.doc(security='Bearer')
    def get(self, patient_id):
        """Get patient details"""
        patient = User.query.get_or_404(patient_id)
        if patient.role != 'patient':
            return {'message': 'Invalid patient ID'}, 404
        
        medical_records = MedicalRecord.query.filter_by(
            patient_id=patient_id
        ).order_by(MedicalRecord.visit_date.desc()).all()
        
        return {
            'success': True,
            'patient': {
                'id': patient.id,
                'full_name': patient.full_name,
                'email': patient.email,
                'phone': patient.phone or '',
                'age': patient.age,
                'gender': patient.gender or '',
                'blood_group': patient.blood_group or '',
                'address': patient.address or '',
                'emergency_contact': patient.emergency_contact or ''
            },
            'medical_records': [{
                'id': mr.id,
                'visit_date': mr.visit_date.isoformat(),
                'symptoms': mr.symptoms or '',
                'diagnosis': mr.diagnosis or '',
                'notes': mr.notes or '',
                'doctor_name': mr.doctor.full_name,
                'report_file': mr.report_file or ''
            } for mr in medical_records]
        }, 200

@doctor_ns.route('/patient/<int:patient_id>/add-prescription-report')
class AddPrescriptionReport(Resource):
    @login_required
    @doctor_required_api
    @api.doc(security='Bearer')
    @api.expect(upload_parser)
    def post(self, patient_id):
        """Add prescription details and medical report for a patient"""
        patient = User.query.get_or_404(patient_id)
        if patient.role != 'patient':
            return {'message': 'Invalid patient ID'}, 404
        
        args = upload_parser.parse_args()
        
        # Get form data
        symptoms = args.get('symptoms')
        diagnosis = args.get('diagnosis')
        notes = args.get('notes', '')
        medications_json = args.get('medications', '[]')
        instructions = args.get('instructions', '')
        report_file = args.get('report')
        
        # Validate required fields
        if not symptoms or not diagnosis:
            return {'message': 'Symptoms and diagnosis are required'}, 400
        
        # Handle file upload
        report_filename = None
        if report_file and allowed_file(report_file.filename):
            report_filename = secure_filename(report_file.filename)
            upload_folder = current_app.config['UPLOAD_FOLDER']
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
            report_file.save(os.path.join(upload_folder, report_filename))
        
        # Create medical record
        medical_record = MedicalRecord(
            patient_id=patient_id,
            doctor_id=current_user.id,
            symptoms=symptoms,
            diagnosis=diagnosis,
            notes=notes,
            report_file=report_filename
        )
        db.session.add(medical_record)
        db.session.flush()
        
        # Create prescription if medications provided
        prescription = None
        if medications_json:
            try:
                medications = json.loads(medications_json)
                if medications and len(medications) > 0:
                    prescription = Prescription(
                        medical_record_id=medical_record.id,
                        patient_id=patient_id,
                        doctor_id=current_user.id,
                        medications=medications,
                        instructions=instructions
                    )
                    db.session.add(prescription)
            except json.JSONDecodeError:
                return {'message': 'Invalid medications JSON format'}, 400
        
        db.session.commit()
        
        return {
            'success': True,
            'message': 'Prescription and report added successfully',
            'medical_record_id': medical_record.id,
            'prescription_id': prescription.id if prescription else None,
            'report_file': report_filename
        }, 201

@doctor_ns.route('/prescriptions')
class GetDoctorPrescriptions(Resource):
    @login_required
    @doctor_required_api
    @api.doc(security='Bearer')
    def get(self):
        """Get all prescriptions created by the doctor"""
        prescriptions = Prescription.query.filter_by(
            doctor_id=current_user.id
        ).order_by(Prescription.created_at.desc()).all()
        
        return {
            'success': True,
            'prescriptions': [{
                'id': p.id,
                'patient_id': p.patient_id,
                'patient_name': p.patient.full_name,
                'medications': p.medications,
                'instructions': p.instructions or '',
                'created_at': p.created_at.isoformat()
            } for p in prescriptions]
        }, 200

@doctor_ns.route('/dashboard')
class DoctorDashboard(Resource):
    @login_required
    @doctor_required_api
    @api.doc(security='Bearer')
    def get(self):
        """Get doctor dashboard data"""
        queue_list = queue_service.get_queue(current_user.id)
        
        today = datetime.utcnow().date()
        appointments_today = Appointment.query.filter(
            Appointment.doctor_id == current_user.id,
            db.func.date(Appointment.appointment_date) == today
        ).all()
        
        patients_served_today = QueueEntry.query.filter(
            QueueEntry.doctor_id == current_user.id,
            QueueEntry.status == 'completed',
            db.func.date(QueueEntry.completed_at) == today
        ).count()
        
        active_queue_entries = []
        for queue_item in queue_list:
            patient = User.query.get(queue_item['patient_id'])
            if patient:
                queue_item['patient'] = {
                    'id': patient.id,
                    'full_name': patient.full_name,
                    'email': patient.email,
                    'phone': patient.phone or ''
                }
                active_queue_entries.append(queue_item)
        
        return {
            'success': True,
            'queue': active_queue_entries,
            'queue_length': len(queue_list),
            'appointments_today': [{
                'id': apt.id,
                'patient_id': apt.patient_id,
                'patient_name': apt.patient.full_name,
                'appointment_date': apt.appointment_date.isoformat(),
                'status': apt.status
            } for apt in appointments_today],
            'patients_served_today': patients_served_today
        }, 200

# ==================== PATIENT API ENDPOINTS ====================

@patient_ns.route('/prescriptions')
class GetPatientPrescriptions(Resource):
    @login_required
    @patient_required_api
    @api.doc(security='Bearer')
    def get(self):
        """Get all prescriptions for the logged-in patient"""
        prescriptions = Prescription.query.filter_by(
            patient_id=current_user.id
        ).order_by(Prescription.created_at.desc()).all()
        
        return {
            'success': True,
            'prescriptions': [{
                'id': p.id,
                'doctor_id': p.doctor_id,
                'doctor_name': p.doctor.full_name,
                'medications': p.medications,
                'instructions': p.instructions or '',
                'created_at': p.created_at.isoformat()
            } for p in prescriptions]
        }, 200

@patient_ns.route('/medical-records')
class GetPatientMedicalRecords(Resource):
    @login_required
    @patient_required_api
    @api.doc(security='Bearer')
    def get(self):
        """Get all medical records for the logged-in patient"""
        medical_records = MedicalRecord.query.filter_by(
            patient_id=current_user.id
        ).order_by(MedicalRecord.visit_date.desc()).all()
        
        return {
            'success': True,
            'medical_records': [{
                'id': mr.id,
                'doctor_id': mr.doctor_id,
                'doctor_name': mr.doctor.full_name,
                'symptoms': mr.symptoms or '',
                'diagnosis': mr.diagnosis or '',
                'notes': mr.notes or '',
                'visit_date': mr.visit_date.isoformat(),
                'report_file': mr.report_file or ''
            } for mr in medical_records]
        }, 200

@patient_ns.route('/dashboard')
class PatientDashboard(Resource):
    @login_required
    @patient_required_api
    @api.doc(security='Bearer')
    def get(self):
        """Get patient dashboard data"""
        # Get upcoming appointments
        upcoming_appointments = Appointment.query.filter(
            Appointment.patient_id == current_user.id,
            Appointment.appointment_date >= datetime.utcnow()
        ).order_by(Appointment.appointment_date.asc()).limit(5).all()
        
        # Get queue position
        queue_position = queue_service.get_position(current_user.id)
        
        return {
            'success': True,
            'upcoming_appointments': [{
                'id': apt.id,
                'doctor_id': apt.doctor_id,
                'doctor_name': apt.doctor.full_name,
                'appointment_date': apt.appointment_date.isoformat(),
                'status': apt.status
            } for apt in upcoming_appointments],
            'queue_position': queue_position
        }, 200

# ==================== PRESCRIPTION API ENDPOINTS ====================

@prescription_ns.route('/<int:prescription_id>')
class GetPrescription(Resource):
    @login_required
    @api.doc(security='Bearer')
    def get(self, prescription_id):
        """Get prescription details"""
        prescription = Prescription.query.get_or_404(prescription_id)
        
        # Check access
        if current_user.id not in [prescription.patient_id, prescription.doctor_id]:
            if not current_user.is_admin():
                return {'message': 'Access denied'}, 403
        
        return {
            'success': True,
            'prescription': {
                'id': prescription.id,
                'patient_id': prescription.patient_id,
                'patient_name': prescription.patient.full_name,
                'doctor_id': prescription.doctor_id,
                'doctor_name': prescription.doctor.full_name,
                'medications': prescription.medications,
                'instructions': prescription.instructions or '',
                'created_at': prescription.created_at.isoformat()
            }
        }, 200

# ==================== MEDICAL RECORD API ENDPOINTS ====================

@medical_record_ns.route('/<int:record_id>')
class GetMedicalRecord(Resource):
    @login_required
    @api.doc(security='Bearer')
    def get(self, record_id):
        """Get medical record details"""
        medical_record = MedicalRecord.query.get_or_404(record_id)
        
        # Check access
        if current_user.id not in [medical_record.patient_id, medical_record.doctor_id]:
            if not current_user.is_admin():
                return {'message': 'Access denied'}, 403
        
        return {
            'success': True,
            'medical_record': {
                'id': medical_record.id,
                'patient_id': medical_record.patient_id,
                'patient_name': medical_record.patient.full_name,
                'doctor_id': medical_record.doctor_id,
                'doctor_name': medical_record.doctor.full_name,
                'symptoms': medical_record.symptoms or '',
                'diagnosis': medical_record.diagnosis or '',
                'notes': medical_record.notes or '',
                'visit_date': medical_record.visit_date.isoformat(),
                'report_file': medical_record.report_file or ''
            }
        }, 200

# ==================== QUEUE API ENDPOINTS ====================

@queue_ns.route('/status')
class QueueStatus(Resource):
    @login_required
    @api.doc(security='Bearer')
    def get(self):
        """Get queue status for current user"""
        if current_user.is_patient():
            position = queue_service.get_position(current_user.id)
            return {
                'success': True,
                'user_type': 'patient',
                'position': position
            }, 200
        elif current_user.is_doctor():
            queue_list = queue_service.get_queue(current_user.id)
            return {
                'success': True,
                'user_type': 'doctor',
                'queue': queue_list,
                'queue_length': len(queue_list)
            }, 200
        else:
            return {'message': 'Invalid user type'}, 400

@queue_ns.route('/status/<int:ticket_id>')
class QueueTicketStatus(Resource):
    @login_required
    @api.doc(security='Bearer')
    def get(self, ticket_id):
        """Get status of a specific queue ticket"""
        ticket = QueueEntry.query.get(ticket_id)
        if not ticket:
            return {'message': 'Ticket not found', 'status': 'deleted'}, 404
        
        # Get real-time position from service
        position_info = queue_service.get_position(ticket.patient_id)
        
        current_position = None
        estimated_wait = 0
        
        if position_info and position_info['doctor_id'] == ticket.doctor_id:
            current_position = position_info['position']
            # Calculate estimated wait
            doctor = User.query.get(ticket.doctor_id)
            avg_time = doctor.avg_consultation_time if doctor else 15
            estimated_wait = (current_position - 1) * avg_time
        
        return {
            'success': True,
            'id': ticket.id,
            'status': ticket.status,
            'position': current_position,
            'estimated_wait': estimated_wait
        }, 200

# Register namespaces
api.add_namespace(auth_ns)
api.add_namespace(doctor_ns)
api.add_namespace(patient_ns)
api.add_namespace(appointment_ns)
api.add_namespace(prescription_ns)
api.add_namespace(medical_record_ns)
api.add_namespace(queue_ns)

