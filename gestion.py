from flask import Blueprint, render_template, request, redirect, url_for, abort
from database import get_db_connection

gestion_bp = Blueprint('gestion_bp', __name__, template_folder='templates')

# --- Rutas para mostrar datos y formularios ---

@gestion_bp.route('/gestion')
def gestion():
    """Renderiza la página de gestión principal con todos los datos necesarios."""
    conn = get_db_connection()
    semestres = conn.execute("SELECT id_semestre, nombre, fecha_inicio, fecha_fin FROM semestres ORDER BY nombre DESC").fetchall()
    cursos = conn.execute("SELECT id_curso, nombre FROM cursos ORDER BY nombre ASC").fetchall()
    profesores = conn.execute("SELECT id_profesor, nombre FROM profesores ORDER BY nombre ASC").fetchall()
    clases = conn.execute("""
        SELECT 
            cl.id_clase, cl.nombre as clase_nombre, cl.descripcion, cl.n_horas, cl.horas_semana,
            cu.nombre as curso_nombre,
            pr.nombre as profesor_nombre,
            se.nombre as semestre_nombre
        FROM clases cl
        LEFT JOIN cursos cu ON cl.id_curso = cu.id_curso
        LEFT JOIN profesores pr ON cl.id_profesor = pr.id_profesor
        LEFT JOIN semestres se ON cl.id_semestre = se.id_semestre
        ORDER BY cl.id_clase DESC
    """).fetchall()
    conn.close()
    return render_template('gestion.html', semestres=semestres, cursos=cursos, profesores=profesores, clases=clases)

@gestion_bp.route('/gestion/add')
def add_form():
    return render_template('add_semestre.html')

@gestion_bp.route('/gestion/edit/<int:id_semestre>')
def edit_form(id_semestre):
    conn = get_db_connection()
    semestre = conn.execute("SELECT * FROM semestres WHERE id_semestre = ?", (id_semestre,)).fetchone()
    conn.close()
    if semestre is None: abort(404)
    return render_template('edit_semestre.html', semestre=semestre)

# --- Rutas para procesar acciones (CRUD) ---

@gestion_bp.route('/gestion/add_clase', methods=['POST'])
def add_clase():
    """Guarda una nueva clase en la base de datos."""
    if request.method == 'POST':
        nombre = request.form['nombre']
        descripcion = request.form.get('descripcion')
        n_horas = request.form.get('n_horas')
        horas_semana = request.form.get('horas_semana')
        id_curso = request.form.get('id_curso')
        id_profesor = request.form.get('id_profesor')
        id_semestre = request.form.get('id_semestre')
        conn = get_db_connection()
        conn.execute("""
            INSERT INTO clases (nombre, descripcion, n_horas, horas_semana, id_curso, id_profesor, id_semestre)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (nombre, descripcion, n_horas, horas_semana, id_curso, id_profesor, id_semestre))
        conn.commit()
        conn.close()
    return redirect(url_for('gestion_bp.gestion'))

@gestion_bp.route('/gestion/add_semestre', methods=['POST'])
def add_semestre():
    if request.method == 'POST':
        nombre = request.form['nombre']
        fecha_inicio = request.form['fecha_inicio']
        fecha_fin = request.form['fecha_fin']
        conn = get_db_connection()
        conn.execute("INSERT INTO semestres (nombre, fecha_inicio, fecha_fin) VALUES (?, ?, ?)",
                       (nombre, fecha_inicio if fecha_inicio else None, fecha_fin if fecha_fin else None))
        conn.commit()
        conn.close()
    return redirect(url_for('gestion_bp.gestion'))

@gestion_bp.route('/gestion/update/<int:id_semestre>', methods=['POST'])
def update_semestre(id_semestre):
    if request.method == 'POST':
        nombre = request.form['nombre']
        fecha_inicio = request.form['fecha_inicio']
        fecha_fin = request.form['fecha_fin']
        conn = get_db_connection()
        conn.execute("UPDATE semestres SET nombre = ?, fecha_inicio = ?, fecha_fin = ? WHERE id_semestre = ?",
                       (nombre, fecha_inicio if fecha_inicio else None, fecha_fin if fecha_fin else None, id_semestre))
        conn.commit()
        conn.close()
    return redirect(url_for('gestion_bp.gestion'))

@gestion_bp.route('/gestion/delete/<int:id_semestre>', methods=['POST'])
def delete_semestre(id_semestre):
    conn = get_db_connection()
    conn.execute("DELETE FROM semestres WHERE id_semestre = ?", (id_semestre,))
    conn.commit()
    conn.close()
    return redirect(url_for('gestion_bp.gestion'))

# --- FUNCIÓN NUEVA PARA ELIMINAR CLASES ---
@gestion_bp.route('/gestion/delete_clase/<int:id_clase>', methods=['POST'])
def delete_clase(id_clase):
    conn = get_db_connection()
    conn.execute("DELETE FROM clases WHERE id_clase = ?", (id_clase,))
    conn.commit()
    conn.close()
    return redirect(url_for('gestion_bp.gestion'))

# --- NUEVAS FUNCIONES PARA EDITAR CLASES ---

@gestion_bp.route('/gestion/edit_clase/<int:id_clase>')
def edit_clase_form(id_clase):
    """Muestra el formulario para editar una clase existente."""
    conn = get_db_connection()
    clase = conn.execute("SELECT * FROM clases WHERE id_clase = ?", (id_clase,)).fetchone()
    if clase is None:
        abort(404)
    cursos = conn.execute("SELECT id_curso, nombre FROM cursos ORDER BY nombre ASC").fetchall()
    profesores = conn.execute("SELECT id_profesor, nombre FROM profesores ORDER BY nombre ASC").fetchall()
    semestres = conn.execute("SELECT id_semestre, nombre FROM semestres ORDER BY nombre DESC").fetchall()
    conn.close()
    return render_template('edit_clase.html', clase=clase, cursos=cursos, profesores=profesores, semestres=semestres)

@gestion_bp.route('/gestion/update_clase/<int:id_clase>', methods=['POST'])
def update_clase(id_clase):
    """Procesa la actualización de los datos de una clase."""
    if request.method == 'POST':
        nombre = request.form['nombre']
        descripcion = request.form.get('descripcion')
        n_horas = request.form.get('n_horas')
        horas_semana = request.form.get('horas_semana')
        id_curso = request.form.get('id_curso')
        id_profesor = request.form.get('id_profesor')
        id_semestre = request.form.get('id_semestre')
        conn = get_db_connection()
        conn.execute("""
            UPDATE clases SET
                nombre = ?,
                descripcion = ?,
                n_horas = ?,
                horas_semana = ?,
                id_curso = ?,
                id_profesor = ?,
                id_semestre = ?
            WHERE id_clase = ?
        """, (nombre, descripcion, n_horas, horas_semana, id_curso, id_profesor, id_semestre, id_clase))
        conn.commit()
        conn.close()
    return redirect(url_for('gestion_bp.gestion'))
