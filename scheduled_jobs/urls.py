from django.urls import path, re_path
from django.contrib.sitemaps.views import sitemap
from login.functions import *
import pandas as pd
from login.models import *
from datetime import datetime
import pytz
import sys
from pathlib import Path
import threading
BASE_DIR = Path(__file__).resolve().parent.parent



from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from django_apscheduler.jobstores import DjangoJobStore, register_job
from django.conf import settings


job_defaults = {
    'coalesce': False,
    'max_instances': 1,
    'misfire_grace_time':None
}
executors = {
    'default': ThreadPoolExecutor(200),
    'processpool': ProcessPoolExecutor(1)
}
scheduler = BackgroundScheduler()#job_defaults=job_defaults, executors=executors, timezone="Asia/Kolkata")
scheduler.add_jobstore(DjangoJobStore(), "default")

urlpatterns = [
]

class Killable_Thread(threading.Thread):
  """A subclass of threading.Thread, with a kill()
method."""
  def __init__(self, *args, **keywords):
    threading.Thread.__init__(self, *args, **keywords)
    self.killed = False

  def start(self):
    """Start the thread."""
    self.__run_backup = self.run
    self.run = self.__run
    threading.Thread.start(self)

  def __run(self):
    """Hacked run function, which installs the
trace."""
    sys.settrace(self.globaltrace)
    self.__run_backup()
    self.run = self.__run_backup

  def globaltrace(self, frame, why, arg):
    if why == 'call':
      return self.localtrace
    else:
      return None

  def localtrace(self, frame, why, arg):
    if self.killed:
      if why == 'line':
        raise SystemExit()
    return self.localtrace

  def kill(self):
    self.killed = True
def thread_killable(func, args_list):
    thr = Killable_Thread(target=func, args=args_list)
    thr.daemon = True
    thr.start()

@register_job(scheduler,'cron', hour=8, minute=25,id='Login_alice',replace_existing=True)
def generateTokenTable_alice():
    from time import sleep
    aliceobjects = AngelTable.objects.filter(Broker__Name="Alice Blue")
    for obj in aliceobjects:
        single_login_alice_v2(str(obj.UserID),str(obj.Password),str(obj.mpin),str(obj.Comment),str(obj.AppID),str(obj.APISecret))
        send_alert(f'Login Triggered for {obj.UserID}')
        # try:
        #     # single_login_alice_v2(row["UserID"], row["Password"], row["mpin"], row["Comment"], env('API_CODE_ALICE'))
        #     login_alice_v2(obj.UserID,obj.Password,obj.mpin,obj.Comment,obj.AppID,obj.APISecret)
        #     print(obj.UserID)
        # except:
        #     print('failed for ',obj.UserID)
        #     pass
        #     sleep(10)

@register_job(scheduler,'cron', hour=8, minute=32,id='Login_angel',replace_existing=True)
def generateTokenTable_angel():
    from time import sleep
    angelobjects = AngelTable.objects.filter(Broker__Name="Angel")
    for obj in angelobjects:
        try:
            # angel_single_login(row["UserID"], row["Password"], row["AppID"], row["Comment"])
            login_angel(obj.UserID,obj.Password,obj.AppID,obj.Comment)
            print(obj.UserID)
        except:
            pass
        sleep(10)

# @register_job(scheduler,'cron', hour=8, minute=27,id='generateTokenTable_finvasia',replace_existing=True)
# def generateTokenTable_finvasia():
#     import pandas as pd
#     import psycopg2
#     from time import sleep
#     con = psycopg2.connect(database=env('DB_NAME'), user=env('DB_USER'), password=env('DB_PASSWORD'), host=env('DB_HOST'), port=env('DB_PORT'))
#     df = pd.read_sql_query('SELECT * FROM todolist_angeltable where "Broker_id" = 5;', con)
#     con.close()
#     lot = 40
#     df_list = []
#     start = 0
#     end = start + lot
#     while end < len(df):
#         df_list.append(df.iloc[start:end])
#         start = end
#         end = start + lot
#     df_list.append(df.iloc[start:])
#     for df_item in df_list:
#         for i, row in df_item.iterrows():
#             print(f'{i} - {row["UserID"]}')
#             try:
#                 # login_finvasia(row["UserID"], row["Password"], row["Comment"], row["APISecret"], row["AppID"], row["mpin"])
#                 thread_killable(func=login_finvasia, args_list=[row["UserID"], row["Password"], row["Comment"], row["APISecret"], row["AppID"], row["mpin"]])
#                 print(row["UserID"])
#             except:
#                 print("exception at - ", row["UserID"])
#                 pass
#         sleep(10)
#     msg = f"Finvasia Login Started for {len(df)} users at - {datetime.now().astimezone(pytz.timezone('Asia/Kolkata')).strftime('%d %b %Y %I:%M:%S.%f %p')}"
#     send_to_telegram(msg)

@register_job(scheduler,'cron', hour=8, minute=15,id='Login_zerodha',replace_existing=True)
def generateTokenTable_zerodha():
    from time import sleep
    zerodhaobjects = AngelTable.objects.filter(Broker__Name="Zerodha")
    for obj in zerodhaobjects:
        try:
            login_zerodha(obj.AppID,obj.APISecret,obj.UserID,obj.Password,obj.Comment)
            # thread_killable(func=master_login_zerodha, args_list=[row['UserID'], row['Password'], row['Comment'], row["AppID"]])
            print(obj.UserID)
        except:
            print("exception at - ", obj.UserID)
            pass
        sleep(10)


import subprocess
def restart_system():
    try:
        # Use the subprocess module to run the command with 'sudo'
        subprocess.run(['sudo', 'reboot'], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
    except OSError as e:
        print(f"Error executing the command: {e}")

# Call the function to restart the system
@register_job(scheduler,'cron', hour=0, minute=0, id='system_restart',replace_existing=True)
def system_restart():
    restart_system()

from strategy.strategy import *
@register_job(scheduler,'cron', hour=9, minute=0,id='Run Strategy',replace_existing=True)
def StrategyStart():
    Strategy_Main()

from nse_feed.kite_tick_feed import *
@register_job(scheduler,'cron', hour=8, minute=50,id='Data Feed',replace_existing=True)
def data_feed():
    master_data_feed()

scheduler.start()
print("Scheduler started!")