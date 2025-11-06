
from flask import Blueprint, render_template, request, redirect, url_for, flash
from database import get_db_connection
import sqlite3
import pulp

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
        
        semestre_nombre = None
        if detalles_list:
            semestre_nombre = detalles_list[0]['semestre_nombre']

        schedule_grid, sorted_hours, days_of_week = _organize_schedule_for_display(detalles_list)
        
        horarios_procesados[id_c] = {
            'id_cronograma': cronograma['id_cronograma'],
            'nombre': cronograma['nombre'],
            'curso_nombre': cronograma['curso_nombre'],
            'semestre_nombre': semestre_nombre,
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
    except sqlite3.IntegrityError:
        conn.rollback()
        flash("no se puede crear dos horarios con el mismo nombre", "error")
    except Exception as e:
        conn.rollback()
        flash(f"Error al crear el horario: {e}", "error")
    finally:
        conn.close()
    return redirect(url_for('horarios_bp.add_horario_form'))

@horarios_bp.route('/crear', methods=['POST'])
def crear_horario():
    id_cronograma = request.form.get('id_cronograma')
    id_clase = request.form.get('id_clase')
    id_semestre_form = request.form.get('id_semestre')
    dia = request.form.get('dia')
    h_inicio = request.form.get('h_inicio')
    h_fin = request.form.get('h_fin')

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


# --- Constantes para la Optimización ---
LIMITE_HORAS_DIARIAS = 4
PENALIZACION_EXCESO_HORAS = 100 
PENALIZACION_INICIO_BLOQUE = 10
PENALIZACION_HUECO = 1
M = 1000 # Un valor 'M' grande para las restricciones de tipo Big M

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
        # --- VALIDACIÓN: Verificar si el nombre ya existe antes de INSERTAR ---
        cursor.execute("SELECT id_cronograma FROM cronogramas WHERE nombre = ?", (nombre_cronograma,))
        if cursor.fetchone():
            flash(f"Error: Ya existe un horario con el nombre '{nombre_cronograma}'. Por favor, elige otro.", "error")
            conn.close()
            return redirect(url_for('horarios_bp.crear_horario_auto_form'))
        cursor.execute("INSERT INTO cronogramas (nombre, id_curso) VALUES (?, ?)", (nombre_cronograma, id_curso))
        id_cronograma = cursor.lastrowid

        # --- Obtener datos para el modelo ---
        clases_raw = conn.execute("""
            SELECT id_clase, nombre, horas_semana, id_profesor
            FROM clases WHERE id_curso = ? AND id_semestre = ? AND horas_semana > 0
        """, (id_curso, id_semestre)).fetchall()

        if not clases_raw:
            flash("No se encontraron clases con horas asignadas para este curso y semestre.", "warning")
            conn.commit()
            return redirect(url_for('horarios_bp.lista_horarios'))

        clases_a_planificar = {c['id_clase']: dict(c) for c in clases_raw}
        ids_clases = list(clases_a_planificar.keys())
        ids_profesores = list(set(c['id_profesor'] for c in clases_a_planificar.values()))

        dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes']
        horas = [f"{h:02d}:00" for h in range(7, 18)]

        # --- Definir el problema de optimización ---
        prob = pulp.LpProblem("Generacion_Horarios_Optimizacion", pulp.LpMinimize)

        # --- Variables de Decisión ---
        vars_horario = pulp.LpVariable.dicts("Horario", (ids_clases, dias, horas), 0, 1, pulp.LpBinary)

        # --- Variables Auxiliares para Costes (Centradas en el Día) ---
        slot_ocupado = pulp.LpVariable.dicts("SlotOcupado", (dias, horas), 0, 1, pulp.LpBinary)
        horas_por_dia = pulp.LpVariable.dicts("HorasPorDia", dias, 0, None, pulp.LpInteger)
        exceso_diario = pulp.LpVariable.dicts("ExcesoDiario", dias, 0, None, pulp.LpInteger)
        inicio_bloque = pulp.LpVariable.dicts("InicioBloque", (dias, horas), 0, 1, pulp.LpBinary)
        hueco = pulp.LpVariable.dicts("Hueco", (dias, horas), 0, 1, pulp.LpBinary)

        # --- Función Objetivo (Minimizar Penalizaciones del Horario del Estudiante) ---
        prob += (
            pulp.lpSum(exceso_diario[d] for d in dias) * PENALIZACION_EXCESO_HORAS
            + pulp.lpSum(inicio_bloque[d][h] for d in dias for h in horas) * PENALIZACION_INICIO_BLOQUE
            + pulp.lpSum(hueco[d][h] for d in dias for h in horas[1:-1]) * PENALIZACION_HUECO
        ), "Costo_Total_Horario_Estudiante"

        # --- Restricciones Duras (Innegociables) ---
        # 1. Cada clase debe cumplir sus horas semanales
        for id_c, clase in clases_a_planificar.items():
            prob += pulp.lpSum(vars_horario[id_c][d][h] for d in dias for h in horas) == clase['horas_semana'], f"Horas_Semanales_{id_c}"

        # 2. Unicidad del Slot de Horario (Un solo slot ocupado a la vez)
        for d in dias:
            for h in horas:
                prob += slot_ocupado[d][h] == pulp.lpSum(vars_horario[id_c][d][h] for id_c in ids_clases), f"Define_Slot_Ocupado_{d}_{h}"

        # 3. No Colisión de Profesores (Un profesor solo puede dar una clase a la vez)
        clases_por_profesor = {id_p: [id_c for id_c, clase in clases_a_planificar.items() if clase['id_profesor'] == id_p] for id_p in ids_profesores}
        profesores_ocupados = conn.execute("SELECT cl.id_profesor, dc.dia, dc.h_inicio FROM detalle_cronogramas dc JOIN clases cl ON dc.id_clase = cl.id_clase").fetchall()
        horarios_profesores_ocupados = {}
        for p in profesores_ocupados:
            horarios_profesores_ocupados.setdefault(p['id_profesor'], []).append((p['dia'], p['h_inicio']))

        for id_p in ids_profesores:
            for d in dias:
                for h in horas:
                    suma_clases_profesor_actual = pulp.lpSum(vars_horario[id_c][d][h] for id_c in clases_por_profesor.get(id_p, []))
                    if (d, h) in horarios_profesores_ocupados.get(id_p, []):
                        prob += suma_clases_profesor_actual == 0, f"Conflicto_Externo_Profesor_{id_p}_{d}_{h}"
                    else:
                        prob += suma_clases_profesor_actual <= 1, f"Unicidad_Interna_Profesor_{id_p}_{d}_{h}"

        # --- Restricciones para Cálculo de Costes (Penalizaciones Flexibles) ---
        for d in dias:
            # 4. Cálculo de horas totales por día
            prob += horas_por_dia[d] == pulp.lpSum(slot_ocupado[d][h] for h in horas), f"Calc_Horas_Por_Dia_{d}"
            # Penalización si las horas del día exceden el límite
            prob += exceso_diario[d] >= horas_por_dia[d] - LIMITE_HORAS_DIARIAS, f"Penaliza_Exceso_{d}"

            # 5. Penalización por cada inicio de bloque en el día
            h0 = horas[0]
            prob += inicio_bloque[d][h0] == slot_ocupado[d][h0], f"Inicio_Bloque_Dia_0_{d}"
            for k in range(1, len(horas)):
                h_actual = horas[k]
                h_anterior = horas[k-1]
                prob += inicio_bloque[d][h_actual] >= slot_ocupado[d][h_actual] - slot_ocupado[d][h_anterior], f"Inicio_Bloque_Dia_Logic_{d}_{h_actual}"

            # 6. Penalización por huecos en el día
            for k in range(len(horas) - 2):
                h_anterior = horas[k]
                h_siguiente = horas[k+2]
                h_actual = horas[k+1]
                # Un hueco es [OCUPADO, VACIO, OCUPADO]
                prob += hueco[d][h_actual] >= slot_ocupado[d][h_anterior] + slot_ocupado[d][h_siguiente] - slot_ocupado[d][h_actual] - 1, f"Hueco_Dia_Logic_{d}_{h_actual}"

        # --- Resolver el problema ---
        prob.solve(pulp.PULP_CBC_CMD(msg=0))

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
            flash(f"Horario '{nombre_cronograma}' generado con éxito. Costo de penalización: {pulp.value(prob.objective):.2f}", "success")
        else:
            conn.rollback()
            flash(f"No se pudo generar un horario que cumpliera todas las restricciones. Estado: {pulp.LpStatus[prob.status]}", "error")
            return redirect(url_for('horarios_bp.crear_horario_auto_form'))

    except sqlite3.IntegrityError:
        conn.rollback()
        flash("no se puede crear dos horarios con el mismo nombre", "error")
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
        conn.execute("DELETE FROM detalle_cronogramas WHERE id_cronograma = ?", (id_cronograma,))
        conn.execute("DELETE FROM cronogramas WHERE id_cronograma = ?", (id_cronograma,))
        conn.commit()
        flash("El horario y todos sus detalles han sido eliminados con éxito.", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Error al eliminar el horario: {e}", "error")
    finally:
        conn.close()
    return redirect(url_for('horarios_bp.lista_horarios'))
