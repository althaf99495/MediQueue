import os
import sys
from services.queue_service import QueueService

def verify_redis():
    print("Verifying Redis connection...")
    
    # Force enable Redis
    os.environ['USE_REDIS'] = 'True'
    
    # Reset singleton to ensure fresh initialization
    QueueService._instance = None
    
    try:
        qs = QueueService()
        
        if qs.use_redis:
            print("SUCCESS: QueueService is using Redis.")
            
            if qs.redis_client:
                try:
                    response = qs.redis_client.ping()
                    if response:
                        print(f"SUCCESS: Redis PING response: {response}")
                        return True
                    else:
                        print("FAILURE: Redis PING failed (no response).")
                except Exception as e:
                    print(f"FAILURE: Redis PING raised exception: {e}")
            else:
                print("FAILURE: use_redis is True but redis_client is None.")
        else:
            print("FAILURE: QueueService fell back to in-memory storage.")
            print("Check if Redis is running and accessible at redis://127.0.0.1:6379/0")
            
    except Exception as e:
        print(f"CRITICAL FAILURE: {e}")
        import traceback
        traceback.print_exc()
        
    return False

if __name__ == "__main__":
    if verify_redis():
        sys.exit(0)
    else:
        sys.exit(1)
