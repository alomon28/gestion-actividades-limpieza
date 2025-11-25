# importarcolonias.py
import sys
import csv

# Asegúrate de que Python encuentre app.py
sys.path.append(r"C:\Users\alond\OneDrive\Escritorio\Proyecto 2 (3)\Proyecto 2 (3)\Proyecto 2\Sistema_Limpieza\CodigosPostales.csv")

from app import app, db
from models import Colonia

csv_file = r"C:\Users\alond\OneDrive\Escritorio\Proyecto 2 (3)\Proyecto 2 (3)\Proyecto 2\Sistema_Limpieza\CodigosPostales.csv"
with app.app_context():
    with open(csv_file, newline='', encoding='latin-1') as f:
        reader = csv.reader(f)

        # Detectar automáticamente la fila de encabezado buscando "Código Postal"
        headers = None
        for row in reader:
            if not row:
                continue
            if "Código Postal" in row[0]:
                headers = row
                break

        if headers is None:
            raise ValueError("No se encontró la fila de encabezado con 'Código Postal'.")

        # Ahora iteramos las filas de datos
        for row in reader:
            if len(row) < 7:
                continue  # fila incompleta

            codigo_postal = row[0].strip()
            estado = row[1].strip()
            municipio = row[2].strip()
            ciudad = row[3].strip()
            tipo_asentamiento = row[4].strip()
            asentamiento = row[5].strip()
            # row[6] = clave_oficina → no se usa

            # Evitar duplicados
            if Colonia.query.filter_by(nombre=asentamiento, codigo_postal=codigo_postal).first():
                continue

            # Crear nueva colonia usando solo los campos del modelo
            nueva_colonia = Colonia(
                nombre=asentamiento,
                codigo_postal=codigo_postal,
                tipo_asentamiento=tipo_asentamiento,
                municipio=municipio,
                estado=estado,
                ciudad=ciudad
            )
            db.session.add(nueva_colonia)

        db.session.commit()
        print("Colonias importadas correctamente")