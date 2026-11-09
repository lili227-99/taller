import mysql.connector

# -----------------------------------------------------
# Datos de conexión a la base de datos
# -----------------------------------------------------
DB_CONFIG = {
    "host": "localhost",
    "user": "root",        # reemplazá por tu usuario de MySQL
    "password": "",        # reemplazá por tu contraseña de MySQL
    "database": "pp2_taller_motos"
}


def obtener_conexion():
    return mysql.connector.connect(**DB_CONFIG)