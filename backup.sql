BEGIN TRANSACTION;
CREATE TABLE clases (
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
INSERT INTO "clases" VALUES(1,'Matemáticas discretas',' rama de las matemáticas que estudia objetos finitos o infinitos, pero numerables, como los números enteros, los grafos o las proposiciones lógica',2,4,2,2,1);
CREATE TABLE cronogramas (
        id_cronograma INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL
    );
CREATE TABLE cursos (
        id_curso INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        descripcion TEXT
    );
INSERT INTO "cursos" VALUES(1,'Ing. de sistemas semetre VII (grupo principal)','es el grupo principal de ingeniera de sistemas septimo semestre');
INSERT INTO "cursos" VALUES(2,'Ing. de sistemas semetre VIII (grupo principal)','es el grupo principal de ingeniería de sistemas octavo semestre');
CREATE TABLE detalle_cronogramas (
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
CREATE TABLE paralelos (
        id_paralelo INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        descripcion TEXT,
        id_curso INTEGER,
        FOREIGN KEY (id_curso) REFERENCES cursos(id_curso)
    );
CREATE TABLE profesores (
        id_profesor INTEGER PRIMARY KEY AUTOINCREMENT,
        cedula TEXT NOT NULL,
        nombre TEXT NOT NULL,
        correo TEXT,
        telefono TEXT
    );
INSERT INTO "profesores" VALUES(1,'1234567890','Profesor de Ejemplo','profe@ejemplo.com','555-1234');
INSERT INTO "profesores" VALUES(2,'261719012','Ricky Abuabara Cortés','ricky.abuabara@pca.edu.co','3168651608');
CREATE TABLE semestres (
        id_semestre INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        fecha_inicio TEXT,
        fecha_fin TEXT
    );
INSERT INTO "semestres" VALUES(1,'2025-1','2025-02-03','2025-05-31');
DELETE FROM "sqlite_sequence";
INSERT INTO "sqlite_sequence" VALUES('profesores',2);
INSERT INTO "sqlite_sequence" VALUES('cursos',2);
INSERT INTO "sqlite_sequence" VALUES('semestres',1);
INSERT INTO "sqlite_sequence" VALUES('clases',1);
COMMIT;
