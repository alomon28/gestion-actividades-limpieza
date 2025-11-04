CREATE DATABASE gestion_limpieza1;
USE gestion_limpieza1;

CREATE TABLE Usuario (
  idUsuario INT AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(100) NOT NULL,
  usuario VARCHAR(50) NOT NULL UNIQUE,
  password VARCHAR(100) NOT NULL,
  rol VARCHAR(50) NOT NULL
);

CREATE TABLE JefeCuadrilla (
  idJefe INT AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(100) NOT NULL,
  telefono VARCHAR(15)
);

CREATE TABLE Cuadrilla (
  idCuadrilla INT AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(100) NOT NULL,
  idJefe INT,
  FOREIGN KEY (idJefe) REFERENCES JefeCuadrilla(idJefe)
);

CREATE TABLE Colonia (
  idColonia INT AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(100) NOT NULL,
  codigoPostal VARCHAR(10)
);

CREATE TABLE Actividad (
  idActividad INT AUTO_INCREMENT PRIMARY KEY,
  descripcion TEXT NOT NULL,
  fecha DATE NOT NULL,
  idCuadrilla INT,
  idColonia INT,
  evidencia VARCHAR(255),
  FOREIGN KEY (idCuadrilla) REFERENCES Cuadrilla(idCuadrilla),
  FOREIGN KEY (idColonia) REFERENCES Colonia(idColonia)
);

CREATE TABLE LogActividad (
  idLog INT AUTO_INCREMENT PRIMARY KEY,
  idActividad INT,
  mensaje VARCHAR(255),
  fechaRegistro DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (idActividad) REFERENCES Actividad(idActividad)
);

-- DATOS DE EJEMPLO
INSERT INTO Usuario (nombre, usuario, password, rol)
VALUES ('Administrador', 'admin', 'admin123', 'Administrador');

INSERT INTO JefeCuadrilla (nombre, telefono)
VALUES ('Carlos Torres', '8441234567'),
       ('María López', '8449876543');

INSERT INTO Cuadrilla (nombre, idJefe)
VALUES ('Cuadrilla Norte', 1),
       ('Cuadrilla Centro', 2);

INSERT INTO Colonia (nombre, codigoPostal)
VALUES ('Los Pinos', '25010'),
       ('Lomas de Lourdes', '25015');

INSERT INTO Actividad (descripcion, fecha, idCuadrilla, idColonia, evidencia)
VALUES ('Limpieza de calles principales', '2025-11-02', 1, 1, 'img/actividad1.jpg');

-- Simulación del patrón Observer registrando un evento:
INSERT INTO LogActividad (idActividad, mensaje)
VALUES (1, 'Nueva actividad registrada y dashboard actualizado');

SELECT * FROM Usuario;
SELECT * FROM JefeCuadrilla;
SELECT * FROM Cuadrilla;
SELECT * FROM Colonia;
SELECT * FROM Actividad;
