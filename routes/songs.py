# routes/songs.py
from flask import Blueprint, jsonify, request
from database import db
from models import Song, Genre, Author
from services.ai_song_service import generar_cancion_ia
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
    
    # Extraemos los strings limpios desde el payload que manda tu frontend
    genre_name = data.get('genre')
    author_name = data.get('author')
    song_name = data.get('name')
    structure_data = data.get('structure') # Este ya viene como el JSON estructurado por tu utils o la IA

    if not song_name or not author_name or not structure_data:
        return jsonify({"message": "Faltan campos obligatorios (name, author, structure)"}), 400

    try:
        # 1. Resolver o Crear el Género (si viene especificado)
        genre_id = None
        if genre_name:
            genre_name_clean = genre_name.strip()
            genre = db.session.query(Genre).filter_by(name=genre_name_clean).first()
            if not genre:
                genre = Genre(name=genre_name_clean)
                db.session.add(genre)
                db.session.flush() # flush() genera el ID en la DB sin cerrar la transacción
            genre_id = genre.id

        # 2. Resolver o Crear el Autor
        author_name_clean = author_name.strip()
        author = db.session.query(Author).filter_by(name=author_name_clean).first()
        if not author:
            author = Author(name=author_name_clean)
            db.session.add(author)
            db.session.flush() # flush() nos da el nuevo ID del autor inmediatamente
        author_id = author.id

        # 3. Crear la Canción vinculando los IDs correctos que acabamos de resolver
        new_song = Song(
            name=song_name.strip(),
            genre_id=genre_id,
            author_id=author_id,
            structure=structure_data # SQLAlchemy mapeará este dict/json automáticamente si el campo es tipo JSON
        )
        
        db.session.add(new_song)
        
        # Un solo commit para asegurar la atomicidad (se guarda todo junto o no se guarda nada)
        db.session.commit()
        
        return jsonify({
            "message": "¡Canción creada con éxito!", 
            "song_id": new_song.id
        }), 201

    except Exception as e:
        db.session.rollback() # Si algo falla, revertimos cualquier inserción a medias
        print(f"[ERROR] Error al guardar la canción: {e}")
        return jsonify({"message": "Ocurrió un error interno al procesar la canción."}), 500


@songs_bp.route('/generate-ia', methods=['POST'])
def generate_song_structure():
    """
    Endpoint para que el frontend envíe lo que el usuario escribe en el chat.
    Payload esperado: { "prompt": "Consigue la letra de De Música Ligera" }
    """
    data = request.get_json(force=True)
    user_prompt = data.get('prompt')
    
    if not user_prompt:
        return jsonify({
            "bot_response": "Hubo un pequeño error: no recibí ningún texto para procesar. ¡Escríbeme algo!",
            "song_data": None
        }), 400
        
    try:
        # Llamamos al servicio de LangChain
        resultado_ia = generar_cancion_ia(user_prompt)
        
        # Devolvemos el diccionario con 'bot_response' y 'song_data'
        return jsonify(resultado_ia), 200
        
    except Exception as e:
        print(f"[ERROR] Error crítico en la ruta /generate-ia: {e}")
        return jsonify({
            "bot_response": "¡Upps! Ocurrió un error inesperado procesando tu solicitud con la IA. Por favor, intenta de nuevo en unos momentos.",
            "song_data": None
        }), 500