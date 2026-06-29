import time
import threading

class RedisCircuitBreaker:
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"
    def __init__(self, failure_threshold=3, cooldown_seconds=30):
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        self.failure_count = 0
        self.last_failure_time = None
        self.state = self.CLOSED
        self._lock = threading.Lock()
    
    def is_open(self):
        with self._lock:
            print(f"Circuit state: {self.state}, failures: {self.failure_count}")
            if self.state == self.CLOSED:
                return False
            if self.state == self.OPEN:
                if time.time() - self.last_failure_time > self.cooldown_seconds:
                    self.state = self.HALF_OPEN
                    return False
                if self.state == self.HALF_OPEN:
                    return False
                return False
    
    def record_failure(self):
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            if self.failure_count >= self.failure_threshold:
                self.state = self.OPEN

    def record_success(self):
        with self._lock:
            if self.state == self.HALF_OPEN:
                self.state = self.CLOSED
            self.failure_count = 0