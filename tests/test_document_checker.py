import signal
import unittest
from unittest.mock import patch
from document_checker.__main__ import def_handler
from document_checker.__main__ import main
from document_checker.__main__ import (
    normalize_document_number,
    calculate_dni_nif_letter,
    calculate_cif_control,
    get_cif_province,
    get_cif_entity_type,
    validate_dni,
    validate_nie,
    validate_cif,
    identify_document,
    validate_special_nif,
    check_special_nif_format,
    SPECIAL_NIF_TYPES,
    COLORS
)


class TestDefHandler(unittest.TestCase):
    """Pruebas del manejador de la señal SIGINT."""

    @patch("builtins.print")
    @patch("sys.exit")
    def test_def_handler_message(
        self,
        mock_exit,
        mock_print
    ) -> None:
        """Comprueba que se muestra el mensaje de salida."""
        def_handler(signal.SIGINT, None)

        expected_message: str = (
            f"\n\n{COLORS['error']}[!] Saliendo..."
            f"{COLORS['reset']}\n"
        )

        mock_print.assert_called_once_with(expected_message)

    @patch("builtins.print")
    def test_def_handler_exit_code(self, mock_print) -> None:
        """Comprueba que el programa termina con el código 130."""
        with self.assertRaises(SystemExit) as context:
            def_handler(signal.SIGINT, None)

        self.assertEqual(context.exception.code, 130)


class TestMain(unittest.TestCase):
    """Pruebas de la interfaz principal del programa."""

    @patch("builtins.print")
    @patch("builtins.input", return_value="12345678Z")
    def test_main_valid_dni(self, mock_input, mock_print) -> None:
        """Comprueba que main muestra correctamente un DNI válido."""
        main()

        mock_input.assert_called_once_with(
            f"\n{COLORS['question']}[?] Número de DNI/NIE/CIF/NIF: {COLORS['reset']}"
        )

        mock_print.assert_any_call(f"\n{COLORS['info']}Tipo de documento:{COLORS['reset']} DNI")
        mock_print.assert_any_call(f"{COLORS['info']}Número:{COLORS['reset']} 12345678Z")

    @patch("builtins.print")
    @patch("builtins.input")
    def test_main_valid_nie_cif(self, mock_input, mock_print) -> None:
        """Comprueba que main muestra correctamente NIE y CIF válidos."""
        cases: tuple[tuple[str, str], ...] = (
            ("X1234567L", "NIE"),
            ("A12345674", "CIF"),
        )

        for document, document_type in cases:
            with self.subTest(document=document):
                mock_input.return_value = document
                mock_print.reset_mock()

                main()

                mock_print.assert_any_call(
                    f"\n{COLORS['info']}Tipo de documento:{COLORS['reset']} {document_type}"
                )
                mock_print.assert_any_call(
                    f"{COLORS['info']}Número:{COLORS['reset']} {document}"
                )

    @patch("builtins.print")
    @patch("builtins.input")
    def test_main_special_nif(self, mock_input, mock_print) -> None:
        """Comprueba la presentación de los NIF especiales."""
        cases: tuple[str, ...] = (
            "K1234567A",
            "L1234567A",
            "MABC1234D",
        )

        warning: str = (
            f"\n{COLORS['error']}[!] El formato del documento es correcto, "
            f"pero no se ha verificado su carácter de control.{COLORS['reset']}"
        )

        for nif in cases:
            with self.subTest(nif=nif):
                mock_input.return_value = nif
                mock_print.reset_mock()

                main()

                mock_print.assert_any_call(
                    f"\n{COLORS['info']}Tipo de documento:{COLORS['reset']} NIF especial"
                )
                mock_print.assert_any_call(
                    f"{COLORS['info']}Número:{COLORS['reset']} {nif}"
                )
                mock_print.assert_any_call(
                    f"{COLORS['info']}Tipo de NIF especial:{COLORS['reset']} {SPECIAL_NIF_TYPES[nif[0]]}"
                )
                mock_print.assert_any_call(warning)


    @patch("builtins.print")
    @patch("builtins.input")
    def test_main_invalid_documents(self, mock_input, mock_print) -> None:
        """Comprueba los mensajes de error de documentos incorrectos."""
        cases: tuple[tuple[str, str], ...] = (
            ("", "El número de documento está vacío"),
            ("T1234567A", "Tipo de documento no reconocido"),
            (
                "MABC1234",
                "El NIF especial debe incluir la letra de control. "
                "Actualmente no es posible calcularla automáticamente."
            ),
        )

        for document, expected_error in cases:
            with self.subTest(document=document):
                mock_input.return_value = document
                mock_print.reset_mock()

                main()

                mock_print.assert_any_call(
                    f"\n{COLORS['error']}[!] {expected_error}{COLORS['reset']}"
                )


