from database import db
from datetime import datetime

# Modelo de Ejemplo: Usuario
class User(db.Model):
    __tablename__ = 'users' # Nombre explícito de la tabla
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relación uno a muchos con Plan (un usuario tiene muchos planes)
    planes = db.relationship('Plan', backref='author', lazy=True, cascade="all, delete-orphan")

# Modelo de Ejemplo: Plan (Para tu VibePlanner)
class Plan(db.Model):
    __tablename__ = 'planes'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Clave foránea que apunta al id de la tabla users
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)