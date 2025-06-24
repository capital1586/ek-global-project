import decimal
import typing
import datetime
import uuid
from django.utils import timezone
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils.translation import gettext_lazy as _

from helpers.caching import ttl_cache



class StockIndices(models.IntegerChoices):
    """Available PSX stock indices."""

    KSE100 = 1, _("KSE100")
    KSE_ALLSHR = 2, _("KSE_ALLSHR")
    KSE30 = 3, _("KSE30")
    KMI30 = 4, _("KMI30")
    KMI_ALLSHR = 5, _("KMI_ALLSHR")
    BKTI = 6, _("BKTI")
    OGTI = 7, _("OGTI")


class Stock(models.Model):
    """Model definition for Stock."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ticker = models.CharField(max_length=120, unique=True)
    title = models.CharField(max_length=100, blank=True, null=True)
    indices = ArrayField(
        models.IntegerField(choices=StockIndices.choices, blank=True),
        default=list,
    )

    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Stock")
        verbose_name_plural = _("Stocks")
        ordering = ["ticker"]

    def __str__(self) -> str:
        return self.title or self.ticker

    @property
    def price(self) -> typing.Optional[decimal.Decimal]:
        """Current price of the stock."""
        latest_rate = self.rates.only("close", "added_at").order_by("-added_at").first()
        if not latest_rate:
            return
        return decimal.Decimal(latest_rate.close).quantize(
            decimal.Decimal("0.01"), rounding=decimal.ROUND_HALF_UP
        )
    
    @ttl_cache(ttl=30)
    def get_price_on_date(
        self, date: datetime.date
    ) -> typing.Optional[decimal.Decimal]:
        rate_on_date = (
            self.rates.filter(added_at__date=date)
            .order_by("-added_at")
            .only("close", "added_at")
            .first()
        )

        if not rate_on_date:
            return
        return decimal.Decimal(rate_on_date.close).quantize(
            decimal.Decimal("0.01"), rounding=decimal.ROUND_HALF_UP
        )


class MarketType(models.TextChoices):
    """Available market types."""

    REGULAR = "REG", _("Regular")
    FUTURE = "FUT", _("Future")
    ODD_LOT = "ODL", _("Odd Lot")


class MarketTrend(models.TextChoices):
    """Available market trends."""

    UP = "up", _("Up")
    DOWN = "down", _("Down")
    NEUTRAL = "neutral", _("Neutral")


class Rate(models.Model):
    """Model definition for a Rate."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    stock = models.ForeignKey(
        "stocks.Stock", on_delete=models.CASCADE, related_name="rates"
    )
    market = models.CharField(max_length=20, choices=MarketType.choices)
    previous_close = models.FloatField()
    open = models.FloatField()
    high = models.FloatField()
    low = models.FloatField()
    close = models.FloatField()
    volume = models.FloatField()
    trend = models.CharField(
        max_length=10, choices=MarketTrend.choices, default=MarketTrend.NEUTRAL
    )
    ldcp = models.FloatField(null=True, blank=True)
    change = models.FloatField(null=True, blank=True)
    pct_change = models.FloatField(null=True, blank=True)

    added_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Rate")
        verbose_name_plural = _("Rates")
        ordering = ["-added_at"]


class KSE100Rate(models.Model):
    """Model definition for KSE100 Rate"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date = models.DateField()
    open = models.FloatField()
    high = models.FloatField()
    low = models.FloatField()
    close = models.FloatField()
    volume = models.FloatField()

    class Meta:
        verbose_name = _("KSE100 Rate")
        verbose_name_plural = _("KSE100 Rates")
        ordering = ["-date"]

    @classmethod
    def get_close_on_date(cls, date: datetime.date):
        rate_on_date = (
            cls.objects.only("close", "date")
            .filter(date=date)
            .only("close", "date")
            .order_by("-date")
            .first()
        )
        if not rate_on_date:
            return None
        return rate_on_date.close

    @classmethod
    def get_latest_rate(cls):
        return cls.objects.latest("date")
