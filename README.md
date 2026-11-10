# Sistema Web de Gestión para Taller de Motos

Proyecto del **Grupo 10** – Prácticas Profesionalizantes II.

Sistema web para que el dueño de un taller de motos digitalice sus registros: clientes, motos y servicios realizados, con inicio de sesión para proteger la información.

## Funcionalidades

- Inicio de sesión con usuario y contraseña (la contraseña se guarda encriptada).
- Clientes: registrar, consultar, editar y eliminar, con búsqueda por nombre o apellido.
- Motos: registrar asociadas a un cliente, editar y eliminar, con búsqueda por patente, marca, modelo o dueño.
- Servicios: registrar los trabajos realizados a cada moto (descripción, costo y fecha).
- Historial de servicios de cada moto, con el total gastado.
- Página de inicio con accesos rápidos.

## Tecnologías

- Python + Flask
- MySQL (XAMPP)
- HTML, CSS y plantillas Jinja2

## Requisitos

- Python 3.10 o superior
- XAMPP con MySQL iniciado (Apache no hace falta)

## Instalación

1. Clonar el repositorio y entrar a la carpeta del proyecto.

2. Crear y activar el entorno virtual (Windows, PowerShell):

   ```powershell
   python -m venv venv
   venv\Scripts\activate
   ```

3. Instalar las librerías:

   ```powershell
   pip install flask mysql-connector-python
   ```

4. Crear la base de datos `taller_motos` en MySQL (phpMyAdmin → pestaña SQL) con las tablas de la sección siguiente.

5. Revisar los datos de conexión en `config.py` (usuario y contraseña de MySQL).

6. Crear un usuario para entrar al sistema:

   ```powershell
   python crear_usuario.py
   ```

7. Iniciar la aplicación:

   ```powershell
   python app.py
   ```

8. Abrir en el navegador: <http://127.0.0.1:5000/>

## Base de datos

```sql
CREATE DATABASE IF NOT EXISTS taller_motos;
USE taller_motos;

CREATE TABLE usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario VARCHAR(50) NOT NULL UNIQUE,
    contrasena VARCHAR(255) NOT NULL
);

CREATE TABLE clientes (
    idcliente INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    telefono VARCHAR(20) NOT NULL,
    direccion VARCHAR(200)
);

CREATE TABLE motos (
    idmoto INT AUTO_INCREMENT PRIMARY KEY,
    marca VARCHAR(50) NOT NULL,
    modelo VARCHAR(50) NOT NULL,
    patente VARCHAR(20) NOT NULL UNIQUE,
    idcliente INT NOT NULL,
    FOREIGN KEY (idcliente) REFERENCES clientes(idcliente) ON DELETE CASCADE
);

CREATE TABLE servicios (
    idservicio INT AUTO_INCREMENT PRIMARY KEY,
    descripcion TEXT NOT NULL,
    costo DECIMAL(10,2) NOT NULL,
    fecha DATE NOT NULL,
    idmoto INT NOT NULL,
    FOREIGN KEY (idmoto) REFERENCES motos(idmoto) ON DELETE CASCADE
);
```

Relaciones: un cliente tiene muchas motos y una moto tiene muchos servicios.

## Estructura del proyecto

```
├── app.py                 # Rutas de Flask (login, clientes, motos, servicios, historial)
├── config.py              # Conexión a MySQL
├── crear_usuario.py       # Script para crear usuarios de acceso
├── static/
│   └── css/estilos.css    # Estilos
└── templates/             # Páginas HTML (Jinja2)
```

## Equipo

| Rol | Integrante |
| --- | --- |
| Frontend | Ezequiel Hauff |
| Backend | Liliana Fleitas |
| Base de datos | Noelia Duarte |