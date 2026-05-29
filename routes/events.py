from flask import Blueprint, request, jsonify
from models import db, Event, Song, EventLogistics
from datetime import datetime

event_bp = Blueprint('events', __name__, url_prefix='/api/events')


@event_bp.route('/', methods=['POST'])
def create_event():
    data = request.get_json(force=True)
    
    new_event = Event(
        title=data['title'],
        event_date=datetime.strptime(data['event_date'], '%Y-%m-%d %H:%M'),
        location=data.get('location'),
        description=data.get('description'),
        structure=data.get('structure')
    )
    
    db.session.add(new_event)
    db.session.flush()

    # --- VALIDAR CANCIONES ---
    if 'song_ids' in data and data['song_ids']:
        requested_ids = data['song_ids']
        
        existing_songs = Song.query.filter(Song.id.in_(requested_ids)).all()
        found_ids = {s.id for s in existing_songs}
        requested_set = set(requested_ids)
        
        missing_ids = requested_set - found_ids
        
        if missing_ids:
            db.session.rollback()
            return jsonify({
                "error": "Algunas canciones no existen",
                "missing": list(missing_ids)
            }), 400
        
        new_event.songs = existing_songs

    # --- LOGÍSTICA ---
    if 'logistics' in data and data['logistics']:
        for log in data['logistics']:
            log_entry = EventLogistics(
                event_id=new_event.id,
                name=log['name'],
                role=log.get('role'),
                phone=log.get('phone')
            )
            db.session.add(log_entry)

    db.session.commit()

    return jsonify({
        "message": "¡Evento creado con éxito!", 
        "event_id": new_event.id
    }), 201
    
    #ejemplo de api rest para crear un evento con estructura JSON y relaciones con canciones y usuarios. El endpoint valida que las canciones y usuarios existan antes de asociarlos al evento, y maneja la logística como una relación adicional.
    # {
    #"title": "Concierto Rock Madrid",
   # "event_date": "2024-12-25 20:00",   //formato ISO para fechas
    #"location": "Wizink Center, Madrid",
    #"description": "Gran concierto de rock navideño",
    #"structure": {
       # "sound_check": "song1",    //puede ser un nombre de canción o una etapa del evento
       # "doors_open": "test",
       # "start_show": "20:00"
      
   # },
   # "song_ids": [1, 2],   //id de canciones
   # "user_ids": [],       //usuarios dentro de la db
    #"logistics": [        //personas que no sou usuarios de la app pero forman parte del evento
       # {
        #    "name": "Carlos Pérez",
        #    "role": "Sonidista",
       #     "phone": "+34912345678"
       # },
       # {
       #     "name": "Ana Gómez",
       #     "role": "Iluminación",
       #     "phone": "+34987654321"
       # }
   # ]
#}