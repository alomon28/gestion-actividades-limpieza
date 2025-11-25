USE limpieza_nueva;
GO

ALTER TABLE Actividades ADD nombre NVARCHAR(200);
GO

ALTER TABLE Actividades ADD colonia NVARCHAR(200);
GO

ALTER TABLE Cuadrillas
ADD colonia_id INT NULL;