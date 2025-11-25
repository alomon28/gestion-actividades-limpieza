# models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# ============================================================
#                       USUARIO
# ============================================================
class Usuario(db.Model):
    __tablename__ = 'Usuarios'
    __table_args__ = {'implicit_returning': False}  # Evita errores con SQL Server

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(150), nullable=False)
    correo = db.Column(db.String(200), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    rol = db.Column(db.String(50), nullable=False)

    # Relaciones uno a uno
    empleado = db.relationship('Empleado', back_populates='usuario', uselist=False)
    jefe_cuadrilla = db.relationship('JefeCuadrilla', back_populates='usuario', uselist=False)

    # Relación con el historial
    historial = db.relationship("Historial", back_populates="usuario", lazy=True)

    def __repr__(self):
        return f"<Usuario id={self.id} nombre={self.nombre} rol={self.rol}>"

# ============================================================
#                   JEFE DE CUADRILLA
# ============================================================
class JefeCuadrilla(db.Model):
    __tablename__ = 'JefesCuadrilla'

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('Usuarios.id'), unique=True, nullable=False)

    usuario = db.relationship('Usuario', back_populates='jefe_cuadrilla')

    cuadrillas = db.relationship(
        'Cuadrilla',
        back_populates='jefe',
        cascade="all, delete-orphan",
        lazy=True
    )

    def __repr__(self):
        return f"<JefeCuadrilla id={self.id} usuario_id={self.usuario_id}>"

# ============================================================
#                       CUADRILLA
# ============================================================
class Cuadrilla(db.Model):
    __tablename__ = 'Cuadrillas'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(150), nullable=False)

    jefe_id = db.Column(db.Integer, db.ForeignKey('JefesCuadrilla.id'))
    colonia_id = db.Column(db.Integer, db.ForeignKey('Colonias.id'))

    jefe = db.relationship('JefeCuadrilla', back_populates='cuadrillas')

    empleados = db.relationship(
        'Empleado',
        back_populates='cuadrilla',
        cascade="all, delete-orphan",
        lazy=True
    )

    colonia = db.relationship('Colonia', back_populates='cuadrillas')

    actividades = db.relationship("Actividad", back_populates="cuadrilla")

    def __repr__(self):
        return f"<Cuadrilla id={self.id} nombre={self.nombre}>"

# ============================================================
#                       EMPLEADO
# ============================================================
class Empleado(db.Model):
    __tablename__ = 'Empleados'

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('Usuarios.id'), unique=True)
    cuadrilla_id = db.Column(db.Integer, db.ForeignKey('Cuadrillas.id'))

    usuario = db.relationship('Usuario', back_populates='empleado')
    cuadrilla = db.relationship('Cuadrilla', back_populates='empleados')

    def __repr__(self):
        return (
            f"<Empleado id={self.id} usuario_id={self.usuario_id} "
            f"cuadrilla_id={self.cuadrilla_id}>"
        )

# ============================================================
#                       COLONIA
# ============================================================
class Colonia(db.Model):
    __tablename__ = 'Colonias'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(200))
    codigo_postal = db.Column(db.String(10))
    tipo_asentamiento = db.Column(db.String(100))
    municipio = db.Column(db.String(100))
    estado = db.Column(db.String(100))
    ciudad = db.Column(db.String(100))

    cuadrillas = db.relationship("Cuadrilla", back_populates="colonia")

    def __repr__(self):
        return f"<Colonia id={self.id} nombre={self.nombre}>"

# ============================================================
#                       ACTIVIDAD
# ============================================================
class Actividad(db.Model):
    __tablename__ = 'Actividades'

    id = db.Column(db.Integer, primary_key=True)
    descripcion = db.Column(db.String(1000))
    fecha = db.Column(db.DateTime)
    cuadrilla_id = db.Column(db.Integer, db.ForeignKey('Cuadrillas.id'))
    estado = db.Column(db.String(100))
    nombre = db.Column(db.String(400))
    colonia = db.Column(db.String(400))

    cuadrilla = db.relationship('Cuadrilla', back_populates='actividades')

    evidencias = db.relationship("Evidencia", backref="actividad", cascade="all, delete-orphan")

# ============================================================
#                       EVIDENCIA
# ============================================================
class Evidencia(db.Model):
    __tablename__ = 'Evidencias'

    id = db.Column(db.Integer, primary_key=True)
    actividad_id = db.Column(db.Integer, db.ForeignKey('Actividades.id'))
    ruta_imagen = db.Column(db.String(500))
    fecha = db.Column(db.DateTime, default=datetime.now)

# ============================================================
#                       HISTORIAL
# ============================================================
class Historial(db.Model):
    __tablename__ = 'Historial'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('Usuarios.id'), nullable=False)
    accion = db.Column(db.String(500), nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.now)

    usuario = db.relationship("Usuario", back_populates="historial")

    def __repr__(self):
        return (
            f"<Historial id={self.id} usuario_id={self.usuario_id} "
            f"accion='{self.accion[:20]}...'>"
        )