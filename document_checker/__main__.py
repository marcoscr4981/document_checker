#!/usr/bin/env python3
import re
import signal
import sys
from types import FrameType
from typing import NotRequired, TypedDict


COLORS: dict[str, str] = {
    "question": "\033[0;32m",
    "info": "\033[0;36m",
    "error": "\033[0;31m",
    "reset": "\033[0m",
}

DNI_LETTERS: str = "TRWAGMYFPDXBNJZSQVHLCKE"
DNI_NUMBER_LENGTH: int = 8

NIE_NUMBER_LENGTH: int = 7
NIE_PREFIX_VALUES: dict[str, str] = {
    "X": "0",
    "Y": "1",
    "Z": "2"
}

SPECIAL_NIF_TYPES: dict[str, str] = {
    "K": "Españoles menores de 14 años residentes en España que no disponen de DNI",
    "L": "Españoles residentes en el extranjero que no disponen de DNI",
    "M": "Extranjeros que no disponen de NIE y necesitan identificación fiscal",
}

CIF_NUMBER_LENGTH: int = 7
CIF_INITIAL_LETTERS: str = "ABCDEFGHJNPQRSUVW"
CIF_CONTROL_LETTERS: str = "JABCDEFGHI"
CIF_MANDATORY_LETTERS: frozenset[str] = frozenset("NPQRSW")
CIF_MANDATORY_NUMBERS: frozenset[str] = frozenset("ABEH")
CIF_ENTITY_TYPES: dict[str, str] = {
        "A": "Sociedad anónima",
        "B": "Sociedad de responsabilidad limitada",
        "C": "Sociedad colectiva",
        "D": "Sociedad comanditaria",
        "E": "Comunidad de bienes",
        "F": "Sociedad cooperativa",
        "G": "Asociación",
        "H": "Comunidad de propietarios en régimen de propiedad horizontal",
        "J": "Sociedad civil",
        "N": "Entidad extranjera",
        "P": "Corporación Local",
        "Q": "Organismo público",
        "R": "Congregación o institución religiosa",
        "S": "Órgano de la Administración General del Estado o de las Comunidades Autónomas",
        "U": "Unión Temporal de Empresas (UTE)",
        "V": "Otro tipo no definido en el resto de claves",
        "W": "Establecimiento permanente de entidad no residente en España",
    }

CIF_PROVINCES: dict[str, str] = {
    "00": "No residente",
    "01": "Álava",
    "02": "Albacete",
    "03": "Alicante",
    "04": "Almería",
    "05": "Ávila",
    "06": "Badajoz",
    "07": "Illes Balears",
    "08": "Barcelona",
    "09": "Burgos",
    "10": "Cáceres",
    "11": "Cádiz",
    "12": "Castellón",
    "13": "Ciudad Real",
    "14": "Córdoba",
    "15": "A Coruña",
    "16": "Cuenca",
    "17": "Girona",
    "18": "Granada",
    "19": "Guadalajara",
    "20": "Gipuzkoa",
    "21": "Huelva",
    "22": "Huesca",
    "23": "Jaén",
    "24": "León",
    "25": "Lleida",
    "26": "La Rioja",
    "27": "Lugo",
    "28": "Madrid",
    "29": "Málaga",
    "30": "Murcia",
    "31": "Navarra",
    "32": "Ourense",
    "33": "Asturias",
    "34": "Palencia",
    "35": "Las Palmas",
    "36": "Pontevedra",
    "37": "Salamanca",
    "38": "Santa Cruz de Tenerife",
    "39": "Cantabria",
    "40": "Segovia",
    "41": "Sevilla",
    "42": "Soria",
    "43": "Tarragona",
    "44": "Teruel",
    "45": "Toledo",
    "46": "Valencia",
    "47": "Valladolid",
    "48": "Bizkaia",
    "49": "Zamora",
    "50": "Zaragoza",
    "51": "Ceuta",
    "52": "Melilla",
}


class DocumentResult(TypedDict):
    document_type: str
    number: str
    entity_type: NotRequired[str]
    province: NotRequired[str | None]
    special_nif_type: NotRequired[str]
    control_verified: NotRequired[bool]


def normalize_document_number(document_number: str) -> str:
    """Normaliza un número de documento de identidad.

    Elimina espacios en blanco, puntos y guiones, y convierte las letras a mayúsculas.

    Args:
        document_number (str): Número de documento original.

    Returns:
        str: Número de documento normalizado.

    Raises:
        ValueError: Si el documento está vacío o contiene caracteres no permitidos.
    """
    normalized: str = re.sub(r"[\s.-]", "", document_number).upper()

    if not normalized:
        raise ValueError("El número de documento está vacío")

    if not re.fullmatch(r"[A-Z0-9]+", normalized):
        raise ValueError("El documento contiene caracteres no permitidos")

    return normalized


