from database import db
from datetime import datetime

# alembic revision --autogenerate -m "tabla song"
# alembic upgrade head


class Author(db.Model):
    __tablename__ = 'authors'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)   # Ej: "Rock", "Pop", "Trap"
    
    # Relación: Un género puede estar en muchas canciones
    songs = db.relationship('Song', backref='author', lazy=True)


class Genre(db.Model):
    __tablename__ = 'genres'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)   # Ej: "Rock", "Pop", "Trap"
    
    # Relación: Un género puede estar en muchas canciones
    songs = db.relationship('Song', backref='genre', lazy=True)

class Song(db.Model):
    __tablename__ = 'songs'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)               # name (varchar)
    
    # Llaves Foráneas (Foreign Keys)
    genre_id = db.Column(db.Integer, db.ForeignKey('genres.id'), nullable=False) # genre foreign
    author_id = db.Column(db.Integer, db.ForeignKey('authors.id'), nullable=False) # genre foreign
    # Campo JSON para la estructura de la canción
    structure = db.Column(db.JSON, nullable=True)                  # structure (json)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)