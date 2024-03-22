import pandas as pd
from datetime import date,timedelta
import datetime
import statistics
import math

df = pd.read_csv('https://api.kite.trade/instruments')


def round_nearest(x):
    return round(round(x / 0.05) * 0.05, -int(math.floor(math.log10(0.05))))

def get_fno_tradingsymbols(exchange:str='NFO'):
    all_options = df.loc[(df['exchange'] == exchange) & (df["segment"] == f"{exchange}-OPT")][['name','instrument_token', 'exchange_token', 'tradingsymbol','instrument_type','strike',"expiry"]].dropna()
    names_list = all_options['name'].unique()
    name_mapping = {
        "NIFTY": "NIFTY 50",
        "BANKNIFTY": "NIFTY BANK",
        "FINNIFTY": "NIFTY FIN SERVICE",
        "BANKEX":'BANKEX',
        'SENSEX':'SENSEX',
        'SNSX50':'SNSX50'
    }
    new_names_list = [name_mapping.get(name, name) for name in names_list]

    return new_names_list

def get_options_min_diff(symbol:str,exchange:str='NFO'):
    if symbol == 'NIFTY 50':
        symbol = 'NIFTY'
    if symbol == "NIFTY BANK":
        symbol = 'BANKNIFTY'
    if symbol == "NIFTY FIN SERVICE":
        symbol = 'FINNIFTY'
    if symbol == "BSE INDEX BANKEX":
        symbol = 'BANKEX'
    if symbol == "BSE INDEX SNSX50":
        symbol = 'SENSEX50'


    all_options = (df.loc[(df['exchange'] == exchange) & (df["segment"] == f"{exchange}-OPT") & (df['name'] == symbol)][['strike']].dropna())
    strike_prices = sorted(list(set(all_options['strike'].tolist())))
    min_diff = statistics.mode(strike_prices[i+1] - strike_prices[i] for i in range(len(strike_prices)-1))
    return min_diff


def get_options_expiry(symbol:str,exchange:str = 'NFO'):
    try:
        if symbol == 'NIFTY 50':
            symbol = 'NIFTY'
        if symbol == "NIFTY BANK":
            symbol = 'BANKNIFTY'
        if symbol == "NIFTY FIN SERVICE":
            symbol = 'FINNIFTY'
        if symbol == "BSE INDEX BANKEX":
            symbol = 'BANKEX'
        if symbol == "BSE INDEX SNSX50":
            symbol = 'SENSEX50'

        all_options = df.loc[(df['exchange'] == exchange) & (df["segment"] == f"{exchange}-OPT") & (df['name'] == symbol)][['name','instrument_token', 'exchange_token', 'tradingsymbol','instrument_type','strike',"expiry"]].dropna()

        all_options['expiry'] = pd.to_datetime(all_options['expiry'])
        expiries = sorted(all_options['expiry'].dt.strftime('%Y-%m-%d').unique().tolist())
        expiries_datetime = pd.to_datetime(expiries, unit='ns')
        current_year, current_month = date.today().year, date.today().month
        next_month = (current_month % 12) + 1  # To handle December
        next_to_next_month = (current_month % 12) + 2
        next_to_next_to_next_month = (current_month % 12) + 3
        current_month_dates = [d for d in expiries_datetime if d.year == current_year and d.month == current_month]
        next_month_dates = [d for d in expiries_datetime if (d.month == next_month and d.year == current_year) or (d.month == 1 and d.year == current_year + 1)]
        next_to_next_month_dates = [d for d in expiries_datetime if (d.month == next_to_next_month and d.year == current_year) or (d.month == 2 and d.year == current_year + 1)]
        next_to_next_to_next_month_dates = [d for d in expiries_datetime if (d.month == next_to_next_to_next_month and d.year == current_year) or (d.month == 3 and d.year == current_year + 1)]
        
        # Find the maximum date for current month, handling the case when the list is empty
        max_current_month = max(current_month_dates, default=None)

        # Find the maximum date for next month, handling the case when the list is empty
        max_next_month = max(next_month_dates, default=None)

        # Find the maximum date for next-to-next month, handling the case when the list is empty
        max_next_to_next_month = max(next_to_next_month_dates, default=None)

        # Find the maximum date for next-to-next-to-next month, handling the case when the list is empty
        max_next_to_next_to_next_month = max(next_to_next_to_next_month_dates, default=None)

        # List of maximum dates for each month
        max_dates = [max_current_month, max_next_month, max_next_to_next_month, max_next_to_next_to_next_month]

        # Sort the maximum dates in ascending order (earliest to latest)
        max_dates_sorted = sorted(filter(None, max_dates))

        # The first two dates in the sorted list will be the two nearest months
        nearest_month1, nearest_month2 = max_dates_sorted[:2]

        # Convert the nearest month dates to strings in the format 'YYYY-MM-DD'
        nearest_month1_str = nearest_month1.strftime('%Y-%m-%d') if nearest_month1 is not None else None
        nearest_month2_str = nearest_month2.strftime('%Y-%m-%d') if nearest_month2 is not None else None



        output_dict = {'current_week':expiries[0],'next_week':expiries[1],'current_month':nearest_month1_str,'next_month':nearest_month2_str}
    except:
        output_dict = {'current_week':None,'next_week':None,'current_month':None,'next_month':None}
    return output_dict

