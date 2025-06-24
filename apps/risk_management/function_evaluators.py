"""Collection of TA-LIB function evaluators for use in criteria"""

import typing
import numpy as np
import functools
import attrs
from django.utils.itercompat import is_iterable

from apps.stocks.models import Rate, Stock

from .criteria import functions
from .criteria.kwargs_schemas import KwargsSchema, MergeKwargsSchemas
from . import kwargs_schemas as ks
from . import arg_evaluators as arg_ev


EVALUATOR_GROUPS = (
    "Price Indicators",
    "Volatility Indicators",
    "Pattern Recognition",
    "Momentum Indicators",
    "Math Operators",
    "Overlap Studies",
    "Statistic Functions",
)


_T = typing.TypeVar("_T")


def _return_first_value(result: typing.Iterable[_T]) -> _T:
    """
    Returns only the first value of the result set.

    Since based on the stock rates data ordering,
    the latest rate data is always the first element of the result set.
    """
    if isinstance(result, np.ndarray):
        if not result.any():
            return 0
    else:
        if not result:
            return 0

    if not is_iterable(result):
        return result
    return _return_first_value(result[0])


####################
# PRICE INDICATORS #
####################


@functions.evaluator(
    alias="OPEN",
    description="The opening price of the latest stock rate.",
    group="Price Indicators",
)
def OPEN(stock: Stock, spec: functions.FunctionSpec):
    try:
        latest_rate: Rate = stock.rates.latest("added_at")
    except Rate.DoesNotExist:
        return functions.Error()
    return latest_rate.open


@functions.evaluator(
    alias="HIGH",
    description="The highest price of the latest stock rate.",
    group="Price Indicators",
)
def HIGH(stock: Stock, spec: functions.FunctionSpec):
    try:
        latest_rate: Rate = stock.rates.latest("added_at")
    except Rate.DoesNotExist:
        return functions.Error()
    return latest_rate.high


@functions.evaluator(
    alias="LOW",
    description="The lowest price of the latest stock rate.",
    group="Price Indicators",
)
def LOW(stock: Stock, spec: functions.FunctionSpec):
    try:
        latest_rate: Rate = stock.rates.latest("added_at")
    except Rate.DoesNotExist:
        return functions.Error()
    return latest_rate.low


@functions.evaluator(
    alias="CLOSE",
    description="The closing price of the latest stock rate.",
    group="Price Indicators",
)
def CLOSE(stock: Stock, spec: functions.FunctionSpec):
    try:
        latest_rate: Rate = stock.rates.latest("added_at")
    except Rate.DoesNotExist:
        return functions.Error()
    return latest_rate.close


@functions.evaluator(
    alias="VOLUME",
    description="The traded volume of the latest stock rate.",
    group="Price Indicators",
)
def VOLUME(stock: Stock, spec: functions.FunctionSpec):
    try:
        latest_rate: Rate = stock.rates.latest("added_at")
    except Rate.DoesNotExist:
        return functions.Error()
    return latest_rate.volume


# TA-LIB function evaluators built by this builder return only the first result in a result set
build_evaluator = functools.partial(
    functions.build_evaluator, result_handler=_return_first_value
)
# `functions.new_evaluator` with custom evaluator builder predefined
new_evaluator = functools.partial(
    functions.new_evaluator, evaluator_builder=build_evaluator
)

#########################
# VOLATILITY INDICATORS #
#########################

ATR = new_evaluator(
    "ATR",
    arg_evaluators=[arg_ev.High, arg_ev.Low, arg_ev.Close],
    kwargs_schema=ks.TimePeriod,
    alias="ATR",
    description="Average True Range. Measures market volatility by decomposing the entire range of an asset price for that period.",
    group="Volatility Indicators",
)

NATR = new_evaluator(
    "NATR",
    arg_evaluators=[arg_ev.High, arg_ev.Low, arg_ev.Close],
    kwargs_schema=ks.TimePeriod,
    alias="NATR",
    description="Normalized Average True Range. The ATR value normalized to represent a percentage of the closing price.",
    group="Volatility Indicators",
)

TRANGE = new_evaluator(
    "TRANGE",
    arg_evaluators=[arg_ev.High, arg_ev.Low, arg_ev.Close],
    kwargs_schema=None,  # Takes no keyword arguments
    alias="TRANGE",
    description="True Range. The greatest of the following: current high minus the current low, the absolute value of the current high minus the previous close, and the absolute value of the current low minus the previous close.",
    group="Volatility Indicators",
)


###################################
# CANDLESTICK PATTERN RECOGNITION #
###################################

CDL2CROWS = new_evaluator(
    "CDL2CROWS",
    arg_evaluators=[arg_ev.Open, arg_ev.High, arg_ev.Low, arg_ev.Close],
    kwargs_schema=None,  # Takes no keyword arguments
    alias="CDL2CROWS",
    group="Pattern Recognition",
    description="Two Crows: A bearish reversal pattern consisting of two black candlesticks after a long white one.",
)

CDL3BLACKCROWS = new_evaluator(
    "CDL3BLACKCROWS",
    arg_evaluators=[arg_ev.Open, arg_ev.High, arg_ev.Low, arg_ev.Close],
    kwargs_schema=None,
    alias="CDL3BLACKCROWS",
    group="Pattern Recognition",
    description="Three Black Crows: A bearish reversal pattern consisting of three consecutive black candlesticks.",
)

CDL3INSIDE = new_evaluator(
    "CDL3INSIDE",
    arg_evaluators=[arg_ev.Open, arg_ev.High, arg_ev.Low, arg_ev.Close],
    kwargs_schema=None,
    alias="CDL3INSIDE",
    group="Pattern Recognition",
    description="Three Inside Up/Down: A three-candlestick pattern signaling a potential reversal.",
)

CDL3LINESTRIKE = new_evaluator(
    "CDL3LINESTRIKE",
    arg_evaluators=[arg_ev.Open, arg_ev.High, arg_ev.Low, arg_ev.Close],
    kwargs_schema=None,
    alias="CDL3LINESTRIKE",
    group="Pattern Recognition",
    description="Three-Line Strike: A four-candlestick reversal pattern consisting of three candles in the direction of the trend followed by a counter candle.",
)

CDL3OUTSIDE = new_evaluator(
    "CDL3OUTSIDE",
    arg_evaluators=[arg_ev.Open, arg_ev.High, arg_ev.Low, arg_ev.Close],
    kwargs_schema=None,
    alias="CDL3OUTSIDE",
    group="Pattern Recognition",
    description="Three Outside Up/Down: A bullish or bearish reversal pattern with three candlesticks.",
)

