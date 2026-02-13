import json
import os
from datetime import datetime
from flask_login import UserMixin
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()

class User(UserMixin):
    def __init__(self, id, email, password_hash, name, role='vendor', created_at=None):
        self.id = id
        self.email = email
        self.password_hash = password_hash
        self.name = name
        self.role = role  # 'vendor' or 'buyer'
        self.created_at = created_at or datetime.utcnow().isoformat()
    
    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'password_hash': self.password_hash,
            'name': self.name,
            'role': self.role,
            'created_at': self.created_at
        }
    
    @staticmethod
    def from_dict(data):
        return User(
            id=data['id'],
            email=data['email'],
            password_hash=data['password_hash'],
            name=data['name'],
            role=data.get('role', 'vendor'),
            created_at=data.get('created_at')
        )

class UserDatabase:
    def __init__(self, filepath='data/users.json'):
        self.filepath = filepath
        self._ensure_file_exists()
    
    def _ensure_file_exists(self):
        if not os.path.exists(self.filepath):
            os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
            with open(self.filepath, 'w') as f:
                json.dump([], f)
    
    def get_all_users(self):
        with open(self.filepath, 'r') as f:
            data = json.load(f)
            return [User.from_dict(u) for u in data]
    
    def get_user_by_id(self, user_id):
        users = self.get_all_users()
        return next((u for u in users if u.id == user_id), None)
    
    def get_user_by_email(self, email):
        users = self.get_all_users()
        return next((u for u in users if u.email == email), None)
    
    def create_user(self, email, password, name, role='vendor'):
        users = self.get_all_users()
        
        # Check if user exists
        if any(u.email == email for u in users):
            raise ValueError("User with this email already exists")
        
        # Generate ID
        user_id = f"user_{len(users) + 1:04d}"
        
        # Hash password
        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        
        # Create user
        user = User(user_id, email, password_hash, name, role)
        
        # Save
        users.append(user)
        self._save_users(users)
        
        return user
    
    def _save_users(self, users):
        with open(self.filepath, 'w') as f:
            json.dump([u.to_dict() for u in users], f, indent=2)

# Initialize database
user_db = UserDatabase()