from django.contrib import admin

from .models import Stock, Rate


admin.site.register(Stock)
admin.site.register(Rate)
