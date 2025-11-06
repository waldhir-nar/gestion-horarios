from flask import Blueprint, render_template, request, redirect, url_for, flash
from database import get_db_connection
import sqlite3
import pulp # <-- AÑADIDO: Importar PuLP

horarios_bp = Blueprint('horarios_bp', __name__,
                        template_folder='templates',
                        url_prefix='/horarios')

def _organize_schedule_for_display(details):
    """
    Helper function to process db records into a structured grid for the template.
    """
    days_of_week = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes']
    
    if not details:
        return {}, [], days_of_week

    hours = sorted(list(set(d['h_inicio'] for d in details)))

    schedule_grid = {hour: {day: None for day in days_of_week} for hour in hours}

    for detail in details:
        hour = detail['h_inicio']
        day = detail['dia']
        if hour in schedule_grid and day in schedule_grid[hour]:
            schedule_grid[hour][day] = detail

    return schedule_grid, hours, days_of_week

@horarios_bp.route('/')
def lista_horarios():
    conn = get_db_connection()
    cronogramas = conn.execute("""
        SELECT cr.id_cronograma, cr.nombre, cu.nombre as curso_nombre
        FROM cronogramas cr
        LEFT JOIN cursos cu ON cr.id_curso = cu.id_curso
        ORDER BY cr.id_cronograma DESC
    """).fetchall()
    
    horarios_procesados = {}
    for cronograma in cronogramas:
        id_c = cronograma['id_cronograma']
        detalles_rows = conn.execute("""
            SELECT d.dia, d.h_inicio, d.h_fin, cl.nombre as clase_nombre, 
                   pr.nombre as profesor_nombre, cu.nombre as curso_nombre, 
                   se.nombre as semestre_nombre
            FROM detalle_cronogramas d
            JOIN clases cl ON d.id_clase = cl.id_clase
            JOIN cursos cu ON cl.id_curso = cu.id_curso
            JOIN profesores pr ON cl.id_profesor = pr.id_profesor
            LEFT JOIN semestres se ON cl.id_semestre = se.id_semestre
            WHERE d.id_cronograma = ?
        """, (id_c,)).fetchall()
        
        detalles_list = [dict(row) for row in detalles_rows]
        
        # Extraer el nombre del semestre del primer detalle (si existe)
        semestre_nombre = None
        if detalles_list:
            semestre_nombre = detalles_list[0]['semestre_nombre']

        schedule_grid, sorted_hours, days_of_week = _organize_schedule_for_display(detalles_list)
        
        horarios_procesados[id_c] = {
            'id_cronograma': cronograma['id_cronograma'],
            'nombre': cronograma['nombre'],
            'curso_nombre': cronograma['curso_nombre'], # Se mantiene como fallback
            'semestre_nombre': semestre_nombre, # Se añade el semestre
            'grid': schedule_grid,
            'sorted_hours': sorted_hours,
            'days_of_week': days_of_week
        }
    conn.close()
    return render_template("horarios.html", horarios_guardados=horarios_procesados)


@horarios_bp.route('/add')
def add_horario_form():
    conn = get_db_connection()
    cronogramas_rows = conn.execute("""
        SELECT cr.id_cronograma, cr.nombre, cr.id_curso, cu.nombre as curso_nombre
        FROM cronogramas cr
        LEFT JOIN cursos cu ON cr.id_curso = cu.id_curso
        ORDER BY cr.nombre ASC
    """).fetchall()
    semestres_rows = conn.execute("SELECT id_semestre, nombre FROM semestres ORDER BY nombre DESC").fetchall()
    profesores_rows = conn.execute("SELECT id_profesor, nombre FROM profesores ORDER BY nombre ASC").fetchall()
    clases_rows = conn.execute("""
        SELECT cl.id_clase, cl.nombre, cl.id_profesor, cu.id_curso, cu.nombre as curso_nombre, se.nombre as semestre_nombre
        FROM clases cl
        JOIN cursos cu ON cl.id_curso = cu.id_curso
        LEFT JOIN semestres se ON cl.id_semestre = se.id_semestre
        ORDER BY cu.nombre, cl.nombre
    """).fetchall()
    cursos_rows = conn.execute("SELECT id_curso, nombre FROM cursos ORDER BY nombre ASC").fetchall()
    conn.close()

    cronogramas = [dict(row) for row in cronogramas_rows]
    semestres = [dict(row) for row in semestres_rows]
    profesores = [dict(row) for row in profesores_rows]
    clases = [dict(row) for row in clases_rows]
    cursos = [dict(row) for row in cursos_rows]

    return render_template("add_horario.html", 
                           cronogramas=cronogramas,
                           semestres=semestres,
                           profesores=profesores,
                           clases=clases, 
                           cursos=cursos)