CDL3STARSINSOUTH = new_evaluator(
    "CDL3STARSINSOUTH",
    arg_evaluators=[arg_ev.Open, arg_ev.High, arg_ev.Low, arg_ev.Close],
    kwargs_schema=None,
    alias="CDL3STARSINSOUTH",
    group="Pattern Recognition",
    description="Three Stars in the South: A rare bullish reversal pattern consisting of three candlesticks.",
)

CDL3WHITESOLDIERS = new_evaluator(
    "CDL3WHITESOLDIERS",
    arg_evaluators=[arg_ev.Open, arg_ev.High, arg_ev.Low, arg_ev.Close],
    kwargs_schema=None,
    alias="CDL3WHITESOLDIERS",
    group="Pattern Recognition",
    description="Three White Soldiers: A bullish reversal pattern with three consecutive long white candles.",
)

CDLABANDONEDBABY = new_evaluator(
    "CDLABANDONEDBABY",
    arg_evaluators=[arg_ev.Open, arg_ev.High, arg_ev.Low, arg_ev.Close],
    kwargs_schema=ks.Penetration,
    alias="CDLABANDONEDBABY",
    group="Pattern Recognition",
    description="Abandoned Baby: A reversal pattern characterized by a gap between the three candles.",
)

CDLADVANCEBLOCK = new_evaluator(
    "CDLADVANCEBLOCK",
    arg_evaluators=[arg_ev.Open, arg_ev.High, arg_ev.Low, arg_ev.Close],
    kwargs_schema=None,
    alias="CDLADVANCEBLOCK",
    group="Pattern Recognition",
    description="Advance Block: A bearish reversal pattern consisting of three candlesticks.",
)

CDLBELTHOLD = new_evaluator(
    "CDLBELTHOLD",
    arg_evaluators=[arg_ev.Open, arg_ev.High, arg_ev.Low, arg_ev.Close],
    kwargs_schema=None,
    alias="CDLBELTHOLD",
    group="Pattern Recognition",
    description="Belt-hold: A pattern with one long candlestick with no shadow in the direction of the trend.",
)

CDLBREAKAWAY = new_evaluator(
    "CDLBREAKAWAY",
    arg_evaluators=[arg_ev.Open, arg_ev.High, arg_ev.Low, arg_ev.Close],
    kwargs_schema=None,
    alias="CDLBREAKAWAY",
    group="Pattern Recognition",
    description="Breakaway: A pattern consisting of five candlesticks that indicates a potential trend reversal.",
)

CDLCLOSINGMARUBOZU = new_evaluator(
    "CDLCLOSINGMARUBOZU",
    arg_evaluators=[arg_ev.Open, arg_ev.High, arg_ev.Low, arg_ev.Close],
    kwargs_schema=None,
    alias="CDLCLOSINGMARUBOZU",
    group="Pattern Recognition",
    description="Closing Marubozu: A candlestick with no shadows and the close is at the high or low.",
)

CDLCONCEALBABYSWALL = new_evaluator(
    "CDLCONCEALBABYSWALL",
    arg_evaluators=[arg_ev.Open, arg_ev.High, arg_ev.Low, arg_ev.Close],
    kwargs_schema=None,
    alias="CDLCONCEALBABYSWALL",
    group="Pattern Recognition",
    description="Concealing Baby Swallow: A bullish reversal pattern formed by four black candlesticks.",
)

CDLCOUNTERATTACK = new_evaluator(
    "CDLCOUNTERATTACK",
    arg_evaluators=[arg_ev.Open, arg_ev.High, arg_ev.Low, arg_ev.Close],
    kwargs_schema=None,
    alias="CDLCOUNTERATTACK",
    group="Pattern Recognition",
    description="Counterattack: A two-candlestick pattern indicating a possible trend reversal.",
)

CDLDARKCLOUDCOVER = new_evaluator(
    "CDLDARKCLOUDCOVER",
    arg_evaluators=[arg_ev.Open, arg_ev.High, arg_ev.Low, arg_ev.Close],
    kwargs_schema=ks.Penetration,
    alias="CDLDARKCLOUDCOVER",
    group="Pattern Recognition",
    description="Dark Cloud Cover: A bearish reversal pattern with a black candlestick closing below the midpoint of the previous white candlestick.",
)

CDLDOJI = new_evaluator(
    "CDLDOJI",
    arg_evaluators=[arg_ev.Open, arg_ev.High, arg_ev.Low, arg_ev.Close],
    kwargs_schema=None,
    alias="CDLDOJI",
    group="Pattern Recognition",
    description="Doji: A candlestick where the open and close are almost the same, signaling indecision.",
)

CDLDOJISTAR = new_evaluator(
    "CDLDOJISTAR",
    arg_evaluators=[arg_ev.Open, arg_ev.High, arg_ev.Low, arg_ev.Close],
    kwargs_schema=None,
    alias="CDLDOJISTAR",
    group="Pattern Recognition",
    description="Doji Star: A pattern where a Doji follows a long candlestick, indicating a potential reversal.",
)

CDLDRAGONFLYDOJI = new_evaluator(
    "CDLDRAGONFLYDOJI",
    arg_evaluators=[arg_ev.Open, arg_ev.High, arg_ev.Low, arg_ev.Close],
    kwargs_schema=None,
    alias="CDLDRAGONFLYDOJI",
    group="Pattern Recognition",
    description="Dragonfly Doji: A Doji with a long lower shadow and no upper shadow, often indicating a bullish reversal.",
)

CDLENGULFING = new_evaluator(
    "CDLENGULFING",
    arg_evaluators=[arg_ev.Open, arg_ev.High, arg_ev.Low, arg_ev.Close],
    kwargs_schema=None,
    alias="CDLENGULFING",
    group="Pattern Recognition",
    description="Engulfing Pattern: A reversal pattern where a larger candlestick engulfs the previous one.",
)

CDLEVENINGDOJISTAR = new_evaluator(
    "CDLEVENINGDOJISTAR",
    arg_evaluators=[arg_ev.Open, arg_ev.High, arg_ev.Low, arg_ev.Close],
    kwargs_schema=ks.Penetration,
    alias="CDLEVENINGDOJISTAR",
    group="Pattern Recognition",
    description="Evening Doji Star: A bearish reversal pattern with a Doji in the middle of a three-candlestick formation.",
)

CDLEVENINGSTAR = new_evaluator(
    "CDLEVENINGSTAR",
    arg_evaluators=[arg_ev.Open, arg_ev.High, arg_ev.Low, arg_ev.Close],
    kwargs_schema=ks.Penetration,
    alias="CDLEVENINGSTAR",
    group="Pattern Recognition",
    description="Evening Star: A bearish reversal pattern with three candlesticks, indicating the end of an uptrend.",
)