def calculate_dni_nif_letter(number: str) -> str:
    """Calcula la letra de control de un DNI o NIE.

    Para el NIE, la letra inicial (X, Y o Z) debe haberse sustituido previamente por su equivalente numérico (0, 1 o 2).

    Args:
        number (str): Cadena de ocho dígitos utilizada para calcular la letra de control.

    Returns:
        str: Letra de control correspondiente al número.

    Raises:
        ValueError: Si el número no contiene exactamente ocho dígitos ASCII.
    """
    if (
        len(number) != DNI_NUMBER_LENGTH
        or not number.isascii()
        or not number.isdigit()
    ):
        raise ValueError("El número debe contener ocho dígitos")

    return DNI_LETTERS[int(number) % 23]

# -----------------------------------------------------------
# DNI
# -----------------------------------------------------------

def validate_dni(dni: str) -> DocumentResult:
    """Valida un DNI y devuelve su representación completa.

    Si el número tiene menos de ocho dígitos, se completa con ceros a la izquierda.

    Si se proporciona una letra de control, comprueba que sea correcta. En caso contrario, la calcula.

    Args:
        dni (str): DNI con o sin letra de control.

    Returns:
        DocumentResult: Objeto con el tipo de documento y el DNI completo con su letra de control.

    Raises:
        ValueError: Si el formato, la longitud o la letra de control son incorrectos.
    """
    if not dni:
        raise ValueError("El DNI no puede estar vacío")

    number: str = dni if dni[-1].isdigit() else dni[:-1]
    provided_letter: str = dni[-1] if dni[-1].isalpha() else ""

    if not number.isascii() or not number.isdigit():
        raise ValueError("El DNI debe contener solo dígitos")

    if not 1 <= len(number) <= DNI_NUMBER_LENGTH:
        raise ValueError("Longitud del DNI incorrecta")

    number = number.zfill(DNI_NUMBER_LENGTH)
    calculated_letter: str = calculate_dni_nif_letter(number)

    if provided_letter and provided_letter != calculated_letter:
        raise ValueError("La letra del DNI es incorrecta")

    return DocumentResult(
        document_type="DNI",
        number=f"{number}{calculated_letter}"
    )


# -----------------------------------------------------------
# NIE
# -----------------------------------------------------------

def validate_nie(nie: str) -> DocumentResult:
    """Valida un NIE y devuelve su representación completa.

    Si el número tiene menos de siete dígitos, se completa con ceros a la izquierda.

    Si se proporciona una letra de control, comprueba que sea correcta. En caso contrario, la calcula.

    Args:
        nie (str): NIE con o sin letra de control.

    Returns:
        DocumentResult: Objeto con el tipo de documento y el NIE completo con su letra de control.

    Raises:
        ValueError: Si el formato, la longitud o la letra de control son incorrectos.
    """
    if len(nie) < 2:
        raise ValueError("El NIE debe contener una letra inicial y un número")

    # Letra inicial
    initial_letter: str = nie[0]

    if initial_letter not in NIE_PREFIX_VALUES:
        raise ValueError("La letra inicial del NIE es incorrecta")

    # Número y letra proporcionada
    number: str = nie[1:] if nie[-1].isdigit() else nie[1:-1]
    provided_letter: str = nie[-1] if nie[-1].isalpha() else ""

    if not number.isascii() or not number.isdigit():
        raise ValueError("El NIE debe contener solo dígitos")

    if not 1 <= len(number) <= NIE_NUMBER_LENGTH:
        raise ValueError("Longitud del NIE incorrecta")

    number = number.zfill(NIE_NUMBER_LENGTH)

    # Cálculo de la letra de control
    calculated_number: str = f"{NIE_PREFIX_VALUES[initial_letter]}{number}"
    calculated_letter: str = calculate_dni_nif_letter(calculated_number)

    if provided_letter and provided_letter != calculated_letter:
        raise ValueError("La letra del NIE es incorrecta")

    return DocumentResult(
        document_type="NIE",
        number=f"{initial_letter}{number}{calculated_letter}"
    )


# -----------------------------------------------------------
# NIF especial
# -----------------------------------------------------------

