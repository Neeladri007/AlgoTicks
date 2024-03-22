from django.contrib import admin

# Register your models here.

from strategy.models import *

# Register the models with the admin site
admin.site.register(InstrumentDetails)
# admin.site.register(TrailTable)
# admin.site.register(OptionPriceRange)