CDLGAPSIDESIDEWHITE = new_evaluator(
    "CDLGAPSIDESIDEWHITE",
    arg_evaluators=[arg_ev.Open, arg_ev.High, arg_ev.Low, arg_ev.Close],
    kwargs_schema=None,
    alias="CDLGAPSIDESIDEWHITE",
    group="Pattern Recognition",
    description="Up/Down-gap side-by-side white lines: A continuation pattern with two white candlesticks forming after a gap.",
)

CDLGRAVESTONEDOJI = new_evaluator(
    "CDLGRAVESTONEDOJI",
    arg_evaluators=[arg_ev.Open, arg_ev.High, arg_ev.Low, arg_ev.Close],
    kwargs_schema=None,
    alias="CDLGRAVESTONEDOJI",
    group="Pattern Recognition",
    description="Gravestone Doji: A Doji with a long upper shadow and no lower shadow, often indicating a bearish reversal.",
)

CDLHAMMER = new_evaluator(
    "CDLHAMMER",
    arg_evaluators=[arg_ev.Open, arg_ev.High, arg_ev.Low, arg_ev.Close],
    kwargs_schema=None,
    alias="CDLHAMMER",
    group="Pattern Recognition",
    description="Hammer: A bullish reversal pattern with a small body and a long lower shadow, indicating potential buying pressure.",
)

CDLHANGINGMAN = new_evaluator(
    "CDLHANGINGMAN",
    arg_evaluators=[arg_ev.Open, arg_ev.High, arg_ev.Low, arg_ev.Close],
    kwargs_schema=None,
    alias="CDLHANGINGMAN",
    group="Pattern Recognition",
    description="Hanging Man: A bearish reversal pattern with a small body and a long lower shadow, indicating potential selling pressure.",
)

CDLHARAMI = new_evaluator(
    "CDLHARAMI",
    arg_evaluators=[arg_ev.Open, arg_ev.High, arg_ev.Low, arg_ev.Close],
    kwargs_schema=None,
    alias="CDLHARAMI",
    group="Pattern Recognition",
    description="Harami: A two-candlestick pattern indicating a potential reversal, where the second candle is contained within the body of the first.",
)

CDLHARAMICROSS = new_evaluator(
    "CDLHARAMICROSS",
    arg_evaluators=[arg_ev.Open, arg_ev.High, arg_ev.Low, arg_ev.Close],
    kwargs_schema=None,
    alias="CDLHARAMICROSS",
    group="Pattern Recognition",
    description="Harami Cross: A variation of the Harami pattern where the second candlestick is a Doji.",
)

CDLHIGHWAVE = new_evaluator(
    "CDLHIGHWAVE",
    arg_evaluators=[arg_ev.Open, arg_ev.High, arg_ev.Low, arg_ev.Close],
    kwargs_schema=None,
    alias="CDLHIGHWAVE",
    group="Pattern Recognition",
    description="High-Wave: A candlestick with long upper and lower shadows, indicating market indecision.",
)

CDLHIKKAKE = new_evaluator(
    "CDLHIKKAKE",
    arg_evaluators=[arg_ev.Open, arg_ev.High, arg_ev.Low, arg_ev.Close],
    kwargs_schema=None,
    alias="CDLHIKKAKE",
    group="Pattern Recognition",
    description="Hikkake Pattern: A continuation or reversal pattern that follows a failed pattern breakout.",
)

CDLHIKKAKEMOD = new_evaluator(
    "CDLHIKKAKEMOD",
    arg_evaluators=[arg_ev.Open, arg_ev.High, arg_ev.Low, arg_ev.Close],
    kwargs_schema=None,
    alias="CDLHIKKAKEMOD",
    group="Pattern Recognition",
    description="Modified Hikkake Pattern: A variation of the Hikkake pattern with a different configuration of candlesticks.",
)

CDLHOMINGPIGEON = new_evaluator(
    "CDLHOMINGPIGEON",
    arg_evaluators=[arg_ev.Open, arg_ev.High, arg_ev.Low, arg_ev.Close],
    kwargs_schema=None,
    alias="CDLHOMINGPIGEON",
    group="Pattern Recognition",
    description="Homing Pigeon: A bullish reversal pattern where the second candlestick is contained within the body of the first.",
)

CDLIDENTICAL3CROWS = new_evaluator(
    "CDLIDENTICAL3CROWS",
    arg_evaluators=[arg_ev.Open, arg_ev.High, arg_ev.Low, arg_ev.Close],
    kwargs_schema=None,
    alias="CDLIDENTICAL3CROWS",
    group="Pattern Recognition",
    description="Identical Three Crows: A bearish reversal pattern consisting of three black candlesticks with identical open and close prices.",
)

CDLINNECK = new_evaluator(
    "CDLINNECK",
    arg_evaluators=[arg_ev.Open, arg_ev.High, arg_ev.Low, arg_ev.Close],
    kwargs_schema=None,
    alias="CDLINNECK",
    group="Pattern Recognition",
    description="In-Neck: A bearish continuation pattern with a black candlestick followed by a small white candlestick.",
)

CDLINVERTEDHAMMER = new_evaluator(
    "CDLINVERTEDHAMMER",
    arg_evaluators=[arg_ev.Open, arg_ev.High, arg_ev.Low, arg_ev.Close],
    kwargs_schema=None,
    alias="CDLINVERTEDHAMMER",
    group="Pattern Recognition",
    description="Inverted Hammer: A bullish reversal pattern with a long upper shadow and a small body, indicating potential buying pressure.",
)

CDLKICKING = new_evaluator(
    "CDLKICKING",
    arg_evaluators=[arg_ev.Open, arg_ev.High, arg_ev.Low, arg_ev.Close],
    kwargs_schema=None,
    alias="CDLKICKING",
    group="Pattern Recognition",
    description="Kicking: A two-candlestick pattern with a gap between a white and black candlestick, signaling a strong reversal.",
)

CDLKICKINGBYLENGTH = new_evaluator(
    "CDLKICKINGBYLENGTH",
    arg_evaluators=[arg_ev.Open, arg_ev.High, arg_ev.Low, arg_ev.Close],
    kwargs_schema=None,
    alias="CDLKICKINGBYLENGTH",
    group="Pattern Recognition",
    description="Kicking by Length: A variation of the Kicking pattern that considers the length of the candlesticks.",
)

CDLLADDERBOTTOM = new_evaluator(
    "CDLLADDERBOTTOM",
    arg_evaluators=[arg_ev.Open, arg_ev.High, arg_ev.Low, arg_ev.Close],
    kwargs_schema=None,
    alias="CDLLADDERBOTTOM",
    group="Pattern Recognition",
    description="Ladder Bottom: A five-candlestick bullish reversal pattern with consecutive lower closes followed by a gap up.",
)

