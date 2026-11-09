
from functools import wraps
from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, session
from werkzeug.security import check_password_hash
from config import obtener_conexion
 
app = Flask(__name__)
app.secret_key = "cambia-esta-clave-por-otra"  # necesaria para los mensajes flash
 
 
# ==========================================================
# LOGIN
# ==========================================================
 
def login_required(f):
    """Si no hay sesión iniciada, manda al login."""
    @wraps(f)
    def decorada(*args, **kwargs):
        if not session.get("usuario"):
            flash("Iniciá sesión para continuar", "error")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorada
 
 
@app.route("/")
def inicio():
    return redirect(url_for("listarclientes"))
 
 
@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("usuario"):
        return redirect(url_for("listarclientes"))
 
    if request.method == "POST":
        usuario = request.form.get("usuario", "").strip()
        contrasena = request.form.get("contrasena", "")
 
        if not usuario or not contrasena:
            flash("Ingresá usuario y contraseña", "error")
            return render_template("login.html")
 
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT usuario, contrasena FROM usuarios WHERE usuario = %s", (usuario,))
        fila = cursor.fetchone()
        cursor.close()
        conexion.close()
 
        # Mismo mensaje si el usuario no existe o la contraseña está mal
        if fila is None or not check_password_hash(fila["contrasena"], contrasena):
            flash("Usuario o contraseña incorrectos", "error")
            return render_template("login.html")
 
        session.clear()
        session["usuario"] = fila["usuario"]
        return redirect(url_for("listarclientes"))
 
    return render_template("login.html")
 
 
@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("Sesión cerrada", "exito")
    return redirect(url_for("login"))
 

@app.after_request
def sin_cache(respuesta):
    """Evita que el navegador guarde copias de las páginas (así el botón Atrás no muestra datos tras cerrar sesión)."""
    respuesta.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    respuesta.headers["Pragma"] = "no-cache"
    respuesta.headers["Expires"] = "0"
    return respuesta



# ==========================================================
# RUTAS DE CLIENTES (una página por acción)
# ==========================================================

# 1. LISTADO: muestra la tabla de clientes
@app.route("/clientes")
def listarclientes():
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    cursor.execute("SELECT idcliente AS id, nombre, apellido, telefono, direccion FROM clientes")
    clientes = cursor.fetchall()
    cursor.close()
    conexion.close()
    return render_template("clientes.html", clientes=clientes)


# 2. NUEVO: GET muestra el formulario, POST guarda
@app.route("/clientes/nuevo", methods=["GET", "POST"])
def nuevocliente():
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        apellido = request.form.get("apellido", "").strip()
        telefono = request.form.get("telefono", "").strip()
        direccion = request.form.get("direccion", "").strip()

        if not nombre or not apellido or not telefono:
            flash("Faltan completar campos obligatorios (nombre, apellido, teléfono)", "error")
            return render_template("cliente_nuevo.html", datos=request.form)

        if not telefono.isdigit():
            flash("El teléfono debe contener solo números", "error")
            return render_template("cliente_nuevo.html", datos=request.form)

        conexion = obtener_conexion()
        cursor = conexion.cursor()

        # Control de duplicados
        cursor.execute("SELECT idcliente FROM clientes WHERE nombre = %s AND apellido = %s", (nombre, apellido))
        if cursor.fetchone():
            cursor.close()
            conexion.close()
            flash("Ya existe un cliente registrado con ese nombre y apellido", "error")
            return render_template("cliente_nuevo.html", datos=request.form)

        cursor.execute(
            "INSERT INTO clientes (nombre, apellido, telefono, direccion) VALUES (%s, %s, %s, %s)",
            (nombre, apellido, telefono, direccion)
        )
        conexion.commit()
        cursor.close()
        conexion.close()

        flash("Cliente registrado con éxito", "exito")
        return redirect(url_for("listarclientes"))

    return render_template("cliente_nuevo.html", datos={})


