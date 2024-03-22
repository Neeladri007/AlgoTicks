from kiteconnect import KiteConnect
from telegram.tgfunctions import send_alert
import math
from pprint import pprint as p
import pandas as pd
import datetime
import time
from .models import *
from login.functions import *
import threading
import logging
import datetime

# logging.basicConfig(level=logging.DEBUG)
logging.basicConfig()

def round_nearest(x):
    return round(round(x / 0.05) * 0.05, -int(math.floor(math.log10(0.05))))

def fno_buy_market_zerodha(kite_object:KiteConnect,tradingsymbol:str,quantity_:int):
    kite = kite_object
    try:
        orderid = kite_object.place_order(tradingsymbol=tradingsymbol,
                                    exchange=kite.EXCHANGE_NFO,
                                    transaction_type=kite.TRANSACTION_TYPE_BUY,
                                    quantity=quantity_,
                                    variety=kite.VARIETY_REGULAR,
                                    order_type=kite.ORDER_TYPE_MARKET,
                                    product=kite.PRODUCT_MIS,
                                    validity=kite.VALIDITY_DAY)
    except:
        orderid = None

    return orderid

def fno_sell_market_zerodha(kite_object:KiteConnect,tradingsymbol:str,quantity_:int):
    kite = kite_object
    orderid = kite_object.place_order(tradingsymbol=tradingsymbol,
                                exchange=kite.EXCHANGE_NFO,
                                transaction_type=kite.TRANSACTION_TYPE_SELL,
                                quantity=quantity_,
                                variety=kite.VARIETY_REGULAR,
                                order_type=kite.ORDER_TYPE_MARKET,
                                product=kite.PRODUCT_MIS,
                                validity=kite.VALIDITY_DAY)

def fno_long_sl_order(kite_object:KiteConnect,tradingsymbol:str,quantity_:int,price_:int):
    kite = kite_object
    try:
        orderid = kite_object.place_order(tradingsymbol=tradingsymbol,
                                exchange=kite.EXCHANGE_NFO,
                                transaction_type=kite.TRANSACTION_TYPE_SELL,
                                quantity=quantity_,
                                variety=kite.VARIETY_REGULAR,
                                order_type=kite.ORDER_TYPE_SL,
                                product=kite.PRODUCT_MIS,
                                price=price_,
                                trigger_price=price_,
                                validity=kite.VALIDITY_DAY)
        send_alert(f'Zerodha: {datetime.datetime.now()} Stop Loss order SUCCESS for {tradingsymbol} @ {price_}')

    except Exception as e:
        text = (f'Zerodha: {datetime.datetime.now().time()} \n Stop Loss order FAILED for {tradingsymbol}\n Reason: {e}')
        final_msg = text#.split('[Read')[0]
        send_alert(final_msg)
        fno_sell_market_zerodha(kite_object,tradingsymbol,quantity_)
        send_alert(f'Zerodha: {datetime.datetime.now().time()} Market order as ltp is less than trigger price for {tradingsymbol}')
    
def fno_long_tp_order(kite_object:KiteConnect,tradingsymbol:str,quantity_:int,price_:int):
    kite = kite_object
    response = (kite.quote(f'NFO:{tradingsymbol}'))
    uc,lc = response[f'NFO:{tradingsymbol}']['upper_circuit_limit'],response[f'NFO:{tradingsymbol}']['lower_circuit_limit']
    if price_ > uc :
        price_ = uc - 0.05
    orderid = kite_object.place_order(tradingsymbol=tradingsymbol,
                                exchange=kite.EXCHANGE_NFO,
                                transaction_type=kite.TRANSACTION_TYPE_SELL,
                                quantity=quantity_,
                                variety=kite.VARIETY_REGULAR,
                                order_type=kite.ORDER_TYPE_LIMIT,
                                product=kite.PRODUCT_MIS,
                                price=price_,
                                validity=kite.VALIDITY_DAY)
    
