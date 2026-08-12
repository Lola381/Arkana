from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import os
import certifi
import jwt
import datetime

load_dotenv()

app = Flask(__name__)
# Enable CORS for frontend requests
CORS(app)

# JWT Secret Key
app.config['SECRET_KEY'] = os.getenv("JWT_SECRET", "arkana_secret_key_12345")

# Connect to MongoDB Atlas
uri = os.getenv("MONGODB_URI")
db_name = os.getenv("DATABASE_NAME", "arkana")

try:
    # Use certifi to bypass Windows SSL handshake issues
    client = MongoClient(uri, tlsCAFile=certifi.where())
    db = client[db_name]
    users_collection = db["users"]
    print(f"Connected to MongoDB Atlas. Database: {db_name}")
except Exception as e:
    print("Database connection failed:", e)
    users_collection = None

# Middleware to verify JWT Token
def token_required(f):
    def decorator(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(" ")[1]
        
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            # Find current user
            current_user = users_collection.find_one({"email": data["email"]})
            if not current_user:
                return jsonify({'message': 'User not found'}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired'}), 401
        except Exception:
            return jsonify({'message': 'Token is invalid'}), 401
            
        return f(current_user, *args, **kwargs)
    decorator.__name__ = f.__name__
    return decorator

# --- API ROUTES ---

@app.route('/api/auth/register', methods=['POST'])
def register():
    #parse data to json
    data_j = request.get_json()
    print("Received registration data:", data_j)

    if users_collection is None:
        return jsonify({"message": "Database not connected"}), 500
        
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    
    if not name or not email or not password:
        return jsonify({"message": "Please fill in all fields"}), 400
        
    email = email.lower().strip()
    
    # Check if user already exists
    existing_user = users_collection.find_one({"email": email})
    if existing_user:
        return jsonify({"message": "Email address already registered"}), 400
        
    # Hash password using secure helper
    hashed_password = generate_password_hash(password)
    
    # Save user
    user_doc = {
        "name": name,
        "email": email,
        "password": hashed_password,
        "created_at": datetime.datetime.utcnow()
    }
    
    try:
        users_collection.insert_one(user_doc)
        
        # Create JWT token
        token = jwt.encode({
            'email': email,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }, app.config['SECRET_KEY'], algorithm="HS256")
        
        return jsonify({
            "message": "User registered successfully",
            "token": token,
            "user": {"name": name, "email": email}
        }), 201
    except Exception as e:
        return jsonify({"message": "Error creating account", "error": str(e)}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    if users_collection is None:
        return jsonify({"message": "Database not connected"}), 500

    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({"message": "Please enter both email and password"}), 400
        
    email = email.lower().strip()
    
    # Find user
    user = users_collection.find_one({"email": email})
    if not user:
        return jsonify({"message": "Invalid email or password"}), 401
        
    # Verify password hash
    if not check_password_hash(user['password'], password):
        return jsonify({"message": "Invalid email or password"}), 401
        
    # Generate Token
    token = jwt.encode({
        'email': email,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }, app.config['SECRET_KEY'], algorithm="HS256")
    
    return jsonify({
        "message": "Login successful",
        "token": token,
        "user": {"name": user.get("name"), "email": email}
    }), 200

@app.route('/api/auth/profile', methods=['GET'])
@token_required
def get_profile(current_user):
    return jsonify({
        "user": {
            "name": current_user.get("name"),
            "email": current_user.get("email")
        }
    }), 200

if __name__ == '__main__':
    # Run the server on port 5000
    app.run(port=5000, debug=True)
