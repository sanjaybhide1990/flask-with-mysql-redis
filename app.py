import time
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
import redis
import json

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Password123@localhost/users'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

redis_client = redis.Redis(host='localhost',port=6379,decode_responses=True)

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    place = db.Column(db.String(100), nullable=False)

    def to_dict(self):
        return {"id": self.id, "name": self.name, "place": self.place}

with app.app_context():
    db.create_all()

@app.route('/user/<int:user_id>',methods= ["GET"])
def get_user(user_id):
    cache_key = f"user:{user_id}"

    cached_user = redis_client.get(cache_key)
    if cached_user:
        return jsonify({
            "source": "From Redis cache",
            "data": json.loads(cached_user)
        })
    user = User.query.get(user_id)

    if user is None:
        return jsonify({"error": "User not found"}), 404
    
    user_data = user.to_dict()

    redis_client.set(cache_key, json.dumps(user_data), ex=120)

    return jsonify({
        "source": "From MySQL database",
        "data": user_data
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
    app.run(debug=True)