class TestNormalizeDocumentNumber(unittest.TestCase):

    def test_normalize_document_number(self) -> None:
        """Comprueba la normalización de documentos válidos."""
        cases: dict[str, str] = {
            "12345678z": "12345678Z",
            "12.345.678-z": "12345678Z",
            " 12345678 z ": "12345678Z",
            "x-1234567-l": "X1234567L",
            "B 1234567 4": "B12345674",
        }

        for document, expected in cases.items():
            with self.subTest(document=document):
                result = normalize_document_number(document)
                self.assertEqual(result, expected)

    def test_invalid_characters(self) -> None:
        """Comprueba el rechazo de caracteres no permitidos."""
        cases: tuple[str, ...] = (
            "",
            "   ",
            "1234@5678Z",
            "1234Ñ5678",
            "1234/5678Z",
        )

        for document in cases:
            with self.subTest(document=document):
                with self.assertRaises(ValueError):
                    normalize_document_number(document)

    def test_normalize_empty_after_cleanup(self) -> None:
        """Comprueba documentos vacíos después de normalizarlos."""
        cases: tuple[str, ...] = (
            "",
            "   ",
            "...",
            "---",
            " . - ",
        )

        for document in cases:
            with self.subTest(document=document):
                with self.assertRaises(ValueError):
                    normalize_document_number(document)


class TestDNI(unittest.TestCase):

    def test_calculate_letter(self) -> None:
        """Comprueba el cálculo de letras de control."""
        cases: dict[str, str] = {
            "12345678": "Z",
            "00000000": "T",
            "00123456": "S",
            "01234567": "L",
        }

        for number, expected in cases.items():
            with self.subTest(number=number):
                self.assertEqual(
                    calculate_dni_nif_letter(number),
                    expected
                )

    def test_invalid_number_for_letter(self) -> None:
        """Comprueba números incorrectos para el cálculo."""
        cases = ("1234567", "123456789", "1234567A", "")

        for number in cases:
            with self.subTest(number=number):
                with self.assertRaises(ValueError):
                    calculate_dni_nif_letter(number)

    def test_validate_dni(self) -> None:
        """Comprueba DNI válidos, con y sin letra."""
        cases: dict[str, str] = {
            "12345678Z": "12345678Z",
            "12345678": "12345678Z",
            "123456": "00123456S",
            "123456S": "00123456S",
            "00000000T": "00000000T",
        }

        for dni, expected in cases.items():
            with self.subTest(dni=dni):
                result = validate_dni(dni)

                self.assertEqual(result["document_type"], "DNI")
                self.assertEqual(result["number"], expected)

    def test_invalid_dni(self) -> None:
        """Comprueba el rechazo de DNI incorrectos."""
        cases = (
            "12345678A",
            "123456A",
            "123456789Z",
            "1234ABCD",
            "",
        )

        for dni in cases:
            with self.subTest(dni=dni):
                with self.assertRaises(ValueError):
                    validate_dni(dni)