CDLLONGLEGGEDDOJI = new_evaluator(
    "CDLLONGLEGGEDDOJI",
    arg_evaluators=[arg_ev.Open, arg_ev.High, arg_ev.Low, arg_ev.Close],
    kwargs_schema=None,
    alias="CDLLONGLEGGEDDOJI",
    group="Pattern Recognition",
    description="Long-Legged Doji: A Doji with long upper and lower shadows, indicating high market volatility and indecision.",
)

CDLLONGLINE = new_evaluator(
    "CDLLONGLINE",
    arg_evaluators=[arg_ev.Open, arg_ev.High, arg_ev.Low, arg_ev.Close],
    kwargs_schema=None,
    alias="CDLLONGLINE",
    group="Pattern Recognition",
    description="Long Line Candle: A long candlestick with a significant body, indicating strong market momentum.",
)

CDLMARUBOZU = new_evaluator(
    "CDLMARUBOZU",
    arg_evaluators=[arg_ev.Open, arg_ev.High, arg_ev.Low, arg_ev.Close],
    kwargs_schema=None,
    alias="CDLMARUBOZU",
    group="Pattern Recognition",
    description="Marubozu: A candlestick with no shadows, indicating a strong trend in the direction of the body.",
)

CDLMATCHINGLOW = new_evaluator(
    "CDLMATCHINGLOW",
    arg_evaluators=[arg_ev.Open, arg_ev.High, arg_ev.Low, arg_ev.Close],
    kwargs_schema=None,
    alias="CDLMATCHINGLOW",
    group="Pattern Recognition",
    description="Matching Low: A bullish reversal pattern with two consecutive candlesticks having the same low.",
)

CDLMATHOLD = new_evaluator(
    "CDLMATHOLD",
    arg_evaluators=[arg_ev.Open, arg_ev.High, arg_ev.Low, arg_ev.Close],
    kwargs_schema=ks.Penetration,
    alias="CDLMATHOLD",
    group="Pattern Recognition",
    description="Mat Hold: A continuation pattern with a gap up, three small candlesticks, and a gap down, indicating strong trend momentum.",
)

CDLMORNINGDOJISTAR = new_evaluator(
    "CDLMORNINGDOJISTAR",
    arg_evaluators=[arg_ev.Open, arg_ev.High, arg_ev.Low, arg_ev.Close],
    kwargs_schema=ks.Penetration,
    alias="CDLMORNINGDOJISTAR",
    group="Pattern Recognition",
    description="Morning Doji Star: A bullish reversal pattern with a Doji in the middle of a three-candlestick formation.",
)

CDLMORNINGSTAR = new_evaluator(
    "CDLMORNINGSTAR",
    arg_evaluators=[arg_ev.Open, arg_ev.High, arg_ev.Low, arg_ev.Close],
    kwargs_schema=ks.Penetration,
    alias="CDLMORNINGSTAR",
    group="Pattern Recognition",
    description="Morning Star: A bullish reversal pattern with three candlesticks, indicating the end of a downtrend.",
)

CDLONNECK = new_evaluator(
    "CDLONNECK",
    arg_evaluators=[arg_ev.Open, arg_ev.High, arg_ev.Low, arg_ev.Close],
    kwargs_schema=None,
    alias="CDLONNECK",
    group="Pattern Recognition",
    description="On-Neck: A bearish continuation pattern with a black candlestick followed by a small white candlestick.",
)

CDLPIERCING = new_evaluator(
    "CDLPIERCING",
    arg_evaluators=[arg_ev.Open, arg_ev.High, arg_ev.Low, arg_ev.Close],
    kwargs_schema=None,
    alias="CDLPIERCING",
    group="Pattern Recognition",
    description="Piercing Pattern: A bullish reversal pattern with a white candlestick that opens below the previous black candlestick and closes above its midpoint.",
)

CDLRICKSHAWMAN = new_evaluator(
    "CDLRICKSHAWMAN",
    arg_evaluators=[arg_ev.Open, arg_ev.High, arg_ev.Low, arg_ev.Close],
    kwargs_schema=None,
    alias="CDLRICKSHAWMAN",
    group="Pattern Recognition",
    description="Rickshaw Man: A Doji with long upper and lower shadows, indicating market indecision and high volatility.",
)

CDLRISEFALL3METHODS = new_evaluator(
    "CDLRISEFALL3METHODS",
    arg_evaluators=[arg_ev.Open, arg_ev.High, arg_ev.Low, arg_ev.Close],
    kwargs_schema=None,
    alias="CDLRISEFALL3METHODS",
    group="Pattern Recognition",
    description="Rising/Falling Three Methods: A continuation pattern with a series of small candlesticks within a trend, indicating a pause before the trend resumes.",
)

CDLSEPARATINGLINES = new_evaluator(
    "CDLSEPARATINGLINES",
    arg_evaluators=[arg_ev.Open, arg_ev.High, arg_ev.Low, arg_ev.Close],
    kwargs_schema=None,
    alias="CDLSEPARATINGLINES",
    group="Pattern Recognition",
    description="Separating Lines: A continuation pattern with two opposite-colored candlesticks that share the same opening price.",
)

CDLSHOOTINGSTAR = new_evaluator(
    "CDLSHOOTINGSTAR",
    arg_evaluators=[arg_ev.Open, arg_ev.High, arg_ev.Low, arg_ev.Close],
    kwargs_schema=None,
    alias="CDLSHOOTINGSTAR",
    group="Pattern Recognition",
    description="Shooting Star: A bearish reversal pattern with a long upper shadow and a small body, indicating potential selling pressure.",
)

CDLSHORTLINE = new_evaluator(
    "CDLSHORTLINE",
    arg_evaluators=[arg_ev.Open, arg_ev.High, arg_ev.Low, arg_ev.Close],
    kwargs_schema=None,
    alias="CDLSHORTLINE",
    group="Pattern Recognition",
    description="Short Line Candle: A short candlestick with a small body, indicating a lack of strong market momentum.",
)

CDLSPINNINGTOP = new_evaluator(
    "CDLSPINNINGTOP",
    arg_evaluators=[arg_ev.Open, arg_ev.High, arg_ev.Low, arg_ev.Close],
    kwargs_schema=None,
    alias="CDLSPINNINGTOP",
    group="Pattern Recognition",
    description="Spinning Top: A candlestick with a small body and long upper and lower shadows, indicating market indecision.",
)

