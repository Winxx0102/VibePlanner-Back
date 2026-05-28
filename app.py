import os
from flask import Flask, jsonify
from database import db
import models  # IMPORTANTE: Cargar los modelos aquí para que Alembic los detecte

app = Flask(__name__)

# 1. Obtenemos la ruta absoluta de la carpeta raíz de tu proyecto (VibePlanner-back)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# 2. Configuración de SQLite usando la ruta absoluta directa
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(BASE_DIR, "database.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializar la base de datos con la app
db.init_app(app)

@app.route('/health', methods=['GET'])
def health():
    # Consulta rápida de prueba con SQLAlchemy
    total_users = models.User.query.count()
    return jsonify({"status": "ok", "users_count": total_users})

if __name__ == '__main__':
    app.run(debug=True)