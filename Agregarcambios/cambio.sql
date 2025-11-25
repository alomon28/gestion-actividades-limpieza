USE Limpieza_DB;
GO
ALTER TABLE colonia ADD codigo_postal VARCHAR(10);
ALTER TABLE colonia ADD tipo_asentamiento VARCHAR(50);
ALTER TABLE colonia ADD estado VARCHAR(50);
ALTER TABLE colonia ADD municipio VARCHAR(50);
ALTER TABLE colonia ADD ciudad VARCHAR(50);
ALTER TABLE colonia ADD clave_oficina VARCHAR(10);
