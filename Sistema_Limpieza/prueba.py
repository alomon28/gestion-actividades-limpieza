import pyodbc
conn = pyodbc.connect("DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost\\SQLEXPRESS;DATABASE=limpieza_nueva;Trusted_Connection=yes;")
print("Conexión exitosa")
conn.close()