# 3. EDITAR: GET muestra el formulario con los datos cargados, POST actualiza
@app.route("/clientes/editar/<int:idcliente>", methods=["GET", "POST"])
def editarcliente(idcliente):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    cursor.execute("SELECT idcliente AS id, nombre, apellido, telefono, direccion FROM clientes WHERE idcliente = %s", (idcliente,))
    cliente = cursor.fetchone()

    if cliente is None:
        cursor.close()
        conexion.close()
        flash("Cliente no encontrado", "error")
        return redirect(url_for("listarclientes"))

    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        apellido = request.form.get("apellido", "").strip()
        telefono = request.form.get("telefono", "").strip()
        direccion = request.form.get("direccion", "").strip()
        datos = {"id": idcliente, "nombre": nombre, "apellido": apellido, "telefono": telefono, "direccion": direccion}

        if not nombre or not apellido or not telefono:
            cursor.close()
            conexion.close()
            flash("Faltan completar campos obligatorios (nombre, apellido, teléfono)", "error")
            return render_template("cliente_editar.html", cliente=datos)

        if not telefono.isdigit():
            cursor.close()
            conexion.close()
            flash("El teléfono debe contener solo números", "error")
            return render_template("cliente_editar.html", cliente=datos)

        # Control de duplicados: otro cliente con el mismo nombre y apellido
        cursor.execute(
            "SELECT idcliente FROM clientes WHERE nombre = %s AND apellido = %s AND idcliente != %s",
            (nombre, apellido, idcliente)
        )
        if cursor.fetchone():
            cursor.close()
            conexion.close()
            flash("Ya existe otro cliente con ese nombre y apellido", "error")
            return render_template("cliente_editar.html", cliente=datos)

        cursor.execute(
            "UPDATE clientes SET nombre = %s, apellido = %s, telefono = %s, direccion = %s WHERE idcliente = %s",
            (nombre, apellido, telefono, direccion, idcliente)
        )
        conexion.commit()
        cursor.close()
        conexion.close()

        flash("Cliente actualizado con éxito", "exito")
        return redirect(url_for("listarclientes"))

    cursor.close()
    conexion.close()
    return render_template("cliente_editar.html", cliente=cliente)


# 4. ELIMINAR: GET pide confirmación, POST borra
@app.route("/clientes/eliminar/<int:idcliente>", methods=["GET", "POST"])
def eliminarcliente(idcliente):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    cursor.execute("SELECT idcliente AS id, nombre, apellido, telefono, direccion FROM clientes WHERE idcliente = %s", (idcliente,))
    cliente = cursor.fetchone()

    if cliente is None:
        cursor.close()
        conexion.close()
        flash("Cliente no encontrado", "error")
        return redirect(url_for("listarclientes"))

    if request.method == "POST":
        cursor.execute("DELETE FROM clientes WHERE idcliente = %s", (idcliente,))
        conexion.commit()
        cursor.close()
        conexion.close()
        flash("Cliente eliminado con éxito", "exito")
        return redirect(url_for("listarclientes"))

    cursor.close()
    conexion.close()
    return render_template("cliente_eliminar.html", cliente=cliente)




# ==========================================================
# RUTAS DE MOTOS (una página por acción)
# Columnas reales:  motos(idmoto, marca, modelo, patente, idcliente)
#                   clientes(idcliente, nombre, apellido, ...)
# Pegar en app.py, antes de:  if __name__ == "__main__":
# (borrar antes las rutas de motos viejas)
# ==========================================================

def obtener_clientes():
    """Trae los clientes para llenar el desplegable del formulario."""
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    cursor.execute("SELECT idcliente, nombre, apellido FROM clientes ORDER BY apellido, nombre")
    clientes = cursor.fetchall()
    cursor.close()
    conexion.close()
    return clientes


# 1. LISTADO: muestra la tabla de motos con el nombre del dueño
@app.route("/motos")
@login_required
def listarmotos():
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    cursor.execute(
        "SELECT m.idmoto, m.marca, m.modelo, m.patente, c.nombre, c.apellido "
        "FROM motos m JOIN clientes c ON m.idcliente = c.idcliente "
        "ORDER BY m.idmoto"
    )
    motos = cursor.fetchall()
    cursor.close()
    conexion.close()
    return render_template("motos.html", motos=motos)


