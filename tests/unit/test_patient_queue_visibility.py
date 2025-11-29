"""
Unit Test for Patient Queue Visibility
Verifies that the queue status is visible on the patient dashboard.
"""
import pytest
from models import db, User, QueueEntry, DoctorAvailability
from services import QueueService
from datetime import datetime

class TestPatientQueueVisibility:
    """Test case for queue visibility on patient dashboard."""

    def test_dashboard_shows_queue_info(self, test_app, authenticated_patient, doctor_user):
        """
        Test that the patient dashboard displays queue information
        when the patient is in a queue.
        """
        with test_app.app_context():
            # Ensure doctor is a doctor role
            if doctor_user.role != 'doctor':
                doctor_user.role = 'doctor'
                db.session.commit()

            # Get the patient user from the authenticated session
            # We need to query it within the app context to get the ID
            patient = User.query.filter_by(email='patient@test.com').first()
            
            # Add patient to queue manually (simulating join_queue)
            queue_service = QueueService()
            
            # Create DB entry
            queue_entry = QueueEntry(
                patient_id=patient.id,
                doctor_id=doctor_user.id,
                status='waiting',
                priority=0
            )
            db.session.add(queue_entry)
            db.session.commit()
            
            # Add to QueueService (Redis/Memory)
            queue_service.enqueue(patient.id, doctor_user.id, priority=0)
            
        # Now check the dashboard
        response = authenticated_patient.get('/patient/dashboard')
        assert response.status_code == 200
        
        # Check for queue specific elements in the HTML
        html = response.data.decode('utf-8')
        
        # These strings are from templates/patient/dashboard.html
        assert "You are in the queue!" in html
        assert "Queue #" in html
        assert f"Dr. {doctor_user.full_name}" in html
        assert "Estimated wait time:" in html
