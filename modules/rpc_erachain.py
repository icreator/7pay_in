#!/usr/bin/env python
# coding: utf8

import urllib
import urllib2
#import json
from gluon.contrib import simplejson as json
import time

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
        log(current.db, 'rpc' + pars + ' EXEPTION: %s' % e)
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

def get_transactions(rpc_url, addr, from_block=2):
    result = []

    height = rpc_request(rpc_url + "/blocks/height")
    i = from_block
    while i < height:
        if i - from_block > 3000:
            break

        i += 1
        try:
            recs = rpc_request(rpc_url + '/transactions/incoming/' + ("%d" % i) + '/' + addr)
        except Exception as e:
            print e
            return result
        
        if len(recs) > 0:
            print 'height: ', i
            
        result += recs
    
    return result