# 2. NUEVA: GET muestra el formulario, POST guarda
@app.route("/motos/nueva", methods=["GET", "POST"])
@login_required
def nuevamoto():
    clientes = obtener_clientes()

    if not clientes:
        flash("Primero tenés que registrar un cliente para poder cargar una moto", "error")
        return redirect(url_for("listarclientes"))

    if request.method == "POST":
        marca = request.form.get("marca", "").strip()
        modelo = request.form.get("modelo", "").strip()
        patente = request.form.get("patente", "").strip().upper()
        idcliente = request.form.get("idcliente", "")

        if not marca or not modelo or not patente or not idcliente:
            flash("Faltan completar campos obligatorios (marca, modelo, patente, cliente)", "error")
            return render_template("moto_nueva.html", datos=request.form, clientes=clientes)

        conexion = obtener_conexion()
        cursor = conexion.cursor()

        # El cliente elegido tiene que existir
        cursor.execute("SELECT idcliente FROM clientes WHERE idcliente = %s", (idcliente,))
        if cursor.fetchone() is None:
            cursor.close()
            conexion.close()
            flash("El cliente seleccionado no existe", "error")
            return render_template("moto_nueva.html", datos=request.form, clientes=clientes)

        # Control de duplicados: la patente es única
        cursor.execute("SELECT idmoto FROM motos WHERE patente = %s", (patente,))
        if cursor.fetchone():
            cursor.close()
            conexion.close()
            flash("Ya existe una moto registrada con esa patente", "error")
            return render_template("moto_nueva.html", datos=request.form, clientes=clientes)

        cursor.execute(
            "INSERT INTO motos (marca, modelo, patente, idcliente) VALUES (%s, %s, %s, %s)",
            (marca, modelo, patente, idcliente)
        )
        conexion.commit()
        cursor.close()
        conexion.close()

        flash("Moto registrada con éxito", "exito")
        return redirect(url_for("listarmotos"))

    return render_template("moto_nueva.html", datos={}, clientes=clientes)


# 3. EDITAR: GET muestra el formulario con los datos cargados, POST actualiza
@app.route("/motos/editar/<int:idmoto>", methods=["GET", "POST"])
@login_required
def editarmoto(idmoto):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    cursor.execute(
        "SELECT idmoto, marca, modelo, patente, idcliente FROM motos WHERE idmoto = %s",
        (idmoto,)
    )
    moto = cursor.fetchone()

    if moto is None:
        cursor.close()
        conexion.close()
        flash("Moto no encontrada", "error")
        return redirect(url_for("listarmotos"))

    clientes = obtener_clientes()

    if request.method == "POST":
        marca = request.form.get("marca", "").strip()
        modelo = request.form.get("modelo", "").strip()
        patente = request.form.get("patente", "").strip().upper()
        idcliente = request.form.get("idcliente", "")
        datos = {"idmoto": idmoto, "marca": marca, "modelo": modelo,
                 "patente": patente, "idcliente": idcliente}

        if not marca or not modelo or not patente or not idcliente:
            cursor.close()
            conexion.close()
            flash("Faltan completar campos obligatorios (marca, modelo, patente, cliente)", "error")
            return render_template("moto_editar.html", moto=datos, clientes=clientes)

        cursor.execute("SELECT idcliente FROM clientes WHERE idcliente = %s", (idcliente,))
        if cursor.fetchone() is None:
            cursor.close()
            conexion.close()
            flash("El cliente seleccionado no existe", "error")
            return render_template("moto_editar.html", moto=datos, clientes=clientes)

        # Control de duplicados: otra moto con la misma patente
        cursor.execute(
            "SELECT idmoto FROM motos WHERE patente = %s AND idmoto != %s",
            (patente, idmoto)
        )
        if cursor.fetchone():
            cursor.close()
            conexion.close()
            flash("Ya existe otra moto registrada con esa patente", "error")
            return render_template("moto_editar.html", moto=datos, clientes=clientes)

        cursor.execute(
            "UPDATE motos SET marca = %s, modelo = %s, patente = %s, idcliente = %s "
            "WHERE idmoto = %s",
            (marca, modelo, patente, idcliente, idmoto)
        )
        conexion.commit()
        cursor.close()
        conexion.close()

        flash("Moto actualizada con éxito", "exito")
        return redirect(url_for("listarmotos"))

    cursor.close()
    conexion.close()
    return render_template("moto_editar.html", moto=moto, clientes=clientes)