CDLSTALLEDPATTERN = new_evaluator(
    "CDLSTALLEDPATTERN",
    arg_evaluators=[arg_ev.Open, arg_ev.High, arg_ev.Low, arg_ev.Close],
    kwargs_schema=None,
    alias="CDLSTALLEDPATTERN",
    group="Pattern Recognition",
    description="Stalled Pattern: A bearish reversal pattern with three candlesticks, indicating the potential end of an uptrend.",
)

CDLSTICKSANDWICH = new_evaluator(
    "CDLSTICKSANDWICH",
    arg_evaluators=[arg_ev.Open, arg_ev.High, arg_ev.Low, arg_ev.Close],
    kwargs_schema=None,
    alias="CDLSTICKSANDWICH",
    group="Pattern Recognition",
    description="Stick Sandwich: A bullish reversal pattern with three candlesticks, where the middle candlestick is opposite in color to the surrounding candlesticks.",
)

CDLTAKURI = new_evaluator(
    "CDLTAKURI",
    arg_evaluators=[arg_ev.Open, arg_ev.High, arg_ev.Low, arg_ev.Close],
    kwargs_schema=None,
    alias="CDLTAKURI",
    group="Pattern Recognition",
    description="Takuri (Dragonfly Doji): A bullish reversal pattern with a long lower shadow and a small body, indicating potential buying pressure.",
)

CDLTASUKIGAP = new_evaluator(
    "CDLTASUKIGAP",
    arg_evaluators=[arg_ev.Open, arg_ev.High, arg_ev.Low, arg_ev.Close],
    kwargs_schema=None,
    alias="CDLTASUKIGAP",
    group="Pattern Recognition",
    description="Tasuki Gap: A continuation pattern with a gap followed by candlesticks that move in the same direction, indicating strong trend momentum.",
)

CDLTHRUSTING = new_evaluator(
    "CDLTHRUSTING",
    arg_evaluators=[arg_ev.Open, arg_ev.High, arg_ev.Low, arg_ev.Close],
    kwargs_schema=None,
    alias="CDLTHRUSTING",
    group="Pattern Recognition",
    description="Thrusting Pattern: A bearish continuation pattern with a black candlestick followed by a small white candlestick that closes below the midpoint of the previous black candlestick.",
)

CDLTRISTAR = new_evaluator(
    "CDLTRISTAR",
    arg_evaluators=[arg_ev.Open, arg_ev.High, arg_ev.Low, arg_ev.Close],
    kwargs_schema=None,
    alias="CDLTRISTAR",
    group="Pattern Recognition",
    description="Tristar: A reversal pattern with three consecutive Dojis, indicating a potential trend change.",
)

CDLUNIQUE3RIVER = new_evaluator(
    "CDLUNIQUE3RIVER",
    arg_evaluators=[arg_ev.Open, arg_ev.High, arg_ev.Low, arg_ev.Close],
    kwargs_schema=None,
    alias="CDLUNIQUE3RIVER",
    group="Pattern Recognition",
    description="Unique Three River Bottom: A bullish reversal pattern with three candlesticks, where the third candlestick is a small white candlestick within the body of the second.",
)

CDLUPSIDEGAP2CROWS = new_evaluator(
    "CDLUPSIDEGAP2CROWS",
    arg_evaluators=[arg_ev.Open, arg_ev.High, arg_ev.Low, arg_ev.Close],
    kwargs_schema=None,
    alias="CDLUPSIDEGAP2CROWS",
    group="Pattern Recognition",
    description="Upside Gap Two Crows: A bearish reversal pattern with a gap up followed by two black candlesticks that close the gap.",
)

CDLXSIDEGAP3METHODS = new_evaluator(
    "CDLXSIDEGAP3METHODS",
    arg_evaluators=[arg_ev.Open, arg_ev.High, arg_ev.Low, arg_ev.Close],
    kwargs_schema=None,
    alias="CDLXSIDEGAP3METHODS",
    group="Pattern Recognition",
    description="Upside/Downside Gap Three Methods: A continuation pattern with a gap followed by three small candlesticks within the gap, indicating trend continuation.",
)


#######################
# MOMENTUM INDICATORS #
#######################

ADX = new_evaluator(
    "ADX",
    arg_evaluators=[arg_ev.High, arg_ev.Low, arg_ev.Close],
    kwargs_schema=ks.TimePeriod,
    alias="ADX",
    group="Momentum Indicators",
    description="Average Directional Index: Measures the strength of a trend without indicating its direction.",
)

ADXR = new_evaluator(
    "ADXR",
    arg_evaluators=[arg_ev.High, arg_ev.Low, arg_ev.Close],
    kwargs_schema=ks.TimePeriod,
    alias="ADXR",
    group="Momentum Indicators",
    description="Average Directional Movement Rating: A smoothed version of ADX, indicating the trend strength.",
)

APO = new_evaluator(
    "APO",
    arg_evaluators=[arg_ev.Real],
    kwargs_schema=MergeKwargsSchemas(ks.FastandSlowPeriod, ks.MAType),
    alias="APO",
    group="Momentum Indicators",
    description="Absolute Price Oscillator: Shows the difference between two moving averages of a security's price.",
)

AROON = new_evaluator(
    "AROON",
    arg_evaluators=[arg_ev.High, arg_ev.Low],
    kwargs_schema=ks.TimePeriod,
    alias="AROON",
    group="Momentum Indicators",
    description="Aroon: Identifies the strength of a trend and the likelihood of its continuation.",
)

AROONOSC = new_evaluator(
    "AROONOSC",
    arg_evaluators=[arg_ev.High, arg_ev.Low],
    kwargs_schema=ks.TimePeriod,
    alias="AROONOSC",
    group="Momentum Indicators",
    description="Aroon Oscillator: Calculates the difference between Aroon Up and Aroon Down.",
)

BOP = new_evaluator(
    "BOP",
    arg_evaluators=[arg_ev.Open, arg_ev.High, arg_ev.Low, arg_ev.Close],
    kwargs_schema=None,
    alias="BOP",
    group="Momentum Indicators",
    description="Balance of Power: Measures the strength of buyers versus sellers.",
)

CCI = new_evaluator(
    "CCI",
    arg_evaluators=[arg_ev.High, arg_ev.Low, arg_ev.Close],
    kwargs_schema=ks.TimePeriod,
    alias="CCI",
    group="Momentum Indicators",
    description="Commodity Channel Index: Identifies cyclical trends in a security's price.",
)

CMO = new_evaluator(
    "CMO",
    arg_evaluators=[arg_ev.Real],
    kwargs_schema=ks.TimePeriod,
    alias="CMO",
    group="Momentum Indicators",
    description="Chande Momentum Oscillator: Measures the momentum of a security's price, developed by Tushar Chande.",
)

