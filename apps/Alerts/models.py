from django.db import models
from django.conf import settings
from django.utils import timezone

class Alert(models.Model):
    """Model for user alerts on stocks."""
    
    # Alert status choices
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('triggered', 'Triggered'),
        ('completed', 'Completed'),
        ('disabled', 'Disabled'),
    )
    
    # Alert condition type choices
    CONDITION_CHOICES = (
        ('price_above', 'Price Above Threshold'),
        ('price_below', 'Price Below Threshold'),
        ('price_up_percent', 'Price Up by Percentage'),
        ('price_down_percent', 'Price Down by Percentage'),
        ('volume_spike', 'Volume Spike'),
        ('rsi_overbought', 'RSI Overbought'),
        ('rsi_oversold', 'RSI Oversold'),
        ('custom', 'Custom Condition'),
    )
    
    # Alert frequency choices
    FREQUENCY_CHOICES = (
        ('one_time', 'One Time'),
        ('repeating', 'Repeating'),
        ('continuous', 'Continuous'),
    )
    
    # Basic fields
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='alerts')
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    symbol = models.CharField(max_length=20)
    
    # Portfolio relation
    portfolio = models.ForeignKey('portfolios.Portfolio', on_delete=models.SET_NULL, 
                                 null=True, blank=True, related_name='alerts')
    stock_id = models.CharField(max_length=50, blank=True, null=True, 
                               help_text="ID of stock transaction in portfolio")
    
    # Alert conditions
    condition_type = models.CharField(max_length=20, choices=CONDITION_CHOICES)
    threshold_value = models.DecimalField(max_digits=15, decimal_places=5, null=True, blank=True)
    custom_condition = models.CharField(max_length=255, blank=True, null=True)
    
    # Alert behavior
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='one_time')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_triggered = models.DateTimeField(null=True, blank=True)
    times_triggered = models.IntegerField(default=0)
    
    # Notification settings
    email_notification = models.BooleanField(default=True)
    sound_notification = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.title} ({self.symbol})"
    
    def mark_as_triggered(self):
        """Mark this alert as triggered and handle its status based on frequency."""
        self.last_triggered = timezone.now()
        self.times_triggered += 1
        
        # Set status based on frequency
        if self.frequency == 'one_time':
            self.status = 'completed'
        else:
            self.status = 'triggered'
            
        self.save()
        return self
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Alert'
        verbose_name_plural = 'Alerts'
