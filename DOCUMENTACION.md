
#en la biblioteca de optimización lineal **PuLP**. Este sistema traduce la creación del horario en un modelo matemático para encontrar una solución óptima que respete todas las reglas y restricciones definidas.

## 2. Tecnologías Utilizadas

- **Backend:** Python 3
- **Framework Web:** Flask
- **Base de Datos:** SQLite 3
- **Frontend:** HTML5, CSS3
- **Motor de Optimización:** PuLP
- **Dependencias Principales:** Ver `requirements.txt` (Flask, Werkzeug, PyMySQL, PuLP)

## 3. Estructura del Proyecto

```
/
|-- main.py                 # Punto de entrada principal de la aplicación Flask.
|-- database.py             # Módulo para la conexión y creación de la BD.
|-- init_db.py              # Script para inicializar la base de datos.
|-- horarios.db             # Archivo de la base de datos SQLite.
|-- devserver.sh            # Script para iniciar el servidor de desarrollo.
|-- requirements.txt        # Lista de dependencias de Python.
|
|-- horarios.py             # Blueprint y lógica para la gestión de horarios.
|-- gestion.py              # Blueprint y lógica para la gestión de clases y semestres.
|-- cursos.py               # Blueprint y lógica para la gestión de cursos.
|-- profesores.py           # Blueprint y lógica para la gestión de profesores.
|
|-- templates/              # Carpeta con todas las plantillas HTML.
|   |-- index.html          # Página de inicio.
|   |-- horarios.html       # Visualización de los horarios.
|   |-- crear_horario_auto.html # Formulario para generación automática.
|   |-- add_horario.html    # Formulario para creación manual.
|   |-- gestion.html        # Panel de gestión de clases y semestres.
|   |-- (y otros archivos HTML para CRUDs)
|
|-- static/                 # Carpeta con archivos estáticos (CSS, JS, imágenes).
|   |-- style.css           # Estilos generales.
|   |-- (y otros archivos CSS)
```

## 4. Instalación y Puesta en Marcha

1.  **Clonar el Repositorio:** `git clone <URL_DEL_REPOSITORIO>`
2.  **Crear Entorno Virtual:** `python -m venv .venv`
3.  **Activar Entorno Virtual:** `source .venv/bin/activate` (en Linux/macOS) o `.\.venv\Scripts\activate` (en Windows).
4.  **Instalar Dependencias:** `pip install -r requirements.txt`
5.  **Inicializar la Base de Datos:** `python init_db.py`. Esto creará el archivo `horarios.db` con todas las tablas necesarias si no existe.
6.  **Ejecutar la Aplicación:** Ejecutar el script `devserver.sh` o el comando: `flask --app main run --debug`. La aplicación estará disponible en `http://127.0.0.1:8080`.

## 5. Esquema de la Base de Datos (`database.py`)

- **`semestres`**: Almacena los periodos académicos (ej: "2024-1").
- **`profesores`**: Guarda la información de los docentes.
- **`cursos`**: Almacena las carreras o programas (ej: "Ingeniería de Sistemas").
- **`clases`**: Representa las asignaturas. Contiene información crucial como las `horas_semana` a cumplir.
- **`cronogramas`**: Es la cabecera de un horario. Contiene un nombre y se asocia a un `id_curso`.
- **`detalle_cronogramas`**: Almacena cada bloque horario (entrada) de un `cronograma`, vinculando una clase, un día, hora de inicio y fin.

## 6. Descripción de Módulos (Blueprints)

### `main.py`
Es el orquestador de la aplicación. Se encarga de:
- Crear la instancia de la aplicación Flask.
- Registrar todos los Blueprints (`horarios_bp`, `gestion_bp`, `cursos_bp`, `profesores_bp`) para modularizar la aplicación.
- Definir la ruta principal (`/`) que da la bienvenida al usuario.

### `horarios.py`
Módulo central de la aplicación, responsable de todo lo relacionado con la visualización y creación de horarios.
- **`lista_horarios()`**: Consulta y muestra todos los horarios guardados con sus detalles.
- **`crear_horario()` (Manual)**: Añade una clase a un horario existente. Realiza validaciones exhaustivas para evitar solapamientos y conflictos de curso o semestre.
- **`crear_horario_auto_form()`**: Muestra el formulario para que el usuario elija los parámetros de la generación automática (nombre del horario, curso y semestre).
- **`ejecutar_creacion_automatica()` (con PuLP)**: Implementa un modelo de optimización para generar un horario factible.
    1.  **Modelo Matemático**: Define el problema usando la biblioteca `pulp`.
    2.  **Variables de Decisión**: Crea una variable binaria para cada posible bloque `(clase, día, hora)`, que será `1` si la clase se asigna a ese espacio, y `0` si no.
    3.  **Restricciones (Reglas del Negocio)**:
        - **Total de Horas:** La suma de bloques asignados a una clase debe ser igual a sus `horas_semana` requeridas.
        - **Unicidad de Curso:** En un mismo bloque `(día, hora)`, no puede haber más de una clase del mismo curso.
        - **Disponibilidad del Profesor:** Un profesor no puede ser asignado a más de una clase simultáneamente, considerando incluso los horarios ya existentes en la base de datos.
    4.  **Resolución**: El motor de `pulp` busca una combinación de variables que satisfaga todas las restricciones.
    5.  **Creación del Horario**: Si se encuentra una solución (`Optimal`), los resultados se guardan en la base de datos. De lo contrario, se notifica al usuario que no fue posible encontrar un horario válido con las condiciones dadas.

### `gestion.py`
Gestiona las entidades de `clases` y `semestres`.
- **`gestion()`**: Es la vista principal que muestra listas de semestres y clases existentes.
- **CRUD para Semestres**: Permite añadir, editar y eliminar semestres.
- **CRUD para Clases**: Permite añadir, editar y eliminar clases, asociándolas a cursos, profesores y semestres.

### `cursos.py`
Ofrece la funcionalidad completa de **CRUD (Crear, Leer, Eliminar)** para la gestión de los cursos o carreras.

### `profesores.py`
Ofrece la funcionalidad completa de **CRUD (Crear, Leer, Editar, Eliminar)** para la gestión de los profesores. Incluye una validación importante: no permite eliminar un profesor si este ya tiene clases asignadas, para mantener la integridad de los datos.
