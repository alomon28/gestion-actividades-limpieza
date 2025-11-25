-- Elimina la base de datos si existe 
-- DROP DATABASE Limpieza_DB;
-- GO

-- Usa la base existente
USE Limpieza_DB;
GO

-- Elimina restricciones antes de eliminar tablas
IF OBJECT_ID('usuario', 'U') IS NOT NULL
BEGIN
    ALTER TABLE cuadrilla DROP CONSTRAINT fk_cuadrilla_jefe;
    ALTER TABLE usuario DROP CONSTRAINT fk_usuario_cuadrilla;
END

IF OBJECT_ID('actividad', 'U') IS NOT NULL
BEGIN
    ALTER TABLE actividad DROP CONSTRAINT fk_actividad_cuadrilla;
END
GO

-- Elimina tablas si existen
DROP TABLE IF EXISTS actividad;
DROP TABLE IF EXISTS colonia;
DROP TABLE IF EXISTS cuadrilla;
DROP TABLE IF EXISTS usuario;
GO

-- Crea tablas
CREATE TABLE usuario (
    id INT IDENTITY(1,1) PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    rol VARCHAR(20) CHECK (rol IN ('superadmin','admin','jefe','empleado')) NOT NULL,
    cuadrilla_id INT NULL
);

CREATE TABLE cuadrilla (
    id INT IDENTITY(1,1) PRIMARY KEY,
    nombre_cuadrilla VARCHAR(100) NOT NULL,
    jefe_id INT NULL
);

CREATE TABLE colonia (
    id INT IDENTITY(1,1) PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    direccion VARCHAR(255)
);

CREATE TABLE actividad (
    id INT IDENTITY(1,1) PRIMARY KEY,
    descripcion VARCHAR(255) NOT NULL,
    fecha DATE NOT NULL,
    responsable VARCHAR(100),
    cuadrilla_id INT NULL,
    colonia_id INT NULL
);
GO

-- Relaciones
ALTER TABLE usuario
ADD CONSTRAINT fk_usuario_cuadrilla FOREIGN KEY (cuadrilla_id) REFERENCES cuadrilla(id);

ALTER TABLE cuadrilla
ADD CONSTRAINT fk_cuadrilla_jefe FOREIGN KEY (jefe_id) REFERENCES usuario(id);

ALTER TABLE actividad
ADD CONSTRAINT fk_actividad_cuadrilla FOREIGN KEY (cuadrilla_id) REFERENCES cuadrilla(id);
GO

-- Inserción segura de datos
IF NOT EXISTS (SELECT 1 FROM usuario WHERE username = 'superadmin')
    INSERT INTO usuario (username, password, rol) VALUES ('superadmin', 'super123', 'superadmin');

IF NOT EXISTS (SELECT 1 FROM usuario WHERE username = 'admin')
    INSERT INTO usuario (username, password, rol) VALUES ('admin', 'admin123', 'admin');

IF NOT EXISTS (SELECT 1 FROM usuario WHERE username = 'jefe_ejemplo')
    INSERT INTO usuario (username, password, rol) VALUES ('jefe_ejemplo', 'jefe123', 'jefe');

IF NOT EXISTS (SELECT 1 FROM usuario WHERE username = 'empleado')
    INSERT INTO usuario (username, password, rol) VALUES ('empleado', 'empleado123', 'empleado');
GO

-- Inserta cuadrilla y actualiza usuario
IF NOT EXISTS (SELECT 1 FROM cuadrilla WHERE nombre_cuadrilla = 'Cuadrilla Centro')
    INSERT INTO cuadrilla (nombre_cuadrilla, jefe_id) VALUES ('Cuadrilla Centro', 
        (SELECT id FROM usuario WHERE username = 'jefe_ejemplo'));

UPDATE usuario SET cuadrilla_id = 
    (SELECT id FROM cuadrilla WHERE nombre_cuadrilla = 'Cuadrilla Centro')
WHERE username = 'empleado';
GO