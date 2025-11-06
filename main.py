# 1. Importaciones necesarias
import os
from flask import Flask, render_template
from database import get_db_connection

# Importar los blueprints de las funcionalidades
from profesores import profesores_bp
from cursos import cursos_bp
from gestion import gestion_bp
from horarios import horarios_bp # <-- AÑADIDO

app = Flask(__name__)

# Añadir una clave secreta para la gestión de sesiones (necesaria para flash)
app.secret_key = os.urandom(24)

# 2. Registrar los blueprints con sus prefijos de URL
app.register_blueprint(profesores_bp, url_prefix='/profesores')
app.register_blueprint(cursos_bp, url_prefix='/cursos')
app.register_blueprint(gestion_bp) 
app.register_blueprint(horarios_bp) # <-- AÑADIDO (usará el prefijo '/horarios' definido en el blueprint)

# --- Rutas HTML Principales ---

@app.route("/")
def index():
    return render_template("index.html")

# La ruta /horarios ha sido movida a horarios_bp, por lo que se elimina de aquí.

@app.route("/aulas")
def aulas():
    return render_template("aulas.html")

# 3. Bloque para iniciar el servidor
if __name__ == '__main__':
  app.run(host='0.0.0.0', port=8080, debug=True)
