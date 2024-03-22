from order_functions.zerodha import *
from telegram.tgfunctions import send_alert
from strategy.models import *
from strategy.helper_functions import *
from strategy.position_management import *
import datetime
from decimal import Decimal
# from alice_blue import *
# from pya3 import *
from order_functions.aliceblue import *
import threading
import pandas as pd
import json
alice = []

# defining some dict for order status capturing
order_dict = {}
order_status = {}

# these 3 are used for live data handeling
live_instrument_dict = {}
instrument_to_ltp = {}
day_to_field_map = {
        0: 'monday_nearest',
        1: 'tuesday_nearest',
        2: 'wednesday_nearest',
        3: 'thursday_nearest',
        4: 'friday_nearest',
        5: 'friday_nearest',
        6: 'monday_nearest'
        # Add more days if needed
    }

cash_df = pd.read_csv('https://api.kite.trade/instruments')
# URLs of the other DataFrames
urls = [
    "https://v2api.aliceblueonline.com/restpy/static/contract_master/NFO.csv",
    'https://v2api.aliceblueonline.com/restpy/static/contract_master/NSE.csv',
    'https://v2api.aliceblueonline.com/restpy/static/contract_master/CDS.csv',
    'https://v2api.aliceblueonline.com/restpy/static/contract_master/BSE.csv',
    'https://v2api.aliceblueonline.com/restpy/static/contract_master/BFO.csv',
    'https://v2api.aliceblueonline.com/restpy/static/contract_master/BCD.csv',
    'https://v2api.aliceblueonline.com/restpy/static/contract_master/MCX.csv',
    'https://v2api.aliceblueonline.com/restpy/static/contract_master/INDICES.csv'
]

# Loop through the URLs to read DataFrames and merge with the original DataFrame
df_alice = pd.DataFrame()
for url in urls:
    df_temp = pd.read_csv(url)  # Assuming the data is in CSV format
    try:
        df_temp = df_temp[['Token','Trading Symbol']]
        df_alice = pd.concat([df_alice,df_temp], ignore_index=True)
    except:
        df_temp = df_temp[['token','symbol']]
        df_temp.rename(columns={'symbol': 'tradingsymbolalice','token':'Token'}, inplace=True)
        df_alice = pd.concat([df_alice,df_temp], ignore_index=True)

    
    # Rename the "Trading Symbol" column to "Trading Symbol Alice"
df_alice.rename(columns={'Trading Symbol': 'tradingsymbolalice'}, inplace=True)
    
    # # Merge DataFrames based on matching values in the 'exchange_token' and 'Token' columns
cash_df = pd.merge(cash_df, df_alice, left_on='exchange_token', right_on='Token', how='left')
cash_df.drop('Token', axis=1)



def get_tradingsymbol(instrument_token): # instrument_token as int
    tradingsymbol = cash_df[cash_df['instrument_token']==instrument_token]['tradingsymbol'].item()
    return tradingsymbol

def calculate_heikin_ashi(df):
    ha_df = pd.DataFrame(index=df.index, columns=['open', 'high', 'low', 'close'])

    # Set the first row of ha_df to be the same as the first row of df
    ha_df.iloc[0] = df.iloc[0][['open', 'high', 'low', 'close']]

    ha_df['close'] = (df['open'] + df['high'] + df['low'] + df['close']) / 4

    for i in range(1, len(df)):
        ha_df.at[df.index[i], 'open'] = round((ha_df.at[df.index[i - 1], 'open'] + ha_df.at[df.index[i - 1], 'close']) / 2, 2)
        ha_df.at[df.index[i], 'high'] = round(max(df.at[df.index[i], 'high'], ha_df.at[df.index[i], 'open'], ha_df.at[df.index[i], 'close']), 2)
        ha_df.at[df.index[i], 'low'] = round(min(df.at[df.index[i], 'low'], ha_df.at[df.index[i], 'open'], ha_df.at[df.index[i], 'close']), 2)
        ha_df.at[df.index[i], 'close'] = round(ha_df.at[df.index[i], 'close'], 2)

    return ha_df
# df = pd.read_csv('https://api.kite.trade/instruments')

