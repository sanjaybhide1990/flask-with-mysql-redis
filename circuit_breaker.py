import time
import threading

class RedisCircuitBreaker:
    def __init__(self, failure_threshold=3, cooldown_seconds=30):
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        self.failure_count = 0
        self.last_failure_time = None
        self._lock = threading.Lock()
    
    def is_open(self):
        with self._lock:
            if self.failure_count < self.failure_threshold:
                return False
            if time.time() - self.last_failure_time > self.cooldown_seconds:
                self.failure_count = 0
                return False
            return True
    
    def record_failure(self):
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()

    def record_success(self):
        with self._lock:
            self.failure_count = 0