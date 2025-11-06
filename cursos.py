from flask import Blueprint, render_template, request, redirect, url_for, flash
from database import get_db_connection

cursos_bp = Blueprint('cursos_bp', __name__, template_folder='templates')

@cursos_bp.route("/")
def lista(): 
    conn = get_db_connection()
    lista_cursos = conn.execute("SELECT id_curso, nombre, descripcion FROM cursos ORDER BY nombre ASC").fetchall()
    conn.close()
    return render_template("cursos.html", cursos=lista_cursos)

@cursos_bp.route("/add", methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        descripcion = request.form.get('descripcion', '').strip()

        if not nombre:
            flash("El nombre del curso es obligatorio.", "error")
            return render_template("add_curso.html", nombre=nombre, descripcion=descripcion)

        conn = get_db_connection()
        # VERIFICACIÓN DE DUPLICADOS (case-insensitive)
        existe = conn.execute('SELECT id_curso FROM cursos WHERE LOWER(nombre) = ?', (nombre.lower(),)).fetchone()
        
        if existe:
            conn.close()
            flash('Ya existe un curso con este nombre. Por favor, elige otro.', 'error')
            return render_template("add_curso.html", nombre=nombre, descripcion=descripcion)

        conn.execute("INSERT INTO cursos (nombre, descripcion) VALUES (?, ?)", (nombre, descripcion))
        conn.commit()
        conn.close()
        flash(f"Curso '{nombre}' añadido con éxito.", "success")
        return redirect(url_for('cursos_bp.lista'))

    return render_template("add_curso.html")

@cursos_bp.route("/edit/<int:id_curso>", methods=['GET', 'POST'])
def edit(id_curso):
    conn = get_db_connection()

    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        descripcion = request.form.get('descripcion', '').strip()

        if not nombre:
            flash("El nombre del curso es un campo obligatorio.", "error")
            curso_para_template = {'id_curso': id_curso, 'nombre': nombre, 'descripcion': descripcion}
            return render_template('edit_curso.html', curso=curso_para_template)

        # VERIFICACIÓN DE DUPLICADOS (case-insensitive, excluyendo el curso actual)
        existe = conn.execute('SELECT id_curso FROM cursos WHERE LOWER(nombre) = ? AND id_curso != ?',
                              (nombre.lower(), id_curso)).fetchone()

        if existe:
            conn.close()
            flash('Ya existe otro curso con este nombre. Por favor, elige otro.', 'error')
            curso_para_template = {'id_curso': id_curso, 'nombre': nombre, 'descripcion': descripcion}
            return render_template('edit_curso.html', curso=curso_para_template)

        conn.execute('UPDATE cursos SET nombre = ?, descripcion = ? WHERE id_curso = ?', (nombre, descripcion, id_curso))
        conn.commit()
        conn.close()
        flash('Curso actualizado con éxito.', 'success')
        return redirect(url_for('cursos_bp.lista'))

    # Lógica para GET
    curso = conn.execute('SELECT * FROM cursos WHERE id_curso = ?', (id_curso,)).fetchone()
    conn.close()
    
    if curso is None:
        flash('El curso que intentas editar no existe.', 'error')
        return redirect(url_for('cursos_bp.lista'))
        
    return render_template('edit_curso.html', curso=curso)

@cursos_bp.route("/delete/<int:id_curso>", methods=['POST'])
def delete(id_curso):
    conn = get_db_connection()
    conn.execute("DELETE FROM cursos WHERE id_curso = ?", (id_curso,))
    conn.commit()
    conn.close()
    flash('Curso eliminado con éxito.', 'success')
    return redirect(url_for('cursos_bp.lista'))
