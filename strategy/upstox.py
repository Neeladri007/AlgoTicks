import urllib.parse
import pandas as pd
import requests

api_key = "bf5d6189-d437-4b59-ba32-4f38866bff55"
secret = "vni2jnvgcj"

rurl = "https://www.google.com"
uri = f"https://api.upstox.com/v2/login/authorization/dialog?response_type=code&client_id={api_key}&redirect_uri={rurl}"

phone = '9689062951'
totp_key = "MZZ3XJZSYJGLX4UA2VJKINLHRI3BINIW"

import pyotp

pyotp.TOTP(totp_key).now()

pin = "452745"

code = "0AtnNM"

url = "https://assets.upstox.com/market-quote/instruments/exchange/complete.csv.gz"

# Read the CSV file from the URL
upstox_df = ((pd.read_csv(url, compression='gzip')))
upstox_df['exchange_token'] = upstox_df['exchange_token'].astype(int)
upstox_df.to_csv('upstox.csv')

import requests

def get_access_token():
    url_access_token = "https://api.upstox.com/v2/login/authorization/token"
    headers = {
        "accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "code": code,
        "client_id": api_key,
        "client_secret": secret,
        "redirect_uri": rurl,
        "grant_type": "authorization_code"
    }

    response = (requests.post(url_access_token, headers=headers, data=data))
    at = (response.json())['access_token']
    return at


access_token = get_access_token()




import asyncio
import json
import ssl
import websockets
from google.protobuf.json_format import MessageToDict
import MarketDataFeed_pb2 as pb
import upstox_client


async def establish_connection(configuration):
    api_version = '2.0'
    api_instance = upstox_client.WebsocketApi(
        upstox_client.ApiClient(configuration))
    api_response = api_instance.get_market_data_feed_authorize(api_version)

    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    websocket = await websockets.connect(api_response.data.authorized_redirect_uri, ssl=ssl_context)
    print('Connection established')
    return websocket


async def subscribe_instruments(websocket, mode, instruments):
    data = {
        "guid": "someguid",
        "method": "sub",
        "data": {"mode": mode, "instrumentKeys": instruments}
    }
    await websocket.send(json.dumps(data).encode('utf-8'))
    print("Subscribed to instruments: " + json.dumps(instruments))


async def unsubscribe_instruments(websocket, mode, instruments):
    data = {
        "guid": "someguid",
        "method": "unsub",
        "data": {"mode": mode, "instrumentKeys": instruments}
    }
    await websocket.send(json.dumps(data).encode('utf-8'))
    print("Unsubscribed from instruments: " + json.dumps(instruments))


async def receive_messages(websocket):
    try:
        while True:
            message = await websocket.recv()
            decoded_data = decode_protobuf(message)
            data_dict = MessageToDict(decoded_data)
            print(json.dumps(data_dict))
    except asyncio.CancelledError:
        print("WebSocket connection is being gracefully shutdown.")
        await websocket.close()


def decode_protobuf(buffer):
    feed_response = pb.FeedResponse()
    feed_response.ParseFromString(buffer)
    return feed_response


async def main():
    mode = 'full'
    # Configure OAuth2 access token for authorization
    configuration = upstox_client.Configuration()
    configuration.access_token = 'ACCESS_TOKEN'

    # Establish WebSocket connection
    websocket = await establish_connection(configuration)

    # Start receiving messages in a separate task
    receiver_task = asyncio.create_task(receive_messages(websocket))

    # Subscribe to initial instruments and more as needed
    await subscribe_instruments(websocket, mode, ['NSE_INDEX|Nifty 50'])

    # Example of subscribing to more instruments later
    await asyncio.sleep(3)  # Wait for some time or certain condition
    await subscribe_instruments(websocket, mode, ['NSE_INDEX|Nifty Bank'])

    # Example of unsubscribing from an instruments
    await asyncio.sleep(3)  # Wait for some time or certain condition
    await unsubscribe_instruments(websocket, mode, ['NSE_INDEX|Nifty 50'])

    await receiver_task

if __name__ == "__main__":
    asyncio.run(main())