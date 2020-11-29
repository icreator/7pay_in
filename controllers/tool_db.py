# coding: utf8

##from __future__ import print_function

if False:
    from gluon import *
    import db

    request = current.request
    response = current.response
    session = current.session
    cache = current.cache
    T = current.T

import socket

session.forget(response)

import common
# запустим сразу защиту от внешних вызов
# тут только то что на локалке TRUST_IP in private/appconfig.ini
common.not_is_local(request)


# тут только то что на локалке


# попробовать что-либо вида
def index():
    # err(1)
    return dict(message="repopulate_db")


def deals_to_tmp():
    if True:
        return 'stoppper - open me'

    db.deals_tmp.truncate('RESTART IDENTITY CASCADE')  # restart autoincrement ID

    # First deals
    db.deals_tmp.insert(
        fee_curr_id=CURR_RUB_ID, name='BUY', name2='to BUY',
        used=False, not_gifted=True,
        MIN_pay=10, MAX_pay=2777,
        fee=3, tax=0.2, fee_min=0, fee_max=0)
    db.deals_tmp.insert(
        fee_curr_id=CURR_RUB_ID, name='to COIN', name2='to COIN',
        used=False, not_gifted=True,
        MIN_pay=10, MAX_pay=2777,
        fee=3, tax=0.2, fee_min=0, fee_max=0)
    db.deals_tmp.insert(
        fee_curr_id=CURR_RUB_ID, name='WALLET', name2='to WALLET',
        used=False, not_gifted=True,
        MIN_pay=10, MAX_pay=2777,
        fee=3, tax=0.2, fee_min=0, fee_max=0)
    db.deals_tmp.insert(cat_id=1,
                        fee_curr_id=CURR_RUB_ID, name='phone +7', name2='to PHONE +7',
                        used=False, not_gifted=True,
                        MIN_pay=10, MAX_pay=2777,
                        fee=3, tax=0.2, fee_min=0, fee_max=0)
    db.deals_tmp.insert(cat_id=1,
                        fee_curr_id=CURR_USD_ID, name='phone', name2='to PHONE',
                        used=False, not_gifted=True,
                        MIN_pay=1, MAX_pay=2777,
                        fee=3, tax=0.2, fee_min=0, fee_max=0)

    for rec in db(db.deals).select():
        if rec.name == 'BUY' or rec.name == 'to COIN' or rec.name == 'WALLET' or rec.name == 'phone +7' or rec.name == 'phone':
            continue

        rec.fee_curr_id = CURR_RUB_ID
        db.deals_tmp.insert(**rec)

    return 'ok'


def deals_from_tmp():
    if True:
        return 'stoppper - open me'

    db.deals.truncate('RESTART IDENTITY CASCADE')  # restart autoincrement ID

    # if True: return 'stoppper - open me'

    for rec in db(db.deals_tmp).select():
        db.deals.insert(**rec)

    return 'ok from TMP'
