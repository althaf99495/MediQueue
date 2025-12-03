import redis
import json
from datetime import datetime
import os
import threading
from collections import defaultdict
import heapq
import itertools

class QueueService:
    _instance = None
    _redis_pool = None
    _lock = threading.Lock()
    
    def __new__(cls, redis_url=None):
        if cls._instance is None:
            cls._instance = super(QueueService, cls).__new__(cls)
            if redis_url is None:
                redis_url = os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/0')
            
            # Check if Redis should be used
            use_redis = os.environ.get('USE_REDIS', 'True').lower() == 'true'
            
            # Try to connect to Redis, but fall back to in-memory if unavailable or disabled
            cls._instance.redis_client = None
            cls._instance.use_redis = False
            
            if use_redis:
                try:
                    print(f"Attempting to connect to Redis at {redis_url}")
                    # Allow more time for initial connection and simpler retry logic
                    cls._redis_pool = redis.ConnectionPool.from_url(
                        redis_url,
                        decode_responses=True,
                        max_connections=10,
                        socket_timeout=5,
                        socket_connect_timeout=5,
                        health_check_interval=30,
                        retry_on_timeout=True
                    )
                    # Test the connection
                    redis_client = redis.Redis(connection_pool=cls._redis_pool)
                    response = redis_client.ping()
                    print(f"[OK] Redis connection successful, ping response: {response}")
                    cls._instance.redis_client = redis_client
                    cls._instance.use_redis = True
                    
                except (redis.ConnectionError, ConnectionRefusedError, Exception) as e:
                    print(f"[WARN] Warning: Could not connect to Redis at {redis_url}")
                    print(f"   Error: {str(e)}")
                    print(f"   Falling back to in-memory queue storage.")
                    print(f"   Note: Queue data will not persist across server restarts.")
                    cls._instance.redis_client = None
                    cls._instance.use_redis = False
            else:
                print("Redis is disabled via configuration. Using in-memory queue storage.")
                print("Note: Queue data will not persist across server restarts.")
                # Initialize in-memory storage
                cls._instance._memory_queues = defaultdict(list)  # doctor_id -> list of (score, entry_data)
                cls._instance._memory_positions = {}  # patient_id -> doctor_id
                cls._instance._counter = itertools.count()  # Counter for unique tuple ordering
                
        return cls._instance

    def __init__(self, redis_url=None):
        # initialization is handled in __new__
        if not hasattr(self, 'use_redis'):
            self.use_redis = False
        if not hasattr(self, '_memory_queues'):
            self._memory_queues = defaultdict(list)
        if not hasattr(self, '_memory_positions'):
            self._memory_positions = {}
        if not hasattr(self, '_counter'):
            self._counter = itertools.count()
    
    def _get_queue_key(self, doctor_id):
        return f"queue:doctor:{doctor_id}"
    
    def _get_position_key(self, patient_id):
        return f"position:patient:{patient_id}"
    
    def enqueue(self, patient_id, doctor_id, priority=0, appointment_id=None, queue_number=None):
        if self.use_redis and self.redis_client:
            queue_key = self._get_queue_key(doctor_id)
            position_key = self._get_position_key(patient_id)
            
            entry_data = {
                'patient_id': patient_id,
                'doctor_id': doctor_id,
                'priority': priority,
                'appointment_id': appointment_id,
                'queue_number': queue_number,
                'joined_at': datetime.utcnow().isoformat()
            }
            
            score = -priority if priority > 0 else datetime.utcnow().timestamp()
            
            self.redis_client.zadd(queue_key, {json.dumps(entry_data): score})
            self.redis_client.set(position_key, str(doctor_id))
            return True
        else:
            # In-memory fallback
            with self._lock:
                entry_data = {
                    'patient_id': patient_id,
                    'doctor_id': doctor_id,
                    'priority': priority,
                    'appointment_id': appointment_id,
                    'queue_number': queue_number,
                    'joined_at': datetime.utcnow().isoformat()
                }
                
                score = -priority if priority > 0 else datetime.utcnow().timestamp()
                
                # Add to sorted list (maintain sorted order)
                # Use counter to ensure unique tuples for heapq (dicts can't be compared)
                queue = self._memory_queues[doctor_id]
                heapq.heappush(queue, (score, next(self._counter), entry_data))
                self._memory_positions[patient_id] = doctor_id
            return True
    
    def dequeue(self, doctor_id):
        if self.use_redis and self.redis_client:
            queue_key = self._get_queue_key(doctor_id)
            
            entries = self.redis_client.zrange(queue_key, 0, 0)
            if not entries:
                return None
            
            entry = json.loads(entries[0])
            self.redis_client.zrem(queue_key, entries[0])
            
            position_key = self._get_position_key(entry['patient_id'])
            self.redis_client.delete(position_key)
            
            return entry
        else:
            # In-memory fallback
            with self._lock:
                queue = self._memory_queues[doctor_id]
                if not queue:
                    return None
                
                score, counter, entry = heapq.heappop(queue)
                if entry['patient_id'] in self._memory_positions:
                    del self._memory_positions[entry['patient_id']]
                return entry
    
    def get_position(self, patient_id):
        if self.use_redis and self.redis_client:
            position_key = self._get_position_key(patient_id)
            doctor_id = self.redis_client.get(position_key)
            
            if not doctor_id:
                return None
            
            # Convert doctor_id to int if it's a string
            try:
                doctor_id = int(doctor_id)
            except (ValueError, TypeError):
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
        else:
            # In-memory fallback
            with self._lock:
                if patient_id not in self._memory_positions:
                    return None
                
                doctor_id = self._memory_positions[patient_id]
                queue = self._memory_queues[doctor_id]
                
                # Find position in sorted queue
                sorted_queue = sorted(queue, key=lambda x: (x[0], x[1]))
                for idx, (score, counter, entry) in enumerate(sorted_queue):
                    if entry['patient_id'] == patient_id:
                        return {
                            'position': idx + 1,
                            'total': len(sorted_queue),
                            'doctor_id': doctor_id,
                            'entry': entry
                        }
                
                return None
    
    def get_queue(self, doctor_id):
        if self.use_redis and self.redis_client:
            queue_key = self._get_queue_key(doctor_id)
            all_entries = self.redis_client.zrange(queue_key, 0, -1)
            
            queue_list = []
            for idx, entry_json in enumerate(all_entries):
                entry = json.loads(entry_json)
                entry['position'] = idx + 1
                queue_list.append(entry)
            
            return queue_list
        else:
            # In-memory fallback
            with self._lock:
                queue = self._memory_queues[doctor_id]
                sorted_queue = sorted(queue, key=lambda x: (x[0], x[1]))
                
                queue_list = []
                for idx, (score, counter, entry) in enumerate(sorted_queue):
                    entry_copy = entry.copy()
                    entry_copy['position'] = idx + 1
                    queue_list.append(entry_copy)
                
                return queue_list
    
    def remove_from_queue(self, patient_id):
        if self.use_redis and self.redis_client:
            position_key = self._get_position_key(patient_id)
            doctor_id = self.redis_client.get(position_key)
            
            if not doctor_id:
                return False
            
            # Convert doctor_id to int if it's a string
            try:
                doctor_id = int(doctor_id)
            except (ValueError, TypeError):
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
        else:
            # In-memory fallback
            with self._lock:
                if patient_id not in self._memory_positions:
                    return False
                
                doctor_id = self._memory_positions[patient_id]
                queue = self._memory_queues[doctor_id]
                
                # Remove entry from queue
                new_queue = [(score, counter, entry) for score, counter, entry in queue if entry['patient_id'] != patient_id]
                self._memory_queues[doctor_id] = new_queue
                del self._memory_positions[patient_id]
                return True
    
    def reorder_queue(self, doctor_id, new_order):
        if self.use_redis and self.redis_client:
            queue_key = self._get_queue_key(doctor_id)
            
            with self.redis_client.pipeline() as pipe:
                pipe.delete(queue_key)
                for idx, entry in enumerate(new_order):
                    pipe.zadd(queue_key, {json.dumps(entry): idx})
                pipe.execute()
            
            return True
        else:
            # In-memory fallback
            with self._lock:
                new_queue = []
                for idx, entry in enumerate(new_order):
                    score = entry.get('priority', 0)
                    score = -score if score > 0 else datetime.utcnow().timestamp() + idx
                    new_queue.append((score, next(self._counter), entry))
                self._memory_queues[doctor_id] = new_queue
                # Update positions
                for entry in new_order:
                    if 'patient_id' in entry:
                        self._memory_positions[entry['patient_id']] = doctor_id
            return True
    
    def get_queue_length(self, doctor_id):
        if self.use_redis and self.redis_client:
            queue_key = self._get_queue_key(doctor_id)
            return self.redis_client.zcard(queue_key)
        else:
            # In-memory fallback
            with self._lock:
                return len(self._memory_queues[doctor_id])
    
    def clear_queue(self, doctor_id):
        if self.use_redis and self.redis_client:
            queue_key = self._get_queue_key(doctor_id)
            return bool(self.redis_client.delete(queue_key))
        else:
            # In-memory fallback
            with self._lock:
                if doctor_id in self._memory_queues:
                    # Remove position entries for patients in this queue
                    queue = self._memory_queues[doctor_id]
                    for score, counter, entry in queue:
                        if entry['patient_id'] in self._memory_positions:
                            del self._memory_positions[entry['patient_id']]
                    del self._memory_queues[doctor_id]
                    return True
                return False

    def clear_all(self):
        """Clear all queues - used for testing"""
        if self.use_redis and self.redis_client:
            self.redis_client.flushdb()
        else:
            with self._lock:
                self._memory_queues.clear()
                self._memory_positions.clear()
                self._counter = itertools.count()