class TestNIE(unittest.TestCase):

    def test_validate_nie(self) -> None:
        """Comprueba NIE válidos y el relleno con ceros."""
        cases: dict[str, str] = {
            "X1234567L": "X1234567L",
            "X1234567": "X1234567L",
            "X12345": "X0012345V",
            "Y1234567X": "Y1234567X",
            "Z1234567R": "Z1234567R",
        }

        for nie, expected in cases.items():
            with self.subTest(nie=nie):
                result = validate_nie(nie)

                self.assertEqual(result["document_type"], "NIE")
                self.assertEqual(result["number"], expected)

    def test_invalid_nie(self) -> None:
        """Comprueba el rechazo de NIE incorrectos."""
        cases = (
            "X1234567A",
            "A1234567L",
            "X12345678L",
            "X1234ABC",
            "X",
            "",
        )

        for nie in cases:
            with self.subTest(nie=nie):
                with self.assertRaises(ValueError):
                    validate_nie(nie)


class TestCIF(unittest.TestCase):

    def test_special_nif_prefixes_are_not_cif(self) -> None:
        """Comprueba que K, L y M no se aceptan como CIF."""
        for initial_letter in "KLM":
            with self.subTest(initial_letter=initial_letter):
                cif = f"{initial_letter}1234567"

                with self.assertRaises(ValueError):
                    calculate_cif_control(cif)

                with self.assertRaises(ValueError):
                    get_cif_entity_type(cif)

                with self.assertRaises(ValueError):
                    validate_cif(cif)

    def test_calculate_cif_control(self) -> None:
        """Comprueba los controles válidos según el prefijo."""
        cases: dict[str, tuple[str, ...]] = {
            "B1234567": ("4",),
            "A1234567": ("4",),
            "P1234567": ("D",),
            "N1234567": ("D",),
            "F1234567": ("4", "D"),
        }

        for cif, expected in cases.items():
            with self.subTest(cif=cif):
                self.assertEqual(
                    calculate_cif_control(cif),
                    expected
                )

    def test_get_cif_province(self) -> None:
        """Comprueba la obtención de la provincia del CIF."""
        cases: dict[str, str] = {
            "B2800000": "Madrid",
            "A0800000": "Barcelona",
            "P4100000": "Sevilla",
            "B0000000": "No residente",
            "B5200000": "Melilla",
        }

        for cif, expected in cases.items():
            with self.subTest(cif=cif):
                self.assertEqual(
                    get_cif_province(cif),
                    expected
                )


    def test_unknown_cif_province(self) -> None:
        """Comprueba los códigos provinciales desconocidos."""
        self.assertIsNone(get_cif_province("B9900000"))

    def test_invalid_cif_control_input(self) -> None:
        """Comprueba entradas incorrectas para el cálculo."""
        cases = (
            "",
            "B123",
            "B12345678",
            "B1234ABC",
            "K1234567",
        )

        for cif in cases:
            with self.subTest(cif=cif):
                with self.assertRaises(ValueError):
                    calculate_cif_control(cif)

    def test_validate_cif(self) -> None:
        """Comprueba CIF válidos con y sin control y su provincia."""
        cases: tuple[tuple[str, str, str], ...] = (
            ("B12345674", "B12345674", "Castellón"),
            ("B1234567", "B12345674", "Castellón"),
            ("P1234567D", "P1234567D", "Castellón"),
            ("P1234567", "P1234567D", "Castellón"),
            ("F12345674", "F12345674", "Castellón"),
            ("F1234567D", "F1234567D", "Castellón"),
        )

        for cif, expected_number, expected_province in cases:
            with self.subTest(cif=cif):
                result = validate_cif(cif)

                self.assertEqual(result["document_type"], "CIF")
                self.assertEqual(result["number"], expected_number)
                self.assertIn("entity_type", result)
                self.assertEqual(result["province"], expected_province)

    def test_invalid_cif(self) -> None:
        """Comprueba el rechazo de CIF incorrectos."""
        cases = (
            "B1234567A",
            "P12345674",
            "B123",
            "K1234567",
            "",
        )

        for cif in cases:
            with self.subTest(cif=cif):
                with self.assertRaises(ValueError):
                    validate_cif(cif)


