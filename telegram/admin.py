from django.contrib import admin
from telegram.models import *
# Register your models here.
@admin.register(TelegramSettings)
class BrokerListAdmin(admin.ModelAdmin):
    list_display = ['chat_id']