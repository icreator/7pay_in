#!/usr/bin/env python
# coding: utf8

import urllib
import urllib2
from gluon import current
from gluon.contrib import simplejson as json
from decimal import Decimal
import time

import db_common


def log(db, mess):
    print 'rpc_erachain - ', mess
    db.logs.insert(mess='YD: %s' % mess)


def log_commit(db, mess):
    log(db, mess)
    db.commit()


def rpc_request(pars, vars=None, test=None):
    if test:
        vars['test_payment'] = True
        vars['test_result'] = test

    if vars:
        vars = urllib.urlencode(vars)
        # print 'rpc VARS:', vars
        rq = urllib2.Request(pars + '?' + vars)
    else:
        rq = urllib2.Request(pars)

    ##rq.add_header('Authorization', 'Bearer ' + token)
    # return rq
    # платеж в процессе - ожидаем и потом еще раз запросим
    try:
        f = urllib2.urlopen(rq)
        # r = f.read()
        r = json.load(f)

        # print 'response - res:', r
    except Exception as e:
        # или любая ошибка - повтор запроса - там должно выдать ОК
        # print 'YmToConfirm while EXEPTION:', e
        log(current.db, 'rpc ' + pars + ' EXCEPTION: %s' % e)
        return e

    # time.sleep(1)

    return r


def get_xcurr_by_system_token(db, token_system, token_key):
    try:
        token_key = int(token_key)  # ASSET KEY in Erachain
    except Exception as e:
        curr_out, xcurr, _ = db_common.get_currs_by_abbrev(db, token_key)
        return xcurr

    token = db((db.tokens.system_id == token_system.id)
               & (db.tokens.token_key == token_key)).select().first()
    if not token:
        return

    return db(db.xcurrs.as_token == token.id).select().first()


def get_addresses(token_system):
    return rpc_request(token_system.connect_url + "/addresses?password=" + token_system.password)


def get_height(rpc_url):
    return rpc_request(rpc_url + "/blocks/height")


def is_not_valid_addr(rpc_url, address):
    res = rpc_request(rpc_url + "/addresses/validate/" + address)
    return not res


# all tokens for account
def get_assets_balances(token_system, address=None):
    return rpc_request(token_system.connect_url + "/addresses/assets/" + (address or token_system.account))


# one token
def get_balance(token_system, token, address=None):
    try:
        bals = get_assets_balances(token_system, address)
        return bals['%d' % token.token_key][0][1]
    except:
        return bals



    ## get transactions/unconfirmedincomes/7F9cZPE1hbzMT21g96U8E1EfMimovJyyJ7
def get_unconf_incomes(rpc_url, address):
    recs = rpc_request(rpc_url + '/transactions/unconfirmedincomes/' + address)
    return recs


def get_tx_info(rpc_url, txid):
    return rpc_request(rpc_url + '/transactions/signature/' + txid)


# for precess incomes in serv_block_proc
def parse_tx_fields(rec):
    title = rec.get('title') ## may be = u''
    return dict(
        creator=rec['creator'],
        recipient=rec['recipient'],
        amount=Decimal(rec['amount']),
        asset=rec['asset'],
        message=rec.get('message', title),
        txid=rec['signature'],
        vout=0,
        block=rec['height'],
        timestamp=rec['timestamp'] / 1000, # in SEC
        confs=rec['confirmations']
    )

# 1631311
def get_transactions(token_system, from_block=2):
    rpc_url = token_system.connect_url
    addr = token_system.account

    result = []

    height = rpc_request(rpc_url + "/blocks/height")
    try:
        height = int(height)
    except Exception as e:
        return result, None

    i = from_block

    while i < height:
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

        if recs_count == 0:
            continue

        if recs.get('error'):
            print recs
            log(current.db, 'get_transactions %s ERROR: %s' % (url_get, recs))
            break

        # print 'erachain incomes - height: ', i, ' recs:', len(recs)

        incomes = []
        for rec in recs:

            if rec['type'] != 31:
                # only SEND transactions
                continue
            if 'amount' not in rec:
                # only SEND transactions
                continue
            if 'balancePos' not in rec or rec['balancePos'] != 1:
                # only SEND PROPERTY action
                continue
            if 'backward' in rec:
                # skip BACKWARD
                continue
            if rec.get('title') is '.main.':
                ## skip my deposit
                continue

            incomes.append(rec)
            # print 'erachain - title:', rec.get('title'), 'message:', rec.get('message')

        result += incomes

    return result, i


def send(db, curr, xcurr, addr, amo, token_system=None, token=None, title=None, mess=None):
    if token is None:
        token = db.tokens[xcurr.as_token]
    if token_system is None:
        token_system = db.systems[token.system_id]

    amo = round(float(amo), 8)

    if token.token_key == 2:
        # if it is COMPU
        txfee = round(float(token_system.txfee or 0.0001), 8)
    else:
        txfee = 0

    try:
        reserve = get_balance(token_system, token)
    except Exception as e:
        return {'error': 'connection lost - [%s]' % curr.abbrev}, None

    if amo + txfee > reserve:
        return {'error': 'out off reserve:[%s]' % reserve}, None

    # проверим готовность базы - is lock - и запишем за одно данные
    log_commit(db, 'try send: %s[%s] %s, fee: %s' % (amo, curr.abbrev, addr, txfee))
    if amo > txfee * 2:
        # if True:
        try:
            ##amo_to_pay = amo - txfee - it already inserted in GET_RATE by db.currs
            amo_to_pay = amo
            # print 'res = erachain.send(addr, amo - txfee)', amo_to_pay
            pars = '/rec_payment/%d/%s/%d/%f/%s?password=%s' % (
                0, token_system.account, token.token_key, amo_to_pay, addr, token_system.password)
            # print pars
            res = rpc_request(token_system.connect_url + pars)
            # print "SENDed? ", type(res), res
            if type(res) == type({}):
                error = res.get('error')
            else:
                return {'error': ("%s" % res) + ' [%s]' % curr.abbrev}, None

            if error:
                error_message = current.CODE_UTF and str(res['message'] + ('%s' % error)).decode(current.CODE_UTF,
                                                                                                 'replace') or str(
                    res['message'] + ('%s' % error))
                return {'error': error_message + ' [%s]' % curr.abbrev}, None

            res = res['signature']

        # else:
        except Exception as e:
            error_message = current.CODE_UTF and str(e).decode(current.CODE_UTF, 'replace') or str(e)
            return {'error': error_message + ' [%s]' % curr.abbrev}, None
    else:
        # тут mess для того чтобы обнулить выход и зачесть его как 0
        res = {'mess': '< txfee', 'error': 'so_small', 'error_description': '%s < txfee %s' % (amo, txfee)}

    bal = get_balance(token_system, token)

    return res, bal
