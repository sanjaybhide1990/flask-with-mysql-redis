import time
import redis
import json
import os
from flask import Flask, jsonify, Response
from flask_sqlalchemy import SQLAlchemy
from flask import g
from dotenv import load_dotenv
from prometheus_flask_exporter import PrometheusMetrics
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from circuit_breaker import RedisCircuitBreaker

load_dotenv()
redis_cb = RedisCircuitBreaker(failure_threshold=3, cooldown_seconds=30)
app = Flask(__name__)

metrics = PrometheusMetrics(app,path=None)

cache_hits = Counter('cache_hits_total','Number of Redis cache hits')
cache_misses = Counter('cache_misses_total','Number of Redis cache misses')
db_query_duration = Histogram('db_query_duration_seconds','Time spent querying MySQL',buckets=[0.01,0.05,0.1,0.5,1.0,2.0])

DB_USER = os.environ.get("DB_USERNAME")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_HOSTNAME = os.environ.get("DB_HOST",os.environ.get("DB_HOST_LOCAL","localhost"))
DB_DATABASE_NAME = os.environ.get("DB_NAME")

app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOSTNAME}/{DB_DATABASE_NAME}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

REDIS_HOST = os.environ.get("REDIS_HOST","localhost")
redis_client = redis.Redis(host=REDIS_HOST,
                           port=6379,
                           decode_responses=True,
                           socket_connect_timeout=0.1,
                           socket_timeout=0.1)

#Adding circuit breaker logic
def get_from_cache(key):
    if redis_cb.is_open():
        return None
    try:
        value = redis_client.get(key)
        redis_cb.record_success()
        return value
    except Exception:
        redis_cb.record_failure()
        return None

def set_in_cache(key, value, ttl=120):
    if redis_cb.is_open():
        return
    try:
        redis_client.set(key, value, ex=ttl)
        redis_cb.record_success()
    except Exception:
        redis_cb.record_failure()

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    place = db.Column(db.String(100), nullable=False)

    def to_dict(self):
        return {"id": self.id, "name": self.name, "place": self.place}

with app.app_context():
    db.create_all()

@app.before_request
def start_timer():
    g.start_time = time.time()

@app.after_request
def add_response_timing(response):
    if hasattr(g, 'start_time'):
        elapsed_ms = round((time.time() - g.start_time) * 1000, 2)
        response.headers["X-Response-Time"] = f"{elapsed_ms}ms"
    return response

@app.route('/metrics')
def metrics_endpoint():
    return Response(generate_latest(),mimetype=CONTENT_TYPE_LATEST)

@app.route('/health/live')
def liveness():
    return jsonify({"status": "ok"}), 200

@app.route('/health/ready')
def readiness():
    checks = {}
    status_code = 200
    try:
        db.session.execute(db.text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = "unavailable"
        status_code = 503
    try:
        redis_client.ping()
        checks["redis"] = "ok"
    except Exception:
        checks["redis"] = "degraded"
    
    return jsonify({"checks": checks}), status_code

@app.route('/user/<int:user_id>',methods= ["GET"])
def get_user(user_id):
    # start_time = time.time()
    cache_key = f"user:{user_id}"

    cached_user = get_from_cache(cache_key)
    if cached_user:
        cache_hits.inc()
        # elapsed_time_for_cache = round((time.time() - start_time)* 1000, 2)
        # app.logger.info("Time taken to fetch from cache: %s ms",elapsed_time_for_cache)
        app.logger.info("Cache hit for the key: %s", cache_key)
        app.logger.info("Data fetched from cache: %s",cached_user)
        
        return jsonify({
            "source": "From Redis cache",
            "data": json.loads(cached_user),
            # "response_time(in ms)": elapsed_time_for_cache
        })
    
    cache_misses.inc()

    with db_query_duration.time():
        user = db.session.get(User,user_id)
    if user is None:
        app.logger.error("User %s not found in the database",user_id)
        return jsonify({"error": "User not found"}), 404

    user_data = user.to_dict()
    set_in_cache(cache_key, json.dumps(user_data))
    
    # elapsed_time_for_db = round((time.time() - start_time)* 1000, 2)
    # app.logger.info("Time taken to fetch from database: %s ms",elapsed_time_for_db)
    return jsonify({
        "source": "From MySQL database",
        "data": user_data
        # "response_time(in ms)": elapsed_time_for_db
    })

@app.route('/addDummyUser')
def add_dummy_user():
    if not User.query.first():
        new_user = User(name="Sanjay", place= "Bengaluru")
        db.session.add(new_user)
        db.session.commit()
        return "Added user Sanjay to the database"
    return "Data already exists"

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=5000,debug=True)
