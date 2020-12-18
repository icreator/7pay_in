# coding: utf8

if False:
    from gluon import *
    import db
    request = current.request
    response = current.response
    session = current.session
    cache = current.cache
    T = current.T

from time import sleep
import datetime
from threading import Thread

try:
    import json
except ImportError:
    from gluon.contrib import simplejson as json
from gluon.tools import fetch

Test = None

# запуск опроса бирж и получение от них цен
import exch_client
import db_common
import db_client
import serv_to_buy
import clients_lib

def log(db, mess):
    print(mess)
    db.logs.insert(mess='RATES: %s' % mess)
def log_commit(db, mess):
    log(db,mess)
    db.commit()

def get_ticker(db, exchg_id, curr_id):
    curr = db.currs[curr_id]
    if curr.used:
        limits = db_common.get_limits(db, exchg_id, curr_id)
        return limits and limits.ticker or curr.abbrev.lower()
def get_curr(db, exchg_id, ticker):
    limit = db((db.exchg_limits.exchg_id==exchg_id) & (db.exchg_limits.ticker==ticker)).select().first()
    return limit and db.currs[limit.curr_id] or db(db.currs.abbrev==ticker.upper()).select().first()

def from_livecoin(db, exchg):
    exchg_id = exchg.id
    for pair in db_common.get_exchg_pairs(db, exchg_id):
        if not pair.used: continue
        t1 = get_ticker(db, exchg_id, pair.curr1_id).upper()
        t2 = get_ticker(db, exchg_id, pair.curr2_id).upper()
        
        print(t1, t2,) # 'pair.ticker:', pair.ticker,
        if Test: continue
            
        try:
        #if True:
            '''
            https://api.livecoin.net/exchange/ticker?currencyPair=EMC/BTC
            {"last":0.00051000,"high":0.00056000,"low":0.00042690,"volume":21150.15056000,
                "vwap":0.00049384964581547641,"max_bid":0.00056000,"min_ask":0.00042690,"best_bid":0.00046000,"best_ask":0.00056960} '''
            cryp_url = 'https://' + exchg.url + '/' + exchg.API + '?currencyPair=' + t1 + '/' + t2
            print(cryp_url)
            res = fetch(cryp_url)
            ## res = {"best_bid":0.00046000,"best_ask":0.00056960}
            res = json.loads(res)
            if type(res) != dict:
                continue
            if not res.get('best_bid'): continue
            buy = float(res['best_ask'])
            sell = float(res['best_bid'])
            #return dict(buy= buy, sell= sell)
            print(sell, buy)
            db_common.store_rates(db, pair, sell, buy)
        except Exception as e:
        #else:
            msg = "serv_rates %s :: %s" % (exchg.url, e)
            print(msg)
            continue
    db.commit()

def from_poloniex(db, exchg):
    exchg_id = exchg.id
    ##PRINT_AS_FUNC and print(conn) or print conn
    for pair in db_common.get_exchg_pairs(db, exchg_id):
        if not pair.used: continue
        t1 = get_ticker(db, exchg_id, pair.curr1_id)
        t2 = get_ticker(db, exchg_id, pair.curr2_id)
        
        '''
        https://poloniex.com/public?command=returnTradeHistory&currencyPair=BTC_DOGE
    [{"globalTradeID":13711923,"tradeID":469269,"date":"2016-01-17 11:37:16","type":"sell",
    "rate":"0.00000039","amount":"273.78000000","total":"0.00010677"},        '''
        print (t1, t2, 'pair.ticker:', pair.ticker)
        if Test: continue
            
        try:
        #if True:
            #params = {'method': 'singlemarketdata', 'marketid': pair.ticker }
            #cryp_url = 'https://' + exchg.url + '/public?command=returnTradeHistory&currencyPair=' + pair.ticker
            cryp_url = 'https://' + exchg.url + '/public?command=returnOrderBook&depth=1&currencyPair=' + pair.ticker
            ## res = {"asks":[["0.00001852",59.39524844]],"bids":[["0.00001851",710.99297675]],"isFrozen":"0"}
            print(cryp_url)
            res = fetch(cryp_url)
            res = json.loads(res)
            if type(res) != dict:
                continue
            if not res.get('isFrozen'): continue
            if True:
                # v1
                sell = 1/float(res['asks'][0][0])
                buy = 1/float(res['bids'][0][0])
            else:
                pass
            #return dict(buy= buy, sell= sell)
            print(sell, buy)
            db_common.store_rates(db, pair, sell, buy)
        except Exception as e:
        #else:
            msg = "serv_rates %s :: %s" % (exchg.url, e)
            print(msg)
            continue
    db.commit()