DX = new_evaluator(
    "DX",
    arg_evaluators=[arg_ev.High, arg_ev.Low, arg_ev.Close],
    kwargs_schema=ks.TimePeriod,
    alias="DX",
    group="Momentum Indicators",
    description="Directional Movement Index: Indicates the strength of a trend by comparing positive and negative movement.",
)

MACD = new_evaluator(
    "MACD",
    arg_evaluators=[arg_ev.Real],
    kwargs_schema=MergeKwargsSchemas(ks.FastandSlowPeriod, ks.SignalPeriod),
    alias="MACD",
    group="Momentum Indicators",
    description="Moving Average Convergence Divergence: A trend-following momentum indicator that shows the relationship between two moving averages.",
)

MACDEXT = new_evaluator(
    "MACDEXT",
    arg_evaluators=[arg_ev.Real],
    kwargs_schema=MergeKwargsSchemas(
        ks.FastandSlowPeriod, ks.FastandSlowMAType, ks.SignalPeriod, ks.SignalMAType
    ),
    alias="MACDEXT",
    group="Momentum Indicators",
    description="MACD with controllable moving average types: A more flexible version of MACD that allows for different types of moving averages.",
)

MACDFIX = new_evaluator(
    "MACDFIX",
    arg_evaluators=[arg_ev.Real],
    kwargs_schema=ks.SignalPeriod,
    alias="MACDFIX",
    group="Momentum Indicators",
    description="MACD Fix: A variant of the MACD with a fixed 9-day signal line.",
)

MFI = new_evaluator(
    "MFI",
    arg_evaluators=[arg_ev.High, arg_ev.Low, arg_ev.Close, arg_ev.Volume],
    kwargs_schema=ks.TimePeriod,
    alias="MFI",
    group="Momentum Indicators",
    description="Money Flow Index: Measures the buying and selling pressure using both price and volume.",
)

MINUS_DI = new_evaluator(
    "MINUS_DI",
    arg_evaluators=[arg_ev.High, arg_ev.Low, arg_ev.Close],
    kwargs_schema=ks.TimePeriod,
    alias="MINUS_DI",
    group="Momentum Indicators",
    description="Minus Directional Indicator: Measures the negative directional movement, used in ADX calculations.",
)

MINUS_DM = new_evaluator(
    "MINUS_DM",
    arg_evaluators=[arg_ev.High, arg_ev.Low],
    kwargs_schema=ks.TimePeriod,
    alias="MINUS_DM",
    group="Momentum Indicators",
    description="Minus Directional Movement: Represents the difference between the low of the current period and the low of the previous period.",
)

MOM = new_evaluator(
    "MOM",
    arg_evaluators=[arg_ev.Real],
    kwargs_schema=ks.TimePeriod,
    alias="MOM",
    group="Momentum Indicators",
    description="Momentum: Measures the speed and change of price movements.",
)

PLUS_DI = new_evaluator(
    "PLUS_DI",
    arg_evaluators=[arg_ev.High, arg_ev.Low, arg_ev.Close],
    kwargs_schema=ks.TimePeriod,
    alias="PLUS_DI",
    group="Momentum Indicators",
    description="Plus Directional Indicator: Measures the positive directional movement, used in ADX calculations.",
)

PLUS_DM = new_evaluator(
    "PLUS_DM",
    arg_evaluators=[arg_ev.High, arg_ev.Low],
    kwargs_schema=ks.TimePeriod,
    alias="PLUS_DM",
    group="Momentum Indicators",
    description="Plus Directional Movement: Represents the difference between the high of the current period and the high of the previous period.",
)

PPO = new_evaluator(
    "PPO",
    arg_evaluators=[arg_ev.Real],
    kwargs_schema=MergeKwargsSchemas(ks.FastandSlowPeriod, ks.MAType),
    alias="PPO",
    group="Momentum Indicators",
    description="Percentage Price Oscillator: Similar to MACD but expressed as a percentage.",
)

ROC = new_evaluator(
    "ROC",
    arg_evaluators=[arg_ev.Real],
    kwargs_schema=ks.TimePeriod,
    alias="ROC",
    group="Momentum Indicators",
    description="Rate of Change: Measures the percentage change in price between the current price and the price a certain number of periods ago.",
)

ROCP = new_evaluator(
    "ROCP",
    arg_evaluators=[arg_ev.Real],
    kwargs_schema=ks.TimePeriod,
    alias="ROCP",
    group="Momentum Indicators",
    description="Rate of Change Percentage: Expresses the rate of change as a percentage.",
)

ROCR = new_evaluator(
    "ROCR",
    arg_evaluators=[arg_ev.Real],
    kwargs_schema=ks.TimePeriod,
    alias="ROCR",
    group="Momentum Indicators",
    description="Rate of Change Ratio: Similar to ROC but expressed as a ratio.",
)

ROCR100 = new_evaluator(
    "ROCR100",
    arg_evaluators=[arg_ev.Real],
    kwargs_schema=ks.TimePeriod,
    alias="ROCR100",
    group="Momentum Indicators",
    description="Rate of Change Ratio 100: Similar to ROCR but scaled by 100.",
)

RSI = new_evaluator(
    "RSI",
    arg_evaluators=[arg_ev.Real],
    kwargs_schema=ks.TimePeriod,
    alias="RSI",
    group="Momentum Indicators",
    description="Relative Strength Index: A momentum oscillator that measures the speed and change of price movements.",
)

STOCH = new_evaluator(
    "STOCH",
    arg_evaluators=[arg_ev.High, arg_ev.Low, arg_ev.Close],
    kwargs_schema=MergeKwargsSchemas(
        ks.FastK_Period,
        ks.SlowK_Period,
        ks.SlowK_MAType,
        ks.SlowD_Period,
        ks.SlowD_MAType,
    ),
    alias="STOCH",
    group="Momentum Indicators",
    description="Stochastic Oscillator: Compares a particular closing price to a range of prices over a certain period.",
)

STOCHF = new_evaluator(
    "STOCHF",
    arg_evaluators=[arg_ev.High, arg_ev.Low, arg_ev.Close],
    kwargs_schema=MergeKwargsSchemas(ks.FastK_Period, ks.FastD_Period, ks.FastD_MAType),
    alias="STOCHF",
    group="Momentum Indicators",
    description="Stochastic Fast: A faster version of the Stochastic Oscillator.",
)

STOCHRSI = new_evaluator(
    "STOCHRSI",
    arg_evaluators=[arg_ev.Real],
    kwargs_schema=MergeKwargsSchemas(
        ks.TimePeriod, ks.FastK_Period, ks.FastD_Period, ks.FastD_MAType
    ),
    alias="STOCHRSI",
    group="Momentum Indicators",
    description="Stochastic RSI: An oscillator that measures the level of RSI relative to its range.",
)

