from django.contrib import admin
import pytz
from login.models import *

# Register your models here.
@admin.register(AngelTable)
class ClientAdmin(admin.ModelAdmin):
    def time_seconds(self, obj):
        try:
            time = obj.LastLoginTime.astimezone(pytz.timezone('Asia/Kolkata')).strftime("%d %b %Y %I:%M:%S.%f %p")
        except:
            time = "NA"
        return time
    time_seconds.admin_order_field = 'LastLoginTime'
    time_seconds.short_description = 'Precised Login Time'
    list_display = [ 'UserID', "Trade", "Broker", 'LastLoginStatus', "time_seconds"]
    list_display_links = ('UserID', )
    # search_fields = ( 'Broker',)
    list_filter = ( 'Broker', 'LastLoginStatus', )

@admin.register(BrokerList)
class BrokerListAdmin(admin.ModelAdmin):
    list_display = ['Name']