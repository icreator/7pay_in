#!/usr/bin/env python
# coding: utf8

import urllib
import urllib2

from gluon import current
from decimal import Decimal

#import json
from gluon.contrib import simplejson as json
import time

def log(db, mess):
    print 'rpc_ethereum_geth - ', mess
    db.logs.insert(mess='GETH: %s' % mess)
def log_commit(db, mess):
    log(db,mess)
    db.commit()

## 123
def rpc_request(rpc_url, method, params=[], test=None):

    ## curl -X POST --data '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":83}'

    if test:
        params['test_result'] = test

    headers = {'Content-Type': 'application/json'}

    # json.dumps() - ' -> "
    data = '{"method":"' + method + '", "jsonrpc": "2.0", "params":'+ ('%s' % json.dumps(params)) + ', "id":1}'
    #return data
    rq = urllib2.Request(rpc_url, data, headers=headers)

    try:
        f = urllib2.urlopen(rq)
        #r = f.read()
        r = json.load(f)

        print 'response - res:', r
    except Exception as e:
        # или любая ошибка - повтор запроса - там должно выдать ОК
        #print 'YmToConfirm while EXEPTION:', e
        log(current.db, 'rpc ' + method + (' %s' % params) + ' EXCEPTION: %s' % e)
        return '%s' % e

    return r

def get_deal_acc_addr(db, deal_id, curr_out, acc, addr, xcurr_in):
    deal_acc = db((db.deal_accs.deal_id == deal_id)
                  & (db.deal_accs.curr_id == curr_out.id)
                  & (db.deal_accs.acc == acc)).select().first()
    if not deal_acc:
        deal_acc_id = db.deal_accs.insert(deal_id = deal_id, curr_id = curr_out.id, acc = acc)
    else:
        deal_acc_id = deal_acc.id

    deal_acc_addr = db((db.deal_acc_addrs.addr==addr)
                       & (db.deal_acc_addrs.xcurr_id==xcurr_in.id)).select().first()

    if not deal_acc_addr:
        deal_acc_addrs_id = db.deal_acc_addrs.insert(deal_acc_id = deal_acc_id, addr=addr, xcurr_id=xcurr_in.id)
        deal_acc_addr = db.deal_acc_addrs[ deal_acc_addrs_id ]

    return deal_acc_id, deal_acc_addr


def get_info(rpc_url):
    res = rpc_request(rpc_url, "eth_blockNumber")
    return res

def is_not_valid_addr(rpc_url, addr):
    res = rpc_request(rpc_url + "/addresses/validate/" + addr)
    return not res


def get_balance(rpc_url, addr):
    res = rpc_request(rpc_url, "eth_getBalance", [addr, "latest"])
    try:
        return res['result']
        balance = int(res['result'], 16)
    except Exception as e:
        return res

    return balance / (10 ^ 18)

def get_reserve(rpc_url, addr):
    return get_balance(rpc_url, addr)

## get transactions/unconfirmedincomes/7F9cZPE1hbzMT21g96U8E1EfMimovJyyJ7
def get_unconf_incomes(rpc_url, addr):
    recs = rpc_request(rpc_url + '/transactions/unconfirmedincomes/' + addr)
    return recs

def get_tx_info(token_system, txid):

    recs = rpc_request(token_system.connect_url + '/transactions/signature/' + txid)
    return recs

def get_transactions(token_system, rpc_url, addr, from_block=2, conf=2):

    result = []

    height = rpc_request(rpc_url + "/blocks/height")
    try:
        height = int(height)
    except Exception as e:
        return result, None

    i = from_block

    ## TODO + confirmed HARD
    while i + conf <= height:
        if len(result) > 100 or i - from_block > 30000:
            break

        i += 1
        recs_count = 0
        url_get = rpc_url + '/transactions/incoming/' + ("%d" % i) + '/' + addr + '/decrypt/%s' % token_system.password

        try:
            recs = rpc_request(url_get)
            recs_count = len(recs)
        except Exception as e:
            print e
            print recs
            log(current.db, 'get_transactions %s EXCEPTION: %s - %s' % (url_get, e, recs))
            return result, i - 1


        if recs_count > 0:
            print 'erachain incomes - height: ', i, ' recs:', len(recs)
        else:
            continue

        incomes = []
        for rec in recs:
            #print rec
            if rec['type'] != 31:
                # only SEND transactions
                continue
            if 'actionKey' not in rec or rec['actionKey'] != 1:
                # only SEND PROPERTY action
                continue
            if 'backward' in rec:
                # skip BACKWADR
                continue
            if rec.get('title') == '.main.':
                ## skip my deposit
                continue

            incomes.append(rec)
            #print 'erachain - title:', rec.get('title'), 'message:', rec.get('message')

        result += incomes

    return result, i


def send(db, curr, xcurr, toAddr, amo, mess=None):

    rpc_url = xcurr.connect_url
    sender = xcurr.main_addr
    txfee = xcurr.txfee

    try:
        reserve = get_reserve(rpc_url, sender)
    except Exception as e:
        return {'error': 'connection lost - [%s]' % curr.abbrev}, None

    ##return dict(txfee=txfee, amo=amo, reserve=reserve)

    if amo + txfee > reserve:
        return {'error': 'out off reserve:[%s]' % reserve}, None

    # проверим готовность базы - is lock - и запишем за одно данные
    log_commit(db, 'try send: %s[%s] %s, fee: %s' % (amo, curr.abbrev, toAddr, txfee))
    if amo > txfee * 2:
        try:
            ##amo_to_pay = amo - txfee - it already inserted in GET_RATE by db.currs
            amo_to_pay = amo # - txfee
            print 'res = geth.send(addr, amo - txfee)', amo_to_pay

            txfee = long(xcurr.txfee * Decimal(1E8)) ## and x 1+E10 by gasPrice
            amo_to_pay = long(amo_to_pay * Decimal(1E18)) ## in WEI

            params = [{
                "from": sender,
                "to": toAddr,
                "value": '%#x' % amo_to_pay,
                #"data": "0x1234",
                "gas": '%#x' % txfee,
                "gasPrice": '%#x' % 1E10
            }]
            print params
            res = rpc_request(rpc_url, "eth_sendTransaction", params)
            try:
                res = res['result']
            except Exception as e:
                return res, None

            if res == "0x0":
                # some error
                return {'error': ("%s" % res) + ' [%s]' % curr.abbrev }, None


        except Exception as e:
            error_message = current.CODE_UTF and str(e).decode(current.CODE_UTF,'replace') or str(e)
            return {'error': error_message + ' [%s]' % curr.abbrev }, None
    else:
        # тут mess для того чтобы обнулить выход и зачесть его как 0
        res = { 'mess':'< txfee', 'error':'so_small', 'error_description': '%s < txfee %s' % (amo, txfee) }

    bal = get_reserve(rpc_url, sender)

    return res, bal