class TestIdentifyDocument(unittest.TestCase):

    def test_identify_document(self) -> None:
        """Comprueba la identificación de documentos válidos."""
        cases = (
            ("12345678Z", "DNI", "12345678Z"),
            ("X1234567L", "NIE", "X1234567L"),
            ("B12345674", "CIF", "B12345674"),
            ("K1234567D", "NIF especial", "K1234567D"),
            ("L1234567D", "NIF especial", "L1234567D"),
            ("M1234567D", "NIF especial", "M1234567D"),
        )

        for document, expected_type, expected_number in cases:
            with self.subTest(document=document):
                result = identify_document(document)

                self.assertEqual(
                    result["document_type"],
                    expected_type
                )
                self.assertEqual(
                    result["number"],
                    expected_number
                )

    def test_invalid_document_type(self) -> None:
        """Comprueba documentos con prefijos desconocidos."""
        cases = ("", "T1234567", "@1234567")

        for document in cases:
            with self.subTest(document=document):
                with self.assertRaises(ValueError):
                    identify_document(document)

class TestSpecialNIF(unittest.TestCase):

    def test_validate_special_nif(self) -> None:
        """Comprueba los NIF especiales con formato correcto."""
        cases: tuple[str, ...] = (
            "K1234567A",
            "L1234567A",
            "M1234567A",
            "K12A4567B",
            "L123B567C",
            "MABC1234D",
        )

        for nif in cases:
            with self.subTest(nif=nif):
                result = validate_special_nif(nif)

                self.assertEqual(result["document_type"], "NIF especial")
                self.assertEqual(result["number"], nif)
                self.assertEqual(
                    result["special_nif_type"],
                    SPECIAL_NIF_TYPES[nif[0]]
                )
                self.assertFalse(result["control_verified"])
                

    def test_special_nif_invalid_length(self) -> None:
        """Comprueba que se rechazan NIF especiales con longitud incorrecta."""
        cases: tuple[str, ...] = (
            "K12345",
            "L12345",
            "M12345",
            "K12345678A",
            "L12345678A",
            "M12345678A",
        )

        for nif in cases:
            with self.subTest(nif=nif):
                with self.assertRaises(ValueError):
                    validate_special_nif(nif)

    def test_invalid_special_nif(self) -> None:
        """Comprueba el rechazo de NIF especiales con formato incorrecto."""
        cases: tuple[str, ...] = (
            "",
            "K",
            "L",
            "M",
            "K1234567",
            "L1234567",
            "M1234567",
            "K12345A",
            "L12345A",
            "M12345A",
            "K12345678A",
            "L12345678A",
            "M12345678A",
            "K12345671",
            "L1234567!",
            "M12345-7A",
        )

        for nif in cases:
            with self.subTest(nif=nif):
                with self.assertRaises(ValueError):
                    validate_special_nif(nif)

    def test_special_nif_valid_format(self) -> None:
        """Comprueba los formatos válidos de los NIF especiales."""
        cases: tuple[str, ...] = (
            "K1234567A",
            "L1234567B",
            "M1234567C",
            "K12A4567D",
            "L123B567E",
            "MABC1234F",
        )

        for nif in cases:
            with self.subTest(nif=nif):
                check_special_nif_format(nif)


    def test_special_nif_invalid_format(self) -> None:
        """Comprueba los formatos incorrectos de los NIF especiales."""
        cases: tuple[str, ...] = (
            "",
            "K",
            "K12345A",
            "L12345678A",
            "M1234567",
            "K1234567",
            "K1234567!",
            "K12345671",
            "X1234567A",
            "K12345-7A",
            "K123456ñA",
        )

        for nif in cases:
            with self.subTest(nif=nif):
                with self.assertRaises(ValueError):
                    check_special_nif_format(nif)