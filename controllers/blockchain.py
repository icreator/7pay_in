# coding: utf8

if False:
    from gluon import *
    request = current.request
    response = current.response
    session = current.session
    cache = current.cache
    T = current.T
    db = None

session.forget(response)

from time import sleep
#import json
#import datetime
#from decimal import Decimal

import db_common
import crypto_client

def help():
    redirect(URL('index'))

@cache.action(time_expire=300, cache_model=cache.disk) #, vars=False, public=True, lang=True)
def index():
    return dict()

def tx():
    if request.extension == 'html':
        response.view = 'blockchain/res.html'

    txid = request.args(1)
    if not txid:
        return {'error':"need txid: /tx_info.json/[curr]/[txid]"}
    curr_abbrev = request.args(0)
    import db_common
    curr,xcurr,e = db_common.get_currs_by_abbrev(db, curr_abbrev)
    if not xcurr:
        return {"error": "invalid curr:  /tx_info.json/[curr]/[txid]"}

    sleep(1)

    conn = None
    token_key = xcurr.as_token
    if token_key:
        token =  db.tokens[token_key]
        token_system = db.systems[token.system_id]
        res = dict(result=crypto_client.get_tx_info(xcurr, token_system, txid, conn))
        return res

    conn = crypto_client.connect(curr, xcurr)
    if not conn:
        return {"error": "not connected to wallet"}
    res = None

    try:
        res = conn.getrawtransaction(txid, 1)  # все выдает
    except Exception as e:
        return {'error': e}

    if 'hex' in res: res.pop('hex')
    txid = res.get('txid')
    if txid: res['txid'] = A(txid, _href=URL('tx',args=[request.args(0), txid]))
    for inp in res.get('vin',[]):
        if 'scriptSig' in inp: inp.pop('scriptSig')
        txid = inp.get('txid')
        if txid:
            inp['txid'] = A(txid, _href=URL('tx',args=[request.args(0), txid]))
        else:
            pass
        pass
    return res
