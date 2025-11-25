USE Limpieza_DB;
GO
CREATE TABLE log_actividad (
    id INT IDENTITY(1,1) PRIMARY KEY,
    actividad_id INT FOREIGN KEY REFERENCES actividad(id),
    usuario_id INT FOREIGN KEY REFERENCES usuario(id),
    cambio NVARCHAR(255),
    fecha DATETIME DEFAULT GETDATE()
);
