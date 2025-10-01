from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, TextAreaField, DateField, FloatField, IntegerField, BooleanField
from wtforms.validators import DataRequired, Email, Length, Optional, NumberRange
from datetime import date

def int_or_none(value):
    if value == '' or value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    password = PasswordField('Password', validators=[DataRequired()])

class UserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=50)])
    phone = StringField('Phone', validators=[Optional(), Length(max=20)])
    role = SelectField('Role', choices=[('admin', 'Admin'), ('doctor', 'Doctor'), ('receptionist', 'Receptionist')], validators=[DataRequired()])
    is_active = BooleanField('Active')
    password = PasswordField('Password', validators=[Optional(), Length(min=6)])

class PatientForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=50)])
    date_of_birth = DateField('Date of Birth', validators=[DataRequired()])
    gender = SelectField('Gender', choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')], validators=[DataRequired()])
    phone = StringField('Phone', validators=[DataRequired(), Length(max=20)])
    email = StringField('Email', validators=[Optional(), Email()])
    address = TextAreaField('Address', validators=[Optional()])
    emergency_contact = StringField('Emergency Contact', validators=[Optional(), Length(max=100)])
    emergency_phone = StringField('Emergency Phone', validators=[Optional(), Length(max=20)])
    blood_type = SelectField('Blood Type', choices=[('', '-- Select --'), ('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'), ('AB+', 'AB+'), ('AB-', 'AB-'), ('O+', 'O+'), ('O-', 'O-')], validators=[Optional()])
    allergies = TextAreaField('Allergies', validators=[Optional()])
    medical_history = TextAreaField('Medical History', validators=[Optional()])
    insurance_info = StringField('Insurance Information', validators=[Optional(), Length(max=100)])

class QueueForm(FlaskForm):
    patient_id = SelectField('Patient', coerce=int, validators=[DataRequired()])
    doctor_id = SelectField('Doctor', coerce=int_or_none, validators=[Optional()])
    priority = SelectField('Priority', choices=[('normal', 'Normal'), ('high', 'High'), ('urgent', 'Urgent')], default='normal', validators=[DataRequired()])
    appointment_type = StringField('Appointment Type', default='consultation', validators=[DataRequired(), Length(max=50)])
    notes = TextAreaField('Notes', validators=[Optional()])
    estimated_time = IntegerField('Estimated Time (minutes)', validators=[Optional(), NumberRange(min=1, max=300)])

class PaymentForm(FlaskForm):
    patient_id = SelectField('Patient', coerce=int, validators=[DataRequired()])
    doctor_id = SelectField('Doctor', coerce=int_or_none, validators=[Optional()])
    amount = FloatField('Amount', validators=[DataRequired(), NumberRange(min=0.01)])
    payment_method = SelectField('Payment Method', choices=[('cash', 'Cash'), ('card', 'Card'), ('insurance', 'Insurance'), ('other', 'Other')], validators=[DataRequired()])
    payment_type = StringField('Payment Type', default='consultation', validators=[DataRequired(), Length(max=50)])
    description = TextAreaField('Description', validators=[Optional()])
    discount = FloatField('Discount', default=0.0, validators=[Optional(), NumberRange(min=0)])
    tax_amount = FloatField('Tax Amount', default=0.0, validators=[Optional(), NumberRange(min=0)])

class PrescriptionForm(FlaskForm):
    patient_id = SelectField('Patient', coerce=int, validators=[DataRequired()])
    diagnosis = TextAreaField('Diagnosis', validators=[DataRequired()])
    symptoms = TextAreaField('Symptoms', validators=[Optional()])
    medications = TextAreaField('Medications', validators=[DataRequired()])
    dosage_instructions = TextAreaField('Dosage Instructions', validators=[DataRequired()])
    duration = StringField('Duration', validators=[Optional(), Length(max=50)])
    special_instructions = TextAreaField('Special Instructions', validators=[Optional()])
    follow_up_date = DateField('Follow-up Date', validators=[Optional()])
    follow_up_notes = TextAreaField('Follow-up Notes', validators=[Optional()])
    lab_tests = TextAreaField('Lab Tests', validators=[Optional()])
    referrals = TextAreaField('Referrals', validators=[Optional()])

class DoctorForm(FlaskForm):
    license_number = StringField('License Number', validators=[DataRequired(), Length(max=50)])
    specialization = StringField('Specialization', validators=[DataRequired(), Length(max=100)])
    qualification = StringField('Qualification', validators=[Optional(), Length(max=200)])
    experience_years = IntegerField('Experience (Years)', default=0, validators=[Optional(), NumberRange(min=0, max=50)])
    consultation_fee = FloatField('Consultation Fee', default=0.0, validators=[Optional(), NumberRange(min=0)])
    availability_status = SelectField('Availability Status', choices=[('available', 'Available'), ('busy', 'Busy'), ('offline', 'Offline')], default='available', validators=[DataRequired()])
    schedule = TextAreaField('Schedule', validators=[Optional()])