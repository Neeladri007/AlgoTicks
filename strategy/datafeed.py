import requests
import pyotp
import pandas as pd
import statistics
from datetime import date
from kiteconnect import KiteConnect
from kiteconnect import KiteTicker
import requests
import json

from strategy.helper_functions import *
data_dict = {}




response = requests.get("http://64.227.168.207/zerodha-creds/KZ8816/")
data = json.loads(response.text)

api_key = data['api_key']
api_sec = data['api_sec']
request_token = data['access_tok']

datakite = KiteConnect(api_key=api_key)
datakite.set_access_token(request_token)
kite = datakite