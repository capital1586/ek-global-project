from django.contrib import admin
from .models import Alert

@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ('title', 'symbol', 'condition_type', 'status', 'user', 'created_at')
    list_filter = ('status', 'condition_type', 'frequency', 'email_notification', 'sound_notification')
    search_fields = ('title', 'symbol', 'user__email')
    readonly_fields = ('last_triggered', 'times_triggered', 'created_at', 'updated_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'title', 'description', 'symbol')
        }),
        ('Alert Configuration', {
            'fields': ('condition_type', 'threshold_value', 'custom_condition', 'frequency')
        }),
        ('Status', {
            'fields': ('status', 'last_triggered', 'times_triggered')
        }),
        ('References', {
            'fields': ('portfolio_id', 'stock_id')
        }),
        ('Notification Settings', {
            'fields': ('email_notification', 'sound_notification')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
