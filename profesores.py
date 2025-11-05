from flask import Blueprint, render_template, request, redirect, url_for, abort
from database import get_db_connection

profesores_bp = Blueprint('profesores_bp', __name__)

# Ruta principal del blueprint, accesible en /profesores/
@profesores_bp.route("/")
def lista(): 
    """Renderiza la lista de profesores desde la base de datos."""
    conn = get_db_connection()
    # Usamos el nombre completo de la tabla si es necesario
    lista_profesores = conn.execute("SELECT id_profesor, cedula, nombre, correo, telefono FROM profesores ORDER BY nombre").fetchall()
    conn.close()
    return render_template("profesores.html", profesores=lista_profesores)

# Ruta para añadir, accesible en /profesores/add
@profesores_bp.route("/add", methods=['GET', 'POST'])
def add():
    """Maneja la adición de un nuevo profesor."""
    if request.method == 'POST':
        cedula = request.form['cedula']
        nombre = request.form['nombre']
        correo = request.form['correo']
        telefono = request.form['telefono']

        conn = get_db_connection()
        conn.execute("INSERT INTO profesores (cedula, nombre, correo, telefono) VALUES (?, ?, ?, ?)",
                       (cedula, nombre, correo, telefono))
        conn.commit()
        conn.close()

        return redirect(url_for('profesores_bp.lista'))

    return render_template("add_profesor.html")

# --- RUTAS PARA EDITAR Y ELIMINAR ---

# Ruta para mostrar el formulario de edición, accesible en /profesores/edit/<id>
@profesores_bp.route('/edit/<int:id_profesor>', methods=['GET'])
def show_edit_form(id_profesor):
    """Muestra el formulario para editar un profesor existente."""
    conn = get_db_connection()
    profesor = conn.execute("SELECT * FROM profesores WHERE id_profesor = ?", (id_profesor,)).fetchone()
    conn.close()
    if profesor is None:
        abort(404)
    return render_template('edit_profesor.html', profesor=profesor)

# Ruta para actualizar, accesible en /profesores/update/<id>
@profesores_bp.route('/update/<int:id_profesor>', methods=['POST'])
def update(id_profesor):
    """Actualiza la información de un profesor."""
    cedula = request.form['cedula']
    nombre = request.form['nombre']
    correo = request.form.get('correo')
    telefono = request.form.get('telefono')

    conn = get_db_connection()
    conn.execute("UPDATE profesores SET cedula = ?, nombre = ?, correo = ?, telefono = ? WHERE id_profesor = ?",
                   (cedula, nombre, correo, telefono, id_profesor))
    conn.commit()
    conn.close()
    
    return redirect(url_for('profesores_bp.lista'))

# Ruta para eliminar, accesible en /profesores/delete/<id>
@profesores_bp.route('/delete/<int:id_profesor>', methods=['POST'])
def delete(id_profesor):
    """Elimina un profesor."""
    conn = get_db_connection()
    
    clases_asignadas = conn.execute('SELECT 1 FROM clases WHERE id_profesor = ?', (id_profesor,)).fetchone()
    
    if clases_asignadas:
        print(f"Intento de eliminar profesor {id_profesor} que tiene clases asignadas.")
    else:
        conn.execute("DELETE FROM profesores WHERE id_profesor = ?", (id_profesor,))
        conn.commit()
        
    conn.close()
    return redirect(url_for('profesores_bp.lista'))