def from_cryptsy(db, exchg):
    exchg_id = exchg.id
    ##PRINT_AS_FUNC and print(conn) or print conn
    for pair in db_common.get_exchg_pairs(db, exchg_id):
        if not pair.used: continue
        t1 = get_ticker(db, exchg_id, pair.curr1_id)
        t2 = get_ticker(db, exchg_id, pair.curr2_id)
        
        '''
        v1 http://www.cryptsy.com/api.php?method=singlemarketdata&marketid=132
        v2 https://www.cryptsy.com/api/v2/markets/132
        pubapi2.cryptsy.com - (Amsterdam, Netherlands)
        DOGE - 132
        {"success":1,"return":{"markets":{"DOGE":{"marketid":"132","label":"DOGE\/BTC","lasttradeprice":"0.00000071","volume":"102058604.42108892","lasttradetime":"2015-07-07 09:30:31","primaryname":"Dogecoin","primarycode":"DOGE","secondaryname":"BitCoin","secondarycode":"BTC","recenttrades":[{"id":"98009366","time":"2015-07-07 
        '''
        print(t1, t2, 'pair.ticker:', pair.ticker,)
        if Test: continue
            
        try:
        #if True:
            #params = {'method': 'singlemarketdata', 'marketid': pair.ticker }
            cryp_url = 'https://' + exchg.url + '/api/v2/markets/' + pair.ticker +'/ticker'
            print(cryp_url)
            res = fetch(cryp_url)
            res = json.loads(res)
            if type(res) != dict:
                continue
            if not res.get('success'): continue
            if True:
                # v2
                # {"success":true,"data":{"id":"132","bid":4.7e-7,"ask":4.9e-7}}
                res = res['data']
                buy = res['ask']
                sell = res['bid']
            else:
                # v1
                rr = res['return']['markets'].get('DOGE')
                if not rr:
                    continue
                ll = rr['label']
                pair_ll = t1 + '/' + t2
                if ll.lower() != pair_ll.lower():
                    print('ll.lower() != pair_ll.lower()', ll.lower(), pair_ll.lower())
                    continue

                # тут обратные ордера поэтому наоборот
                buy = rr['sellorders'][0]['price']
                sell = rr['buyorders'][0]['price']
            #return dict(buy= buy, sell= sell)
            print(sell, buy)
            db_common.store_rates(db, pair, sell, buy)
        except Exception as e:
        #else:
            msg = "serv_rates %s :: %s" % (exchg.url, e)
            print(msg)
            continue
    db.commit()

#  с биржи BTC-e.com
## api/3/ticker/btc_usd-btc_rur...
def from_btc_e_3(db,exchg):
    exchg_id = exchg.id
    pairs = []
    for pair in db_common.get_exchg_pairs(db, exchg_id):
        if not pair.used: continue
        t1 = get_ticker(db, exchg_id, pair.curr1_id)
        t2 = get_ticker(db, exchg_id, pair.curr2_id)
        if t1 and t2:
            pairs.append(t1+'_'+t2)
    pairs = '-'.join(pairs)
    url = 'https://' + exchg.url + '/api/3/ticker/' + pairs
    #url = 'https://btc-e.com/api/3/ticker/' + pairs
    print(url)
    try:
        resp = fetch(url)
        res = json.loads(resp)
        for k,v in res.iteritems():
            print( k[:3], k[4:],  ) # v
            curr1 = get_curr(db, exchg_id, k[:3])
            curr2 = get_curr(db, exchg_id, k[4:])
            if not curr1 or not curr2:
                print('not curr found for serv rate')
                continue
            pair = db((db.exchg_pairs.curr1_id == curr1.id)
                  & (db.exchg_pairs.curr2_id == curr2.id)).select().first()
            if not pair:
                print('pair nor found in get_exchg_pairs')
                continue
            db_common.store_rates(db, pair, v['sell'], v['buy'])
            print('updates:', v['sell'], v['buy'])
        db.commit()
        return resp
    except Exception as e:
        msg = "serv_rates %s :: %s" % (exchg.url, e)
        print(msg)
        return msg
    

    
