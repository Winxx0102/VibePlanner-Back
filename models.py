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
    structure = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # --- RELACIONES ---
    
    # Canciones que se tocarán (Setlist)
    songs = db.relationship('Song', secondary=event_songs, lazy='subquery',
        backref=db.backref('events', lazy=True))

    # Personas de logística (externas, no están en DB de users)
    logistics = db.relationship('EventLogistics', backref='event', lazy=True)

    # --- MÉTODO PARA API REST ---
    def to_json(self):
        return {
            "id": self.id,
            "title": self.title,
            "event_date": self.event_date.isoformat() if self.event_date else None,
            "location": self.location,
            "description": self.description,
            "structure": self.structure,
            "songs": [{"id": s.id, "name": s.name} for s in self.songs],
            "logistics": [{"name": l.name, "role": l.role, "phone": l.phone} for l in self.logistics]
        }


# Modelo para personas de logística (no están en la tabla Users)
class EventLogistics(db.Model):
    __tablename__ = 'event_logistics'
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(50))
    phone = db.Column(db.String(20))