def get_futures_expiry(symbol:str,exchange:str = 'NFO'):
    try:
        if symbol == 'NIFTY 50':
            symbol = 'NIFTY'
        if symbol == "NIFTY BANK":
            symbol = 'BANKNIFTY'
        if symbol == "NIFTY FIN SERVICE":
            symbol = 'FINNIFTY'
        if symbol == "BSE INDEX BANKEX":
            symbol = 'BANKEX'
        if symbol == "BSE INDEX SNSX50":
            symbol = 'SENSEX50'
        
        all_options = df.loc[(df['exchange'] == exchange) & (df["segment"] == f"{exchange}-FUT") & (df['name'] == symbol)][['name','instrument_token', 'exchange_token', 'tradingsymbol','instrument_type','strike',"expiry"]].dropna()
        all_options['expiry'] = pd.to_datetime(all_options['expiry'])
        expiries = sorted(all_options['expiry'].dt.strftime('%Y-%m-%d').unique().tolist())
        expiries_datetime = pd.to_datetime(expiries, unit='ns')
        current_year, current_month = date.today().year, date.today().month
        next_month = (current_month % 12) + 1  # To handle December
        next_to_next_month = (current_month % 12) + 2
        next_to_next_to_next_month = (current_month % 12) + 3
        current_month_dates = [d for d in expiries_datetime if d.year == current_year and d.month == current_month]
        next_month_dates = [d for d in expiries_datetime if (d.month == next_month and d.year == current_year) or (d.month == 1 and d.year == current_year + 1)]
        next_to_next_month_dates = [d for d in expiries_datetime if (d.month == next_to_next_month and d.year == current_year) or (d.month == 2 and d.year == current_year + 1)]
        next_to_next_to_next_month_dates = [d for d in expiries_datetime if (d.month == next_to_next_to_next_month and d.year == current_year) or (d.month == 3 and d.year == current_year + 1)]
        
        # Find the maximum date for current month, handling the case when the list is empty
        max_current_month = max(current_month_dates, default=None)

        # Find the maximum date for next month, handling the case when the list is empty
        max_next_month = max(next_month_dates, default=None)

        # Find the maximum date for next-to-next month, handling the case when the list is empty
        max_next_to_next_month = max(next_to_next_month_dates, default=None)

        # Find the maximum date for next-to-next-to-next month, handling the case when the list is empty
        max_next_to_next_to_next_month = max(next_to_next_to_next_month_dates, default=None)

        # List of maximum dates for each month
        max_dates = [max_current_month, max_next_month, max_next_to_next_month, max_next_to_next_to_next_month]

        # Sort the maximum dates in ascending order (earliest to latest)
        max_dates_sorted = sorted(filter(None, max_dates))

        # The first two dates in the sorted list will be the two nearest months
        nearest_month1, nearest_month2 = max_dates_sorted[:2]

        # Convert the nearest month dates to strings in the format 'YYYY-MM-DD'
        nearest_month1_str = nearest_month1.strftime('%Y-%m-%d') if nearest_month1 is not None else None
        nearest_month2_str = nearest_month2.strftime('%Y-%m-%d') if nearest_month2 is not None else None



        output_dict = {'current_week':expiries[0],'next_week':expiries[1],'current_month':nearest_month1_str,'next_month':nearest_month2_str}
    except:
        output_dict = {'current_week':None,'next_week':None,'current_month':None,'next_month':None}
    return output_dict


def get_options_instrument_list(symbol:str,expiry="current_week"):
    symbol = symbol.upper()
    df = pd.read_csv('https://api.kite.trade/instruments')
    all_options = df.loc[(df['exchange'] == "NFO") & (df["segment"] == "NFO-OPT") & (df['name'] == symbol)][['name','instrument_token', 'exchange_token', 'tradingsymbol','instrument_type','strike',"expiry"]].dropna()
    exp_dict = get_options_expiry(symbol)
    exp = exp_dict[expiry]
    symbol_df = all_options[all_options['expiry']==exp.strftime('%Y-%m-%d')]
    instruments = symbol_df['instrument_token'].tolist()

    return instruments

