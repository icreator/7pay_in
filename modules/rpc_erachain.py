#!/usr/bin/env python
# coding: utf8

import urllib
import urllib2
#import json
from gluon.contrib import simplejson as json
import time

PASSWORD = '1'

def log(db, mess):
    print 'rpc_erachain - ', mess
    db.logs.insert(mess='YD: %s' % mess)
def log_commit(db, mess):
    log(db,mess)
    db.commit()


def rpc_request(pars, vars=None, password=None, test=None):

    if test:
        vars['test_payment'] = True
        vars['test_result'] = test

    if vars:
        vars = urllib.urlencode(vars)
        #print 'rpc VARS:', vars
        rq = urllib2.Request(pars, vars)
    else:
        rq = urllib2.Request(pars)

    ##rq.add_header('Authorization', 'Bearer ' + token)
    #return rq
        # платеж в процессе - ожидаем и потом еще раз запросим
    try:
        f = urllib2.urlopen(rq)
        #r = f.read()
        r = json.load(f)

        #print 'response - res:', r
    except Exception as e:
        from gluon import current
        # или любая ошибка - повтор запроса - там должно выдать ОК
        #print 'YmToConfirm while EXEPTION:', e
        log(current.db, 'rpc ' + pars + ' EXEPTION: %s' % e)
        return e

    #time.sleep(1)

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

    res = rpc_request(rpc_url + "/blocks/height")

    return res

def is_not_valid_addr(rpc_url, addr):
    res = rpc_request(rpc_url + "/addresses/validate/" + addr)
    return not res

    
def get_balances(rpc_url, addr):
    
    res = rpc_request(rpc_url + "/addresses/assets/" + addr)
    #res = rpc_request(rpc_url + "/addresses/balance/" + addr)
    
    return res

def get_reserve(token_system, token):
    bals = get_balances(token_system.connect_url, token_system.account)
    return bals['%d' % token.token_key][0][1]

## get transactions/unconfirmedincomes/7F9cZPE1hbzMT21g96U8E1EfMimovJyyJ7
def get_unconf_incomes(rpc_url, addr):
    recs = rpc_request(rpc_url + '/transactions/unconfirmedincomes/' + addr)
    return recs

def get_transactions(rpc_url, addr, from_block=2):
    result = []

    height = rpc_request(rpc_url + "/blocks/height")
    i = from_block
    while i < height:
        if i - from_block > 3000:
            break

        i += 1
        try:
            recs = rpc_request(rpc_url + '/transactions/incoming/' + ("%d" % i) + '/' + addr
                              + '/decrypt/%s' % PASSWORD)
        except Exception as e:
            print e
            return result
        
        if len(recs) > 0:
            print 'height: ', i
            
        result += recs
    
    return result

def send(db, curr, xcurr, addr, amo, token_system = None, token = None):
    
    if token == None:
        token = db.tokens[xcurr.as_token]
    if token_system == None:
        token_system = db.systems[token.system_id]
        
    amo = round(float(amo),8)
    
    if token.token_key == 2:
        # if it is COMPU
        txfee = round(float(token_system.txfee or 0.0001), 8)
    else:
        txfee = 0
    
    try:
        reserve = get_reserve(token_system, token)
    except Exception as e:
        return {'error': 'connection lost - [%s]' % curr.abbrev }, None
        
    if amo + txfee > reserve:
        return {'error':'out off reserve:[%s]' % reserve }, None
    
    # проверим готовность базы - is lock - и запишем за одно данные
    log_commit(db, 'try send: %s[%s] %s, fee: %s' % (amo, curr.abbrev, addr, txfee))
    if amo > txfee*2:
        #if True:
        try:
            amo_to_pay = amo - txfee
            print 'res = erachain.send(addr, amo - txfee)', amo_to_pay
            vars = { 'assetKey': token.token_key, 'feePow': 0,
                'amount': amo_to_pay, 'sender': token_system.account, 'recipient': addr,
                'password': PASSWORD}
            data = {'password': PASSWORD}
            pars = '/rec_payment/%d/%s/%d/%f/%s?password=%s' % (0, token_system.account, token.token_key, amo_to_pay, addr, PASSWORD )
            print pars, data
            res = rpc_request(token_system.connect_url + pars)
            print "SENDed? ", type(res), res
            if type(res) == type({}):
                error = res.get('error')
            else:
                return {'error': ("%s" % res) + ' [%s]' % curr.abbrev }, None

            if error:
                error_message = current.CODE_UTF and str(res['message'] + ('%s' % error)).decode(current.CODE_UTF,'replace') or str(res['message'] + ('%s' % error))
                return {'error': error_message  + ' [%s]' % curr.abbrev }, None
            
            res = res['signature']

        #else:
        except Exception as e:
            error_message = current.CODE_UTF and str(e).decode(current.CODE_UTF,'replace') or str(e)
            return {'error': error_message + ' [%s]' % curr.abbrev }, None
    else:
        # тут mess для того чтобы обнулить выход и зачесть его как 0
        res = { 'mess':'< txfee', 'error':'so_small', 'error_description': '%s < txfee %s' % (amo, txfee) }

    bal = get_reserve(token_system, token)

    return res, bal