def fno_short_sl_order(kite_object:KiteConnect,tradingsymbol:str,quantity_:int,price_:int):
    kite = kite_object
    try:
        orderid = kite_object.place_order(tradingsymbol=tradingsymbol,
                                exchange=kite.EXCHANGE_NFO,
                                transaction_type=kite.TRANSACTION_TYPE_BUY,
                                quantity=quantity_,
                                variety=kite.VARIETY_REGULAR,
                                order_type=kite.ORDER_TYPE_SL,
                                product=kite.PRODUCT_MIS,
                                price=price_,
                                trigger_price=price_,
                                validity=kite.VALIDITY_DAY)
        import datetime
        send_alert(f'Zerodha: {datetime.datetime.now().time()} long trigger order SUCCESS for {tradingsymbol}')

    except Exception as e:
        import datetime
        text = (f'Zerodha: {datetime.datetime.now().time()} \n long trigger order FAILED for {tradingsymbol}\n Reason: {e}')
        final_msg = text#.split('[Read')[0]
        send_alert(final_msg)
        orderid = fno_buy_market_zerodha(kite_object,tradingsymbol,quantity_)
        send_alert(f'Zerodha: {datetime.datetime.now().time()} Market order as ltp is greater than trigger price for {tradingsymbol}')
    
    return orderid

def fno_short_tp_order(kite_object:KiteConnect,tradingsymbol:str,quantity_:int,price_:int):
    kite = kite_object
    response = (kite.quote(f'NSE:{tradingsymbol}'))
    uc,lc = response[f'NSE:{tradingsymbol}']['upper_circuit_limit'],response[f'NSE:{tradingsymbol}']['lower_circuit_limit']
    if price_ < lc :
        price_ = lc + 0.05
    
    orderid = kite_object.place_order(tradingsymbol=tradingsymbol,
                                exchange=kite.EXCHANGE_NFO,
                                transaction_type=kite.TRANSACTION_TYPE_BUY,
                                quantity=quantity_,
                                variety=kite.VARIETY_REGULAR,
                                order_type=kite.ORDER_TYPE_LIMIT,
                                product=kite.PRODUCT_MIS,
                                price=price_,
                                validity=kite.VALIDITY_DAY)

def modify_order_quantity(object,orderid,new_quantity):
    new_order_id = object.modify_order(
        variety=object.VARIETY_REGULAR,
        order_id = orderid,
        quantity = new_quantity)

def modify_sl_order_price(object,orderid,new_price):
    new_order_id = object.modify_order(
        variety=object.VARIETY_REGULAR,
        order_id = orderid,
        trigger_price = new_price,
        price = new_price)



# Position Management


# def order_management_zerodha():
#     user = UserTable.objects.filter(Broker__BrokerName='Zerodha').first()
#     object = pickle_object_read('zerodha_objects',user.BrokerID)
#     # main try exception loop to get strategy specifications from the database
#     try:
#         strategy_specs = Specifications.objects.get(StrategyName='s1')
#         max_trades = float(str(strategy_specs.MaxTrades).replace(",",""))
#         max_profit_trades = float(str(strategy_specs.MaxProfitTrades).replace(",",""))
#         tp_percentage = float(str(strategy_specs.TakeProfit).replace(",",""))
#         sl_percentage = float(str(strategy_specs.StopLoss).replace(",",""))
#         tsl_jump = float(str(strategy_specs.TSL_Step).replace(",",""))
#         exit = strategy_specs.Exit_Time
#     except:
#         max_trades = 3
#         max_profit_trades = 1
#         tp_percentage = 3
#         sl_percentage = 10
#         tsl_jump = .4
#         exit = '15:08:59'

#     conf_dict = {'max_trades':max_trades,
#                  'max_profit_trades':max_profit_trades,
#                  'tp_percentage':tp_percentage,
#                  'sl_percentage':sl_percentage,
#                  'tsl_jump':tsl_jump,
#                  'exit':exit
#                  }

#     # Variable Decalration
#     order_ids = []
#     start,end = '09:15:00','15:29:59'
#     rejected_status_send_dict = dict()
#     check_frequency = 1

#     import datetime
#     # starting the mail while loop to check at a certain frequency
#     while datetime.datetime.now().strftime("%H:%M:%S") < end and datetime.datetime.now().strftime("%H:%M:%S") > start:
#         print(datetime.datetime.now().strftime("%H:%M:%S"))

