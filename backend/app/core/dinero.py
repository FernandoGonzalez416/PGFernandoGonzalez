from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

CUANTIA = Decimal("0.01")

TiposAceptados = str | Decimal | int


def redondear(valor: Decimal) -> Decimal:
    """Cuantiza a dos decimales con ROUND_HALF_UP (P21)."""
    return valor.quantize(CUANTIA, rounding=ROUND_HALF_UP)


def a_decimal(valor: TiposAceptados) -> Decimal:
    """Convierte a `Decimal` aceptando `str`, `Decimal` e `int`.

    Un `float` se rechaza salvo que sea exactamente representable por su
   decimal más corto: `1.5` y `2.0` pasan, `0.1` y `2.675` no. Es la diferencia
    entre `0.1` (que en binario vale 0.1000000000000000055) y `2.675` (que vale
    2.674999...), donde redondear a dos decimales daría 0.10 y 2.67 en lugar de
    0.10 y 2.68. Para dinero, un `float` nunca es una entrada válida.
    """
    if isinstance(valor, bool):
        raise TypeError("Un booleano no es un valor numérico válido")

    if isinstance(valor, Decimal):
        return valor

    if isinstance(valor, int):
        return Decimal(valor)

    if isinstance(valor, float):
        exacto = Decimal(valor)
        if exacto != Decimal(str(valor)):
            raise TypeError(
                f"El float {valor!r} no es representable de forma exacta como "
                "decimal; envíalo como str o Decimal"
            )
        return exacto

    if isinstance(valor, str):
        try:
            return Decimal(valor)
        except InvalidOperation as error:
            raise ValueError(f"'{valor}' no es un número decimal válido") from error

    raise TypeError(f"Tipo no soportado: {type(valor).__name__}")


def a_cuantia(valor: TiposAceptados) -> Decimal:
    """Convierte y cuantiza a dos decimales en un solo paso."""
    return redondear(a_decimal(valor))