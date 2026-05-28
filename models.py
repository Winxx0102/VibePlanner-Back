from database import db
from datetime import datetime

# ==========================================
# TABLAS DE ASOCIACIÓN (Many-to-Many)
# ==========================================

# Para relacionar: Eventos <-> Canciones (Setlist)
event_songs = db.Table('event_songs',
    db.Column('event_id', db.Integer, db.ForeignKey('events.id'), primary_key=True),
    db.Column('song_id', db.Integer, db.ForeignKey('songs.id'), primary_key=True)
)

# Para relacionar: Eventos <-> Usuarios (Asistentes del Staff/Registro)
event_assistants = db.Table('event_assistants',
    db.Column('event_id', db.Integer, db.ForeignKey('events.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True)
)


# ==========================================
# MODELOS EXISTENTES
# ==========================================

class Author(db.Model):
    __tablename__ = 'authors'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    songs = db.relationship('Song', backref='author', lazy=True)


class Genre(db.Model):
    __tablename__ = 'genres'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    songs = db.relationship('Song', backref='genre', lazy=True)


class Song(db.Model):
    __tablename__ = 'songs'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    genre_id = db.Column(db.Integer, db.ForeignKey('genres.id'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('authors.id'), nullable=False)
    structure = db.Column(db.JSON, nullable=True) 
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)


# ==========================================
# NUEVO MODELO: EVENTO
# ==========================================

class Event(db.Model):
    __tablename__ = 'events'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    event_date = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(200))
    description = db.Column(db.Text)
    
    # --- CAMPO JSON EXTRA PARA FRONTEND ---
    # Aquí puedes guardar info como: etapas del show, catering, equipos necesarios, etc.
    structure = db.Column(db.JSON, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # --- RELACIONES ---
    
    # Canciones que se tocarán (Setlist)
    songs = db.relationship('Song', secondary=event_songs, lazy='subquery',
        backref=db.backref('events', lazy=True))
    
    # Usuarios registrados en el evento
    attendees = db.relationship('User', secondary=event_assistants, lazy='subquery',
        backref=db.backref('events', lazy=True))

    # Personas de logística (externas, no están en DB de users)
    # Usaremos una tabla embebida simple o un modelo ligero si necesitan más datos
    logistics = db.relationship('EventLogistics', backref='event', lazy=True)

    # --- MÉTODO PARA API REST ---
    def to_json(self):
        return {
            "id": self.id,
            "title": self.title,
            "event_date": self.event_date.isoformat() if self.event_date else None,
            "location": self.location,
            "description": self.description,
            "structure": self.structure, # Ya es JSON friendly
            "songs": [{"id": s.id, "name": s.name} for s in self.songs],
            "attendees": [{"id": u.id, "username": u.username} for u in self.attendees],
            "logistics": [{"name": l.name, "role": l.role} for l in self.logistics]
        }


# Modelo para personas de logística (no están en la tabla Users)
class EventLogistics(db.Model):
    __tablename__ = 'event_logistics'
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(50)) # Ej: "Sonidista", "Iluminación"
    phone = db.Column(db.String(20))