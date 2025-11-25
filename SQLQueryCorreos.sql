USE limpieza_nueva;
GO
CREATE TRIGGER trg_asignar_rol
ON Usuarios
AFTER INSERT
AS
BEGIN
    SET NOCOUNT ON;

    UPDATE u
    SET u.rol = CASE
        WHEN i.correo LIKE '%@super-admin.com' THEN 'SuperAdmin'
        WHEN i.correo LIKE '%@administrador.com' THEN 'Admin'
        WHEN i.correo LIKE '%@jefecuadrilla.com' THEN 'JefeCuadrilla'
        ELSE 'Empleado'
    END
    FROM Usuarios u
    INNER JOIN inserted i ON u.id = i.id;
END;