def from_btc_e(db, exchg):
    from_btc_e_3(db, exchg)
    return
    
    for pair in db_common.get_exchg_pairs(db, exchg.id):
        if not pair.used: continue
        curr1 = db.currs[pair.curr1_id]
        if not curr1.used: continue
        curr2 = db.currs[pair.curr2_id]
        if not curr2.used: continue
        
        #PRINT_AS_FUNC and print(pair) or print pair
        limits1 = db_common.get_limits(db, exchg.id, pair.curr1_id)
        limits2 = db_common.get_limits(db, exchg.id, pair.curr2_id)
        #if not limits1 or not limits2: continue
        # если нет лимитов то берем мелкие буквы
        #PRINT_AS_FUNC and print(pair.curr1_id, pair.curr2_id) or print pair.curr1_id, pair.curr2_id
        t1 = limits1 and limits1.ticker or None
        if not t1:
            t1 = curr1.abbrev.lower()
        t2 = limits2 and limits2.ticker or None
        if not t2:
            t2 = curr2.abbrev.lower()
        print("   ",  t1, t2)
        if Test: continue
        try:
            tab = exch_client.getDept(exchg.name, t1, t2)
            pass
        except Exception as e:
            msg = "serv_rates %s :: %s" % (exchg.url, e)
            print(msg)
            continue

        db_common.store_depts(db, pair, tab)

def get_from_exch(db, exchg):
    if exchg.API_type == 'btc-e_3':
        return from_btc_e_3(db,exchg)
    elif exchg.API_type == 'poloniex':
        return from_poloniex(db, exchg)
    elif exchg.API_type == 'livecoin':
        return from_livecoin(db, exchg)
    elif exchg.API_type == 'cryptsy':
        return from_cryptsy(db, exchg)
    else:
        conn = exch_client.conn(exchg)
        res = from_btc_e(db,exchg)
        exch_client.conn_close(exchg)
        return res
    #return conn

def get(db, not_local, interval=None):
    interval = interval or 66
    print( __name__, 'not_local:',not_local, ' interval:', interval)
    not_local = not_local == 'True'

    proc_buys_period = 550
    i_pb = proc_buys_period
    # запуск обработки все истории входов по фиату только 1 раз при перезапуске сервера
    serv_to_buy_proc_history_one = True

    while True:
        # по всем биржам
        for exchg in db(db.exchgs).select():
            if not exchg.used: continue
            print(exchg.name)
            if True:
                get_from_exch(db, exchg)
            else:
                # rise error - https://groups.google.com/g/web2py/c/7Dl1lUeotgk/m/GiR89Y_0BAAJ
                threadGetRate = Thread(target=get_from_exch, args=(db, exchg))
                threadGetRate.start()
            pass

        print('\n', datetime.datetime.now())
        
        if not_local:
            # если я запустил это локально - то нельзя проверять историю диллеров
            # так как иначе будут 2-е выплаты!
            i_pb = i_pb + interval
            if i_pb > proc_buys_period:
                i_pb = 0
                #if True:
                try:
                    # если есть невыплаченные покупки криптовалюты
                    if serv_to_buy_proc_history_one:
                        # запустим историю только 1 раз за запуск сервера!
                        # если вдруг что-то не так в момент работы сервера, то это саппорт решать должен
                        # в контроллере edealers есть list_incoms - которая проверяет историю
                        # и ттам можно сделать лист входов или их в стек выплат записать
                        mess = serv_to_buy.proc_history(db)
                        #PRINT_AS_FUNC and print(mess) or print mess
                        serv_to_buy_proc_history_one = not serv_to_buy_proc_history_one
                        print('\n', datetime.datetime.now())
                    elif True:
                        ## сейчас у нас ссылка неработает из-за pixle HTTPS
                        ## так что будем пробовать историю
                        mess = serv_to_buy.proc_history(db, only_list=None, ed_acc=None,
                                from_dt_in='same')
                        ##PRINT_AS_FUNC and print(mess) or print mess
                    # внутри db.commit()
                except Exception as e:
                #else:
                    db.rollback()
                    log_commit(db, 'serv_to_buy.proc_history ERROR: %s' % e)

            if True:
                try:
                    # если есть невыплаченные покупки криптовалюты
                    clients_lib.notify(db)
                except Exception as e:
                    db.rollback()
                    log_commit(db, 'clients_lib.notify ERROR: %s' % e)

        else:
            print('local use - skeep serv_to_buy.proc_history and clients_lib.notify')

        if Test: break
        print( 'sleep',interval,'sec')
        sleep(interval)

if Test: get(db)

# если делать вызов как модуля то нужно убрать это иначе неизвестный db
import sys
#PRINT_AS_FUNC and print(sys.argv) or print sys.argv
if len(sys.argv)>1:
    get(db, sys.argv[1], float(sys.argv[2]))
