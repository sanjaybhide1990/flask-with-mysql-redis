import time
from flask import Flask, jsonify
import redis

app = Flask(__name__)

redis_client = redis.Redis(host='localhost',port=6379,decode_responses=True)

def simulate_db_query():
    time.sleep(3)
    return {"status":"success","data":"Message fetched from Redis"}

@app.route('/data')
def get_data():
    cache_key = "redis_cache_key"
    cached_data = redis_client.get(cache_key)

    if cached_data: 
        return jsonify({"source": "Redis Cache", "content": cached_data})
    
    real_data = simulate_db_query()

    redis_client.set(cache_key, real_data["data"],ex=120)

    return jsonify({"source": "From a different source", "response": real_data["data"]})

if __name__ == '__main__':
    app.run(debug=True)