def calculate_next_entry_time(interval):
    current_time = datetime.datetime.now()  # Current time including seconds
    start_time = datetime.datetime.strptime('09:15:00', '%H:%M:%S')  # Market opening time
    interval_map = {
        'minute': 60,
        '3minute': 3 * 60,
        '5minute': 5 * 60,
        '10minute': 10 * 60,
        '15minute': 15 * 60,
        '30minute': 30 * 60,
        '60minute': 60 * 60,
    }
    interval_seconds = interval_map.get(interval, 60)
    seconds_diff = (current_time - start_time).seconds
    next_entry_seconds = interval_seconds * ((seconds_diff + interval_seconds - 1) // interval_seconds)
    next_entry_time = start_time + datetime.timedelta(seconds=next_entry_seconds)

    return next_entry_time.time()

def calculate_current_entry_time(interval):
    current_time =  datetime.datetime.now() + datetime.timedelta(seconds=1) # Current time including seconds
    # current_time = datetime.datetime(2014,2,21,11,45,1,1)
    start_time = datetime.datetime.strptime('09:15:00', '%H:%M:%S')  # Market opening time
    interval_map = {
        'minute': 60,
        '3minute': 3 * 60,
        '5minute': 5 * 60,
        '10minute': 10 * 60,
        '15minute': 15 * 60,
        '30minute': 30 * 60,
        '60minute': 60 * 60,
    }
    interval_seconds = interval_map.get(interval, 60)
    seconds_diff = (current_time - start_time).seconds
    next_entry_seconds = interval_seconds * ((seconds_diff + interval_seconds - 1) // interval_seconds)
    next_entry_time = start_time + datetime.timedelta(seconds=(next_entry_seconds - interval_seconds))

    return next_entry_time.time()

def check_single_strategy(strategy,today_field_name,today_day_of_week,alice_object,alice_data,kite_object,orderbook,positionbook):
    
    today_nearest_price = float(getattr(strategy, today_field_name))
    run_days = [strategy.run_monday, strategy.run_tuesday, strategy.run_wednesday, strategy.run_thursday, strategy.run_friday,True,True]
    run_today = run_days[today_day_of_week] if today_day_of_week < len(run_days) else False
    entry_multiplier = 1 + float(strategy.entry_buffer)/100
    try:
        instrument_alice = alice_object.get_instrument_by_token(strategy.instrument_segment[:3], live_instrument_dict[strategy.strategy_name]['data'][int(strategy.instrument_token)]['exchange_token'])
    except:
        pass

    # if (run_today):
    #     print(strategy.start_time < datetime.datetime.now().time())
    #     print(strategy.end_time > datetime.datetime.now().time())
    #     print(strategy.intraday_exit >datetime.datetime.now().time())

    # basic checks before running the model
    if strategy.start_time < datetime.datetime.now().time() and strategy.end_time > datetime.datetime.now().time() and run_today and strategy.intraday_exit >datetime.datetime.now().time():

        # print(datetime.datetime.now().time())
        # try:
            # Trade_status = [('1',"Scan Pending"),('2',"Entry Sent to exchange"),("3","Entry Order Executed - TP SL Placement Pending"),("4","TP SL Placed"),("5","TP/SL hit - Other order pending"),("6",'Trade Complete: TP/SL Pending cancelled')]
        if int(strategy.trade_status) == 1:
            # get the instrument token or tokens based on client's filter condition from the InstrumentDetails table eg:Banknigty current week calls
            print('Entered Scan...')
            tokens = list(live_instrument_dict[strategy.strategy_name]['data'].keys())
            
            # if client didnt single out instrument then filter it further to the final instrument
            if len(tokens) > 0 :
                final_token = min(tokens, key=lambda x: abs(instrument_to_ltp[x] - today_nearest_price))
                ltp = instrument_to_ltp[final_token]
                # final_token = min((token for token in tokens if instrument_to_ltp[token] < today_nearest_price), key=lambda x: abs(instrument_to_ltp[x] - today_nearest_price))

                send_alert(f"Strategy Name :{strategy.strategy_name}, selected instrument: {get_tradingsymbol(final_token)}")

                strategy.instrument_token = final_token
                # get ltp or candle historical data based on client's logic checking criteris for entry
                end =  datetime.date.today()
                start = datetime.date.today() - datetime.timedelta(days = 5)
                no_of_candles_needed = 2
                instrument_df = (pd.DataFrame(kite_object.historical_data(final_token,start,end,strategy.interval)))
                # Convert 'date' column to datetime format
                instrument_df['date'] = pd.to_datetime(instrument_df['date'])
                print(instrument_df)

                # Get the latest time (first row of the sorted DataFrame)
                latest_time = instrument_df.iloc[-1]['date'].time()
                # print(instrument_df)
                instrument_df = calculate_heikin_ashi(instrument_df).tail(no_of_candles_needed).reset_index()
                
                # print(instrument_df)

                h1,l1 = instrument_df['high'][0],instrument_df['low'][0]
                strategy.trigger_price = round_nearest(h1 * entry_multiplier)
                strategy.limit_price = round_nearest(h1 * entry_multiplier *1.005)
                
                if strategy.last_candle_low:
                    strategy.sl_price = max(round_nearest(l1),round_nearest(h1 * entry_multiplier * (1-float(strategy.initial_sl)/100)))
                else:
                    strategy.sl_price = round_nearest(h1 * entry_multiplier * (1-float(strategy.initial_sl)/100))
            
                # ----- place order in alice at trigger price 
                print(strategy.instrument_segment[:3], live_instrument_dict[strategy.strategy_name]['data'][final_token]['exchange_token'])
                instrument_alice = alice_object.get_instrument_by_token(strategy.instrument_segment[:3], live_instrument_dict[strategy.strategy_name]['data'][final_token]['exchange_token'])
                
                quantity = int(strategy.quantity) * int(live_instrument_dict[strategy.strategy_name]['lot_size'])

                order_params_alice = {
                                    "complexty": "regular",
                                    "discqty": "0",
                                    "exch": strategy.instrument_segment[:3],
                                    "pCode": 'NRML',
                                    "prctyp": "SL",
                                    "price": float(round_nearest(h1 * entry_multiplier *1.005)),
                                    "qty": quantity,
                                    "ret": "DAY",
                                    "symbol_id": str(instrument_alice.token),
                                    "trading_symbol": instrument_alice.symbol,
                                    "transtype": 'BUY',
                                    "trigPrice": float(round_nearest(h1 * entry_multiplier))
                                }
                ltp = instrument_to_ltp[final_token]
                print(f"ltp: {ltp}, entry:{float(round_nearest(h1 * entry_multiplier))}, latest Time:{latest_time}, current candle time: {calculate_current_entry_time(strategy.interval)}")
                # print(latest_time == calculate_current_entry_time(strategy.interval))
                if ltp < float(round_nearest(h1 * entry_multiplier)) and latest_time == calculate_current_entry_time(strategy.interval):
                    response  = place_order_alice(alice_data.UserID,alice_data.AccessToken, order_params_alice)
                    print(response)
                    # ---- get the order id
                    oid = response[0]['NOrdNo']
                    send_alert(f"Strategy Name :{strategy.strategy_name}, selected instrument: {get_tradingsymbol(final_token)}, trigger-price: {round_nearest(h1 * entry_multiplier)},entry-price: {round_nearest(h1 * entry_multiplier *1.005)}, order_id: {oid}")

                    #  ---- save the order id
                    strategy.entry_oid = oid
                    strategy.trade_status = 2
                    strategy.save()
                elif ltp > float(round_nearest(h1 * entry_multiplier)) and latest_time == calculate_current_entry_time(strategy.interval):
                    strategy.trade_status = 1
                    strategy.start_time = calculate_next_entry_time(strategy.interval)
                    strategy.save()
        
        elif int(strategy.trade_status) == 2:
            # get order status from orderbook
            order_status = (orderbook[orderbook['Nstordno'] == strategy.entry_oid]['Status'].values)[0]
            # order_status
            # print(order_status)
            # order_status = "pending"
            print(f'entered 2 : {strategy.strategy_name} ; Entry Order Status: {order_status}')

            if order_status == 'trigger pending':

                tokens = list(live_instrument_dict[strategy.strategy_name]['data'].keys())
                final_token = min(tokens, key=lambda x: abs(instrument_to_ltp[x] - today_nearest_price))
                
                # final_token = min((token for token in tokens if instrument_to_ltp[token] < today_nearest_price), key=lambda x: abs(instrument_to_ltp[x] - today_nearest_price))
                
                if int(strategy.instrument_token) != int(final_token) and False:
                    send_alert(f"{strategy.strategy_name}: Changing Instrument as price changed")
                    

                    # get ltp or candle historical data based on client's logic checking criteris for entry
                    end =  datetime.date.today()
                    start = datetime.date.today() - datetime.timedelta(days = 5)
                    no_of_candles_needed = 2
                    candle_data = (pd.DataFrame(kite_object.historical_data(final_token,start,end,strategy.interval)))
                    instrument_df = calculate_heikin_ashi(candle_data).tail(no_of_candles_needed).reset_index()
                    print(candle_data.tail(no_of_candles_needed))
                    print(instrument_df)
                    h1,l1 = instrument_df['high'][0],instrument_df['low'][0]
                    strategy.instrument_token = final_token

                    # modify entry price , sl ,tp (if needed)
                    strategy.trigger_price = round_nearest(h1 * entry_multiplier)
                    strategy.limit_price = round_nearest(h1 * entry_multiplier *1.005)
                    if strategy.last_candle_low:
                        strategy.sl_price = max(round_nearest(l1),round_nearest(h1 * entry_multiplier * (1-float(strategy.initial_sl)/100)))
                    else:
                        strategy.sl_price = round_nearest(h1 * entry_multiplier * (1-float(strategy.initial_sl)/100))
                
                    # ----- place order in alice at trigger price 
                    instrument_alice = alice_object.get_instrument_by_token(strategy.instrument_segment[:3], live_instrument_dict[strategy.strategy_name]['data'][final_token]['exchange_token'])
                    quantity = int(strategy.quantity) * int(live_instrument_dict[strategy.strategy_name]['lot_size'])
                    alice_object.cancel_order(strategy.entry_oid)
                    order_params_alice = {
                                            "complexty": "regular",
                                            "discqty": "0",
                                            "exch": strategy.instrument_segment[:3],
                                            "pCode": 'NRML',
                                            "prctyp": "SL",
                                            "price": float(round_nearest(h1 * entry_multiplier *1.005)),
                                            "qty": quantity,
                                            "ret": "DAY",
                                            "symbol_id": str(instrument_alice.token),
                                            "trading_symbol": instrument_alice.symbol,
                                            "transtype": 'BUY',
                                            "trigPrice": float(round_nearest(h1 * entry_multiplier))
                                        }

                    response  = place_order_alice(alice_data.UserID,alice_data.AccessToken, order_params_alice)
                    # ---- get the order id
                    oid = response[0]['NOrdNo']
                    send_alert(f"Strategy Name :{strategy.strategy_name}, selected instrument: {get_tradingsymbol(final_token)}, trigger-price: {round_nearest(h1 * entry_multiplier)},entry-price: {round_nearest(h1 * entry_multiplier *1.005)}, order_id: {oid}")

                    #  ---- save the order id
                    strategy.entry_oid = oid
                    strategy.trade_status = 2
                    strategy.save()

                else:
                    final_token = strategy.instrument_token
                    ltp = instrument_to_ltp[int(final_token)]
                    end =  datetime.date.today()
                    start = datetime.date.today() - datetime.timedelta(days = 5)
                    no_of_candles_needed = 2
                    candle_data = (pd.DataFrame(kite_object.historical_data(final_token,start,end,strategy.interval)))
                    # # Convert 'date' column to datetime format
                    # candle_data['date'] = pd.to_datetime(candle_data['date'])

                    # # Get the latest time (first row of the sorted DataFrame)
                    # latest_time = candle_data.iloc[-1]['date'].time()

                    instrument_df = calculate_heikin_ashi(candle_data).tail(no_of_candles_needed).reset_index()
                    # print(candle_data.tail(no_of_candles_needed))
                    # print(instrument_df)
                    # instrument_df = calculate_heikin_ashi((pd.DataFrame(kite_object.historical_data(strategy.instrument_token,start,end,strategy.interval))).tail(no_of_candles_needed).reset_index())
                    h1,l1 = instrument_df['high'][0],instrument_df['low'][0]
                    # print(instrument_df)

                    # # modify entry price , sl ,tp (if needed)
                    # if latest_time == calculate_current_entry_time(strategy.interval):#for the wait till new data
                
                    if float(strategy.trigger_price) != float(round_nearest(h1 * entry_multiplier)) and ltp < float(round_nearest(h1 * entry_multiplier)):
                        print(float(strategy.trigger_price),float(round_nearest(h1 * entry_multiplier)))
                        strategy.trigger_price = round_nearest(h1 * entry_multiplier)

                        if strategy.last_candle_low:
                            strategy.sl_price = max(round_nearest(l1),round_nearest(h1 * (1-float(strategy.initial_sl)/100)))
                        else:
                            strategy.sl_price = round_nearest(h1 * (1-float(strategy.initial_sl)/100))
                        
                        instrument_alice = alice_object.get_instrument_by_token(strategy.instrument_segment[:3], live_instrument_dict[strategy.strategy_name]['data'][int(strategy.instrument_token)]['exchange_token'])
                        price = round_nearest(h1 * entry_multiplier *1.005)
                        trigger_price = round_nearest(h1 * entry_multiplier)
                        oid = strategy.entry_oid

                        #  modify old order
                        quantity = int(strategy.quantity) * int(live_instrument_dict[strategy.strategy_name]['lot_size'])
                        instrument_alice = alice_object.get_instrument_by_token(strategy.instrument_segment[:3], live_instrument_dict[strategy.strategy_name]['data'][int(strategy.instrument_token)]['exchange_token'])

                        order_params_alice = json.dumps({
                            "discqty": 0,
                            "exch": strategy.instrument_segment[:3],
                            "filledQuantity": 0,
                            "nestOrderNumber": oid,
                            "prctyp": "SL",
                            "price": str(price),
                            "qty": int(quantity),
                            "trading_symbol": instrument_alice.symbol,
                            "trigPrice": str(trigger_price),
                            "transtype": "BUY",
                            "pCode": "NRML"
                            })
                        response  = modify_order_alice(alice_data.UserID,alice_data.AccessToken, order_params_alice)

                        strategy.trigger_price = trigger_price
                        strategy.limit_price = price
                        strategy.entry_oid = oid
                        strategy.save()

                        send_alert(f"Strategy Name :{strategy.strategy_name}, selected instrument: {get_tradingsymbol(final_token)}, trigger-price modified to: {trigger_price},entry-price modified to: {price}")

                    elif ltp > float(round_nearest(h1 * entry_multiplier)):
                        strategy.start_time = calculate_next_entry_time(strategy.interval)
                        strategy.save()

                    # modify order

            elif order_status == 'complete':
                # strategy.trade_status = 3
                # strategy.save()
                # place sl order
                instrument_alice = alice_object.get_instrument_by_token(strategy.instrument_segment[:3], live_instrument_dict[strategy.strategy_name]['data'][int(strategy.instrument_token)]['exchange_token'])
                quantity = int(strategy.quantity) * int(live_instrument_dict[strategy.strategy_name]['lot_size'])
                order_params_alice = {
                                    "complexty": "regular",
                                    "discqty": "0",
                                    "exch": strategy.instrument_segment[:3],
                                    "pCode": 'NRML',
                                    "prctyp": "SL",
                                    "price": round_nearest(float(strategy.sl_price)*.99),
                                    "qty": quantity,
                                    "ret": "DAY",
                                    "symbol_id": str(instrument_alice.token),
                                    "trading_symbol": instrument_alice.symbol,
                                    "transtype": 'SELL',
                                    "trigPrice": float(strategy.sl_price)
                                    }

                response  = place_order_alice(alice_data.UserID,alice_data.AccessToken, order_params_alice)
                oid = response[0]['NOrdNo']

                send_alert(f'Strategy Name :{strategy.strategy_name},Entry order executed, Placing SL order, SELL@{float(strategy.sl_price)}')
                strategy.sl_oid = oid
                strategy.trade_status = 4
                strategy.save()

            elif order_status == 'open':
                send_alert(f'Strategy Name :{strategy.strategy_name},Entry order triggered... but order is in OPEN state...waiting for the entry to happen...')
            
            elif order_status == 'cancelled':
                send_alert(f'Strategy Name :{strategy.strategy_name},Entry order cancelled from outside.... Algo will not work.')
            
            elif order_status == 'rejected':
                erej_res = (orderbook[orderbook['Nstordno'] == str(strategy.entry_oid)]['RejReason'].values)[0]
                send_alert(f'Strategy Name :{strategy.strategy_name}, Entry Order placement rejected, Reason {erej_res}')
            
            else:
                send_alert(f"Strategy Name :{strategy.strategy_name},Entry Order status didn't match: Update the code for {order_status}")

        elif int(strategy.trade_status) == 4:
            print('entered 4')
            sl_order_status = (orderbook[orderbook['Nstordno'] == strategy.sl_oid]['Status'].values)[0]
            quantity = int(strategy.quantity) * int(live_instrument_dict[strategy.strategy_name]['lot_size'])
            print(sl_order_status)

            if int((positionbook[positionbook['Tsym'] == instrument_alice.symbol]['Netqty'].values)[0]) >= quantity:
                main_position_status = "Running"
            else:
                main_position_status = "Closed"

            if sl_order_status == 'trigger pending':
                if main_position_status == 'Running':

                    # end =  datetime.date.today()
                    # start = datetime.date.today() - datetime.timedelta(days = 5)
                    # no_of_candles_needed = 2
                    # candle_data = (pd.DataFrame(kite_object.historical_data(int(strategy.instrument_token),start,end,strategy.interval)))
                    # instrument_df = calculate_heikin_ashi(candle_data).tail(no_of_candles_needed).reset_index()
                    # print(candle_data.tail(no_of_candles_needed))
                    # print(instrument_df)

                    ltp = instrument_to_ltp[int(strategy.instrument_token)]
                    candle_high = (float(strategy.trigger_price)) * (100/(100 + float(strategy.entry_buffer)))
                    ltp_change_percentage = ((ltp - candle_high) / (candle_high)) * 100
                    print(f"ltp : {ltp}, profit : {ltp_change_percentage}")
                    stop_loss = strategy.sl_price
                    
                    # Update the stop loss based on target levels
                    if ltp_change_percentage >= (strategy.target10 + strategy.final_trail_price):
                        # Update stop loss to final_trail_sl percentage above current LTP
                        stop_loss = ltp * (1 + (strategy.trail10 + ((ltp_change_percentage - strategy.target10)//strategy.final_trail_sl)* strategy.final_trail_price)/ 100)
                    elif ltp_change_percentage >= strategy.target10:
                        stop_loss = candle_high * (1 + float(strategy.trail10) / 100)
                    elif ltp_change_percentage >= strategy.target9:
                        stop_loss = candle_high * (1 + float(strategy.trail9) / 100)
                    elif ltp_change_percentage >= strategy.target8:
                        stop_loss = candle_high * (1 + float(strategy.trail8) / 100)
                    elif ltp_change_percentage >= strategy.target7:
                        stop_loss = candle_high * (1 + float(strategy.trail7) / 100)
                    elif ltp_change_percentage >= strategy.target6:
                        stop_loss = candle_high * (1 + float(strategy.trail6) / 100)
                    elif ltp_change_percentage >= strategy.target5:
                        stop_loss = candle_high * (1 + float(strategy.trail5) / 100)
                    elif ltp_change_percentage >= strategy.target4:
                        stop_loss = candle_high * (1 + float(strategy.trail4) / 100)
                    elif ltp_change_percentage >= strategy.target3:
                        stop_loss = candle_high * (1 + float(strategy.trail3) / 100)
                    elif ltp_change_percentage >= strategy.target2:
                        stop_loss = candle_high * (1 + float(strategy.trail2) / 100)
                    elif ltp_change_percentage >= strategy.target1:
                        stop_loss = candle_high * (1 + float(strategy.trail1) / 100)

                    if round_nearest(float(strategy.sl_price)) < round_nearest(float(stop_loss)):
                        # cancel old sl order place new sl order
                        # alice_object.cancel_order(strategy.sl_oid)
                        # quantity = int(strategy.quantity) * int(live_instrument_dict[strategy.strategy_name]['lot_size'])
                        # instrument_alice = alice_object.get_instrument_by_token(strategy.instrument_segment[:3], live_instrument_dict[strategy.strategy_name]['data'][int(strategy.instrument_token)]['exchange_token'])
                        # order_params_alice = {
                        #                     "complexty": "regular",
                        #                     "discqty": 0,
                        #                     "exch": strategy.instrument_segment[:3],
                        #                     "pCode": 'NRML',
                        #                     "prctyp": "SL",
                        #                     "price": round_nearest(stop_loss * .99),
                        #                     "qty": quantity,
                        #                     "ret": "DAY",
                        #                     "symbol_id": str(instrument_alice.token),
                        #                     "trading_symbol": instrument_alice.symbol,
                        #                     "transtype": 'SELL',
                        #                     "trigPrice": round_nearest(stop_loss)
                        #                 }

                        # response  = place_order_alice(alice_data.UserID,alice_data.AccessToken, order_params_alice)
                        # # ---- get the order id
                        # oid = response[0]['NOrdNo']

                        # modify order
                        #  modify old order
                        quantity = int(strategy.quantity) * int(live_instrument_dict[strategy.strategy_name]['lot_size'])
                        instrument_alice = alice_object.get_instrument_by_token(strategy.instrument_segment[:3], live_instrument_dict[strategy.strategy_name]['data'][int(strategy.instrument_token)]['exchange_token'])

                        order_params_alice = json.dumps({
                            "discqty": 0,
                            "exch": strategy.instrument_segment[:3],
                            "filledQuantity": 0,
                            "nestOrderNumber": strategy.sl_oid,
                            "prctyp": "SL",
                            "price": str(round_nearest(stop_loss * .99)),
                            "qty": int(quantity),
                            "trading_symbol": instrument_alice.symbol,
                            "trigPrice": str(round_nearest(stop_loss)),
                            "transtype": "SELL",
                            "pCode": "NRML"
                            })
                        response  = modify_order_alice(alice_data.UserID,alice_data.AccessToken, order_params_alice)

                        # send_alert(f"Strategy Name :{strategy.strategy_name}, selected instrument: {instrument_alice.symbol}, Stop Loss modifying to: {round_nearest(float(stop_loss))}, update : {strategy.sl_oid}")
                        strategy.sl_price = round_nearest(float(stop_loss))
                        # strategy.sl_oid = oid
                        strategy.save()
                    
                else:
                    send_alert(f"{strategy.strategy_name}: Cancelling SL order as the position is already closed")
                    alice_object.cancel_order(strategy.sl_oid)
                    strategy.trade_status = 1
                    strategy.save()
            
            elif sl_order_status == 'cancelled':
                send_alert(f'Strategy Name :{strategy.strategy_name}, SL order cancelled from outside.... Algo will not trail SL ....')
                strategy.trade_status = 6
                strategy.save()

            elif sl_order_status == 'complete':
                send_alert(f'Strategy Name :{strategy.strategy_name}, SL/TSL hit, Trade complete')
                if True: 
                    #float(strategy.sl_price) > float(strategy.limit_price):
                    strategy.trade_status = 1
                    strategy.start_time = calculate_next_entry_time(strategy.interval)
                    strategy.save()
                else:
                    strategy.trade_status = 1
                    strategy.save()
            
            elif sl_order_status == 'rejected':
                rej_res = rej_res = (orderbook[orderbook['Nstordno'] == str(strategy.sl_oid)]['RejReason'].values)[0]
                send_alert(f'Strategy Name :{strategy.strategy_name}, SL/TSL order placement rejected, Reason: {rej_res}')
            
            elif sl_order_status == 'open':
                send_alert(f'Strategy Name :{strategy.strategy_name}, SL/TSL order triggered but still in OPEN state')
                instrument_alice = alice_object.get_instrument_by_token(strategy.instrument_segment[:3], live_instrument_dict[strategy.strategy_name]['data'][int(strategy.instrument_token)]['exchange_token'])
                quantity = int(strategy.quantity) * int(live_instrument_dict[strategy.strategy_name]['lot_size'])
                alice_object.cancel_order(strategy.sl_oid)
                order_params_alice = {
                                    "complexty": "regular",
                                    "discqty": "0",
                                    "exch": strategy.instrument_segment[:3],
                                    "pCode": 'NRML',
                                    "prctyp": "MKT",
                                    "price": '0',
                                    "qty": quantity,
                                    "ret": "DAY",
                                    "symbol_id": str(instrument_alice.token),
                                    "trading_symbol": instrument_alice.symbol,
                                    "transtype": 'SELL',
                                    "trigPrice": '0'
                                }

                response  = place_order_alice(alice_data.UserID,alice_data.AccessToken, order_params_alice)
                strategy.trade_status = 1
                strategy.start_time = calculate_next_entry_time(strategy.interval)
                strategy.save()
                
            
            else:
                send_alert(f"Strategy Name :{strategy.strategy_name}, SL Order status didn't match: Update the code for {order_status}")

        elif int(strategy.trade_status) >= 5:
            pass

    # condition for intraday exit
    elif run_today and strategy.intraday_exit < datetime.datetime.now().time():

        if int(strategy.trade_status) <= 4:

            if int(strategy.trade_status) == 2 :
                alice_object.cancel_order(strategy.entry_oid)
                send_alert(f"Strategy Name :{strategy.strategy_name}, Intraday Exit - Cancelling Entry order - Order ID: {strategy.entry_oid}")
                strategy.trade_status = 6
                strategy.save()

            if int(strategy.trade_status) == 4 :
                alice_object.cancel_order(strategy.sl_oid)
                send_alert(f"Strategy Name :{strategy.strategy_name}, Intraday Exit - Cancelling Stop Loss order - Order ID: {strategy.sl_oid}")
                instrument_alice = alice_object.get_instrument_by_token(strategy.instrument_segment[:3], live_instrument_dict[strategy.strategy_name]['data'][int(strategy.instrument_token)]['exchange_token'])
                quantity = int(strategy.quantity) * int(live_instrument_dict[strategy.strategy_name]['lot_size'])
                order_params_alice = {
                                    "complexty": "regular",
                                    "discqty": "0",
                                    "exch": strategy.instrument_segment[:3],
                                    "pCode": 'NRML',
                                    "prctyp": "MKT",
                                    "price": '0',
                                    "qty": quantity,
                                    "ret": "DAY",
                                    "symbol_id": str(instrument_alice.token),
                                    "trading_symbol": instrument_alice.symbol,
                                    "transtype": 'SELL',
                                    "trigPrice": '0'
                                }

                response  = place_order_alice(alice_data.UserID,alice_data.AccessToken, order_params_alice)
                oid = response[0]['NOrdNo']
                send_alert(f"Strategy Name :{strategy.strategy_name}, Intraday Exit at market, update : {oid}")
                strategy.trade_status = 6
                strategy.save()
                 
def scan_trigger_modify_cancel(kite_object,alice_object,alice_data):
    # Define start and end times
    start_time = datetime.time(9, 0)  # 9:00 am
    end_time = datetime.time(23, 30)  # 11:30 pm
    time.sleep(5)

    # Main loop
    while True:
        current_time = datetime.datetime.now().time()  # Get current time
        print(f"Strategy Running: @{current_time}")

        # Check if current time is within the desired range
        if start_time <= current_time <= end_time:
            unique_strategies = InstrumentDetails.objects.all()
            today_day_of_week = datetime.date.today().weekday()
            today_field_name = day_to_field_map.get(today_day_of_week)

            try:
                orderbook = pd.DataFrame(alice_object.get_order_history())
                try:
                    positionbook = pd.DataFrame(alice_object.get_netwise_positions())
                except:
                    positionbook = pd.DataFrame()
                # orderbook.to_csv("ob_suraj.csv")
                # print(orderbook)
            except:
                orderbook = pd.DataFrame()
                positionbook = pd.DataFrame()
                print('No Orders found...')

            for strategy in unique_strategies:
                threading.Thread(target = check_single_strategy,args = (strategy,today_field_name,today_day_of_week,alice_object,alice_data,kite_object,orderbook,positionbook,)).start()
            time.sleep(.45)    
        else:
            break 

def close_websocket(ws,h,m,s):
    import time
    while True :
        time.sleep(300)
        from datetime import datetime
        from datetime import time as datetime_time
        print(datetime.now())
        if datetime.now().time() > datetime_time(h,m,s):
            ws.close()
            break

# Functions for live monitoring of any addition and deletion of strategy //////// in the InstrumentDetails table++++++++++
def get_initial_instruments_list_and_update_live_instrument_dict():
    ins_details = InstrumentDetails.objects.all()
    for strategy in ins_details:

        # getting the variable values
        strategy_name = strategy.strategy_name
        name = strategy.instrument_name
        segment = strategy.instrument_segment
        instrument_type = strategy.instrument_type
        strike = strategy.strike
        expiry_type = strategy.expiry
        exchange = segment[:3]
        if strategy.instrument_type == 'CE' or strategy.instrument_type == 'PE':
            expiry_dict = get_options_expiry(name,exchange)
        elif strategy.instrument_type == 'FUT':
            expiry_dict = get_futures_expiry(name,exchange)
        else:
            expiry_dict = {'current_week':'','next_week':'','current_month':'','next_month':''}
        # print(expiry_dict)

        # get the instrument token or tokens based on client's filter condition from the InstrumentDetails table eg:Banknigty current week calls
        try:
            try:
                temp_token_df = pd.DataFrame()
                # for strike given options
                expiry_dict = get_options_expiry(strategy.instrument_name,(strategy.instrument_segment)[:3])
                temp_token_df = df[(df['name'] == strategy.instrument_name) & (df['segment'] == strategy.instrument_segment) & (df['expiry'] == expiry_dict[strategy.expiry]) & (df['instrument_type'] == strategy.instrument_type) & (df['strike'] == int(strategy.strike))]
                a = temp_token_df.iloc[0]
                result_dict = temp_token_df[['instrument_token','exchange_token','tradingsymbol']].set_index('instrument_token').to_dict(orient='index')
            except:
                temp_token_df = pd.DataFrame()
                # for strike given options
                expiry_dict = get_options_expiry(strategy.instrument_name,(strategy.instrument_segment)[:3])
                temp_token_df = df[(df['name'] == strategy.instrument_name) & (df['segment'] == strategy.instrument_segment) & (df['expiry'] == expiry_dict[strategy.expiry]) & (df['instrument_type'] == strategy.instrument_type)]
                a = temp_token_df.iloc[0]
                result_dict = temp_token_df[['instrument_token','exchange_token','tradingsymbol']].set_index('instrument_token').to_dict(orient='index')
        except:
            try:
            # for futures
                expiry_dict = get_futures_expiry(strategy.instrument_name,(strategy.instrument_segment)[:3])
                temp_token_df = df[(df['name'] == strategy.instrument_name) & (df['segment'] == strategy.instrument_segment) & (df['expiry'] == expiry_dict[strategy.expiry]) & (df['instrument_type'] == strategy.instrument_type)]
                a = temp_token_df.iloc[0]
            except:
                try:
                    temp_token_df = df[(df['name'] == strategy.instrument_name) & (df['segment'] == strategy.instrument_segment) & (df['instrument_type'] == strategy.instrument_type)]
                    a = temp_token_df.iloc[0]
                except:
                    send_alert(f'Failed to start strategy: {strategy.strategy_name}-- [Reason: Details does not match with any instrument]')


        if len(temp_token_df) > 0:
            send_alert(f'Starting strategy: {strategy.strategy_name}, instrument_domain: {len(temp_token_df)}')
            final_df = temp_token_df[['instrument_token','exchange_token','tradingsymbol','lot_size']]
            lot_size = (final_df['lot_size'].unique().tolist())[0]
            result_dict = final_df[['instrument_token','exchange_token','tradingsymbol']].set_index('instrument_token').to_dict(orient='index')
            
            # Check if the name already exists in the dictionary
            if name in live_instrument_dict.keys():
                # Update the existing key with the new data
                live_instrument_dict[strategy_name]['data'].update(result_dict)
            else:
                # Create a new key and assign the value
                live_instrument_dict[strategy_name] = {'data': result_dict, 'lot_size': lot_size}
            print('sending alert')
            # send_alert(f'Starting strategy: {strategy.strategy_name}, instrument_domain: {len(final_df)}')


    instrument_list = []
    for k,v in live_instrument_dict.items():
        for k1,v1 in v.items():
            if k1 == 'data':
                for k2 in v1.keys():
                    instrument_list.append(k2)
    print(len(instrument_list))
    return instrument_list

def live_strategy_database_check(kws):
    inss_old = InstrumentDetails.objects.all()
    while True:
        inss = InstrumentDetails.objects.all()
        if inss_old != inss:
            removed_inss = [ins for ins in inss_old if ins not in inss]
            new_inss = [ins for ins in inss if ins not in inss_old]

            # subscribing new instruments to the socket
            for strategy in new_inss:
                # getting the variable values
                strategy_name = strategy.strategy_name
                name = strategy.instrument_name
                segment = strategy.instrument_segment
                exchange = segment[:3]
                if strategy.instrument_type == 'CE' or strategy.instrument_type == 'PE':
                    expiry_dict = get_options_expiry(name,exchange)
                elif strategy.instrument_type == 'FUT':
                    expiry_dict = get_futures_expiry(name,exchange)
                else:
                    expiry_dict = {'current_week':'','next_week':'','current_month':'','next_month':''}

                # get the instrument token or tokens based on client's filter condition from the InstrumentDetails table eg:Banknigty current week calls
                try:
                    try:
                        temp_token_df = pd.DataFrame()
                        # for strike given options
                        expiry_dict = get_options_expiry(strategy.instrument_name,(strategy.instrument_segment)[:3])
                        temp_token_df = df[(df['name'] == strategy.instrument_name) & (df['segment'] == strategy.instrument_segment) & (df['expiry'] == expiry_dict[strategy.expiry]) & (df['instrument_type'] == strategy.instrument_type) & (df['strike'] == int(strategy.strike))]
                        a = temp_token_df.iloc[0]
                        result_dict = temp_token_df[['instrument_token','exchange_token','tradingsymbol']].set_index('instrument_token').to_dict(orient='index')
                    except:
                        temp_token_df = pd.DataFrame()
                        # for strike given options
                        expiry_dict = get_options_expiry(strategy.instrument_name,(strategy.instrument_segment)[:3])
                        temp_token_df = df[(df['name'] == strategy.instrument_name) & (df['segment'] == strategy.instrument_segment) & (df['expiry'] == expiry_dict[strategy.expiry]) & (df['instrument_type'] == strategy.instrument_type)]
                        a = temp_token_df.iloc[0]
                        result_dict = temp_token_df[['instrument_token','exchange_token','tradingsymbol']].set_index('instrument_token').to_dict(orient='index')
                except:
                    try:
                    # for futures
                        expiry_dict = get_futures_expiry(strategy.instrument_name,(strategy.instrument_segment)[:3])
                        temp_token_df = df[(df['name'] == strategy.instrument_name) & (df['segment'] == strategy.instrument_segment) & (df['expiry'] == expiry_dict[strategy.expiry]) & (df['instrument_type'] == strategy.instrument_type)]
                        a = temp_token_df.iloc[0]
                        result_dict = temp_token_df[['instrument_token','exchange_token','tradingsymbol']].set_index('instrument_token').to_dict(orient='index')
                    except:
                        try:
                            temp_token_df = df[(df['name'] == strategy.instrument_name) & (df['segment'] == strategy.instrument_segment) & (df['instrument_type'] == strategy.instrument_type)]
                            a = temp_token_df.iloc[0]
                            result_dict = temp_token_df[['instrument_token','exchange_token','tradingsymbol']].set_index('instrument_token').to_dict(orient='index')
                        except:
                            send_alert(f'Failed to start strategy: {strategy.strategy_name}-- [Reason: Details does not match with any instrument]')

                

                if len(temp_token_df) > 0:
                    lot_size = (temp_token_df['lot_size'].unique().tolist())[0]
                    result_dict = temp_token_df[['instrument_token','exchange_token','tradingsymbol']].set_index('instrument_token').to_dict(orient='index')

                    if name in live_instrument_dict.keys():
                        live_instrument_dict[strategy_name]['data'].update(result_dict)
                    else:
                        live_instrument_dict[strategy_name] = {'data': result_dict, 'lot_size': lot_size}

                    new_ins_to_subscribe = temp_token_df['instrument_token'].tolist()
                    kws.subscribe(new_ins_to_subscribe)
                    send_alert(f'Started strategy: {strategy.strategy_name}, new instrument domain: {len(new_ins_to_subscribe)}')


            # unsubscribing old instruments to the socket
            for strategy in removed_inss:
                try:
                    strategy_name = strategy.strategy_name
                    name = strategy.instrument_name
                    old_ins_to_unsubscribe = list(live_instrument_dict[strategy_name]['data'].keys())
                    kws.unsubscribe(old_ins_to_unsubscribe)
                    send_alert(f'Stopping Strategy :{strategy_name}')
                except:
                    send_alert(f'Failed to stop strategy :{strategy_name}')

        time.sleep(1.5)
        inss_old = inss


# function for live ltp update to instrument_to_ltp dict ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
def update_ltp(ticks):
    # print("pushing ticks to q")
    for tick in ticks:
        instrument_to_ltp[tick['instrument_token']] = tick['last_price']


def Strategy_Main():
    return None
    from kiteconnect import KiteConnect,KiteTicker

    # Replace these variables with actual values from 'data'
    # brokerobj = AngelTable.objects.filter(Broker__Name=="Zerodha").first()
    # api_key = brokerobj.AppID
    # request_token = brokerobj.AccessToken
    # datakite = KiteConnect(api_key=api_key)
    # datakite.set_access_token(request_token)
    # kws = KiteTicker(api_key, request_token)

    # temp kite object
    import json,requests
    response = requests.get("http://64.227.168.207/zerodha-creds/KZ8816/")
    data = json.loads(response.text)
    api_key,api_sec,request_token = data['api_key'],data['api_sec'],data['access_tok']
    datakite = KiteConnect(api_key=api_key)
    datakite.set_access_token(request_token)
    kite = datakite
    kite.profile()
    kws = KiteTicker(api_key, request_token)
    alice_data = AngelTable.objects.filter(Broker__Name="Alice Blue").first()
    alice = AliceBlue(alice_data.UserID,alice_data.AccessToken,['NSE','NFO','BSE','BFO'])

    print("Objects Created....")

    # getting final set if instruments
    final_instruments = get_initial_instruments_list_and_update_live_instrument_dict()
    final_instruments = [256265] + final_instruments
    # final_instruments = [256265]

    print(f'Subscribing {len(final_instruments)} instruments....')

    def on_ticks(ws, ticks):
        # print(ticks)
        # print(instrument_to_ltp)
        # print(live_instrument_dict)
        threading.Thread(target=update_ltp,args=(ticks,)).start()


    def on_connect(ws, response):
        ws.set_mode(ws.MODE_FULL, final_instruments)
        threading.Thread(target=send_alert, args = ("Algo started ...",)).start()
        threading.Thread(target=close_websocket, args = (ws,15,30,00,)).start()

        # to trigger orders or modify or cancel orders based on the condition
        threading.Thread(target = scan_trigger_modify_cancel, args = (kite,alice,alice_data)).start()

        # to check in live if there is some changes in the strategy table, now addition or anything
        threading.Thread(target = live_strategy_database_check, args = (kws,)).start()
        print('Datafeed Socket Started')

    def on_close(ws, code, reason):
        ws.stop()
        threading.Thread(target=send_alert, args = ("Algo Stopped ...",)).start()

    # Assign the callbacks.
    kws.on_ticks = on_ticks
    kws.on_connect = on_connect
    kws.on_close = on_close

    # starting the socket
    kws.connect(threaded=True)