#         # first try except to fetch orderbook_kite and positions
#         try:
#             orderbook_kite = pd.DataFrame(object.orders())
#             # orderbook_kite.to_csv('obb.csv')
#             # positionbook = pd.DataFrame((object.positions())['net'])

#             # orderbook_kite columns - placed_by	order_id	exchange_order_id	parent_order_id	status	status_message	status_message_raw	order_timestamp	exchange_update_timestamp	exchange_timestamp	variety	modified	exchange	tradingsymbol	instrument_token	order_type	transaction_type	validity	validity_ttl	product	quantity	disclosed_quantity	price	trigger_price	average_price	filled_quantity	pending_quantity	cancelled_quantity	market_protection	meta	tag	guid
#             # positionbook columns - tradingsymbol	exchange	instrument_token	product	quantity	overnight_quantity	multiplier	average_price	close_price	last_price	value	pnl_kite	m2m	unrealised	realised	buy_quantity	buy_price	buy_value	buy_m2m	sell_quantity	sell_price	sell_value	sell_m2m	day_buy_quantity	day_buy_price	day_buy_value	day_sell_quantity	day_sell_price	day_sell_value
            
#             # grouping by the symbol and running parallely
#             try:
#                 groups_kite = orderbook_kite.groupby("tradingsymbol")
#                 for name_kite,group in groups_kite:
#                     # calculating net position from orderbook_kite
#                     net_positon_quantity = orderbook_kite[(orderbook_kite['transaction_type'] == 'BUY') & (orderbook_kite['tradingsymbol'] == name_kite) ]['filled_quantity'].sum() - orderbook_kite[(orderbook_kite['transaction_type'] == 'SELL') & (orderbook_kite['tradingsymbol'] == name_kite)]['filled_quantity'].sum()
#                     print(f'{name_kite}:{net_positon_quantity}')
#                     # if there were no previous position i.e it is the first entry then it will throw an error
#                     # try:
#                     #     net_positon_quantity = ((positionbook[positionbook["tradingsymbol"]==name_kite]["buy_quantity"]- positionbook[positionbook["tradingsymbol"]==name_kite]["sell_quantity"]).values)[0]
#                     # except:
#                     #     net_positon_quantity = 0
#                     # print(f'{name_kite}:{net_positon_quantity}')
#                     if name_kite.startswith("NSE:"):
#                         # Remove "NSE:" from the beginning of the string
#                         name_kite = name_kite[len("NSE:"):]
#                     try:
#                         # manage_stock(object,name_kite,group,net_positon_quantity,conf_dict)
#                         threading.Thread(target = manage_stock, args = (object,name_kite,group,net_positon_quantity,conf_dict)).start()
#                     except:
#                         pass
#             except:
#                 print("Exception Loop 1")
#                 pass
#             time.sleep(check_frequency)
#         except:
#             print("Failed to fetch orderbook_kite")
#             time.sleep(1)
#             pass

# def manage_stock(object,name_kite,group,net_positon_quantity,conf_dict): 

#     # getting trigger pending order(s) details
#     trigger_pending_count_kite = len(group[group['status']=="TRIGGER PENDING"])
#     if trigger_pending_count_kite > 0:
#         trigger_pending_qty_kite = ((group[group['status']=="TRIGGER PENDING"]['quantity'].values)[0])
#         trigger_pending_ids_kite = list(group[group['status']=="TRIGGER PENDING"]['order_id'].values)
#         trigger_pending_sides_kite = list(group[group['status']=="TRIGGER PENDING"]['transaction_type'].values)
#         last_trigger_order_time_kite = pd.Timestamp((group[group['order_id']==trigger_pending_ids_kite[0]]['order_timestamp']).values[0])
#     else:
#         trigger_pending_qty_kite = 0
#         trigger_pending_ids_kite = ["No trigger Pending order"]
#         trigger_pending_sides_kite = []
#         last_trigger_order_time_kite = datetime.datetime(year = 2023, month = 1, day = 1,hour=9,minute=1,second=1)
    