TRIX = new_evaluator(
    "TRIX",
    arg_evaluators=[arg_ev.Real],
    kwargs_schema=ks.TimePeriod,
    alias="TRIX",
    group="Momentum Indicators",
    description="Triple Exponential Moving Average Oscillator: Measures the rate of change of a triple exponentially smoothed moving average.",
)

ULTOSC = new_evaluator(
    "ULTOSC",
    arg_evaluators=[arg_ev.High, arg_ev.Low, arg_ev.Close],
    kwargs_schema=KwargsSchema(
        "ULTOSC_TimePeriods",
        {
            "timeperiod1": attrs.field(type=int, default=7),
            "timeperiod2": attrs.field(type=int, default=14),
            "timeperiod3": attrs.field(type=int, default=28),
        },
    ),
    alias="ULTOSC",
    group="Momentum Indicators",
    description="Ultimate Oscillator: Combines short-term, intermediate-term, and long-term price action into one oscillator.",
)

WILLR = new_evaluator(
    "WILLR",
    arg_evaluators=[arg_ev.High, arg_ev.Low, arg_ev.Close],
    kwargs_schema=ks.TimePeriod,
    alias="WILLR",
    group="Momentum Indicators",
    description="Williams %R: A momentum indicator that measures overbought and oversold levels.",
)


#############################
# MATH OPERATOR FUNCTIONS #
#############################

ADD = new_evaluator(
    "ADD",
    arg_evaluators=[arg_ev.Real0, arg_ev.Real1],
    kwargs_schema=None,
    alias="ADD",
    description="Vector Arithmetic Addition",
    group="Math Operators",
)

DIV = new_evaluator(
    "DIV",
    arg_evaluators=[arg_ev.Real0, arg_ev.Real1],
    kwargs_schema=None,
    alias="DIV",
    description="Vector Arithmetic Division",
    group="Math Operators",
)

MAX = new_evaluator(
    "MAX",
    arg_evaluators=[arg_ev.Real],
    kwargs_schema=ks.TimePeriod,
    alias="MAX",
    description="Highest value over a specified period",
    group="Math Operators",
)

MAXINDEX = new_evaluator(
    "MAXINDEX",
    arg_evaluators=[arg_ev.Real],
    kwargs_schema=ks.TimePeriod,
    alias="MAXINDEX",
    description="Index of highest value over a specified period",
    group="Math Operators",
)

MIN = new_evaluator(
    "MIN",
    arg_evaluators=[arg_ev.Real],
    kwargs_schema=ks.TimePeriod,
    alias="MIN",
    description="Lowest value over a specified period",
    group="Math Operators",
)

MININDEX = new_evaluator(
    "MININDEX",
    arg_evaluators=[arg_ev.Real],
    kwargs_schema=ks.TimePeriod,
    alias="MININDEX",
    description="Index of lowest value over a specified period",
    group="Math Operators",
)

MINMAX = new_evaluator(
    "MINMAX",
    arg_evaluators=[arg_ev.Real],
    kwargs_schema=ks.TimePeriod,
    alias="MINMAX",
    description="Lowest and highest values over a specified period",
    group="Math Operators",
)

MINMAXINDEX = new_evaluator(
    "MINMAXINDEX",
    arg_evaluators=[arg_ev.Real],
    kwargs_schema=ks.TimePeriod,
    alias="MINMAXINDEX",
    description="Indexes of lowest and highest values over a specified period",
    group="Math Operators",
)

MULT = new_evaluator(
    "MULT",
    arg_evaluators=[arg_ev.Real0, arg_ev.Real1],
    kwargs_schema=None,
    alias="MULT",
    description="Vector Arithmetic Multiplication",
    group="Math Operators",
)

SUB = new_evaluator(
    "SUB",
    arg_evaluators=[arg_ev.Real0, arg_ev.Real1],
    kwargs_schema=None,
    alias="SUB",
    description="Vector Arithmetic Subtraction",
    group="Math Operators",
)

SUM = new_evaluator(
    "SUM",
    arg_evaluators=[arg_ev.Real],
    kwargs_schema=ks.TimePeriod,
    alias="SUM",
    description="Summation over a specified period",
    group="Math Operators",
)


##########################
# STATISTIC FUNCTIONS #
##########################

BETA = new_evaluator(
    "BETA",
    arg_evaluators=[arg_ev.Real0, arg_ev.Real1],
    kwargs_schema=ks.TimePeriod,
    alias="BETA",
    description="Beta (measures the volatility of an asset in comparison to the market as a whole)",
    group="Statistic Functions",
)

CORREL = new_evaluator(
    "CORREL",
    arg_evaluators=[arg_ev.Real0, arg_ev.Real1],
    kwargs_schema=ks.TimePeriod,
    alias="CORREL",
    description="Pearson's Correlation Coefficient (r) (measures the linear correlation between two datasets)",
    group="Statistic Functions",
)

LINEARREG = new_evaluator(
    "LINEARREG",
    arg_evaluators=[arg_ev.Real],
    kwargs_schema=ks.TimePeriod,
    alias="LINEARREG",
    description="Linear Regression (calculates a linear regression for a series of values)",
    group="Statistic Functions",
)

LINEARREG_ANGLE = new_evaluator(
    "LINEARREG_ANGLE",
    arg_evaluators=[arg_ev.Real],
    kwargs_schema=ks.TimePeriod,
    alias="LINEARREG_ANGLE",
    description="Linear Regression Angle (calculates the angle of the linear regression line)",
    group="Statistic Functions",
)

LINEARREG_INTERCEPT = new_evaluator(
    "LINEARREG_INTERCEPT",
    arg_evaluators=[arg_ev.Real],
    kwargs_schema=ks.TimePeriod,
    alias="LINEARREG_INTERCEPT",
    description="Linear Regression Intercept (calculates the y-intercept of the linear regression line)",
    group="Statistic Functions",
)

LINEARREG_SLOPE = new_evaluator(
    "LINEARREG_SLOPE",
    arg_evaluators=[arg_ev.Real],
    kwargs_schema=ks.TimePeriod,
    alias="LINEARREG_SLOPE",
    description="Linear Regression Slope (calculates the slope of the linear regression line)",
    group="Statistic Functions",
)

STDDEV = new_evaluator(
    "STDDEV",
    arg_evaluators=[arg_ev.Real],
    kwargs_schema=MergeKwargsSchemas(ks.TimePeriod, ks.NbDev),
    alias="STDDEV",
    description="Standard Deviation (measures the amount of variation or dispersion of a set of values)",
    group="Statistic Functions",
)

