# routes/songs.py
from flask import Blueprint, jsonify, request
from database import db
from models import Song, Genre

songs_bp = Blueprint('songs', __name__, url_prefix='/api/songs')

@songs_bp.route('/', methods=['GET'])
def get_all_songs():
    
    all_songs = Song.query.all()
    return jsonify({"songs": [song.name for song in all_songs]})

@songs_bp.route('/<int:song_id>', methods=['GET'])
def get_song(song_id):
    song = Song.query.get_or_404(song_id)
    return jsonify({
        "id": song.id,
        "name": song.name,
        "structure": song.structure
    })

@songs_bp.route('/', methods=['POST'])
def create_song():
    data = request.get_json(force=True)
    
    
    new_song = Song(
        name=data.get('name'),
        genre_id=data.get('genre_id'),
        author_id=data.get('author_id'),
        structure=data.get('structure')
    )
    
    db.session.add(new_song)
    db.session.commit()
    
    return jsonify({"message": "¡Canción creada con éxito!", "song_id": new_song.id}), 201