#     # getting open order(s) deatisl
#     open_count_kite = len(group[group['status']=="OPEN"])
#     if open_count_kite > 0:
#         open_qty_kite = ((group[group['status']=="OPEN"]['quantity'].values)[0])
#         open_ids_kite = list(group[group['status']=="OPEN"]['order_id'].values)
#         open_ids_kite_sides = list(group[group['status']=="OPEN"]['transaction_type'].values)
#     else:
#         open_qty_kite = 0
#         open_ids_kite = ["No open order"]
#         open_ids_kite_sides = []


#     print(f"{name_kite}:[STOP LOSS---{trigger_pending_ids_kite}-{trigger_pending_count_kite}-{trigger_pending_sides_kite}:{trigger_pending_ids_kite}]")
    
#     # ######################################################### ----------- 

#     # creating a list of all non executed ids
#     all_non_executed_ids = trigger_pending_ids_kite

#     # check if there id only tp and sl pending when position == 0 also be sure it is not checking intermediately 
#     # i.e: say we have to place two trigger orders and one trigger is placed and then on there it started checking for the open positions
#     tp_sl_left_alone = False
#     total_orders = len(group)

#     try:
#         if net_positon_quantity == 0 and max(trigger_pending_count_kite) == 1 and total_orders > 1:
#             tp_sl_left_alone = True
#     except:
#         pass
    
#     # canceling all orders if there is any rejected order /////// or if there is no position left ///// or sl or tp hit
#     if tp_sl_left_alone:
#         for orderid in all_non_executed_ids:
#             try:
#                 object.cancel_order(object.VARIETY_REGULAR,orderid)
#                 send_alert(f'Zerodha : {name_kite}:open order cancled (order id:{orderid})')
#                 send_alert(f'{name_kite} : Reason: TP SL L A -{tp_sl_left_alone}, tc - {trigger_pending_count_kite}')
#             except:
#                 pass
    
#     #  code for intraday exit
#     if (datetime.datetime.now().time() >= datetime.time(9,28,00)) and (datetime.datetime.now().time() <= datetime.time(9,28,10)):
#         if net_positon_quantity == 0 and trigger_pending_qty_kite != 0:
#             for orderid in all_non_executed_ids:
#                 try:
#                     object.cancel_order(object.VARIETY_REGULAR,orderid)
#                     send_alert(f'{name_kite}:open order cancled (order id:{orderid}) - Order not triggered till 9:27 am')
#                 except:
#                     send_alert(f'ERROR : FAILED : {name_kite}:open order cancled (order id:{orderid}) - Order not triggered till 9:27 am')
#                     pass



#     #  code for intraday exit
#     if (datetime.datetime.now().time() > datetime.time(15,8,59)):
#         for orderid in all_non_executed_ids:
#             try:
#                 object.cancel_order(object.VARIETY_REGULAR,orderid)
#                 send_alert(f'Zerodha : {name_kite}:open order cancled (order id:{orderid})')
#                 send_alert(f'{name_kite} : Reason: TP SL L A -{tp_sl_left_alone}, tc - {trigger_pending_count_kite}')
#             except:
#                 pass
#         if net_positon_quantity > 0:
#             fno_sell_market_zerodha(object,name_kite,abs(net_positon_quantity))
#             send_alert(f'{name_kite}:Existing position exited at market - Reason: Intraday Exit')

#     # ######################################################### ----------- special treantment for quantity modification
#     if net_positon_quantity != 0 and abs(net_positon_quantity) != trigger_pending_qty_kite and trigger_pending_qty_kite != 0:
#         modify_order_quantity(object,str(trigger_pending_ids_kite[0]),abs(net_positon_quantity))
#         send_alert(f'{name_kite}:Modifying SL order quantity from {trigger_pending_qty_kite} to {abs(net_positon_quantity)}')

#     # ######################################################### ------------- order management start
#     # place tp and sl ---------------- OROROROR ---------------------------- # if TP or SL got cancelled accidentally, then again place the order:
#     if (net_positon_quantity != 0 and trigger_pending_count_kite == 0 and open_qty_kite == 0 ):
#         print("placing  sl")

#         #getting the last completed price of the order 
#         last_complete_trade_price = list((group.sort_values(by = 'order_id'))[group['status']=='COMPLETE']['price'].values)[-1]

#         if last_complete_trade_price == 0:
#             last_complete_trade_price = round_nearest(list((group.sort_values(by = 'order_id'))[group['status']=='COMPLETE']['average_price'].values)[-1])

