from django.contrib import admin
from .models import Stock, StockScreener, StockWatchlist, LastDataUpdate


admin.site.register(Stock)
admin.site.register(StockScreener)
admin.site.register(StockWatchlist)
admin.site.register(LastDataUpdate)
