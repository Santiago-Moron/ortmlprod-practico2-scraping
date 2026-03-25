# Práctico 2 - Web Scraping y base de datos

En este práctico se implementará un web scraper utilizando Python para extraer información de propiedades inmobiliarias de un sitio web y almacenarlas en una base de datos local.

## Objetivos
- Implementar un web scraper utilizando Playwright
- Almacenar los datos en SQLite.

## Estructura del Proyecto

El proyecto está organizado de la siguiente manera:

- `src/main.py`: Punto de entrada de la aplicación
- `src/scrapers/gallito.py`: Implementación del scraper
- `src/structs/property.py`: Modelos de datos con Pydantic
- `src/database/database_connection.py`: Instanciación y operaciones de la base de datos SQLite.
- `requirements.in`: Dependencias del proyecto (pip)
-  `pyroject.toml`: Dependencias del proyecto (Poetry)

## Índice de Contenidos

1. [Playwright](#1-playwright)
  
   1.1 [¿Qué es Playwright?](#11-qué-es-playwright)

   1.2 [¿Para qué sirve Playwright?](#12-para-qué-sirve-playwright)

   1.3 [¿Qué ventajas y desventajas tiene Playwright sobre otros frameworks de scraping?](#13-qué-ventajas-y-desventajas-tiene-playwright-sobre-otros-frameworks-de-scraping)

   1.4 [¿Cómo funciona Playwright?](#14-cómo-funciona-playwright)

   1.5 [¿Cómo instalar Playwright?](#15-cómo-instalar-playwright)

   1.6 [¿Cómo usar Playwright?](#16-cómo-usar-playwright)

2. [Scraping local](#2-scraping-local)

   2.1 [Instalación de dependencias](#21-instalación-de-dependencias)

   2.2 [Ejecución del scraper](#22-ejecución-del-scraper)

   2.3 [Almacenamiento de datos](#23-almacenamiento-de-datos)

3. [Almacenamiento en base de datos](#3-almacenamiento-en-base-de-datos)


## 1. Playwright

### 1.1. ¿Qué es Playwright?

Playwright es un framework de automatización de navegadores desarrollado por Microsoft. Permite controlar programáticamente los navegadores Chrome, Firefox y Safari, facilitando la automatización de pruebas y web scraping.

### 1.2 ¿Para qué sirve Playwright?

Playwright se utiliza principalmente para:
- Automatización de pruebas end-to-end
- Web scraping y extracción de datos
- Generación de screenshots y PDFs
- Automatización de tareas en navegadores
- Testing de aplicaciones web

### 1.3 ¿Qué ventajas y desventajas tiene Playwright sobre otros frameworks de scraping?

Ventajas:
- Soporte para múltiples navegadores
- API moderna y fácil de usar
- Pensado para nuevas versiones de navegadores
- Manejo automático de esperas
- Soporte para páginas dinámicas (JavaScript)

Desventajas:
- Mayor consumo de recursos
- No sirve para automatizar aplicaciones móviles

### 1.4 ¿Cómo funciona Playwright?

Playwright funciona:
1. Iniciando una instancia del navegador
2. Creando un contexto aislado
3. Abriendo páginas dentro del contexto
4. Interactuando con elementos mediante selectores
5. Extrayendo información del DOM

### 1.5 ¿Cómo instalar Playwright?

```bash
# Instalar el paquete de Python
pip install playwright

# Instalar los navegadores
playwright install

# Instalar dependencias
playwright install-deps
```

### 1.6 ¿Cómo usar Playwright?

Ejemplo básico de uso:

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto('https://ejemplo.com')
    title = page.title()
    browser.close()
```


## 2. Scraping local

### 2.1 Instalación de dependencias

Si se usa Poetry, solo se debe estar situado en el directorio donde se encuentra pyproject.toml y usar el comando:
```bash
poetry install
```
En caso de estar usando pip y un entorno virtual, los pasos son los siguientes:

1. Crear y activar entorno virtual:
```bash
virtualenv venv -p $(which python3.11)
source venv/bin/activate
```

2. Instalar dependencias:
```bash
pip install -r requirements.txt
```

### 2.2 Ejecución del scraper

1. Configurar parámetros en `src/settings/config.yml`
2. Ejecutar el scraper:
```bash
python src/main.py
```

### 2.3 Tests replicables con Playwright
Se puede usar Playwright para interactuar con la página web y que automáticamente se codifique cada acción que realizamos en un archivo python. Para hacerlo, usar el comando:
```bash
 poetry run playwright codegen
```

### 2.3 Almacenamiento de datos

Los datos se almacenan en:
- `data/scraped_data/properties/`: Archivos JSONL con metadatos
- `data/scraped_data/images/`: Imágenes descargadas
- '

## 3.0 Almacenamiento en base de datos
Usaremos SQLite ya que no requiere de una instalación local y es sencillo de usar. Se debe definir un esquema de datos (schema) con los atributos que se scrapean de la página web y almacenar esa información en la base de datos SQLite.
Perfecto. Acá te sugiero contenido para expandir la sección 3.0, con explicación conceptual y ejemplos de código:

3.0 Almacenamiento en base de datos
Usaremos SQLite ya que no requiere de una instalación local y es sencillo de usar. Se debe definir un esquema de datos (schema) con los atributos que se scrapean de la página web y almacenar esa información en la base de datos SQLite.

¿Por qué usar una base de datos?
Durante el procesamiento de datos es común trabajar con grandes volúmenes de información que necesitan ser consultados, filtrados y actualizados de forma eficiente. Guardar los datos en archivos CSV o JSON puede funcionar para casos simples, pero presenta limitaciones cuando:

- Se necesita evitar registros duplicados.
- Se quieren hacer consultas complejas (filtros, joins, agregaciones).
- Varios procesos necesitan leer y escribir al mismo tiempo.
- Se requiere garantizar integridad de los datos (tipos, restricciones).

Buenas prácticas al interactuar con bases de datos:
- Siempre cerrar la conexión al finalizar: conn.close()
- Usar CREATE TABLE IF NOT EXISTS para que el script sea re-ejecutable sin errores.
- Preferir INSERT OR IGNORE / INSERT OR REPLACE para manejar duplicados.
- Versionar el archivo .db con cuidado — para repositorios git, considerar agregarlo al .gitignore y compartirlo por separado.

## 4. Ejercicio


El ejercicio de este práctico consiste en crear un scraper para una página a elección, y dejarlo en el código en la carpeta `src/scrapers`.

El scraper debe poder correr localmente y almacenar los datos en una BD local SQLite.
