# coding: utf8

if False:
    from gluon import *
    import db

    request = current.request
    response = current.response
    session = current.session
    cache = current.cache
    T = current.T

import rates_lib
import datetime

session.forget(response)

import common
# запустим сразу защиту от внешних вызов
# тут только то что на локалке TRUST_IP in private/appconfig.ini
common.not_is_local(request)

def index():
    return dict(message="use CRON for this controller")

# take external rates for cron
def get_ext_rates():
    import serv_rates
    serv_rates.get(db, 'True', -1)

def proc_history():
    import serv_to_buy
    return serv_to_buy.proc_history(db, only_list=None, ed_acc=None, from_dt_in='same')
