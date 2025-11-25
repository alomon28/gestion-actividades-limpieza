# ============================================================
#                      IMPORTS Y CONFIG
# ============================================================
import os
import uuid
from datetime import datetime
from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, session, send_from_directory
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from singleton_db import SingletonDB
from models import (
    db, Usuario, Cuadrilla, Actividad, Colonia,
    Empleado, JefeCuadrilla, Historial, Evidencia
)

app = Flask(__name__)
app.secret_key = "super_secret_key"

# --------- CONFIGURACIÓN SQL SERVER ----------
app.config['SQLALCHEMY_DATABASE_URI'] = (
    "mssql+pyodbc://localhost\\SQLEXPRESS/limpieza_nueva"
    "?driver=ODBC+Driver+17+for+SQL+Server"
    "&trusted_connection=yes"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Límite máximo por petición (opcional) - 20MB
app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024

# Carpeta para guardar evidencias dentro de static/
EVIDENCIAS_FOLDER = os.path.join(app.static_folder, 'evidencias')
os.makedirs(EVIDENCIAS_FOLDER, exist_ok=True)

# Tipos permitidos
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

db_instance = SingletonDB(app)
db = db_instance.db

# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generar_nombre_unico(filename):
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    unique = uuid.uuid4().hex
    return f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{unique}.{ext}" if ext else f"{unique}"

def registrar_historial(usuario_id, accion):
    """Guarda en la tabla Historial todas las acciones importantes."""
    if not usuario_id:
        print("No hay usuario en sesión, historial no registrado.")
        return
    try:
        nuevo = Historial(usuario_id=usuario_id, accion=accion)
        db.session.add(nuevo)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error al registrar historial: {e}")

# ============================================================
#                     LOGIN / LOGOUT
# ============================================================
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        correo = request.form.get('correo')
        password = request.form.get('password')

        if not correo or not password:
            flash("Por favor, completa todos los campos.", "warning")
            return redirect(url_for('login'))

        usuario = Usuario.query.filter_by(correo=correo).first()

        if usuario and check_password_hash(usuario.password_hash, password):
            session['usuario_id'] = usuario.id
            session['rol'] = usuario.rol
            flash(f"Bienvenido, {usuario.nombre}", "success")

            if usuario.rol in ["Admin", "SuperAdmin"]:
                return redirect(url_for('dashboard_global'))
            if usuario.rol == "JefeCuadrilla":
                return redirect(url_for('dashboard_jefe'))
            if usuario.rol == "Empleado":
                return redirect(url_for('dashboard_empleado'))

        flash("Correo o contraseña incorrectos.", "danger")
        return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("Sesión cerrada exitosamente.", "info")
    return redirect(url_for('login'))

# ============================================================
#                     REGISTRO USUARIO
# (mantener tu implementación)
# ============================================================
@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        correo = request.form.get('correo')
        password = request.form.get('password')

        if not nombre or not correo or not password:
            flash("Todos los campos son obligatorios.", "warning")
            return redirect(url_for('registro'))

        try:
            password_hash = generate_password_hash(password)
            nuevo = Usuario(nombre=nombre.strip(), correo=correo.strip(),
                            password_hash=password_hash, rol='Empleado')
            db.session.add(nuevo)
            db.session.commit()

            # Crear registro Empleado
            if not Empleado.query.filter_by(usuario_id=nuevo.id).first():
                db.session.add(Empleado(usuario_id=nuevo.id))
                db.session.commit()

            flash("Usuario registrado correctamente.", "success")
            return redirect(url_for('login'))

        except Exception as e:
            db.session.rollback()
            flash(f"Error al registrar usuario: {e}", "danger")

    return render_template('registro.html')

# ============================================================
#                          DASHBOARDS
# ============================================================
@app.route('/dashboard_global')
def dashboard_global():
    if session.get('rol') not in ['Admin', 'SuperAdmin']:
        flash("Acceso denegado.", "danger")
        return redirect(url_for('login'))

    return render_template('dashboard_global.html',
                           total_usuarios=Usuario.query.count(),
                           total_cuadrillas=Cuadrilla.query.count(),
                           total_actividades=Actividad.query.count(),
                           total_colonias=Colonia.query.count())

@app.route('/dashboard_jefe')
def dashboard_jefe():
    if session.get('rol') != 'JefeCuadrilla':
        flash("Acceso denegado.", "danger")
        return redirect(url_for('login'))

    jefe = JefeCuadrilla.query.filter_by(usuario_id=session['usuario_id']).first()
    cuadrillas = Cuadrilla.query.filter_by(jefe_id=jefe.id).all() if jefe else []
    return render_template('dashboard_jefe.html', cuadrillas=cuadrillas)

@app.route('/dashboard_empleado')
def dashboard_empleado():
    if session.get('rol') != 'Empleado':
        flash("Acceso denegado.", "danger")
        return redirect(url_for('login'))

    emp = Empleado.query.filter_by(usuario_id=session['usuario_id']).first()
    actividades = Actividad.query.filter_by(cuadrilla_id=emp.cuadrilla_id).all() if emp and emp.cuadrilla_id else []
    # Opcional: pasar conteo de evidencias o últimas evidencias por actividad
    actividad_data = []
    for a in actividades:
        evid_count = Evidencia.query.filter_by(actividad_id=a.id).count()
        actividad_data.append({'actividad': a, 'evid_count': evid_count})
    return render_template('dashboard_empleado.html', actividades=actividad_data)

# ============================================================
#                       ASIGNACIONES (vista general)
# (mantén tu implementación; adaptada para formatos de fecha)
# ============================================================
@app.route('/asignaciones')
def asignaciones():
    if 'rol' not in session:
        flash("Acceso denegado.", "danger")
        return redirect(url_for('login'))

    asignaciones_list = []
    rol = session['rol']
    usuario_id = session['usuario_id']

    if rol == 'JefeCuadrilla':
        jefe = JefeCuadrilla.query.filter_by(usuario_id=usuario_id).first()
        if jefe:
            cuadrillas = Cuadrilla.query.filter_by(jefe_id=jefe.id).all()
            for c in cuadrillas:
                actividades = Actividad.query.filter_by(cuadrilla_id=c.id).all()
                for a in actividades:
                    asignaciones_list.append({
                        'actividad': a,
                        'cuadrilla': c,
                        'colonia': a.colonia,
                        'fecha': a.fecha,
                        'estado': a.estado
                    })

    elif rol in ['Admin', 'SuperAdmin']:
        actividades = Actividad.query.all()
        for a in actividades:
            cuadrilla = Cuadrilla.query.get(a.cuadrilla_id)
            asignaciones_list.append({
                'actividad': a,
                'cuadrilla': cuadrilla,
                'colonia': a.colonia,
                'fecha': a.fecha,
                'estado': a.estado
            })

    elif rol == 'Empleado':
        emp = Empleado.query.filter_by(usuario_id=usuario_id).first()
        if emp and emp.cuadrilla_id:
            cuadrilla = Cuadrilla.query.get(emp.cuadrilla_id)
            actividades = Actividad.query.filter_by(cuadrilla_id=emp.cuadrilla_id).all()
            for a in actividades:
                asignaciones_list.append({
                    'actividad': a,
                    'cuadrilla': cuadrilla,
                    'colonia': a.colonia,
                    'fecha': a.fecha,
                    'estado': a.estado
                })

    return render_template('asignaciones.html', asignaciones=asignaciones_list)

# ============================================================
#                 JEFE: ASIGNAR ACTIVIDAD
# ============================================================
@app.route('/asignar_actividad', methods=['GET', 'POST'])
def asignar_actividad():
    if session.get('rol') != 'JefeCuadrilla':
        flash("Acceso denegado.", "danger")
        return redirect(url_for('login'))

    jefe = JefeCuadrilla.query.filter_by(usuario_id=session['usuario_id']).first()
    cuadrillas = Cuadrilla.query.filter_by(jefe_id=jefe.id).all() if jefe else []
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        colonia = request.form.get('colonia')
        cuadrilla_id = request.form.get('cuadrilla_id')
        if not nombre or not colonia or not cuadrilla_id:
            flash("Todos los campos son obligatorios.", "warning")
            return redirect(url_for('asignar_actividad'))
        try:
            nueva = Actividad(
                nombre=nombre.strip(),
                colonia=colonia.strip(),
                cuadrilla_id=int(cuadrilla_id),
                fecha=datetime.now(),
                estado="Pendiente"
            )
            db.session.add(nueva)
            db.session.commit()
            flash("Actividad asignada correctamente.", "success")
            return redirect(url_for('dashboard_jefe'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error al asignar actividad: {e}", "danger")
    return render_template('asignar_actividad.html', cuadrillas=cuadrillas)


# ============================================================
#        ADMIN: GESTIÓN USUARIOS (CRUD)
# ============================================================

@app.route('/gestion_usuarios')
def gestion_usuarios():
    if session.get('rol') not in ['Admin', 'SuperAdmin']:
        flash("Acceso denegado.", "danger")
        return redirect(url_for('login'))

    return render_template('gestion_usuarios.html', usuarios=Usuario.query.all())


@app.route('/crear_usuario', methods=['GET', 'POST'])
def crear_usuario():
    if session.get('rol') not in ['Admin', 'SuperAdmin']:
        flash("Acceso denegado.", "danger")
        return redirect(url_for('login'))

    roles = ['Empleado', 'JefeCuadrilla', 'Admin', 'SuperAdmin']

    if request.method == 'POST':
        nombre = request.form.get('nombre')
        correo = request.form.get('correo')
        password = request.form.get('password')
        rol = request.form.get('rol')

        if not nombre or not correo or not password:
            flash("Todos los campos son obligatorios.", "warning")
            return redirect(url_for('crear_usuario'))

        try:
            nuevo = Usuario(
                nombre=nombre,
                correo=correo,
                password_hash=generate_password_hash(password),
                rol=rol
            )
            db.session.add(nuevo)
            db.session.commit()

            # Registro asociado
            if rol == 'Empleado':
                db.session.add(Empleado(usuario_id=nuevo.id))
            if rol == 'JefeCuadrilla':
                db.session.add(JefeCuadrilla(usuario_id=nuevo.id))
            db.session.commit()

            registrar_historial(session['usuario_id'], f"Creó el usuario {nuevo.nombre}")

            flash("Usuario creado correctamente.", "success")
            return redirect(url_for('gestion_usuarios'))

        except Exception as e:
            db.session.rollback()
            flash(f"Error: {e}", "danger")

    return render_template('crear_usuario.html', roles=roles)

# ------------------------------------------------------------------
#               EDITAR USUARIO
# ------------------------------------------------------------------
@app.route('/editar_usuario/<int:id>', methods=['GET', 'POST'])
def editar_usuario(id):
    if session.get('rol') not in ['Admin', 'SuperAdmin']:
        flash("Acceso denegado.", "danger")
        return redirect(url_for('login'))

    usuario = Usuario.query.get_or_404(id)
    roles = ['Empleado', 'JefeCuadrilla', 'Admin', 'SuperAdmin']

    if request.method == 'POST':
        try:
            usuario.nombre = request.form.get('nombre')
            usuario.correo = request.form.get('correo')
            nuevo_rol = request.form.get('rol')

            # VALIDACIÓN: Solo empleados pueden convertirse en JefeCuadrilla
            if nuevo_rol == 'JefeCuadrilla' and usuario.rol != 'Empleado':
                flash("Solo los usuarios con rol Empleado pueden convertirse en Jefe de Cuadrilla.", "warning")
                return redirect(url_for('editar_usuario', id=id))
            
            # Actualizar rol
            usuario.rol = nuevo_rol
            db.session.commit()

            # Sincronizar con tablas auxiliares
            # EMPLEADO
            if nuevo_rol == 'Empleado':
                if not Empleado.query.filter_by(usuario_id=usuario.id).first():
                    db.session.add(Empleado(usuario_id=usuario.id))

                jefe = JefeCuadrilla.query.filter_by(usuario_id=usuario.id).first()
                if jefe:
                    for c in jefe.cuadrillas:
                        c.jefe_id = None
                    db.session.delete(jefe)

                db.session.commit()

            # JEFE
            if nuevo_rol == 'JefeCuadrilla':
                if not JefeCuadrilla.query.filter_by(usuario_id=usuario.id).first():
                    db.session.add(JefeCuadrilla(usuario_id=usuario.id))

                emp = Empleado.query.filter_by(usuario_id=usuario.id).first()
                if emp:
                    db.session.delete(emp)

                db.session.commit()

            # ADMIN / SUPERADMIN
            if nuevo_rol in ['Admin', 'SuperAdmin']:
                emp = Empleado.query.filter_by(usuario_id=usuario.id).first()
                if emp:
                    db.session.delete(emp)

                jefe = JefeCuadrilla.query.filter_by(usuario_id=usuario.id).first()
                if jefe:
                    for c in jefe.cuadrillas:
                        c.jefe_id = None
                    db.session.delete(jefe)

                db.session.commit()

            registrar_historial(session['usuario_id'], f"Editó al usuario {usuario.nombre}")
            flash("Usuario actualizado correctamente.", "success")
            return redirect(url_for('gestion_usuarios'))

        except Exception as e:
            db.session.rollback()
            flash(f"Error: {e}", "danger")

    return render_template('editar_usuario.html', usuario=usuario, roles=roles)

# ------------------------------------------------------------------
#           ELIMINAR USUARIO
# ------------------------------------------------------------------
@app.route('/eliminar_usuario/<int:id>', methods=['POST'])
def eliminar_usuario(id):
    if session.get('rol') not in ['Admin', 'SuperAdmin']:
        flash("Acceso denegado.", "danger")
        return redirect(url_for('login'))

    usuario = Usuario.query.get_or_404(id)

    try:
        # eliminar registros asociados
        emp = Empleado.query.filter_by(usuario_id=usuario.id).first()
        if emp:
            db.session.delete(emp)

        jefe = JefeCuadrilla.query.filter_by(usuario_id=usuario.id).first()
        if jefe:
            for c in jefe.cuadrillas:
                c.jefe_id = None
            db.session.delete(jefe)

        db.session.delete(usuario)
        db.session.commit()

        registrar_historial(session['usuario_id'], f"Eliminó al usuario {usuario.nombre}")
        flash("Usuario eliminado correctamente.", "success")

    except Exception as e:
        db.session.rollback()
        flash(f"Error: {e}", "danger")

    return redirect(url_for('gestion_usuarios'))

# ------------------------------------------------------------------
#           HACER JEFE A UN USUARIO
# ------------------------------------------------------------------
@app.route('/hacer_jefe/<int:usuario_id>', methods=['POST'])
def hacer_jefe(usuario_id):
    if session.get('rol') not in ['Admin', 'SuperAdmin']:
        flash("Acceso denegado.", "danger")
        return redirect(url_for('login'))

    usuario = Usuario.query.get_or_404(usuario_id)

    # ------------------------------------------------------------------
    # VALIDACIÓN: Solo los usuarios con rol Empleado pueden ascender a Jefe
    # ------------------------------------------------------------------
    if usuario.rol != 'Empleado':
        flash("Solo los usuarios con rol Empleado pueden convertirse en Jefe de Cuadrilla.", "warning")
        return redirect(url_for('gestion_usuarios'))
    # ------------------------------------------------------------------

    try:
        # Asignar nuevo rol
        usuario.rol = 'JefeCuadrilla'
        db.session.commit()

        # Crear registro en tabla JefeCuadrilla si no existe
        if not JefeCuadrilla.query.filter_by(usuario_id=usuario.id).first():
            db.session.add(JefeCuadrilla(usuario_id=usuario.id))
            db.session.commit()

        registrar_historial(session['usuario_id'], f"Asignó como jefe a {usuario.nombre}")
        flash("El usuario ahora es Jefe de Cuadrilla.", "success")

    except Exception as e:
        db.session.rollback()
        flash(f"Error: {e}", "danger")

    return redirect(url_for('gestion_usuarios'))


# ============================================================
#        GESTIÓN CUADRILLAS (CRUD + asignar empleados)
# ============================================================

@app.route('/gestion_cuadrillas')
def gestion_cuadrillas():
    if session.get('rol') not in ['Admin', 'SuperAdmin']:
        flash("Acceso denegado.", "danger")
        return redirect(url_for('login'))

    return render_template('gestion_cuadrillas.html', cuadrillas=Cuadrilla.query.all())


@app.route('/crear_cuadrilla', methods=['GET', 'POST'])
def crear_cuadrilla():
    if session.get('rol') not in ['Admin', 'SuperAdmin']:
        flash("Acceso denegado", "danger")
        return redirect(url_for('login'))

    jefes = db.session.query(Usuario, JefeCuadrilla).join(JefeCuadrilla).all()
    colonias = Colonia.query.all()

    if request.method == 'POST':
        nombre = request.form['nombre']
        jefe_id = request.form.get('jefe_id')
        colonia_id = request.form.get('colonia_id')
        nueva_colonia = request.form.get('nueva_colonia', '').strip()

        nueva = Cuadrilla(nombre=nombre)

        # nueva colonia
        if nueva_colonia:
            col = Colonia.query.filter_by(nombre=nueva_colonia).first()
            if not col:
                col = Colonia(nombre=nueva_colonia)
                db.session.add(col)
                db.session.commit()
            nueva.colonia_id = col.id
        else:
            nueva.colonia_id = int(colonia_id) if colonia_id else None

        nueva.jefe_id = int(jefe_id) if jefe_id else None
        db.session.add(nueva)
        db.session.commit()

        registrar_historial(session['usuario_id'], f"Creó la cuadrilla {nueva.nombre}")
        flash("Cuadrilla creada correctamente", "success")

        return redirect(url_for('gestion_cuadrillas'))

    return render_template('crear_cuadrilla.html', jefes=jefes, colonias=colonias)


@app.route('/editar_cuadrilla/<int:id>', methods=['GET', 'POST'])
def editar_cuadrilla(id):
    if session.get('rol') not in ['Admin', 'SuperAdmin']:
        flash("Acceso denegado", "danger")
        return redirect(url_for('login'))

    cuadrilla = Cuadrilla.query.get_or_404(id)
    jefes = db.session.query(Usuario, JefeCuadrilla).join(JefeCuadrilla).all()
    colonias = Colonia.query.all()

    if request.method == 'POST':
        try:
            cuadrilla.nombre = request.form['nombre']
            jefe_id = request.form.get('jefe_id')
            colonia_id = request.form.get('colonia_id')
            nueva_colonia = request.form.get('nueva_colonia', '').strip()

            if nueva_colonia:
                col = Colonia.query.filter_by(nombre=nueva_colonia).first()
                if not col:
                    col = Colonia(nombre=nueva_colonia)
                    db.session.add(col)
                    db.session.commit()
                cuadrilla.colonia_id = col.id
            else:
                cuadrilla.colonia_id = int(colonia_id) if colonia_id else None

            cuadrilla.jefe_id = int(jefe_id) if jefe_id else None
            db.session.commit()

            registrar_historial(session['usuario_id'], f"Editó la cuadrilla {cuadrilla.nombre}")
            flash("Cuadrilla actualizada", "success")

            return redirect(url_for('gestion_cuadrillas'))

        except Exception as e:
            db.session.rollback()
            flash(f"Error: {e}", "danger")

    return render_template('editar_cuadrilla.html',
                           cuadrilla=cuadrilla,
                           jefes=jefes,
                           colonias=colonias)


@app.route('/eliminar_cuadrilla/<int:id>', methods=['POST'])
def eliminar_cuadrilla(id):
    if session.get('rol') not in ['Admin', 'SuperAdmin']:
        flash("Acceso denegado.", "danger")
        return redirect(url_for('login'))

    cuadrilla = Cuadrilla.query.get_or_404(id)

    try:
        for emp in cuadrilla.empleados:
            emp.cuadrilla_id = None

        db.session.delete(cuadrilla)
        db.session.commit()

        registrar_historial(session['usuario_id'], f"Eliminó la cuadrilla {cuadrilla.nombre}")
        flash("Cuadrilla eliminada correctamente.", "success")

    except Exception as e:
        db.session.rollback()
        flash(f"Error: {e}", "danger")

    return redirect(url_for('gestion_cuadrillas'))


@app.route('/asignar_empleados/<int:cuadrilla_id>', methods=['GET', 'POST'])
def asignar_empleados(cuadrilla_id):
    if session.get('rol') not in ['Admin', 'SuperAdmin']:
        flash("Acceso denegado.", "danger")
        return redirect(url_for('login'))

    cuadrilla = Cuadrilla.query.get_or_404(cuadrilla_id)
    empleados_usuarios = Usuario.query.filter_by(rol='Empleado').all()

    if request.method == 'POST':
        seleccionados = request.form.getlist('empleados')

        try:
            # limpiar todos
            for emp in cuadrilla.empleados:
                emp.cuadrilla_id = None

            # asignar nuevos
            for uid in seleccionados:
                uid_int = int(uid)
                emp = Empleado.query.filter_by(usuario_id=uid_int).first()
                if not emp:
                    emp = Empleado(usuario_id=uid_int)
                    db.session.add(emp)
                emp.cuadrilla_id = cuadrilla.id

            db.session.commit()

            registrar_historial(session['usuario_id'],
                                f"Asignó empleados a la cuadrilla {cuadrilla.nombre}")

            flash("Empleados asignados correctamente.", "success")
            return redirect(url_for('gestion_cuadrillas'))

        except Exception as e:
            db.session.rollback()
            flash(f"Error: {e}", "danger")

    asignados_ids = [e.usuario_id for e in cuadrilla.empleados]

    return render_template('asignar_empleados.html',
                           cuadrilla=cuadrilla,
                           empleados_usuarios=empleados_usuarios,
                           asignados_ids=asignados_ids)


# ============================================================
#                  JEFE: MIS EMPLEADOS
# ============================================================

@app.route('/mis_empleados')
def mis_empleados():
    if session.get('rol') != 'JefeCuadrilla':
        flash("Acceso denegado.", "danger")
        return redirect(url_for('login'))

    jefe = JefeCuadrilla.query.filter_by(usuario_id=session['usuario_id']).first()

    if not jefe:
        flash("No se encontró tu registro como jefe.", "warning")
        return redirect(url_for('dashboard_jefe'))

    cuadrillas = Cuadrilla.query.filter_by(jefe_id=jefe.id).all()
    empleados_detalles = []

    for c in cuadrillas:
        for emp in c.empleados:
            usuario = Usuario.query.get(emp.usuario_id)
            empleados_detalles.append({
                'usuario': usuario,
                'cuadrilla': c
            })

    return render_template('mis_empleados.html',
                           empleados=empleados_detalles,
                           cuadrillas=cuadrillas)


# ============================================================
#             EMPLEADO: MI CUADRILLA
# ============================================================

@app.route('/mi_cuadrilla')
def mi_cuadrilla():
    if session.get('rol') != 'Empleado':
        flash("Acceso denegado.", "danger")
        return redirect(url_for('login'))

    empleado = Empleado.query.filter_by(usuario_id=session['usuario_id']).first()
    if not empleado or not empleado.cuadrilla:
        flash("No estás asignado a ninguna cuadrilla.", "warning")
        return redirect(url_for('dashboard_empleado'))

    cuadrilla = empleado.cuadrilla
    jefe_usuario = cuadrilla.jefe.usuario if cuadrilla.jefe else None
    compañeros = [e.usuario for e in cuadrilla.empleados if e.usuario_id != session['usuario_id']]

    return render_template('mi_cuadrilla.html',
                           cuadrilla=cuadrilla,
                           jefe=jefe_usuario,
                           compañeros=compañeros)


# ============================================================
#                 RUTAS DE EVIDENCIAS (NUEVAS)
# ============================================================
@app.route('/actividad/<int:actividad_id>/evidencias', methods=['GET'])
def ver_evidencias(actividad_id):
    """Ver evidencias subidas para una actividad y formulario para subir nuevas (si rol Empleado)."""
    actividad = Actividad.query.get_or_404(actividad_id)
    evidencias = Evidencia.query.filter_by(actividad_id=actividad_id).order_by(Evidencia.fecha.desc()).all()
    return render_template('ver_evidencias.html', actividad=actividad, evidencias=evidencias)

@app.route('/actividad/<int:actividad_id>/evidencias/subir', methods=['POST'])
def subir_evidencias(actividad_id):
    """
    Maneja subida de múltiples archivos:
    - Input name esperado: 'evidencias' (multiple)
    - Solo empleados (rol == 'Empleado') pueden subir; se registra historial.
    """
    if 'usuario_id' not in session or session.get('rol') != 'Empleado':
        flash("No tienes permiso para subir evidencias.", "danger")
        return redirect(url_for('login'))

    actividad = Actividad.query.get_or_404(actividad_id)
    files = request.files.getlist('evidencias')

    if not files or len(files) == 0:
        flash("Selecciona al menos una imagen.", "warning")
        return redirect(url_for('ver_evidencias', actividad_id=actividad_id))

    saved = 0
    errores = []
    for f in files:
        if f and allowed_file(f.filename):
            filename = secure_filename(f.filename)
            nombre_unico = generar_nombre_unico(filename)
            destino_path = os.path.join(EVIDENCIAS_FOLDER, nombre_unico)
            try:
                f.save(destino_path)
                # Guardar registro en DB: guardamos la ruta relativa dentro de static para usar url_for
                ruta_relativa = f"evidencias/{nombre_unico}"
                nueva_evid = Evidencia(actividad_id=actividad_id, ruta_imagen=ruta_relativa, fecha=datetime.now())
                db.session.add(nueva_evid)
                saved += 1
            except Exception as e:
                errores.append(str(e))
        else:
            errores.append(f"Archivo no permitido: {f.filename}")

    # Confirmar DB
    try:
        db.session.commit()
        if saved > 0:
            registrar_historial(session['usuario_id'],
                                f"Subió {saved} evidencia(s) para la actividad '{actividad.nombre}' (id:{actividad.id})")
            flash(f"{saved} evidencia(s) subidas correctamente.", "success")
        if errores:
            flash("Algunas advertencias: " + "; ".join(errores), "warning")
    except Exception as e:
        db.session.rollback()
        flash(f"Error al guardar evidencias en la base de datos: {e}", "danger")

    return redirect(url_for('ver_evidencias', actividad_id=actividad_id))

@app.route('/static/evidencias/<path:filename>')
def static_evidencias(filename):
    """Ruta para servir evidencias (opcional - Flask sirve static automáticamente, pero exponer aquí si quieres)."""
    return send_from_directory(EVIDENCIAS_FOLDER, filename)

# ============================================================
#                 ELIMINAR EVIDENCIA
# ============================================================
@app.route('/evidencia/<int:evidencia_id>/eliminar', methods=['POST'])
def eliminar_evidencia(evidencia_id):
    evidencia = Evidencia.query.get_or_404(evidencia_id)

    # Eliminar archivo físico
    ruta_completa = os.path.join(app.static_folder, evidencia.ruta_imagen)
    if os.path.exists(ruta_completa):
        os.remove(ruta_completa)

    # Guardar actividad ID para redirigir de vuelta
    actividad_id = evidencia.actividad_id

    db.session.delete(evidencia)
    db.session.commit()

    flash("Evidencia eliminada correctamente", "success")
    return redirect(url_for('ver_evidencias', actividad_id=actividad_id))

# ============================================================
#                 HISTORIAL (Vista)
# ============================================================
@app.route('/historial')
def ver_historial():
    historial = Historial.query.order_by(Historial.fecha.desc()).all()
    return render_template('historial_cambios.html', historial=historial)

# ============================================================
#                       Actualizar Estado
# ============================================================
@app.route('/actualizar_estado/<int:id_actividad>', methods=['POST'])
def actualizar_estado(id_actividad):
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    nuevo_estado = request.form.get("estado")
    actividad = Actividad.query.get_or_404(id_actividad)
    try:
        actividad.estado = nuevo_estado
        db.session.commit()
        registrar_historial(session['usuario_id'], f"Cambió estado de actividad {actividad.nombre} a {nuevo_estado}")
        flash("Estado actualizado correctamente", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error al actualizar: {e}", "danger")
    return redirect(url_for("dashboard_empleado"))

# ============================================================
#                        MAIN
# ============================================================
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)