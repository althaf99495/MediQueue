import redis
import json
from datetime import datetime
import os

class QueueService:
    def __init__(self, redis_url=None):
        if redis_url is None:
            redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
        
        try:
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            self.redis_client.ping()
        except (redis.ConnectionError, redis.ResponseError):
            self.redis_client = None
    
    def _get_queue_key(self, doctor_id):
        return f"queue:doctor:{doctor_id}"
    
    def _get_position_key(self, patient_id):
        return f"position:patient:{patient_id}"
    
    def enqueue(self, patient_id, doctor_id, priority=0, appointment_id=None):
        if not self.redis_client:
            return False
        
        queue_key = self._get_queue_key(doctor_id)
        position_key = self._get_position_key(patient_id)
        
        entry_data = {
            'patient_id': patient_id,
            'doctor_id': doctor_id,
            'priority': priority,
            'appointment_id': appointment_id,
            'joined_at': datetime.utcnow().isoformat()
        }
        
        score = -priority if priority > 0 else datetime.utcnow().timestamp()
        
        self.redis_client.zadd(queue_key, {json.dumps(entry_data): score})
        self.redis_client.set(position_key, doctor_id)
        
        return True
    
    def dequeue(self, doctor_id):
        if not self.redis_client:
            return None
        
        queue_key = self._get_queue_key(doctor_id)
        
        entries = self.redis_client.zrange(queue_key, 0, 0)
        if not entries:
            return None
        
        entry = json.loads(entries[0])
        self.redis_client.zrem(queue_key, entries[0])
        
        position_key = self._get_position_key(entry['patient_id'])
        self.redis_client.delete(position_key)
        
        return entry
    
    def get_position(self, patient_id):
        if not self.redis_client:
            return None
        
        position_key = self._get_position_key(patient_id)
        doctor_id = self.redis_client.get(position_key)
        
        if not doctor_id:
            return None
        
        queue_key = self._get_queue_key(doctor_id)
        all_entries = self.redis_client.zrange(queue_key, 0, -1)
        
        for idx, entry_json in enumerate(all_entries):
            entry = json.loads(entry_json)
            if entry['patient_id'] == patient_id:
                return {
                    'position': idx + 1,
                    'total': len(all_entries),
                    'doctor_id': doctor_id,
                    'entry': entry
                }
        
        return None
    
    def get_queue(self, doctor_id):
        if not self.redis_client:
            return []
        
        queue_key = self._get_queue_key(doctor_id)
        all_entries = self.redis_client.zrange(queue_key, 0, -1)
        
        queue_list = []
        for idx, entry_json in enumerate(all_entries):
            entry = json.loads(entry_json)
            entry['position'] = idx + 1
            queue_list.append(entry)
        
        return queue_list
    
    def remove_from_queue(self, patient_id):
        if not self.redis_client:
            return False
        
        position_key = self._get_position_key(patient_id)
        doctor_id = self.redis_client.get(position_key)
        
        if not doctor_id:
            return False
        
        queue_key = self._get_queue_key(doctor_id)
        all_entries = self.redis_client.zrange(queue_key, 0, -1)
        
        for entry_json in all_entries:
            entry = json.loads(entry_json)
            if entry['patient_id'] == patient_id:
                self.redis_client.zrem(queue_key, entry_json)
                self.redis_client.delete(position_key)
                return True
        
        return False
    
    def reorder_queue(self, doctor_id, new_order):
        if not self.redis_client:
            return False
        
        queue_key = self._get_queue_key(doctor_id)
        
        self.redis_client.delete(queue_key)
        
        for idx, entry in enumerate(new_order):
            score = idx
            self.redis_client.zadd(queue_key, {json.dumps(entry): score})
        
        return True
    
    def get_queue_length(self, doctor_id):
        if not self.redis_client:
            return 0
        
        queue_key = self._get_queue_key(doctor_id)
        return self.redis_client.zcard(queue_key)
    
    def clear_queue(self, doctor_id):
        if not self.redis_client:
            return False
        
        queue_key = self._get_queue_key(doctor_id)
        self.redis_client.delete(queue_key)
        return True
