from strategy.strategy import *

# get_initial_instruments_list_and_update_live_instrument_dict()

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