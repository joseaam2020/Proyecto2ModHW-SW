# Proyecto 2 Modelación de Hardware Software

Simulador de producción en serie para el curso de Modelación de Hardware y Software

## Instrucciones de instalación y uso

### 1. Instalar dependencias

Abre una terminal en la carpeta del proyecto y ejecuta:

```
python -m venv env
```

Activa el entorno virtual:

- **Windows:**
	```
	.\env\Scripts\activate
	```
- **Linux/Mac:**
	```
	source env/bin/activate
	```

Instala las dependencias necesarias:

```
pip install flask
pip install reportlab
```

### 2. Ejecutar la simulación (main.py)

En la terminal, ejecuta:

```
python main.py
```

Esto generará los reportes de la simulación en la carpeta `reports/`.

### 3. Ejecutar la aplicación web (app.py)

Desde la carpeta raíz del proyecto, ejecuta:

```
python -m web.app
```

O desde la carpeta `web/`:

```
python app.py
```

Luego abre tu navegador y entra a:

```
http://127.0.0.1:5000/
```

Aquí podrás visualizar los reportes generados por la simulación.