def check_special_nif_format(nif: str) -> None:
    """Comprueba la estructura de un NIF especial.

    Args:
        nif (str): NIF especial normalizado.

    Raises:
        ValueError: Si el formato es incorrecto.
    """
    if len(nif) == 8:
        raise ValueError(
            "El NIF especial debe incluir la letra de control. "
            "Actualmente no es posible calcularla automáticamente."
        )

    if len(nif) != 9:
        raise ValueError("Longitud del NIF especial incorrecta")

    if nif[0] not in SPECIAL_NIF_TYPES:
        raise ValueError("Prefijo del NIF especial incorrecto")

    characters: str = nif[1:8]
    control_letter: str = nif[8]

    if not characters.isascii() or not characters.isalnum():
        raise ValueError("Los siete caracteres intermedios deben ser alfanuméricos")

    if not ("A" <= control_letter <= "Z"):
        raise ValueError("Carácter de control incorrecto")
    

def validate_special_nif(nif: str) -> DocumentResult:
    """Comprueba el formato de un NIF especial K, L o M.

    Comprueba que el documento tenga una estructura correcta. No verifica la letra de control.

    Args:
        nif (str): NIF especial normalizado de nueve caracteres.

    Returns:
        DocumentResult: Diccionario con el tipo de documento, el número, su descripción y el estado de verificación.

    Raises:
        ValueError: Si el formato del NIF especial es incorrecto.
    """
    check_special_nif_format(nif)

    initial_letter: str = nif[0]

    return DocumentResult(
        document_type="NIF especial",
        number=nif,
        special_nif_type=SPECIAL_NIF_TYPES[initial_letter],
        control_verified=False
    )


# -----------------------------------------------------------
# CIF
# -----------------------------------------------------------

