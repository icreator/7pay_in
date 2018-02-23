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

def get_info(rpc_url):

    res = rpc_request(rpc_url + "/blocks/height")

    return res

def get_balances(rpc_url, addr):

    
    res = rpc_request(rpc_url + "/addresses/assets/" + addr)
    #res = rpc_request(rpc_url + "/addresses/balance/" + addr)
    
    return res

def get_transactions(rpc_url, addr, from_block=2):
    result = []

    print from_block
    height = rpc_request(rpc_url + "/blocks/height")
    i = from_block
    while i < height:
        if i - from_block > 300:
            break

        ++i
        try:
            #except Exception as e:
            recs = rpc_request(rpc_url + '/transactions/incoming/' + i + '/' + addr)
            print i
            print recs
        except Exception as e:
            return result
        
        result += recs
    
    return result
