from django.db import models
from django.utils import timezone
from django.conf import settings

class Stock(models.Model):
    symbol = models.CharField(max_length=20, db_index=True)
    company_name = models.CharField(max_length=200)
    sector = models.CharField(max_length=100, db_index=True)
    current_price = models.DecimalField(max_digits=10, decimal_places=2)
    change_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    volume = models.BigIntegerField()
    open_price = models.DecimalField(max_digits=10, decimal_places=2)
    high_price = models.DecimalField(max_digits=10, decimal_places=2)
    low_price = models.DecimalField(max_digits=10, decimal_places=2)
    vwap = models.DecimalField(max_digits=10, decimal_places=2)
    pe_ratio = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    market_cap = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    date = models.DateField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Additional fields for technical analysis
    industry = models.CharField(max_length=100, null=True, blank=True)
    country = models.CharField(max_length=50, default='Pakistan')
    exchange = models.CharField(max_length=20, default='PSX')
    dividend_yield = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    pb_ratio = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    ps_ratio = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    year_high = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    year_low = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    ma50 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    ma200 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    rsi14 = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    avg_volume = models.BigIntegerField(null=True, blank=True)
    relative_volume = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    change = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    class Meta:
        unique_together = ('symbol', 'date')
        indexes = [
            models.Index(fields=['symbol', 'date']),
            models.Index(fields=['sector']),
            models.Index(fields=['date']),
            models.Index(fields=['symbol', 'sector']),
            models.Index(fields=['date', 'sector']),
        ]
        ordering = ['-date', 'symbol']  # Default ordering

    def __str__(self):
        return f"{self.symbol} - {self.date}"
    
    def save(self, *args, **kwargs):
        # Calculate change if not provided but change_percentage is available
        if self.change is None and self.change_percentage is not None and self.current_price is not None:
            self.change = (self.change_percentage * self.current_price) / 100
        
        super().save(*args, **kwargs)

class StockScreener(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    filters = models.JSONField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_public = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class StockWatchlist(models.Model):
    name = models.CharField(max_length=100)
    stocks = models.ManyToManyField(Stock)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class LastDataUpdate(models.Model):
    last_update = models.DateField()
    is_success = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        get_latest_by = 'last_update'