def calculate_cif_control_digits(digits: str) -> int:
    """Calcula el dígito base de control a partir de siete cifras.

    Args:
        digits (str): Cadena de siete dígitos.

    Returns:
        int: Dígito de control entre 0 y 9.

    Raises:
        ValueError: Si la cadena no contiene siete dígitos ASCII.
    """
    if (
        len(digits) != CIF_NUMBER_LENGTH
        or not digits.isascii()
        or not digits.isdigit()
    ):
        raise ValueError("Se requieren exactamente siete dígitos")

    sum_even_numbers: int = sum(int(digits[i]) for i in (1, 3, 5))

    sum_odd_numbers: int = 0

    for i in (0, 2, 4, 6):
        double: int = int(digits[i]) * 2
        sum_odd_numbers += (double // 10) + (double % 10)

    total: int = sum_even_numbers + sum_odd_numbers

    return (10 - (total % 10)) % 10


def calculate_cif_control(cif: str) -> tuple[str, ...]:
    """Calcula los caracteres de control válidos de un CIF.

    Args:
        cif (str): CIF sin carácter de control, formado por una letra inicial y siete dígitos.

    Returns:
        tuple[str, ...]: Caracteres de control válidos. Puede contener un número, una letra o ambos.

    Raises:
        ValueError: Si el formato o la longitud son incorrectos.
    """
    if len(cif) != CIF_NUMBER_LENGTH + 1:
        raise ValueError("Longitud del CIF incorrecta")

    initial_letter: str = cif[0]
    digits: str = cif[1:]

    if (
        initial_letter not in CIF_INITIAL_LETTERS
        or not digits.isascii()
        or not digits.isdigit()
    ):
        raise ValueError("Formato del CIF incorrecto")

    # Cálculo del dígito de control
    control: int = calculate_cif_control_digits(digits)

    # Determinar los caracteres de control válidos
    if initial_letter in CIF_MANDATORY_LETTERS:
        return (CIF_CONTROL_LETTERS[control],)

    if initial_letter in CIF_MANDATORY_NUMBERS:
        return (str(control),)

    return (str(control), CIF_CONTROL_LETTERS[control])


def get_cif_province(cif: str) -> str | None:
    """Obtiene la provincia asociada al código del CIF.

    Args:
        cif (str): CIF previamente validado.

    Returns:
        str | None: Provincia asociada al código, o None si no existe una correspondencia conocida.
    """
    province_code: str = cif[1:3]

    return CIF_PROVINCES.get(province_code)


def get_cif_entity_type(cif: str) -> str:
    """Obtiene el tipo de entidad correspondiente a un CIF.

    Args:
        cif (str): Número de documento CIF.

    Returns:
        str: Descripción del tipo de entidad.

    Raises:
        ValueError: Si el documento está vacío o su letra inicial no corresponde a una entidad válida.
    """
    if not cif:
        raise ValueError("El CIF no puede estar vacío")

    initial_letter: str = cif[0].upper()

    if initial_letter not in CIF_ENTITY_TYPES:
        raise ValueError(f"La letra inicial '{initial_letter}' no corresponde a un CIF válido")

    return CIF_ENTITY_TYPES[initial_letter]


def validate_cif(cif: str) -> DocumentResult:
    """Valida un CIF y devuelve sus datos.

    Comprueba el carácter de control si se proporciona.
    Si no se proporciona, calcula los controles válidos.

    Args:
        cif (str): CIF con o sin carácter de control.

    Returns:
        DocumentResult: Objeto con el tipo de documento, su número y el tipo de entidad.

    Raises:
        ValueError: Si el formato, la longitud o el carácter de control son incorrectos.
    """
    if len(cif) not in (8, 9):
        raise ValueError("Longitud del CIF incorrecta")

    cif_base: str = cif[:8]
    provided_control: str = cif[8] if len(cif) == 9 else ""

    valid_controls: tuple[str, ...] = calculate_cif_control(cif_base)

    if provided_control and provided_control not in valid_controls:
        raise ValueError("Carácter de control del CIF incorrecto")

    entity_type: str = get_cif_entity_type(cif_base)

    if provided_control:
        complete_number: str = cif_base + provided_control
    else:
        complete_number = cif_base + valid_controls[0]

    province: str | None = get_cif_province(cif)

    return DocumentResult(
        document_type="CIF",
        number=complete_number,
        entity_type=entity_type,
        province=province
    )

# -----------------------------------------------------------
# -----------------------------------------------------------

def identify_document(document_number: str) -> DocumentResult:
    """Identifica y comprueba un documento DNI, NIE, CIF o NIF especial.

    El documento debe estar previamente normalizado.
    Los NIF especiales K, L y M se comprueban únicamente a nivel de formato, sin verificar su carácter de control.

    Args:
        document_number (str): Número de documento normalizado.

    Returns:
        DocumentResult: Información del documento identificado y resultado de las comprobaciones realizadas.

    Raises:
        ValueError: Si el documento está vacío, su tipo no se reconoce o no supera las comprobaciones.
    """
    if not document_number:
        raise ValueError("El documento no puede estar vacío")

    initial_character: str = document_number[0]

    if "0" <= initial_character <= "9":
        return validate_dni(document_number)

    if initial_character in "XYZ":
        return validate_nie(document_number)

    if initial_character in SPECIAL_NIF_TYPES:
        return validate_special_nif(document_number)

    if initial_character in CIF_INITIAL_LETTERS:
        return validate_cif(document_number)

    raise ValueError("Tipo de documento no reconocido")


def def_handler(_sig: int, _frame: FrameType | None) -> None:
    """Gestiona SIGINT para finalizar el programa ordenadamente.

    Args:
        sig (int): Señal recibida.
        frame (FrameType | None): Marco de ejecución interrumpido.
    """
    print(f"\n\n{COLORS['error']}[!] Saliendo...{COLORS['reset']}\n")
    sys.exit(130)


def main() -> None:
    """Solicita, valida y muestra un documento DNI, NIE, CIF o NIF especial."""
    try:
        document_number: str = input(f"\n{COLORS['question']}[?] Número de DNI/NIE/CIF/NIF: {COLORS['reset']}")

        normalized_document: str = normalize_document_number(document_number)

        result: DocumentResult = identify_document(normalized_document)

        print(f"\n{COLORS['info']}Tipo de documento:{COLORS['reset']} {result['document_type']}")
        print(f"{COLORS['info']}Número:{COLORS['reset']} {result['number']}")

        special_nif: str | None = result.get("special_nif_type")
        if special_nif:
            print(f"{COLORS['info']}Tipo de NIF especial:{COLORS['reset']} {special_nif}")

        entity_type: str | None = result.get("entity_type")
        if entity_type:
            print(f"{COLORS['info']}Entidad:{COLORS['reset']} {entity_type}")

        province: str | None = result.get("province")
        if province:
            print(f"{COLORS['info']}Provincia (referencia histórica):{COLORS['reset']} {province}")

        # Advertencia cuando no se ha verificado el control
        if result.get("control_verified") is False:
            print(
                f"\n{COLORS['error']}[!] El formato del documento es correcto, "
                f"pero no se ha verificado su carácter de control.{COLORS['reset']}"
            )

    except ValueError as e:
        print(f"\n{COLORS['error']}[!] {e}{COLORS['reset']}")

    print()


if __name__ == "__main__":
    signal.signal(signal.SIGINT, def_handler)
    main()
