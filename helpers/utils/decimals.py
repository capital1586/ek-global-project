import decimal
import typing


def to_n_decimal_places(
    value: typing.Any, n: int, *, rounding: str = decimal.ROUND_HALF_UP
):
    """
    Converts decimal, integer, float, interger string/float, et. al.
    to `decimal.Decimal` in 'n' decimal places.

    Returns None and empty strings as is.

    :param value: The value to convert
    :param n: The target number of decimal places
    :param rounding: The rounding mode to use.
    """
    if n < 1:
        raise ValueError("n cannot be less than 1")

    if value is None or value == "":
        return value

    exp = decimal.Decimal(f"1.{'0' * n}")
    if isinstance(value, decimal.Decimal):
        return value.quantize(exp, rounding)
    return decimal.Decimal(value).quantize(exp, rounding)
