from flask import Blueprint, render_template, request, redirect, url_for
from database import get_db_connection

# Creamos el Blueprint para la sección de cursos
cursos_bp = Blueprint('cursos_bp', __name__, template_folder='templates')

@cursos_bp.route("/")
def lista(): 
    """Renderiza la lista de cursos desde la base de datos."""
    conn = get_db_connection()
    # Usamos 'id_curso' de acuerdo al esquema de la base de datos
    lista_cursos = conn.execute("SELECT id_curso, nombre, descripcion FROM cursos").fetchall()
    conn.close()
    return render_template("cursos.html", cursos=lista_cursos)

@cursos_bp.route("/add", methods=['GET', 'POST'])
def add():
    """Maneja la adición de un nuevo curso."""
    if request.method == 'POST':
        nombre = request.form['nombre']
        descripcion = request.form['descripcion']

        conn = get_db_connection()
        conn.execute("INSERT INTO cursos (nombre, descripcion) VALUES (?, ?)",
                       (nombre, descripcion))
        conn.commit()
        conn.close()

        # Redirigir a la lista de cursos para ver el nuevo registro
        return redirect(url_for('cursos_bp.lista'))

    # Si es GET, solo muestra el formulario
    return render_template("add_curso.html")

# La ruta ahora usa id_curso
@cursos_bp.route("/delete/<int:id_curso>")
def delete(id_curso):
    """Elimina un curso por su ID."""
    conn = get_db_connection()
    conn.execute("DELETE FROM cursos WHERE id_curso = ?", (id_curso,))
    conn.commit()
    conn.close()
    return redirect(url_for('cursos_bp.lista'))
