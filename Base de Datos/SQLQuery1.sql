USE limpieza_nueva;
GO
CREATE TABLE Usuarios (
    id INT IDENTITY PRIMARY KEY,
    nombre NVARCHAR(150) NOT NULL,
    correo NVARCHAR(200) NOT NULL UNIQUE,
    password_hash NVARCHAR(256) NOT NULL,
    rol NVARCHAR(50) NOT NULL
);

CREATE TABLE JefesCuadrilla (
    id INT IDENTITY PRIMARY KEY,
    usuario_id INT NOT NULL,
    FOREIGN KEY (usuario_id) REFERENCES Usuarios(id)
);

CREATE TABLE Cuadrillas (
    id INT IDENTITY PRIMARY KEY,
    nombre NVARCHAR(150) NOT NULL,
    jefe_id INT NULL,
    FOREIGN KEY (jefe_id) REFERENCES JefesCuadrilla(id)
);

CREATE TABLE Empleados (
    id INT IDENTITY PRIMARY KEY,
    usuario_id INT NOT NULL,
    cuadrilla_id INT NULL,
    FOREIGN KEY (usuario_id) REFERENCES Usuarios(id),
    FOREIGN KEY (cuadrilla_id) REFERENCES Cuadrillas(id)
);

CREATE TABLE Colonias (
    id INT IDENTITY PRIMARY KEY,
    nombre NVARCHAR(200),
    codigo_postal NVARCHAR(10),
    tipo_asentamiento NVARCHAR(100),
    municipio NVARCHAR(100),
    estado NVARCHAR(100),
    ciudad NVARCHAR(100)
);

CREATE TABLE Actividades (
    id INT IDENTITY PRIMARY KEY,
    descripcion NVARCHAR(500),
    fecha DATETIME DEFAULT GETDATE(),
    cuadrilla_id INT,
    estado NVARCHAR(50),
    FOREIGN KEY (cuadrilla_id) REFERENCES Cuadrillas(id)
);

CREATE TABLE Evidencias (
    id INT IDENTITY PRIMARY KEY,
    actividad_id INT NOT NULL,
    ruta_imagen NVARCHAR(500) NOT NULL,
    fecha DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (actividad_id) REFERENCES Actividades(id)
);

CREATE TABLE Actividad_Colonia (
    actividad_id INT NOT NULL,
    colonia_id INT NOT NULL,
    PRIMARY KEY (actividad_id, colonia_id),
    FOREIGN KEY (actividad_id) REFERENCES Actividades(id),
    FOREIGN KEY (colonia_id) REFERENCES Colonias(id)
);