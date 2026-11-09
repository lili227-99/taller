# Crea un usuario para poder entrar al sistema.
# Se corre UNA vez desde la carpeta del proyecto:  python crear_usuario.py
from getpass import getpass
from werkzeug.security import generate_password_hash
from config import obtener_conexion

usuario = input("Usuario: ").strip()
contrasena = getpass("Contraseña: ")

if not usuario or not contrasena:
    print("El usuario y la contraseña no pueden estar vacíos.")
    raise SystemExit

conexion = obtener_conexion()
cursor = conexion.cursor()


cursor.execute("SELECT usuario FROM usuarios WHERE usuario = %s", (usuario,))
if cursor.fetchone():
    print("Ese usuario ya existe.")
else:
    # La contraseña se guarda "encriptada", nunca en texto normal
    cursor.execute(
        "INSERT INTO usuarios (usuario, contrasena) VALUES (%s, %s)",
        (usuario, generate_password_hash(contrasena))
    )
    conexion.commit()
    print("Usuario creado con éxito.")

cursor.close()
conexion.close()