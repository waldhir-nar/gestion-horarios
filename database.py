import sqlite3

DATABASE_NAME = 'horarios.db'

def get_db_connection():
    """Crea y retorna una conexión a la base de datos SQLite."""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Inicializa la base de datos y crea todas las tablas si no existen."""
    conn = get_db_connection()
    cursor = conn.cursor()

    schema = """
    CREATE TABLE IF NOT EXISTS semestres (
        id_semestre INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        fecha_inicio TEXT,
        fecha_fin TEXT
    );

    CREATE TABLE IF NOT EXISTS profesores (
        id_profesor INTEGER PRIMARY KEY AUTOINCREMENT,
        cedula TEXT NOT NULL,
        nombre TEXT NOT NULL,
        correo TEXT,
        telefono TEXT
    );

    CREATE TABLE IF NOT EXISTS cursos (
        id_curso INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        descripcion TEXT
    );

    CREATE TABLE IF NOT EXISTS paralelos (
        id_paralelo INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        descripcion TEXT,
        id_curso INTEGER,
        FOREIGN KEY (id_curso) REFERENCES cursos(id_curso)
    );

    CREATE TABLE IF NOT EXISTS clases (
        id_clase INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        descripcion TEXT,
        n_horas INTEGER,
        horas_semana INTEGER,
        id_curso INTEGER,
        id_profesor INTEGER,
        id_semestre INTEGER,
        FOREIGN KEY (id_curso) REFERENCES cursos(id_curso),
        FOREIGN KEY (id_profesor) REFERENCES profesores(id_profesor),
        FOREIGN KEY (id_semestre) REFERENCES semestres(id_semestre)
    );

    /* MODIFICACIÓN: Se añade la restricción UNIQUE a la columna nombre */
    CREATE TABLE IF NOT EXISTS cronogramas (
        id_cronograma INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        id_curso INTEGER,
        FOREIGN KEY (id_curso) REFERENCES cursos(id_curso)
    );

    CREATE TABLE IF NOT EXISTS detalle_cronogramas (
        id_detalle INTEGER PRIMARY KEY AUTOINCREMENT,
        id_cronograma INTEGER,
        dia TEXT,
        h_inicio TEXT,
        h_fin TEXT,
        id_clase INTEGER,
        id_curso INTEGER,
        FOREIGN KEY (id_clase) REFERENCES clases(id_clase),
        FOREIGN KEY (id_curso) REFERENCES cursos(id_curso),
        FOREIGN KEY (id_cronograma) REFERENCES cronogramas(id_cronograma)
    );
    """
   
    cursor.executescript(schema)
    print("Base de datos 'horarios.db' y todas sus tablas han sido creadas/verificadas.")
   
    cursor.execute("SELECT COUNT(*) FROM profesores")
    count = cursor.fetchone()[0]
    if count == 0:
        cursor.execute("INSERT INTO profesores (cedula, nombre, correo, telefono) VALUES (?, ?, ?, ?)",
                       ('1234567890', 'Profesor de Ejemplo', 'profe@ejemplo.com', '555-1234'))
        conn.commit()
        print("Profesor de ejemplo insertado.")

    conn.close()