TSF = new_evaluator(
    "TSF",
    arg_evaluators=[arg_ev.Real],
    kwargs_schema=ks.TimePeriod,
    alias="TSF",
    description="Time Series Forecast (calculates a linear regression forecast for a series of values)",
    group="Statistic Functions",
)

VAR = new_evaluator(
    "VAR",
    arg_evaluators=[arg_ev.Real],
    kwargs_schema=MergeKwargsSchemas(ks.TimePeriod, ks.NbDev),
    alias="VAR",
    description="Variance (measures how far a set of numbers are spread out from their average value)",
    group="Statistic Functions",
)


#############################
# OVERLAP STUDIES FUNCTIONS #
#############################

BBANDS = new_evaluator(
    "BBANDS",
    arg_evaluators=[arg_ev.Real],
    kwargs_schema=MergeKwargsSchemas(ks.TimePeriod, ks.NbDevUpAndDown, ks.MAType),
    alias="BBANDS",
    description="Bollinger Bands (technical analysis tool defining upper and lower price range levels)",
    group="Overlap Studies",
)

DEMA = new_evaluator(
    "DEMA",
    arg_evaluators=[arg_ev.Real],
    kwargs_schema=ks.TimePeriod,
    alias="DEMA",
    description="Double Exponential Moving Average (reduces the lag of the standard EMA)",
    group="Overlap Studies",
)

EMA = new_evaluator(
    "EMA",
    arg_evaluators=[arg_ev.Real],
    kwargs_schema=ks.TimePeriod,
    alias="EMA",
    description="Exponential Moving Average (places greater weight on the most recent data)",
    group="Overlap Studies",
)

HT_TRENDLINE = new_evaluator(
    "HT_TRENDLINE",
    arg_evaluators=[arg_ev.Real],
    kwargs_schema=None,
    alias="HT_TRENDLINE",
    description="Hilbert Transform - Instantaneous Trendline (identifies current trend direction)",
    group="Overlap Studies",
)

KAMA = new_evaluator(
    "KAMA",
    arg_evaluators=[arg_ev.Real],
    kwargs_schema=ks.TimePeriod,
    alias="KAMA",
    description="Kaufman Adaptive Moving Average (adapts to market volatility)",
    group="Overlap Studies",
)

MA = new_evaluator(
    "MA",
    arg_evaluators=[arg_ev.Real],
    kwargs_schema=MergeKwargsSchemas(ks.TimePeriod, ks.MAType),
    alias="MA",
    description="Moving Average (smooths out price data to identify the trend direction)",
    group="Overlap Studies",
)

MAMA = new_evaluator(
    "MAMA",
    arg_evaluators=[arg_ev.Real],
    kwargs_schema=ks.FastandSlowLimit,
    alias="MAMA",
    description="MESA Adaptive Moving Average (adjusts based on market conditions)",
    group="Overlap Studies",
)

MAVP = new_evaluator(
    "MAVP",
    # arg_evaluators=[arg_ev.Real, arg_ev.Periods],
    # kwargs_schema=MergeKwargsSchemas(ks.MinandMaxPeriod, ks.MAType),
    arg_evaluators=[
        arg_ev.Real
    ],  # Make Periods a kwarg, so user can specify it since we have no way of evaluating it
    kwargs_schema=MergeKwargsSchemas(ks.Periods, ks.MinandMaxPeriod, ks.MAType),
    alias="MAVP",
    description="Moving Average with Variable Period (changes period dynamically based on input)",
    group="Overlap Studies",
)

MIDPOINT = new_evaluator(
    "MIDPOINT",
    arg_evaluators=[arg_ev.Real],
    kwargs_schema=ks.TimePeriod,
    alias="MIDPOINT",
    description="MidPoint over period (average of the maximum and minimum values)",
    group="Overlap Studies",
)

MIDPRICE = new_evaluator(
    "MIDPRICE",
    arg_evaluators=[arg_ev.High, arg_ev.Low],
    kwargs_schema=ks.TimePeriod,
    alias="MIDPRICE",
    description="Midpoint Price over period (average of the high and low prices)",
    group="Overlap Studies",
)

SAR = new_evaluator(
    "SAR",
    arg_evaluators=[arg_ev.High, arg_ev.Low],
    kwargs_schema=MergeKwargsSchemas(ks.Acceleration, ks.Maximum),
    alias="SAR",
    description="Parabolic SAR (tracks the price over time and identifies potential reversals)",
    group="Overlap Studies",
)

SAREXT = new_evaluator(
    "SAREXT",
    arg_evaluators=[arg_ev.High, arg_ev.Low],
    kwargs_schema=KwargsSchema(
        "SAREXT_Params",
        {
            "startvalue": attrs.field(type=float, default=0),
            "offsetonreverse": attrs.field(type=float, default=0),
            "accelerationinitlong": attrs.field(type=float, default=0),
            "accelerationlong": attrs.field(type=float, default=0),
            "accelerationmaxlong": attrs.field(type=float, default=0),
            "accelerationinitshort": attrs.field(type=float, default=0),
            "accelerationshort": attrs.field(type=float, default=0),
            "accelerationmaxshort": attrs.field(type=float, default=0),
        },
    ),
    alias="SAREXT",
    description="Parabolic SAR - Extended (extended version of Parabolic SAR with additional parameters)",
    group="Overlap Studies",
)

SMA = new_evaluator(
    "SMA",
    arg_evaluators=[arg_ev.Real],
    kwargs_schema=ks.TimePeriod,
    alias="SMA",
    description="Simple Moving Average (calculates the average of a selected range of prices)",
    group="Overlap Studies",
)

T3 = new_evaluator(
    "T3",
    arg_evaluators=[arg_ev.Real],
    kwargs_schema=MergeKwargsSchemas(ks.TimePeriod, ks.VFactor),
    alias="T3",
    description="Triple Exponential Moving Average (T3) (offers a smoother average with less lag)",
    group="Overlap Studies",
)

TEMA = new_evaluator(
    "TEMA",
    arg_evaluators=[arg_ev.Real],
    kwargs_schema=ks.TimePeriod,
    alias="TEMA",
    description="Triple Exponential Moving Average (reduces lag more effectively than DEMA)",
    group="Overlap Studies",
)

TRIMA = new_evaluator(
    "TRIMA",
    arg_evaluators=[arg_ev.Real],
    kwargs_schema=ks.TimePeriod,
    alias="TRIMA",
    description="Triangular Moving Average (gives more weight to the middle portion of the period)",
    group="Overlap Studies",
)

WMA = new_evaluator(
    "WMA",
    arg_evaluators=[arg_ev.Real],
    kwargs_schema=ks.TimePeriod,
    alias="WMA",
    description="Weighted Moving Average (gives more weight to recent data)",
    group="Overlap Studies",
)
