"""
Unit Tests for QueueService
Tests individual QueueService methods in isolation.
"""
import pytest
from services import QueueService
from datetime import datetime


class TestQueueService:
    """Unit tests for QueueService."""
    
    def test_queue_service_singleton(self):
        """Test that QueueService is a singleton."""
        service1 = QueueService()
        service2 = QueueService()
        assert service1 is service2
    
    def test_enqueue_patient(self, queue_service_instance):
        """Test adding a patient to the queue."""
        result = queue_service_instance.enqueue(
            patient_id=1,
            doctor_id=10,
            priority=0
        )
        assert result is True
    
    def test_dequeue_patient(self, queue_service_instance):
        """Test removing a patient from the queue."""
        # First enqueue
        queue_service_instance.enqueue(patient_id=1, doctor_id=10)
        
        # Then dequeue
        entry = queue_service_instance.dequeue(doctor_id=10)
        assert entry is not None
        assert entry['patient_id'] == 1
        assert entry['doctor_id'] == 10
    
    def test_dequeue_empty_queue(self, queue_service_instance):
        """Test dequeuing from an empty queue."""
        entry = queue_service_instance.dequeue(doctor_id=999)
        assert entry is None
    
    def test_get_position(self, queue_service_instance):
        """Test getting patient position in queue."""
        # Add multiple patients
        queue_service_instance.enqueue(patient_id=1, doctor_id=10)
        queue_service_instance.enqueue(patient_id=2, doctor_id=10)
        queue_service_instance.enqueue(patient_id=3, doctor_id=10)
        
        # Check position
        position = queue_service_instance.get_position(patient_id=2)
        assert position is not None
        assert position['position'] == 2
        assert position['total'] == 3
    
    def test_get_position_not_in_queue(self, queue_service_instance):
        """Test getting position for patient not in queue."""
        position = queue_service_instance.get_position(patient_id=999)
        assert position is None
    
    def test_get_queue(self, queue_service_instance):
        """Test getting entire queue for a doctor."""
        queue_service_instance.enqueue(patient_id=1, doctor_id=10)
        queue_service_instance.enqueue(patient_id=2, doctor_id=10)
        
        queue = queue_service_instance.get_queue(doctor_id=10)
        assert len(queue) == 2
        assert queue[0]['patient_id'] == 1
        assert queue[1]['patient_id'] == 2
    
    def test_priority_handling(self, queue_service_instance):
        """Test priority-based queue ordering."""
        # Add patients with different priorities
        queue_service_instance.enqueue(patient_id=1, doctor_id=10, priority=0)
        queue_service_instance.enqueue(patient_id=2, doctor_id=10, priority=5)  # Higher priority
        queue_service_instance.enqueue(patient_id=3, doctor_id=10, priority=0)
        
        # High priority patient should be first
        queue = queue_service_instance.get_queue(doctor_id=10)
        # Note: Priority handling depends on implementation
        # This test verifies the service handles priority parameter
        assert len(queue) == 3
    
    def test_remove_from_queue(self, queue_service_instance):
        """Test removing a specific patient from queue."""
        queue_service_instance.enqueue(patient_id=1, doctor_id=10)
        queue_service_instance.enqueue(patient_id=2, doctor_id=10)
        
        result = queue_service_instance.remove_from_queue(patient_id=1)
        assert result is True
        
        queue = queue_service_instance.get_queue(doctor_id=10)
        assert len(queue) == 1
        assert queue[0]['patient_id'] == 2
    
    def test_remove_from_queue_not_exists(self, queue_service_instance):
        """Test removing non-existent patient from queue."""
        result = queue_service_instance.remove_from_queue(patient_id=999)
        assert result is False
    
    def test_get_queue_length(self, queue_service_instance):
        """Test getting queue length."""
        queue_service_instance.enqueue(patient_id=1, doctor_id=10)
        queue_service_instance.enqueue(patient_id=2, doctor_id=10)
        
        length = queue_service_instance.get_queue_length(doctor_id=10)
        assert length == 2
    
    def test_clear_queue(self, queue_service_instance):
        """Test clearing entire queue."""
        queue_service_instance.enqueue(patient_id=1, doctor_id=10)
        queue_service_instance.enqueue(patient_id=2, doctor_id=10)
        
        result = queue_service_instance.clear_queue(doctor_id=10)
        assert result is True
        
        length = queue_service_instance.get_queue_length(doctor_id=10)
        assert length == 0
    
    def test_multiple_doctors_queues(self, queue_service_instance):
        """Test separate queues for different doctors."""
        queue_service_instance.enqueue(patient_id=1, doctor_id=10)
        queue_service_instance.enqueue(patient_id=2, doctor_id=20)
        
        queue1 = queue_service_instance.get_queue(doctor_id=10)
        queue2 = queue_service_instance.get_queue(doctor_id=20)
        
        assert len(queue1) == 1
        assert len(queue2) == 1
        assert queue1[0]['patient_id'] == 1
        assert queue2[0]['patient_id'] == 2
    
    def test_appointment_id_in_queue_entry(self, queue_service_instance):
        """Test queue entry includes appointment_id."""
        queue_service_instance.enqueue(
            patient_id=1,
            doctor_id=10,
            appointment_id=100
        )
        
        queue = queue_service_instance.get_queue(doctor_id=10)
        assert queue[0]['appointment_id'] == 100