# 4. ELIMINAR: GET pide confirmación, POST borra
@app.route("/motos/eliminar/<int:idmoto>", methods=["GET", "POST"])
@login_required
def eliminarmoto(idmoto):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    cursor.execute(
        "SELECT m.idmoto, m.marca, m.modelo, m.patente, c.nombre, c.apellido "
        "FROM motos m JOIN clientes c ON m.idcliente = c.idcliente "
        "WHERE m.idmoto = %s",
        (idmoto,)
    )
    moto = cursor.fetchone()

    if moto is None:
        cursor.close()
        conexion.close()
        flash("Moto no encontrada", "error")
        return redirect(url_for("listarmotos"))

    if request.method == "POST":
        cursor.execute("DELETE FROM motos WHERE idmoto = %s", (idmoto,))
        conexion.commit()
        cursor.close()
        conexion.close()
        flash("Moto eliminada con éxito", "exito")
        return redirect(url_for("listarmotos"))

    cursor.close()
    conexion.close()
    return render_template("moto_eliminar.html", moto=moto)



# ==========================================================
# RUTAS DE SERVICIOS (una página por acción)
# Columnas reales: servicios(idservicio, descripcion, costo, fecha, idmoto)
#                  motos(idmoto, ...)  clientes(idcliente, ...)
# Pegar en app.py, antes de:  if __name__ == "__main__":
# (borrar antes las rutas de servicios viejas)
# ==========================================================
from datetime import date, datetime


def obtener_motos():
    """Trae las motos (con su dueño) para llenar el desplegable del formulario."""
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    cursor.execute(
        "SELECT m.idmoto, m.marca, m.modelo, m.patente, c.nombre, c.apellido "
        "FROM motos m JOIN clientes c ON m.idcliente = c.idcliente "
        "ORDER BY m.marca, m.modelo"
    )
    motos = cursor.fetchall()
    cursor.close()
    conexion.close()
    return motos


def validar_servicio(descripcion, costo_txt, fecha_txt, idmoto):
    """Devuelve (costo, fecha, mensaje_de_error). Si todo está bien, el error es None."""
    if not descripcion or not costo_txt or not idmoto:
        return None, None, "Faltan completar campos obligatorios (moto, descripción, costo)"

    try:
        costo = round(float(costo_txt.replace(",", ".")), 2)
        if costo < 0:
            raise ValueError
    except ValueError:
        return None, None, "El costo debe ser un número válido (0 o mayor)"

    if not fecha_txt:
        fecha_txt = date.today().isoformat()
    try:
        datetime.strptime(fecha_txt, "%Y-%m-%d")
    except ValueError:
        return None, None, "La fecha no es válida"

    return costo, fecha_txt, None


# 1. LISTADO: historial de servicios, del más nuevo al más viejo
@app.route("/servicios")
@login_required
def listarservicios():
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    cursor.execute(
        "SELECT s.idservicio, s.fecha, s.descripcion, s.costo, "
        "m.marca, m.modelo, m.patente, c.nombre, c.apellido "
        "FROM servicios s "
        "JOIN motos m ON s.idmoto = m.idmoto "
        "JOIN clientes c ON m.idcliente = c.idcliente "
        "ORDER BY s.fecha DESC, s.idservicio DESC"
    )
    servicios = cursor.fetchall()
    cursor.close()
    conexion.close()
    return render_template("servicios.html", servicios=servicios)


# 2. NUEVO: GET muestra el formulario, POST guarda
@app.route("/servicios/nuevo", methods=["GET", "POST"])
@login_required
def nuevoservicio():
    motos = obtener_motos()

    if not motos:
        flash("Primero tenés que registrar una moto para poder cargar un servicio", "error")
        return redirect(url_for("listarmotos"))

    hoy = date.today().isoformat()

    if request.method == "POST":
        descripcion = request.form.get("descripcion", "").strip()
        costo_txt = request.form.get("costo", "").strip()
        fecha_txt = request.form.get("fecha", "").strip()
        idmoto = request.form.get("idmoto", "")

        costo, fecha, error = validar_servicio(descripcion, costo_txt, fecha_txt, idmoto)
        if error:
            flash(error, "error")
            return render_template("servicio_nuevo.html", datos=request.form, motos=motos, hoy=hoy)

        conexion = obtener_conexion()
        cursor = conexion.cursor()

        # La moto elegida tiene que existir
        cursor.execute("SELECT idmoto FROM motos WHERE idmoto = %s", (idmoto,))
        if cursor.fetchone() is None:
            cursor.close()
            conexion.close()
            flash("La moto seleccionada no existe", "error")
            return render_template("servicio_nuevo.html", datos=request.form, motos=motos, hoy=hoy)

        cursor.execute(
            "INSERT INTO servicios (descripcion, costo, fecha, idmoto) VALUES (%s, %s, %s, %s)",
            (descripcion, costo, fecha, idmoto)
        )
        conexion.commit()
        cursor.close()
        conexion.close()

        flash("Servicio registrado con éxito", "exito")
        return redirect(url_for("listarservicios"))

    return render_template("servicio_nuevo.html", datos={}, motos=motos, hoy=hoy)


