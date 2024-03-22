from telegram.tgfunctions import send_alert
from pprint import pprint as p
import pandas as pd
import requests
import json
import copy
from queue import Queue
from kiteconnect import KiteConnect, KiteTicker
from datetime import timedelta, time
import datetime
import threading
import pickle

from nse_feed.helper import *
# Creating the kite object

def login_kite_and_kws():
    response = requests.get("http://64.227.168.207/zerodha-creds/KZ8816/")
    data_string = response.text
    data = json.loads(data_string)
    api_key = data['api_key']
    request_token = data['access_tok']
    datakite = KiteConnect(api_key=api_key)
    datakite.set_access_token(request_token)
    kite = datakite
    kws = KiteTicker(api_key, request_token)
    return kite,kws


# step 1: get all fno-spot tradingsymbol and instrument token

# p(instrument_token_dict)


df = pd.read_csv('https://api.kite.trade/instruments')

def create_data_dict():
    global instrument_token_dict, data_dict, kite, ltp_dict,df
    for token,details in instrument_token_dict.items():
        
        try:
            try:
                ltp = (kite.quote(f'{details["exchange"]}:{details["tradingsymbol"]}'))[f'{details["exchange"]}:{details["tradingsymbol"]}']['last_price']
                strike_diff = get_options_min_diff(details["tradingsymbol"])
                expiries = get_options_expiry(details["tradingsymbol"])
                fut_expiries = get_futures_expiry(details["tradingsymbol"])
            except:
                ltp = (kite.quote(f'BSE:{details["tradingsymbol"]}'))[f'BSE:{details["tradingsymbol"]}']['last_price']
                strike_diff = get_options_min_diff(details["tradingsymbol"],'BFO')
                expiries = get_options_expiry(details["tradingsymbol"],'BFO')
                fut_expiries = get_futures_expiry(details["tradingsymbol"],'BFO')

            symbol = details["tradingsymbol"]
            ltp_dict[token]={'name':details["tradingsymbol"],'ltp': ltp,'strike_diff':strike_diff}

            current_month,next_month,current_week,next_week = expiries['current_month'],expiries['next_month'],expiries['current_week'],expiries['next_week']
            current_month_fut,next_month_fut = fut_expiries['current_month'],fut_expiries['next_month']

            if details["tradingsymbol"] in ['NIFTY 50','NIFTY BANK','NIFTY FIN SERVICE','SENSEX','BSE INDEX BANKEX']:
                dist = 24
                # Ensure that these values are integers
                strike_start, strike_end = map(int, (
                    (ltp // strike_diff * strike_diff - (dist / 2 - 1) * strike_diff),
                    (ltp // strike_diff * strike_diff + (dist / 2) * strike_diff)
                ))
                
                data_dict[details["tradingsymbol"]] = {
                    'CE': {current_week: {k: None for k in range(strike_start, int(strike_end + strike_diff), int(strike_diff))},
                            next_week: {k: None for k in range(strike_start, int(strike_end + strike_diff), int(strike_diff))}},
                    'EQ': {},
                    'FUT':{current_month_fut:None, next_month_fut:None},
                    'PE': {current_week: {k: None for k in range(strike_start, int(strike_end + strike_diff), int(strike_diff))},
                            next_week: {k: None for k in range(strike_start, int(strike_end + strike_diff),int( strike_diff))}}
                }
            else:
                dist = 16
                strike_start,strike_end = (ltp//strike_diff*strike_diff - (dist/2 - 1)*strike_diff),(ltp//strike_diff*strike_diff + (dist/2)*strike_diff)
                # for abnormal strile gaps
                cw_filter_df_ce = list(set(df[(df['name'] == details["tradingsymbol"]) &(df['instrument_type'] == 'CE') & (df['expiry'] == current_week)]['strike'].tolist()))
                call_strikes=nearest_values(ltp, cw_filter_df_ce, count=8)

                cw_filter_df_pe = list(set(df[(df['name'] == details["tradingsymbol"]) &(df['instrument_type'] == 'PE') & (df['expiry'] == current_week)]['strike'].tolist()))
                put_strikes=nearest_values(ltp, cw_filter_df_pe, count=8)

                data_dict[details["tradingsymbol"]] = {
                    'CE': {current_week: {k: None for k in call_strikes}},
                    'EQ': {},
                    'FUT':{current_month:None, next_month:None},
                    'PE': {current_week: {k: None for k in put_strikes}}
                }
            print(f'Done for {details["tradingsymbol"]}')
        except:
            print(f'failed for {details["tradingsymbol"]}')

def update_master_instrument_token_dict():
    global master_instrument_token_dict
    # Iterate through the data_dict and extract instrument token details
    for symbol, symbol_data in data_dict.items():
        print(symbol)
        for option_type, option_data in symbol_data.items():
            if option_type in ['CE','PE']:
                for expiry_date, strike_prices in option_data.items():
                    for strike_price in strike_prices.keys():
                        
                        symbol_ = symbol
                        if symbol == 'NIFTY 50':
                            symbol_ = 'NIFTY'
                        if symbol == "NIFTY BANK":
                            symbol_ = 'BANKNIFTY'
                        if symbol == "NIFTY FIN SERVICE":
                            symbol_ = 'FINNIFTY'
                        if symbol == "BSE INDEX BANKEX":
                            symbol = 'BANKEX'
                        # Filter the DataFrame based on conditions
                        filtered_df = df[(df['name'] == symbol_) &
                                        (df['instrument_type'] == option_type) &
                                        (df['expiry'] == expiry_date) &
                                        (df['strike'] == strike_price)]

                        # Assuming instrument_token is present in the filtered_df
                        instrument_token = filtered_df['instrument_token'].values[0]
                        
                        # Add the instrument token details to the dictionary
                        master_instrument_token_dict[instrument_token] = {
                            'tradingsymbol': symbol,
                            'option_side': option_type,
                            'expiry': expiry_date,
                            'strike': strike_price
                        }
            elif option_type == 'FUT':
                for expiry_date in option_data.keys(): 
                    symbol_ = symbol
                    if symbol == 'NIFTY 50':
                        symbol_ = 'NIFTY'
                    if symbol == "NIFTY BANK":
                        symbol_ = 'BANKNIFTY'
                    if symbol == "NIFTY FIN SERVICE":
                        symbol_ = 'FINNIFTY'
                    if symbol == "BSE INDEX BANKEX":
                        symbol = 'BANKEX'
                    # Filter the DataFrame based on conditions
                    filtered_df = df[(df['name'] == symbol_) &
                                    (df['instrument_type'] == option_type) &
                                    (df['expiry'] == expiry_date) &
                                    (df['strike'] == 0)]

                    # Assuming instrument_token is present in the filtered_df
                    instrument_token = filtered_df['instrument_token'].values[0]
                    
                    # Add the instrument token details to the dictionary
                    master_instrument_token_dict[instrument_token] = {
                        'tradingsymbol': symbol,
                        'option_side': option_type,
                        'expiry': expiry_date,
                        'strike': 0
                    }
            elif option_type == 'EQ':
                segment = 'NSE'
                if symbol == 'NIFTY 50':
                    segment = 'INDICES'
                if symbol == "NIFTY BANK":
                    segment = 'INDICES'
                if symbol == "NIFTY FIN SERVICE":
                    segment = 'INDICES'
                if symbol == "BSE INDEX BANKEX" or symbol == 'BANKEX':
                    symbol = 'BANKEX'
                    segment = 'INDICES'
                if symbol == "SENSEX":
                    segment = 'INDICES'
                # Filter the DataFrame based on conditions
                filtered_df = df[(df['tradingsymbol'] == symbol) & (df['segment'] == segment) &
                                (df['instrument_type'] == option_type)]

                # Assuming instrument_token is present in the filtered_df
                instrument_token = filtered_df['instrument_token'].values[0]

                # Add the instrument token details to the dictionary
                master_instrument_token_dict[instrument_token] = {
                    'tradingsymbol': symbol,
                    'option_side': 'EQ',
                    'expiry': None,
                    'strike': 0
                }

def process_and_update_ticks():
    global today, timestamp_dict, master_instrument_token_dict
    while datetime.datetime.now().time() <= time(15, 30, 5):
        ticks  = ticks_q.get()
        print('new ticks ',len(ticks))
        for tick in ticks:
            try:
                if 'last_trade_time' in tick:
                    if tick['last_trade_time'].date().day == datetime.datetime.today().day:
                        # print(tick['last_trade_time'])
                        if tick['last_trade_time'] < datetime.datetime(today.year, today.month, today.day, 9,15,0):
                            tick['last_trade_time'] = datetime.datetime(today.year, today.month, today.day, 9,15,0)
                        instrument_info = master_instrument_token_dict[tick['instrument_token']]
                        # Selective deep copy for nested structures
                        key = tick['last_trade_time']
                        # final_data = {"ltt":tick['last_trade_time'],'ltp':tick['last_price'],'vt':tick['volume_traded'],'tb':tick['total_buy_quantity'],'ts':tick['total_sell_quantity'],'oi':tick['oi'],'depth_buy':tick['depth']['buy'],'depth_sell':tick['depth']['sell']}
                        final_data = {"ltt":tick['last_trade_time'],
                                      'ltp':tick['last_price'],
                                      'vt':tick['volume_traded'],
                                      'tb':tick['total_buy_quantity'],
                                      'ts':tick['total_sell_quantity'],
                                      'oi':tick['oi'],
                                      'bid':[[entry['quantity'], entry['price'], entry['orders']] for entry in tick['depth']['buy']],
                                      'ask':[[entry['quantity'], entry['price'], entry['orders']] for entry in tick['depth']['sell']]}

                        if master_instrument_token_dict[tick['instrument_token']]['option_side'] != 'EQ' and master_instrument_token_dict[tick['instrument_token']]['option_side'] != 'FUT':
                            timestamp_dict[key][instrument_info['tradingsymbol']][instrument_info['option_side']][instrument_info['expiry']][instrument_info['strike']] = final_data
                        elif  master_instrument_token_dict[tick['instrument_token']]['option_side'] == 'FUT':
                            timestamp_dict[key][instrument_info['tradingsymbol']][instrument_info['option_side']][instrument_info['expiry']] = final_data
                        else:
                            timestamp_dict[key][instrument_info['tradingsymbol']][instrument_info['option_side']] = final_data

                else:
                    if tick['exchange_timestamp'].date().day == datetime.datetime.today().day:
                        if tick['exchange_timestamp'] < datetime.datetime(today.year, today.month, today.day, 9,15,0):
                            tick['exchange_timestamp'] = datetime.datetime(today.year, today.month, today.day, 9,15,0)
                        instrument_info = master_instrument_token_dict[tick['instrument_token']]
                        # Selective deep copy for nested structures
                        final_data = {"ltt":tick['exchange_timestamp'],'ltp':tick['last_price']}
                        key = tick['exchange_timestamp']
                        if master_instrument_token_dict[tick['instrument_token']]['option_side'] != 'EQ' and master_instrument_token_dict[tick['instrument_token']]['option_side'] != 'FUT':
                            timestamp_dict[key][instrument_info['tradingsymbol']][instrument_info['option_side']][instrument_info['expiry']][instrument_info['strike']] = final_data
                        elif  master_instrument_token_dict[tick['instrument_token']]['option_side'] == 'FUT':
                            timestamp_dict[key][instrument_info['tradingsymbol']][instrument_info['option_side']][instrument_info['expiry']] = final_data
                        else:
                            timestamp_dict[key][instrument_info['tradingsymbol']][instrument_info['option_side']] = final_data
                           
            except Exception as e:
                print(f'failed for {e}',instrument_info['tradingsymbol'],'-',instrument_info['option_side'])

    date_str = datetime.datetime.today().strftime("%d-%m-%Y")
    with open(f'{date_str}.pkl', 'wb') as f:
        pickle.dump(timestamp_dict, f, protocol=pickle.HIGHEST_PROTOCOL)


def master_data_feed():

    kite,kws = login_kite_and_kws()
    print('Kite,kws Objects created')

    data_dict = {}
    ticks_q = Queue()
    ltp_dict = {}
    today = datetime.datetime.now().date()
    start_time = datetime.datetime(today.year, today.month, today.day, 9, 00, 0)
    end_time = datetime.datetime(today.year, today.month, today.day, 15, 30, 0)
    timestamps = list(generate_timestamps(start_time, end_time))
    timestamp_dict = {}
    timestamp_dict = {ts: copy.deepcopy(data_dict) for ts in timestamps}
    timestamp_keys = list(timestamp_dict.keys())
    master_instrument_token_dict = {}
    print("Initial Variables created")

    output_list,instrument_token_dict = get_fno_cash_instrument_tokens_list_and_dict()

    create_data_dict()
    print('FNO Spot Ltp Fetched')

    update_master_instrument_token_dict()
    print('All instrument details updated')

    all_instruments_final = list(master_instrument_token_dict.keys())
    all_instruments_final = [int(item) for item in all_instruments_final]


    def on_ticks(ws, ticks):
        # print(ticks)
        threading.Thread(target=push_tick_to_q, args = (ticks,)).start()

    def on_connect(ws, response):
        print('Socket Started...')
        # send_alert('socket Started...')
        ws.set_mode(ws.MODE_FULL, all_instruments_final)
        threading.Thread(target=close_websocket, args = (ws,16,30,00,)).start()
        threading.Thread(target=process_and_update_ticks, args = ()).start()

    def on_close(ws, code, reason):
        ws.stop()
        threading.Thread(target=send_alert, args = ("Feed Stopped ...",)).start()

    # Assign the callbacks.
    kws.on_ticks = on_ticks
    kws.on_connect = on_connect
    kws.on_close = on_close

    # starting the socket
    kws.connect(threaded=True)





