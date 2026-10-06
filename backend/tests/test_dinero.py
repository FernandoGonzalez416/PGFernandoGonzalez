from decimal import Decimal

import pytest

from app.core.dinero import CUANTIA, a_cuantia, a_decimal, redondear


class TestRedondear:
    @pytest.mark.parametrize(
        ("entrada", "esperado"),
        [
            (Decimal("0.005"), Decimal("0.01")),
            (Decimal("1.005"), Decimal("1.01")),
            (Decimal("2.675"), Decimal("2.68")),
        ],
    )
    def test_limites_redondean_half_up(self, entrada: Decimal, esperado: Decimal) -> None:
        assert redondear(entrada) == esperado

    def test_exactos_no_cambian(self) -> None:
        assert redondear(Decimal("55.00")) == Decimal("55.00")

    def test_copia_enteros(self) -> None:
        assert redondear(Decimal("7")) == Decimal("7.00")

    def test_negativos_redondean_lejos_del_cero(self) -> None:
        assert redondear(Decimal("-2.675")) == Decimal("-2.68")

    def test_produce_siempre_dos_decimales(self) -> None:
        assert str(redondear(Decimal("3.1"))) == "3.10"


class TestADecimal:
    def test_acepta_str(self) -> None:
        assert a_decimal("18.50") == Decimal("18.50")

    def test_acepta_decimal(self) -> None:
        assert a_decimal(Decimal("18.50")) == Decimal("18.50")

    def test_acepta_entero(self) -> None:
        assert a_decimal(12) == Decimal(12)

    @pytest.mark.parametrize("valor", [2.0, 1.5, 0.0, 24.0])
    def test_acepta_float_exacto(self, valor: float) -> None:
        assert a_decimal(valor) == Decimal(str(valor))

    @pytest.mark.parametrize("valor", [0.1, 2.675, 0.005, 55.55])
    def test_rechaza_float_ambiguo(self, valor: float) -> None:
        with pytest.raises(TypeError):
            a_decimal(valor)

    def test_el_float_ambiguo_se_romperia_sin_el_rechazo(self) -> None:
        with pytest.raises(TypeError):
            a_decimal(2.675)
        assert redondear(Decimal("2.675")) == Decimal("2.68")

    def test_rechaza_booleano(self) -> None:
        with pytest.raises(TypeError):
            a_decimal(True)

    @pytest.mark.parametrize("valor", [None, [], {}, 3 + 2j])
    def test_rechaza_tipo_no_numerico(self, valor: object) -> None:
        with pytest.raises(TypeError):
            a_decimal(valor)

    def test_str_no_numerico_es_value_error(self) -> None:
        with pytest.raises(ValueError):
            a_decimal("abc")


class TestACuantia:
    def test_convierte_y_cuantiza(self) -> None:
        assert a_cuantia("18.567") == Decimal("18.57")

    def test_es_el_mismo_paso_que_dos_llamadas(self) -> None:
        assert a_cuantia("18.567") == redondear(a_decimal("18.567"))

    def test_cuantia_es_dos_decimales(self) -> None:
        assert CUANTIA == Decimal("0.01")