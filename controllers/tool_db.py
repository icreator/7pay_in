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


# vvv=True - включает секртную сессию и выдает страницу ошибки
def not_is_local(vvv=None):
    http_host = request.env.http_host.split(':')[0]
    remote_addr = request.env.remote_addr
    # http_host[7pay.in] remote_addr[91.77.112.36]
    # raise HTTP(200, T('appadmin is disabled because insecure channel http_host[%s] remote_addr[%s]') % (http_host, remote_addr))
    try:
        hosts = (http_host, socket.gethostname(),
                 socket.gethostbyname(http_host),
                 '::1', '127.0.0.1', '::ffff:127.0.0.1')
    except:
        hosts = (http_host,)

    if vvv and (request.env.http_x_forwarded_for or request.is_https):
        session.secure()

    if (remote_addr not in hosts) and (remote_addr not in TRUST_IP):
        # and request.function != 'manage':
        if vvv: raise HTTP(200, T('ERROR: not admin in local'))
        return True


# запустим сразу защиту от внешних вызов
if False:
    not_is_local(True)


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
