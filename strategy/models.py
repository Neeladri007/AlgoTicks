from django.db import models

# Create your models here.
from django.db import models
import pandas as pd

INTERVAL_CHOICES = [
        ('minute', 'Minute'),
        ('day', 'Day'),
        ('3minute', '3-Minute'),
        ('5minute', '5-Minute'),
        ('10minute', '10-Minute'),
        ('15minute', '15-Minute'),
        ('30minute', '30-Minute'),
        ('60minute', '60-Minute'),
    ]
    

df = pd.read_csv('https://api.kite.trade/instruments')
options_df = df[df['tick_size'] >= 0.05]['name'].unique().tolist()
options_df = [(item,item) for item in options_df]

ins_type = df['segment'].unique().tolist()
ins_type = [(item,item) for item in ins_type]

option_sides = df['instrument_type'].unique().tolist()
option_sides = [(item,item) for item in option_sides]
EXPIRY_oPTIONS = [("current_week","Current Week"),("next_week","Next Week"),("current_month","Current Month"),("next_month","Next Month")]

Trade_status = [('A',"Scan Pending"),
                ('B','Scan Completed Instrument Finalized, waiting for trigger'),
                ('C',"Entry Sent to exchange"),
                ("D","Entry Order Executed - TP SL Placement Pending"),
                ("E","SL Placed - TP Left"),
                ("F","SL Placed - No TP Order"),
                ("G","TP Placed -SL Left"),
                ("H","TP Placed -No SL Order"),
                ("I","TP SL Both Placed"),
                ("J","TP hit - SL order pending"),
                ("K","SL hit - TP order pending"),
                ('L',"Position Exited without TP SL hit, Cancelling the orders"),
                ('M',"TP Cancelled, No Position Running, SL Yet to cancel"),
                ('N',"TP Cancelled, No Position Running, No SL Order"),
                ('O',"SL Cancelled, No Position Running, TP Yet to cancel"),
                ('P',"SL Cancelled, No Position Running, No TP Order"),
                ('Q',"Waiting to Exit Main Position in Market no TP/SL order"),
                ("R",'Trade Complete')]

ACTION_CHOICES = [('Buy','Buy'),('Sell','Sell')]

class InstrumentDetails(models.Model):
    # Fields for basic details of a trading strategy
    strategy_name = models.CharField(max_length=50,null = False,blank = False)
    start_time = models.TimeField(null = True,blank = True,default='09:15:00')
    end_time = models.TimeField(null = True,blank = True,default='15:15:00')
    instrument_name = models.CharField(max_length=50, choices=options_df)
    instrument_segment = models.CharField(max_length=100,choices=ins_type)
    instrument_type = models.CharField(max_length=10,choices=option_sides)
    instrument_token = models.CharField(max_length=20,null = True,blank = True)
    expiry = models.CharField(max_length=100,choices=EXPIRY_oPTIONS,null = True,blank = True)
    strike = models.CharField(max_length = 50,null =True,blank = True)
    interval = models.CharField(max_length=10, choices=INTERVAL_CHOICES)
    quantity = models.CharField(max_length = 50,verbose_name = "Quantiry (enter no of lots for Fut and Options)")
    transaction_side = models.CharField(max_length=10, choices=ACTION_CHOICES,default = 'Buy')
    run_monday = models.BooleanField(default=False)
    run_tuesday = models.BooleanField(default=False)
    run_wednesday = models.BooleanField(default=False)
    run_thursday = models.BooleanField(default=False)
    run_friday = models.BooleanField(default=False)
    entry_buffer = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Entry Buffer",default = 1)
    monday_nearest = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Monday Nearest Price")
    tuesday_nearest = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Tuesday Nearest Price")
    wednesday_nearest = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Wednesday Nearest Price")
    thursday_nearest = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Thursday Nearest Price")
    friday_nearest = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Friday Nearest Price")
    initial_sl = models.CharField(max_length=10,default='10',null = True,blank = True,verbose_name = "Initial SL in %" )
    last_candle_low = models.BooleanField(default=False,verbose_name = "SL Min of last candle low and initial SL?")
    target1 = models.DecimalField(max_digits=10, decimal_places=2,null = True,blank = True)
    trail1 = models.DecimalField(max_digits=10, decimal_places=2,null = True,blank = True)
    target2 = models.DecimalField(max_digits=10, decimal_places=2,null = True,blank = True)
    trail2 = models.DecimalField(max_digits=10, decimal_places=2,null = True,blank = True)
    target3 = models.DecimalField(max_digits=10, decimal_places=2,null = True,blank = True)
    trail3 = models.DecimalField(max_digits=10, decimal_places=2,null = True,blank = True)
    target4 = models.DecimalField(max_digits=10, decimal_places=2,null = True,blank = True)
    trail4 = models.DecimalField(max_digits=10, decimal_places=2,null = True,blank = True)
    target5 = models.DecimalField(max_digits=10, decimal_places=2,null = True,blank = True)
    trail5 = models.DecimalField(max_digits=10, decimal_places=2,null = True,blank = True)
    target6 = models.DecimalField(max_digits=10, decimal_places=2,null = True,blank = True)
    trail6 = models.DecimalField(max_digits=10, decimal_places=2,null = True,blank = True)
    target7 = models.DecimalField(max_digits=10, decimal_places=2,null = True,blank = True)
    trail7 = models.DecimalField(max_digits=10, decimal_places=2,null = True,blank = True)
    target8 = models.DecimalField(max_digits=10, decimal_places=2,null = True,blank = True)
    trail8 = models.DecimalField(max_digits=10, decimal_places=2,null = True,blank = True)
    target9 = models.DecimalField(max_digits=10, decimal_places=2,null = True,blank = True)
    trail9 = models.DecimalField(max_digits=10, decimal_places=2,null = True,blank = True)
    target10 = models.DecimalField(max_digits=10, decimal_places=2,null = True,blank = True)
    trail10 = models.DecimalField(max_digits=10, decimal_places=2,null = True,blank = True)
    final_trail_price  = models.DecimalField(max_digits=10, decimal_places=2,null = True,blank = True,default = 2)
    final_trail_sl  = models.DecimalField(max_digits=10, decimal_places=2,null = True,blank = True,default = 2)
    intraday_exit = models.TimeField(null = True,blank = True,default='15:15:00')
    instrument_token = models.CharField(max_length=20,null = True,blank = True)
    trigger_price = models.CharField(max_length=20,null = True,blank = True)
    limit_price = models.CharField(max_length=20,null = True,blank = True)
    entry_oid = models.CharField(max_length=20,null = True,blank = True)
    tp_price = models.CharField(max_length=20,null = True,blank = True)
    tp_oid = models.CharField(max_length=20,null = True,blank = True)
    sl_price = models.CharField(max_length=20,null = True,blank = True)
    sl_oid = models.CharField(max_length=20,null = True,blank = True)
    trade_status = models.CharField(max_length=20,choices=Trade_status,default = "1",null = True,blank = True)
    pnl = models.CharField(max_length=20,null = True,blank = True)
    max_drawdown = models.CharField(max_length=20,null = True,blank = True)
    max_profit = models.CharField(max_length=20,null = True,blank = True)

    def __str__(self):
        return f"{self.strategy_name}- {self.instrument_name}- {self.instrument_type}-{self.start_time} to {self.end_time}"

