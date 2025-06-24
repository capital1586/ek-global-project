from django.db import models

# Create your models here.

class Stock(models.Model):
    symbol = models.CharField(max_length=20)
    name = models.CharField(max_length=200)
    sector = models.CharField(max_length=100, null=True, blank=True)
    industry = models.CharField(max_length=100, null=True, blank=True)
    market_cap = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    change_percent = models.DecimalField(max_digits=5, decimal_places=2)
    volume = models.BigIntegerField()
    pe_ratio = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    prev_close = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    open_price = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    high_price = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    low_price = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    change = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['symbol']),
            models.Index(fields=['sector']),
            models.Index(fields=['industry']),
        ]
    
    def __str__(self):
        return self.symbol
        
    @classmethod
    def update_or_create_from_api(cls, data):
        """Create or update stock from API data"""
        return cls.objects.update_or_create(
            symbol=data['Symbol'],
            defaults={
                'name': data['CompanyName'],
                'sector': data.get('Sector'),
                'industry': data.get('Industry'),
                'price': data['Last'],
                'prev_close': data['LDCP'],
                'change': data['Change'],
                'change_percent': data['PctChange'],
                'open_price': data['Open'],
                'high_price': data['High'],
                'low_price': data['Low'],
                'volume': data['Volume'],
            }
        )
