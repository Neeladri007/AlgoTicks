import pandas as pd
from datetime import date
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
        "BANKEX":'BSE INDEX BANKEX',
        'SENSEX':'SENSEX'
    }
    new_names_list = [name_mapping.get(name, name) for name in names_list]

    return new_names_list


def get_fno_cash_instrument_tokens_list_and_dict():
    new_names_list = get_fno_tradingsymbols()
    all_data = df.loc[(df['exchange'] == 'NSE') & (df['tradingsymbol'].isin(new_names_list))][['name','instrument_token', 'exchange_token', 'tradingsymbol','instrument_type','strike',"expiry"]]
    output_list = all_data['instrument_token'].unique().tolist()
    instrument_dict = all_data.set_index('instrument_token').to_dict(orient='index')

    new_names_list = get_fno_tradingsymbols('BFO')
    new_names_list.remove('SENSEX50')
    all_data = df.loc[(df['exchange'] == 'BSE') & (df['tradingsymbol'].isin(new_names_list))][['name','instrument_token', 'exchange_token', 'tradingsymbol','instrument_type','strike',"expiry"]]
    output_list2 = all_data['instrument_token'].unique().tolist()
    instrument_dict2 = all_data.set_index('instrument_token').to_dict(orient='index')
    instrument_dict.update(instrument_dict2)

    return output_list+output_list2,instrument_dict

def get_options_min_diff(symbol:str,exchange:str='NFO'):
    if symbol == 'NIFTY 50':
        symbol = 'NIFTY'
    if symbol == "NIFTY BANK":
        symbol = 'BANKNIFTY'
    if symbol == "NIFTY FIN SERVICE":
        symbol = 'FINNIFTY'
    if symbol == "BSE INDEX BANKEX":
        symbol = 'BANKEX'

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

        all_options = df.loc[(df['exchange'] == exchange) & (df["segment"] == f"{exchange}-OPT") & (df['name'] == symbol)][['name','instrument_token', 'exchange_token', 'tradingsymbol','instrument_type','strike',"expiry"]].dropna()

        all_options['expiry'] = pd.to_datetime(all_options['expiry'])
        expiries = sorted(all_options['expiry'].dt.strftime('%Y-%m-%d').unique().tolist())
        expiries_datetime = pd.to_datetime(expiries, unit='ns')
        current_year, current_month = date.today().year, date.today().month
        next_month = (current_month % 12) + 1  # To handle December
        next_to_next_month = (current_month % 12) + 2
        current_month_dates = [d for d in expiries_datetime if d.year == current_year and d.month == current_month]
        next_month_dates = [d for d in expiries_datetime if (d.month == next_month and d.year == current_year) or (d.month == 1 and d.year == current_year + 1)]
        next_to_next_month_dates = [d for d in expiries_datetime if (d.month == next_to_next_month and d.year == current_year) or (d.month == 2 and d.year == current_year + 1)]
        if len(current_month_dates)!=0:
            max_current_month = max(current_month_dates)
            max_next_month = max(next_month_dates)
        else:
            max_current_month = max(next_month_dates)
            max_next_month = max(next_to_next_month_dates)

        output_dict = {'current_week':expiries[0],'next_week':expiries[1],'current_month':max_current_month.strftime('%Y-%m-%d'),'next_month':max_next_month.strftime('%Y-%m-%d')}
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
        
        all_options = df.loc[(df['exchange'] == exchange) & (df["segment"] == f"{exchange}-FUT") & (df['name'] == symbol)][['name','instrument_token', 'exchange_token', 'tradingsymbol','instrument_type','strike',"expiry"]].dropna()
        all_options['expiry'] = pd.to_datetime(all_options['expiry'])
        expiries = sorted(all_options['expiry'].dt.strftime('%Y-%m-%d').unique().tolist())
        expiries_datetime = pd.to_datetime(expiries, unit='ns')
        current_year, current_month = date.today().year, date.today().month
        next_month = (current_month % 12) + 1  # To handle December
        next_to_next_month = (current_month % 12) + 2
        current_month_dates = [d for d in expiries_datetime if d.year == current_year and d.month == current_month]
        next_month_dates = [d for d in expiries_datetime if (d.month == next_month and d.year == current_year) or (d.month == 1 and d.year == current_year + 1)]
        next_to_next_month_dates = [d for d in expiries_datetime if (d.month == next_to_next_month and d.year == current_year) or (d.month == 2 and d.year == current_year + 1)]
        if len(current_month_dates)!=0:
            max_current_month = max(current_month_dates)
            max_next_month = max(next_month_dates)
        else:
            max_current_month = max(next_month_dates)
            max_next_month = max(next_to_next_month_dates)

        output_dict = {'current_week':expiries[0],'next_week':expiries[1],'current_month':max_current_month.strftime('%Y-%m-%d'),'next_month':max_next_month.strftime('%Y-%m-%d')}
    except:
        output_dict = {'current_week':None,'next_week':None,'current_month':None,'next_month':None}
        
    return output_dict


