from models import Usuario

class UsuarioFactory:
    """
    Factory para crear usuarios.
    El trigger en la base de datos se encargará de asignar el rol real
    según el dominio del correo:
        - @super-admin.com   → SuperAdmin
        - @administrador.com → Admin
        - @jefecuadrilla.com → JefeCuadrilla
        - Otros correos       → Empleado
    """
    @staticmethod
    def crear_usuario(nombre, correo, password_hash):
        if not correo or "@" not in correo:
            raise ValueError("El correo electrónico no es válido.")

        # Creamos el usuario con rol temporal 'Empleado'
        # El trigger actualizará el rol real automáticamente
        return Usuario(
            nombre=nombre.strip(),
            correo=correo.strip(),
            password_hash=password_hash,
            rol='Empleado'  # Valor temporal; trigger lo ajusta
        )