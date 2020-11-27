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

##
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

def get_height(rpc_url):
    res = rpc_request(rpc_url, "eth_blockNumber")
    return int(res['result'], 16)

def is_not_valid_addr(rpc_url, addr):
    res = rpc_request(rpc_url, "eth_getBalance", [addr, "latest"])
    try:
        return res['error'] != None
    except Exception as e:
        return False


def get_balance(rpc_url, addr):
    res = rpc_request(rpc_url, "eth_getBalance", [addr, "latest"])
    try:
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


def get_tx_info(rpc_url, txid):
    res = rpc_request(rpc_url, "eth_getTransactionReceipt", [txid])
    return res


def get_block(rpc_url, block):

    try:
        res = rpc_request(rpc_url, "eth_getBlockByNumber", ['int' == type(block) and ('%#x' % block) or block, True])
        return res
    except Exception as e:
        print e
        log(current.db, 'get_transactions %s EXCEPTION: %s' % (rpc_url, e))
        return "%s" % e


# for precess incomes in serv_block_proc
def parse_tx_fields(rec, block):
    rec['amount'] = Decimal(rec['volume'][2:].decode('hex')) * Decimal('1-E18')
    rec['message'] = rec['input'][2:].decode('hex')
    rec['creator'] = rec['from']
    rec['txid'] = rec['hash']
    rec['timestamp'] = block['timestamp'][2:].decode('hex')
    rec['block'] = block['number'][2:].decode('hex')


def get_transactions(xcurr, from_block=2):

    rpc_url = xcurr.connect_url
    conf = xcurr.conf
    addr = xcurr.main_addr

    result = []

    res = rpc_request(rpc_url, "eth_blockNumber")
    try:
        height = int(res['result'], 16)
    except Exception as e:
        return result, None

    i = from_block

    ## TODO + confirmed HARD
    while i + conf <= height:
        if len(result) > 100 or i - from_block > 30000:
            break

        i += 1
        recs_count = 0

        try:
            res = rpc_request(rpc_url, "eth_getBlockByNumber", ['%#x' % from_block, True])
            recs = res['result']['transactions']
            recs_count = len(recs)
        except Exception as e:
            print e
            print res
            log(current.db, 'get_transactions %s EXCEPTION: %s - %s' % (rpc_url, e, res))
            return result, i - 1


        if recs_count > 0:
            print 'geth incomes - height: ', i, ' recs:', len(recs)
        else:
            continue

        incomes = []
        for rec in recs:
            if rec['status'] != '0x1' or not rec['to'] or not rec['value'] or not rec['input'] or not rec['from'] or rec['to'] != addr:
                continue

            rec['timestamp'] = res['timestamp]'][2:].decode('hex')
            rec['confirmations'] = height - i

            incomes.append(rec)
            print 'geth: ', rec

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
                "data": '0x' + (u'ETH stablecoin from erachain.org'.encode("hex")),
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
