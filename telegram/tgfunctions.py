import requests
import threading
import pandas as pd
from telegram.models import TelegramSettings

df = pd.read_csv('https://api.kite.trade/instruments')

def send_alert(msg,instrument_token = ""):
    threading.Thread(target=send_alert_normal,args=(msg,instrument_token)).start()

def send_alert_normal(msg,instrument_token = ""):

    if instrument_token != "":
        tradingsymbol = str(df[df['instrument_token'] == instrument_token]['tradingsymbol'].item()) + ': '
    else:
        tradingsymbol = ""

    settings = TelegramSettings.objects.first()  # Assuming you have only one instance
    TOKEN = settings.token
    chat_id = settings.chat_id
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={chat_id}&text={tradingsymbol + msg}&parse_mode=Markdown"
    requests.get(url)