# 3. EDITAR: GET muestra el formulario con los datos cargados, POST actualiza
@app.route("/servicios/editar/<int:idservicio>", methods=["GET", "POST"])
@login_required
def editarservicio(idservicio):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    cursor.execute(
        "SELECT idservicio, descripcion, costo, fecha, idmoto FROM servicios WHERE idservicio = %s",
        (idservicio,)
    )
    servicio = cursor.fetchone()

    if servicio is None:
        cursor.close()
        conexion.close()
        flash("Servicio no encontrado", "error")
        return redirect(url_for("listarservicios"))

    motos = obtener_motos()

    if request.method == "POST":
        descripcion = request.form.get("descripcion", "").strip()
        costo_txt = request.form.get("costo", "").strip()
        fecha_txt = request.form.get("fecha", "").strip()
        idmoto = request.form.get("idmoto", "")
        datos = {"idservicio": idservicio, "descripcion": descripcion, "costo": costo_txt,
                 "fecha": fecha_txt, "idmoto": idmoto}

        costo, fecha, error = validar_servicio(descripcion, costo_txt, fecha_txt, idmoto)
        if error:
            cursor.close()
            conexion.close()
            flash(error, "error")
            return render_template("servicio_editar.html", servicio=datos, motos=motos)

        cursor.execute("SELECT idmoto FROM motos WHERE idmoto = %s", (idmoto,))
        if cursor.fetchone() is None:
            cursor.close()
            conexion.close()
            flash("La moto seleccionada no existe", "error")
            return render_template("servicio_editar.html", servicio=datos, motos=motos)

        cursor.execute(
            "UPDATE servicios SET descripcion = %s, costo = %s, fecha = %s, idmoto = %s WHERE idservicio = %s",
            (descripcion, costo, fecha, idmoto, idservicio)
        )
        conexion.commit()
        cursor.close()
        conexion.close()

        flash("Servicio actualizado con éxito", "exito")
        return redirect(url_for("listarservicios"))

    cursor.close()
    conexion.close()
    return render_template("servicio_editar.html", servicio=servicio, motos=motos)


# 4. ELIMINAR: GET pide confirmación, POST borra
@app.route("/servicios/eliminar/<int:idservicio>", methods=["GET", "POST"])
@login_required
def eliminarservicio(idservicio):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    cursor.execute(
        "SELECT s.idservicio, s.fecha, s.descripcion, s.costo, "
        "m.marca, m.modelo, m.patente, c.nombre, c.apellido "
        "FROM servicios s "
        "JOIN motos m ON s.idmoto = m.idmoto "
        "JOIN clientes c ON m.idcliente = c.idcliente "
        "WHERE s.idservicio = %s",
        (idservicio,)
    )
    servicio = cursor.fetchone()

    if servicio is None:
        cursor.close()
        conexion.close()
        flash("Servicio no encontrado", "error")
        return redirect(url_for("listarservicios"))

    if request.method == "POST":
        cursor.execute("DELETE FROM servicios WHERE idservicio = %s", (idservicio,))
        conexion.commit()
        cursor.close()
        conexion.close()
        flash("Servicio eliminado con éxito", "exito")
        return redirect(url_for("listarservicios"))

    cursor.close()
    conexion.close()
    return render_template("servicio_eliminar.html", servicio=servicio)



if __name__ == "__main__":
    app.run(debug=True)