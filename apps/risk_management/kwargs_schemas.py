"""
Collection of custom keyword argument types for TA-LIB functions

Note:
You should use manually create a new keyword argument type or merge existing ones,
for TA-LIB functions that have more intricate or complex keyword arguments.
"""

import typing
import attrs
import numpy as np

from .criteria.kwargs_schemas import KwargsSchema


TimePeriod = KwargsSchema(
    "TimePeriod", {"timeperiod": attrs.field(type=int, default=14)}
)

Penetration = KwargsSchema(
    "Penetration", {"penetration": attrs.field(type=float, default=0.0)}
)

FastandSlowPeriod = KwargsSchema(
    "FastandSlowPeriod",
    {
        "fastperiod": attrs.field(type=int, default=0),
        "slowperiod": attrs.field(type=int, default=0),
    },
)

FastandSlowMAType = KwargsSchema(
    "FastandSlowMAType",
    {
        "fastmatype": attrs.field(type=int, default=0),
        "slowmatype": attrs.field(type=int, default=0),
    },
)

MAType = KwargsSchema(
    "MAType",
    {
        "matype": attrs.field(type=int, default=0),
    },
)

SignalMAType = KwargsSchema(
    "SignalMAType",
    {
        "signalmatype": attrs.field(type=int, default=0),
    },
)

SignalPeriod = KwargsSchema(
    "SignalPeriod",
    {
        "signalperiod": attrs.field(type=int, default=0),
    },
)

FastK_Period = KwargsSchema(
    "FastK_Period",
    {
        "fastk_period": attrs.field(type=int, default=0),
    },
)

SlowK_Period = KwargsSchema(
    "SlowK_Period",
    {
        "slowk_period": attrs.field(type=int, default=0),
    },
)


FastD_Period = KwargsSchema(
    "FastD_Period",
    {
        "fastd_period": attrs.field(type=int, default=0),
    },
)

SlowD_Period = KwargsSchema(
    "SlowD_Period",
    {
        "slowd_period": attrs.field(type=int, default=0),
    },
)

FastK_MAType = KwargsSchema(
    "FastK_MAType",
    {
        "fastk_matype": attrs.field(type=int, default=0),
    },
)

SlowK_MAType = KwargsSchema(
    "SlowK_MAType",
    {
        "slowk_matype": attrs.field(type=int, default=0),
    },
)

FastD_MAType = KwargsSchema(
    "FastD_MAType",
    {
        "fastd_matype": attrs.field(type=int, default=0),
    },
)

SlowD_MAType = KwargsSchema(
    "SlowD_MAType",
    {
        "slowd_matype": attrs.field(type=int, default=0),
    },
)

NbDev = KwargsSchema(
    "NbDev",
    {
        "nbdev": attrs.field(type=int, default=1),
    },
)

NbDevUpAndDown = KwargsSchema(
    "NbDevUpAndDown",
    {
        "nbdevup": attrs.field(type=int, default=2),
        "nbdevdn": attrs.field(type=int, default=2),
    },
)

FastandSlowLimit = KwargsSchema(
    "FastandSlowLimit",
    {
        "fastlimit": attrs.field(type=int, default=0),
        "slowlimit": attrs.field(type=int, default=0),
    },
)

MinandMaxPeriod = KwargsSchema(
    "MinandMaxPeriod",
    {
        "minperiod": attrs.field(type=int, default=0),
        "maxperiod": attrs.field(type=int, default=0),
    },
)

Acceleration = KwargsSchema(
    "Acceleration",
    {
        "acceleration": attrs.field(type=float, default=0.02),
    },
)

Maximum = KwargsSchema(
    "Maximum",
    {
        "maximum": attrs.field(type=float, default=0.2),
    },
)

VFactor = KwargsSchema(
    "VFactor",
    {
        "vfactor": attrs.field(type=float, default=0.2),
    },
)


def punctuated_string_to_list(value: str, punctuator: str = ",") -> typing.List[str]:
    """Converts a punctuated string to a list of strings"""
    return value.split(punctuator)


def to_float_ndarray(values: typing.Iterable) -> np.ndarray:
    """Converts an iterable of values to a numpy float ndarray"""
    if isinstance(values, np.ndarray):
        return values.astype(float)

    if isinstance(values, str):
        values = list(map(float, punctuated_string_to_list(values)))

    return np.array(values, dtype=float)


Periods = KwargsSchema(
    "Periods",
    {
        "periods": attrs.field(
            type=np.ndarray[float],
            converter=to_float_ndarray,
            validator=attrs.validators.instance_of(np.ndarray),
        ),
    },
)