#         tp_percentage = conf_dict['tp_percentage']
#         sl_percentage = conf_dict['sl_percentage']

#         fac = net_positon_quantity/abs(net_positon_quantity)

#         tp_price = round_nearest(last_complete_trade_price  + fac * 30)
#         sl_price = round_nearest(last_complete_trade_price  - fac * 10)

#         if net_positon_quantity > 0:
#             if trigger_pending_count_kite == 0:
#                 fno_long_sl_order(object,name_kite,abs(net_positon_quantity),sl_price)
 
    
#     #  tsl function
#     if trigger_pending_count_kite == 1 and net_positon_quantity != 0:
#         print("Entered TSL Function")
#         #getting the last completed price of the order 
#         last_complete_trade_price = list((group.sort_values(by = 'order_id'))[group['status']=='COMPLETE']['price'].values)[-1]

#         if last_complete_trade_price == 0:
#             last_complete_trade_price = round_nearest(list((group.sort_values(by = 'order_id'))[group['status']=='COMPLETE']['average_price'].values)[-1])

#         trigger_pending_qty_kite = ((group[group['status']=="TRIGGER PENDING"]['quantity'].values)[0])
#         trigger_pending_ids_kite = list(group[group['status']=="TRIGGER PENDING"]['order_id'].values)
#         trigger_pending_sides_kite = list(group[group['status']=="TRIGGER PENDING"]['transaction_type'].values)
#         ltp = float((object.ltp(f'NFO:{name_kite}'))[f'NFO:{name_kite}']['last_price'])

#         #  sl is a trigger order
#         existing_sl = group[group['order_id'] == trigger_pending_ids_kite[0]]['trigger_price'].values[0]

#         # calculating new sl
#         print("Calculating new SL")
#         if net_positon_quantity > 0:
#             transactiontype = "SELL"
#             new_sl = existing_sl + (ltp-existing_sl)//10*10

#         # if the new sl is updated then modify sl
#         send_alert(f"New SL = {new_sl}, existing_sl = {existing_sl}")
#         if new_sl  >  existing_sl and new_sl != last_complete_trade_price :
#             send_alert(f"{name_kite}: Updating TSL to {new_sl}")
#             modify_sl_order_price(object,trigger_pending_ids_kite[0],new_sl)

#             send_alert(f"{name_kite}: Stop Loss Modified from {transactiontype}@{existing_sl} to {transactiontype}@{new_sl}")
#     print("ckeck ran successfully...")

# 3333333333333######################################3 for reference
# Constants
# Products
PRODUCT_MIS = "MIS"
PRODUCT_CNC = "CNC"
PRODUCT_NRML = "NRML"
PRODUCT_CO = "CO"

# Order types
ORDER_TYPE_MARKET = "MARKET"
ORDER_TYPE_LIMIT = "LIMIT"
ORDER_TYPE_SLM = "SL-M"
ORDER_TYPE_SL = "SL"

# Varities
VARIETY_REGULAR = "regular"
VARIETY_CO = "co"
VARIETY_AMO = "amo"
VARIETY_ICEBERG = "iceberg"
VARIETY_AUCTION = "auction"

# Transaction type
TRANSACTION_TYPE_BUY = "BUY"
TRANSACTION_TYPE_SELL = "SELL"

# Validity
VALIDITY_DAY = "DAY"
VALIDITY_IOC = "IOC"
VALIDITY_TTL = "TTL"

# Position Type
POSITION_TYPE_DAY = "day"
POSITION_TYPE_OVERNIGHT = "overnight"

# Exchanges
EXCHANGE_NSE = "NSE"
EXCHANGE_BSE = "BSE"
EXCHANGE_NFO = "NFO"
EXCHANGE_CDS = "CDS"
EXCHANGE_BFO = "BFO"
EXCHANGE_MCX = "MCX"
EXCHANGE_BCD = "BCD"

# Margins segments
MARGIN_EQUITY = "equity"
MARGIN_COMMODITY = "commodity"

# Status constants
STATUS_COMPLETE = "COMPLETE"
STATUS_REJECTED = "REJECTED"
STATUS_CANCELLED = "CANCELLED"