@horarios_bp.route('/crear_cronograma', methods=['POST'])
def crear_cronograma():
    nombre_cronograma = request.form.get('nombre_cronograma')
    id_curso = request.form.get('id_curso')
    if not nombre_cronograma or not id_curso:
        flash("Tanto el nombre del horario como el curso son obligatorios.", "error")
        return redirect(url_for('horarios_bp.add_horario_form'))
    conn = get_db_connection()
    try:
        conn.execute("INSERT INTO cronogramas (nombre, id_curso) VALUES (?, ?)", (nombre_cronograma, id_curso))
        conn.commit()
        flash(f"Horario '{nombre_cronograma}' creado y asociado al curso con éxito.", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Error al crear el horario: {e}", "error")
    finally:
        conn.close()
    return redirect(url_for('horarios_bp.add_horario_form'))

@horarios_bp.route('/crear', methods=['POST'])
def crear_horario():
    # --- RECOGIDA DE DATOS ---
    id_cronograma = request.form.get('id_cronograma')
    id_clase = request.form.get('id_clase')
    id_semestre_form = request.form.get('id_semestre')
    dia = request.form.get('dia')
    h_inicio = request.form.get('h_inicio')
    h_fin = request.form.get('h_fin')

    # --- VALIDACIONES BÁSICAS ---
    if not all([id_cronograma, id_clase, id_semestre_form, dia, h_inicio, h_fin]):
        flash("Error: Todos los campos del formulario son obligatorios.", "error")
        return redirect(url_for('horarios_bp.add_horario_form'))
    
    if h_inicio >= h_fin:
        flash("Error: La hora de inicio debe ser anterior a la hora de fin.", "error")
        return redirect(url_for('horarios_bp.add_horario_form'))

    conn = get_db_connection()
    try:
        clase_info = conn.execute("SELECT id_curso, id_semestre FROM clases WHERE id_clase = ?", (id_clase,)).fetchone()
        if not clase_info:
            flash(f"Error: No se encontró la clase con ID {id_clase}.", "error")
            conn.close()
            return redirect(url_for('horarios_bp.add_horario_form'))
        
        id_curso_clase = clase_info['id_curso']
        id_semestre_clase = clase_info['id_semestre']

        if str(id_semestre_clase) != id_semestre_form:
            semestre_clase_nombre = conn.execute("SELECT nombre FROM semestres WHERE id_semestre = ?", (id_semestre_clase,)).fetchone()['nombre']
            semestre_form_nombre = conn.execute("SELECT nombre FROM semestres WHERE id_semestre = ?", (id_semestre_form,)).fetchone()['nombre']
            flash(f"Conflicto de semestres: La clase pertenece a '{semestre_clase_nombre}' pero seleccionaste '{semestre_form_nombre}'.", "error")
            conn.close()
            return redirect(url_for('horarios_bp.add_horario_form'))

        cronograma_info = conn.execute("SELECT id_curso, nombre FROM cronogramas WHERE id_cronograma = ?", (id_cronograma,)).fetchone()
        id_curso_cronograma = cronograma_info['id_curso']
        if id_curso_cronograma is not None and id_curso_cronograma != id_curso_clase:
            curso_clase_nombre = conn.execute("SELECT nombre FROM cursos WHERE id_curso = ?", (id_curso_clase,)).fetchone()['nombre']
            curso_horario_nombre = conn.execute("SELECT nombre FROM cursos WHERE id_curso = ?", (id_curso_cronograma,)).fetchone()['nombre']
            flash(f"Conflicto de cursos: La clase es de '{curso_clase_nombre}' pero el horario es para '{curso_horario_nombre}'.", "error")
            conn.close()
            return redirect(url_for('horarios_bp.add_horario_form'))

        primera_clase_horario = conn.execute("SELECT cl.id_semestre FROM detalle_cronogramas dc JOIN clases cl ON dc.id_clase = cl.id_clase WHERE dc.id_cronograma = ? LIMIT 1", (id_cronograma,)).fetchone()
        if primera_clase_horario and primera_clase_horario['id_semestre'] != id_semestre_clase:
            semestre_existente_nombre = conn.execute("SELECT nombre FROM semestres WHERE id_semestre = ?", (primera_clase_horario['id_semestre'],)).fetchone()['nombre']
            semestre_clase_nombre = conn.execute("SELECT nombre FROM semestres WHERE id_semestre = ?", (id_semestre_clase,)).fetchone()['nombre']
            flash(f"Conflicto de horario: Este horario ya contiene clases del '{semestre_existente_nombre}'. No puedes añadir una clase del '{semestre_clase_nombre}'.", "error")
            conn.close()
            return redirect(url_for('horarios_bp.add_horario_form'))
        
        conflicto_horario = conn.execute("""
            SELECT dc.h_inicio, dc.h_fin, cl.nombre FROM detalle_cronogramas dc
            JOIN clases cl ON dc.id_clase = cl.id_clase
            WHERE dc.id_cronograma = ? AND dc.dia = ? AND dc.h_fin > ? AND dc.h_inicio < ?
        """, (id_cronograma, dia, h_inicio, h_fin)).fetchone()

        if conflicto_horario:
            flash(f"Conflicto de horario: El rango de {h_inicio} a {h_fin} se solapa con la clase '{conflicto_horario['nombre']}' ({conflicto_horario['h_inicio']} - {conflicto_horario['h_fin']}) el mismo día.", "error")
            conn.close()
            return redirect(url_for('horarios_bp.add_horario_form'))

        conn.execute("INSERT INTO detalle_cronogramas (id_cronograma, dia, h_inicio, h_fin, id_clase, id_curso) VALUES (?, ?, ?, ?, ?, ?)", (id_cronograma, dia, h_inicio, h_fin, id_clase, id_curso_clase))
        conn.commit()
        flash("Clase agregada al horario con éxito.", "success")

    except Exception as e:
        conn.rollback()
        flash(f"Ocurrió un error inesperado: {e}", "error")
    finally:
        conn.close()

    return redirect(url_for('horarios_bp.add_horario_form'))

@horarios_bp.route('/crear_automatico')
def crear_horario_auto_form():
    """Muestra el formulario para iniciar la creación automática de horarios."""
    conn = get_db_connection()
    cursos = conn.execute("SELECT id_curso, nombre FROM cursos ORDER BY nombre ASC").fetchall()
    semestres = conn.execute("SELECT id_semestre, nombre FROM semestres ORDER BY nombre DESC").fetchall()
    conn.close()
    return render_template('crear_horario_auto.html', cursos=cursos, semestres=semestres)

@horarios_bp.route('/ejecutar_creacion_automatica', methods=['POST'])
def ejecutar_creacion_automatica():
    """Ejecuta el algoritmo de generación automática de horarios usando PuLP."""
    nombre_cronograma = request.form.get('nombre')
    id_curso = request.form.get('id_curso')
    id_semestre = request.form.get('id_semestre')

    if not all([nombre_cronograma, id_curso, id_semestre]):
        flash("Nombre, curso y semestre son obligatorios.", "error")
        return redirect(url_for('horarios_bp.crear_horario_auto_form'))

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO cronogramas (nombre, id_curso) VALUES (?, ?)", (nombre_cronograma, id_curso))
        id_cronograma = cursor.lastrowid

        # --- Definir el problema de optimización ---
        prob = pulp.LpProblem("Generacion_Horarios", pulp.LpMinimize)

        # --- Obtener datos para el modelo ---
        clases_raw = conn.execute("""
            SELECT id_clase, nombre, horas_semana, id_profesor
            FROM clases WHERE id_curso = ? AND id_semestre = ? AND horas_semana > 0
        """, (id_curso, id_semestre)).fetchall()

        if not clases_raw:
            flash("No se encontraron clases con horas asignadas para este curso y semestre.", "warning")
            conn.commit() # Guardar el cronograma vacío
            return redirect(url_for('horarios_bp.lista_horarios'))

        # Convertir a diccionarios para fácil acceso
        clases_a_planificar = {c['id_clase']: dict(c) for c in clases_raw}
        ids_clases = list(clases_a_planificar.keys())
        ids_profesores = list(set(c['id_profesor'] for c in clases_a_planificar.values()))

        dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes']
        horas = [f"{h:02d}:00" for h in range(7, 18)] # Horario de 7 AM a 5 PM
        bloques_horarios = [(d, h) for d in dias for h in horas]

        # --- Crear variables de decisión ---
        # x[(id_clase, dia, hora)] = 1 si la clase se da en ese bloque, 0 si no
        vars_horario = pulp.LpVariable.dicts("Horario", (ids_clases, dias, horas), 0, 1, pulp.LpBinary)

        # --- Objetivo (dummy): solo queremos una solución factible ---
        prob += 0, "Función Objetivo Dummy"

        # --- Añadir Restricciones ---
        # 1. Cada clase debe cumplir sus horas semanales
        for id_c, clase in clases_a_planificar.items():
            prob += pulp.lpSum(vars_horario[id_c][d][h] for d, h in bloques_horarios) == clase['horas_semana'], f"Horas_Semanales_{id_c}"

        # 2. En un bloque (día, hora) determinado, solo puede haber una clase del curso actual
        for d, h in bloques_horarios:
            prob += pulp.lpSum(vars_horario[id_c][d][h] for id_c in ids_clases) <= 1, f"Unicidad_Curso_{d}_{h}"

        # 3. Un profesor no puede dar dos clases a la vez (en ningún curso/horario)
        profesores_ocupados = conn.execute("""
            SELECT cl.id_profesor, dc.dia, dc.h_inicio 
            FROM detalle_cronogramas dc
            JOIN clases cl ON dc.id_clase = cl.id_clase
            WHERE cl.id_profesor IN (%s)
        """ % ','.join('?' for _ in ids_profesores), ids_profesores).fetchall()
        
        horarios_profesores_ocupados = {}
        for p in profesores_ocupados:
            horarios_profesores_ocupados.setdefault(p['id_profesor'], []).append((p['dia'], p['h_inicio']))

        for id_p in ids_profesores:
            clases_del_profesor = [id_c for id_c, clase in clases_a_planificar.items() if clase['id_profesor'] == id_p]
            for d, h in bloques_horarios:
                # Suma de clases del profesor en el bloque actual
                suma_clases_profesor_actual = pulp.lpSum(vars_horario[id_c][d][h] for id_c in clases_del_profesor)
                
                # Comprobar si el profesor ya está ocupado por otro horario
                if (d, h) in horarios_profesores_ocupados.get(id_p, []):
                    # Si ya está ocupado, no puede dar ninguna clase del horario actual
                    prob += suma_clases_profesor_actual == 0, f"Conflicto_Profesor_Ocupado_{id_p}_{d}_{h}"
                else:
                    # Si no está ocupado, solo puede dar una clase a la vez
                    prob += suma_clases_profesor_actual <= 1, f"Unicidad_Profesor_{id_p}_{d}_{h}"

        # --- Resolver el problema ---
        prob.solve(pulp.PULP_CBC_CMD(msg=0)) # msg=0 para suprimir logs de PuLP

        # --- Procesar el resultado ---
        if pulp.LpStatus[prob.status] == 'Optimal':
            for id_clase in ids_clases:
                for d in dias:
                    for h in horas:
                        if vars_horario[id_clase][d][h].varValue == 1:
                            h_inicio_num = int(h.split(':')[0])
                            h_fin = f"{h_inicio_num + 1:02d}:00"
                            cursor.execute("""
                                INSERT INTO detalle_cronogramas (id_cronograma, dia, h_inicio, h_fin, id_clase, id_curso)
                                VALUES (?, ?, ?, ?, ?, ?)
                            """, (id_cronograma, d, h, h_fin, id_clase, id_curso))
            conn.commit()
            flash(f"Horario '{nombre_cronograma}' generado con éxito usando optimización.", "success")
        else:
            # Si no se encuentra solución, revertir la creación del cronograma
            conn.rollback()
            flash(f"No se pudo generar un horario que cumpliera todas las restricciones. Posibles causas: falta de disponibilidad de profesores, demasiadas horas de clase para los bloques disponibles.", "error")
            # Es importante eliminar el cronograma vacío que se creó al inicio
            return redirect(url_for('horarios_bp.crear_horario_auto_form'))

    except sqlite3.IntegrityError:
        conn.rollback()
        flash(f"Error: El nombre del horario '{nombre_cronograma}' ya existe. Por favor, elige otro.", "error")
        return redirect(url_for('horarios_bp.crear_horario_auto_form'))
    except Exception as e:
        conn.rollback()
        flash(f"Ocurrió un error inesperado durante la generación: {e}", "error")
        return redirect(url_for('horarios_bp.crear_horario_auto_form'))
    finally:
        conn.close()

    return redirect(url_for('horarios_bp.lista_horarios'))

@horarios_bp.route('/delete/<int:id_cronograma>', methods=['POST'])
def delete_horario(id_cronograma):
    """Elimina un horario y todos sus detalles."""
    conn = get_db_connection()
    try:
        # Eliminar primero los detalles del cronograma
        conn.execute("DELETE FROM detalle_cronogramas WHERE id_cronograma = ?", (id_cronograma,))
        # Luego, eliminar el cronograma principal
        conn.execute("DELETE FROM cronogramas WHERE id_cronograma = ?", (id_cronograma,))
        conn.commit()
        flash("El horario y todos sus detalles han sido eliminados con éxito.", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Error al eliminar el horario: {e}", "error")
    finally:
        conn.close()
    return redirect(url_for('horarios_bp.lista_horarios'))