def get_instrument_token_details_dict(exchange='NFO'):
    df = pd.read_csv('https://api.kite.trade/instruments')
    all_options = df.loc[(df['exchange'] == exchange)][['name','instrument_token', 'exchange_token', 'tradingsymbol','instrument_type','strike',"expiry"]]
    # Convert the DataFrame to a dictionary with 'instrument_token' as the key
    instrument_details = all_options.set_index('instrument_token').to_dict(orient='index')
    return instrument_details

def get_fno_cash_instrument_tokens_list_and_dict():
    # df = pd.read_csv('https://api.kite.trade/instruments')
    df = pd.read_csv('ins.csv')
    new_names_list = get_fno_tradingsymbols()
    all_data = df.loc[(df['exchange'] == 'NSE') & (df['tradingsymbol'].isin(new_names_list))][['name','instrument_token', 'exchange_token', 'tradingsymbol','instrument_type','strike',"expiry",'exchange']]
    output_list = all_data['instrument_token'].unique().tolist()
    instrument_dict = all_data.set_index('instrument_token').to_dict(orient='index')

    new_names_list = get_fno_tradingsymbols('BFO')
    all_data = df.loc[(df['exchange'] == 'BSE') & (df['tradingsymbol'].isin(new_names_list))][['name','instrument_token', 'exchange_token', 'tradingsymbol','instrument_type','strike',"expiry",'exchange']]
    output_list2 = all_data['instrument_token'].unique().tolist()
    instrument_dict2 = all_data.set_index('instrument_token').to_dict(orient='index')
    instrument_dict.update(instrument_dict2)

    return output_list+output_list2,instrument_dict

def get_current_fno_and_spot_instrument_tokens_and_dict(symbol):
    symbol = symbol.upper()
    df = pd.read_csv('https://api.kite.trade/instruments')
    # df = pd.read_csv('ins.csv')
    expiries = get_options_expiry(symbol)
    name_mapping = {
        "NIFTY": "NIFTY 50",
        "BANKNIFTY": "NIFTY BANK",
        "FINNIFTY": "NIFTY FIN SERVICE"
    }
    current_month,next_month,current_week,next_week = expiries['current_month'],expiries['next_month'],expiries['current_week'],expiries['next_week']
    try:
        segment = (df.loc[(df['tradingsymbol']==symbol)&((df['exchange'] == 'NSE'))]['segment'].tolist())[0]
    except:
        segment = (df.loc[(df['tradingsymbol']==name_mapping[symbol])&((df['exchange'] == 'NSE'))]['segment'].tolist())[0]

    if segment == 'NSE':
        all_data = df.loc[(df['tradingsymbol'].str.contains(symbol))][['name','instrument_token', 'exchange_token', 'tradingsymbol','instrument_type','strike',"expiry"]]
        cash_instrument_df = df.loc[(df['tradingsymbol'] == symbol) & (df['exchange'] == 'NSE')][['name','instrument_token', 'exchange_token', 'tradingsymbol','instrument_type','strike',"expiry"]]
        current_month_fno_instruments_df = all_data[all_data['expiry'] == current_month.strftime('%Y-%m-%d')]

        master_df = pd.concat([current_month_fno_instruments_df,cash_instrument_df])
        instrument_list = master_df['instrument_token'].unique().tolist()
        instrument_dict = master_df.set_index('instrument_token').to_dict(orient='index')
    if segment == 'INDICES':
        
        all_data = df.loc[(df['name']==(symbol))][['name','instrument_token', 'exchange_token', 'tradingsymbol','instrument_type','strike',"expiry"]]
        cash_instrument_df = df.loc[(df['tradingsymbol'] == name_mapping[symbol]) & (df['exchange'] == 'NSE')][['name','instrument_token', 'exchange_token', 'tradingsymbol','instrument_type','strike',"expiry"]]
        current_week_fno_instruments_df = all_data[all_data['expiry'] == current_week.strftime('%Y-%m-%d')]

        master_df = pd.concat([current_week_fno_instruments_df,cash_instrument_df])
        instrument_list = master_df['instrument_token'].unique().tolist()
        instrument_dict = master_df.set_index('instrument_token').to_dict(orient='index')
    return instrument_list,instrument_dict


def push_tick_to_q(ticks):
    global ticks_q
    try:
        ticks_q.put(ticks)
    except:
        print("ticka_q access denied, race condition happening")

def nearest_values(number, values, count=8):
    sorted_values = sorted(values, key=lambda x: abs(x - number))
    result = sorted_values[:count]
    return result

# Function to generate timestamps from start to end at each second
def generate_timestamps(start, end):
    current = start
    while current <= end:
        yield current
        current += timedelta(seconds=1)


# websocket functions
def close_websocket(ws,h,m,s):
    import time
    while True :
        time.sleep(300)
        print(datetime.datetime.now())
        if datetime.datetime.now().time() > datetime.time(h,m,s):
            ws.close()
            break