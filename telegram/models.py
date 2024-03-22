from django.db import models

# Create your models here.
class TelegramSettings(models.Model):
    token = models.CharField(max_length=255)
    chat_id = models.CharField(max_length=255)

    def __str__(self):
        return f'Telegram Settings - {self.token}'