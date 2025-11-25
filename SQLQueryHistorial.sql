USE limpieza_nueva;
GO
sp_help Actividades;
UPDATE Actividades
SET nombre = descripcion
WHERE descripcion IS NOT NULL;
GO

SELECT * FROM Actividades ORDER BY id DESC;
SELECT * FROM JefesCuadrilla;
SELECT id, nombre, rol FROM Usuarios WHERE id = 1;
EXEC sp_columns Historial;
SELECT TOP 20 * FROM Historial ORDER BY fecha DESC;
SELECT * FROM Cuadrillas
SELECT * FROM JefesCuadrilla
SELECT * FROM Usuarios
