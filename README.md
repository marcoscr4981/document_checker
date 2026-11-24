# Document Checker

Herramienta de línea de comandos (CLI) desarrollada en Python para identificar, normalizar y validar documentos de identificación fiscal españoles: **DNI, NIE, CIF y NIF especiales (K, L y M)**.

El programa permite introducir un número de documento, identificar su tipo y comprobar su formato y, cuando corresponde, su carácter de control.

Para DNI, NIE y CIF, si no se proporciona el carácter de control, el programa lo calcula automáticamente. En los NIF especiales K, L y M únicamente comprueba la estructura del documento, sin verificar su letra de control.

## Características

- Identificación automática de DNI, NIE, CIF y NIF especiales K, L y M.
- Normalización mediante la eliminación de espacios, puntos y guiones.
- Conversión automática de letras a mayúsculas.
- Validación de caracteres, formatos y longitudes permitidas.
- Cálculo y comprobación de letras de control de DNI y NIE.
- Cálculo y comprobación del carácter de control de CIF, tanto numérico como alfabético.
- Identificación del tipo de entidad correspondiente a un CIF.
- Consulta de la provincia asociada a códigos históricos de CIF.
- Identificación y comprobación del formato de los NIF especiales K, L y M.
- Advertencia cuando no se ha verificado el carácter de control.
- Gestión de errores mediante excepciones `ValueError`.
- Implementación utilizando exclusivamente la biblioteca estándar de Python.
- Mensajes de la terminal diferenciados mediante colores ANSI.
- Gestión de interrupciones mediante Ctrl + C, con mensaje de salida y código de terminación 130.

### Reglas de validación

| Documento | Parte principal | Comportamiento |
|---|---|---|
| DNI | De 1 a 8 dígitos | Completa con ceros a la izquierda hasta alcanzar ocho dígitos. |
| NIE | Prefijo X, Y o Z y de 1 a 7 dígitos | Completa con ceros a la izquierda hasta alcanzar siete dígitos. |
| CIF | Letra inicial y 7 dígitos | Exige exactamente siete dígitos, sin completar con ceros. |
| NIF especial | Prefijo K, L o M y 7 caracteres alfanuméricos | Exige nueve caracteres en total, incluida la letra final. |

Para DNI, NIE y CIF, el carácter de control es opcional en la entrada. Si se proporciona, se comprueba su validez; en caso contrario, se calcula automáticamente.

Para los NIF especiales, la letra final es obligatoria, pero no se verifica su correspondencia con los caracteres anteriores.

**Nota:** La validación comprueba formatos y algoritmos de control cuando están implementados. No verifica que un documento exista, esté vigente o haya sido asignado oficialmente.

## Estructura del proyecto

```text
document_checker/
├── document_checker/
│   ├── __init__.py
│   └── __main__.py
├── tests/
│   ├── __init__.py
│   └── test_document_checker.py
├── .gitignore
├── CHANGELOG.md
├── LICENSE
└── README.md
```

## Requisitos

- Python 3.10 o superior.
- No requiere dependencias externas.

## Instalación

Clonar el repositorio:

```bash
git clone https://github.com/USUARIO/document_checker.git
```

Acceder al directorio del proyecto:

```bash
cd document_checker
```

Sustituir `USUARIO` por el nombre de usuario correspondiente de GitHub.

## Uso

Ejecutar la aplicación desde el directorio raíz:

```bash
python -m document_checker
```

El programa solicitará un número de documento:

```text
[?] Número de DNI/NIE/CIF/NIF:
```

### Ejemplo: DNI

**Entrada:**

```text
12345678Z
```

**Salida:**

```text
Tipo de documento: DNI
Número: 12345678Z
```

### Ejemplo: DNI sin letra de control

**Entrada:**

```text
12345678
```

**Salida:**

```text
Tipo de documento: DNI
Número: 12345678Z
```

### Ejemplo: NIE

**Entrada:**

```text
X1234567L
```

**Salida:**

```text
Tipo de documento: NIE
Número: X1234567L
```

### Ejemplo: CIF

**Entrada:**

```text
B12345674
```

**Salida:**

```text
Tipo de documento: CIF
Número: B12345674
Entidad: Sociedad de responsabilidad limitada
Provincia (referencia histórica): Castellón
```

Cuando existe una correspondencia en el catálogo histórico de provincias, el programa también muestra esa información como referencia histórica.

### Ejemplo: NIF especial

**Entrada:**

```text
K1234567A
```

**Salida:**

```text
Tipo de documento: NIF especial
Número: K1234567A
Tipo de NIF especial: Españoles menores de 14 años residentes en España que no disponen de DNI

[!] El formato del documento es correcto, pero no se ha verificado su carácter de control.
```

Este ejemplo muestra la comprobación del formato, no la validez del carácter de control.

### Documentos incorrectos

Si el formato del documento o su carácter de control no son válidos, el programa muestra un mensaje indicando el motivo.

Por ejemplo:

```text
[!] La letra del DNI es incorrecta
```

## Pruebas

El proyecto incluye pruebas unitarias desarrolladas con `unittest`, perteneciente a la biblioteca estándar de Python.

Las pruebas comprueban:

- Normalización de documentos.
- Rechazo de caracteres no permitidos y entradas vacías.
- Cálculo de letras de control de DNI y NIE.
- Validación de documentos con y sin carácter de control.
- Relleno de ceros en DNI y NIE.
- Cálculo de controles numéricos y alfabéticos de CIF.
- Identificación del tipo de entidad de un CIF.
- Comprobación del formato de NIF especiales K, L y M.
- Identificación automática del tipo de documento.
- Gestión de formatos incorrectos y casos límite.
- Presentación de resultados y mensajes de error desde `main()`.
- Comprobación del mensaje y código de salida del manejador de SIGINT.

Para ejecutar las pruebas desde la raíz del proyecto:

```bash
python -m unittest discover -s tests -v
```

## Tecnologías utilizadas

- **Python:** lenguaje de programación.
- **re:** normalización y validación de caracteres.
- **typing:** definición de tipos y estructura de resultados mediante `TypedDict`.
- **signal:** gestión de la señal SIGINT para permitir una salida controlada mediante `Ctrl + C`.
- **sys:** finalización del programa mediante códigos de salida.
- **types:** anotación del marco de ejecución mediante `FrameType`.
- **ANSI:** códigos de escape para mostrar mensajes con colores en la terminal.
- **unittest:** pruebas unitarias.
- **unittest.mock:** simulación de entrada, salida y comportamiento durante las pruebas.

## Limitaciones

- No consulta bases de datos oficiales.
- No verifica la identidad del titular.
- No comprueba si el documento existe o está vigente.
- Los NIF especiales K, L y M se comprueban únicamente a nivel de formato; no se verifica su letra de control.
- La provincia asociada a un CIF es una referencia histórica y no permite determinar de forma fiable la ubicación actual de la entidad.
- El programa está diseñado para su ejecución desde la terminal.

## Licencia

Este proyecto se distribuye bajo los términos indicados en el archivo `LICENSE`.
