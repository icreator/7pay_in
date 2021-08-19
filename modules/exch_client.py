# coding: utf8

import decimal

import urllib
import btceapi_my


#print (btceapi_my.getDepth(btceapi_my.BTCEConnection('btc-e.com', 20),"btc_usd"))

exchgs_tab = {}        

def conn(exchg):
    if not exchg.name in exchgs_tab or not exchgs_tab[exchg.name]:
        print (exchg.name, "connect to", exchg.url)
        exchgs_tab[exchg.name] = [btceapi_my.BTCEConnection(exchg.url, 20), exchg.API_type]

    #print (exchgs_tab[exchg.name])
    return exchgs_tab[exchg.name]

def conn_close(exchg):
    exchgs_tab[exchg.name][0].close()
    exchgs_tab[exchg.name] = None
    #print ("exchgs_tab", exchgs_tab)

def depth(exchg_name, curr_in, curr_out):
    if True:
    #try:
        conn = exchgs_tab[exchg_name][0]
        if exchgs_tab[exchg_name][1] == "upbit":
            # ВНИМАНИЕ - тут выдает объем заявок в первой валюте пары
            # ltc_rur - и для покупки и для продажи объем в LTC
            sells, pays = getDepth_UpBit(conn, curr_in, curr_out)
        elif exchgs_tab[exchg_name][1] == "btce":
            # ВНИМАНИЕ - тут выдает объем заявок в первой валюте пары
            # ltc_rur - и для покупки и для продажи объем в LTC
            sells, pays = btceapi_my.getDepth(conn, curr_in, curr_out)
    else:
    #except Exception as e:
        msg = " - depth: %s" % e
        raise Exception(msg)

    return sells, pays

def tradeHistory(exchg_name, pair, count):
    try:
        conn = exchgs_tab[exchg_name][0]
        history = btceapi_my.getTradeHistory(conn, pair, count)
    except Exception as e:
        msg = " - tradeHistory: %s" % e
        raise Exception(msg)

    return history

def make_sell_buy_depth(num_rows, data, log=None):

        if log: print (data[0],data[1],data[3],data[4])
        amount1 = 0
        amount2 = 0
        tab = range(num_rows) # 5 -> 0,1,2,3,4

        best = data[0][0]

        # это продажа или покупка?
        s_b = data[0][0] < data[-1][0]
        for i in range(num_rows):
            price = decimal.Decimal(best*decimal.Decimal(1+(s_b and 1 or -1)*i/100.0)).quantize(decimal.Decimal('.00000001'), rounding=decimal.ROUND_DOWN)
            tab[i]=[price,0,0]
        if log: print (tab,"\n", s_b, "(s_b and 1 or -1)=",(s_b and 1 or -1))
                
        i = 0
        for d in data:
            if log: print (d[0],d[1], amount1, amount2)
            amount2 += d[1]*d[0]
            amount1 += d[1]                
            if s_b and tab[i][0] < d[0]*decimal.Decimal(0.995): i += 1
            if i > num_rows-1: break
            if s_b and tab[i][0] < d[0]*decimal.Decimal(0.995): i += 1 # может одну ступеньку проскочить
            if not s_b and tab[i][0] > d[0]*decimal.Decimal(1.005): i += 1
            if i > num_rows-1: break
            if not s_b and tab[i][0] > d[0]*decimal.Decimal(1.005): i += 1 # может одну ступеньку проскочить
            if i > num_rows-1: break
            if log: print (s_b, "i:", i, "use price:", tab[i][0], "for d[0]:", d[0])
            tab[i][1] = amount1
            tab[i][2] = amount2
        
        # if any %% missed
        for i in range(1, num_rows):
                if tab[i][1] == 0:
                        tab[i][1] = tab[i-1][1]
                        tab[i][2] = tab[i-1][2]
                        
        return tab

def getDept(exchg_name, curr_in, curr_out):
    try:
        sells, pays = depth(exchg_name, curr_in, curr_out)
    except Exception as e:
        msg = "getDepth: %s" % e
        raise Exception(msg)

    log = None
    #if pair == "clr_rub" and exchgs_tab[exchg_name][1] == "upbit": log = True
    num_rows = 5
    sells_d = make_sell_buy_depth(num_rows, sells, log)
    pays_d = make_sell_buy_depth(num_rows, pays, log)
    return [sells_d, pays_d]

def getDepts(exchg_name, pairs):

        
        resp = []
        num_rows = 10
        for pair in pairs:
            try:
                s_p = getDept(exchg_name, pair)
            except Exception as e:
                raise Exception(e)

            resp.append(s_p)

        #exhc.close()
        return resp

######################################################
## upbit.org/trade/api/ratingssimple/CLR/RUB
def getDepth_UpBit(conn, curr_in, curr_out):
    pair = curr_in.upper() + '/' + curr_out.upper()
    str_ = "/trade/api/getOpenOrders"
    params = {"method":"getOpenOrders", 
        "pair": pair,
        "count": 30, }
    ##https://upbit.org/trade/api/ratingssimple/CLR/RUB
    str_ = '/trade/api/ratingssimple/' + pair
    #encoded_params = urllib.urlencode(params)
    encoded_params = None
    
    #print (str_, encoded_params)
    try:
        res = conn.makeJSONRequest(str_, None, encoded_params)
    except Exception as e:
        msg = " makeJSONRequest:: %s" % e
        raise Exception(msg)
    #print (res)
    

    '''
{
    u'return':
        {
           u'sell':
                [
                  {u'rank': u'5100', u'my': Decimal('0'), u'valueB': u'255', u'valueA': u'0.05'},
                  {u'rank': u'5460', u'my': Decimal('0'), u'valueB': u'1092', u'valueA': u'0.2'},
           u'buy': [
                   {u'rank': u'4821', u'my': Decimal('0'), u'valueB': u'113.8', u'valueA': u'0.0236'},
                   {u'rank': u'3350.1', u'my': Decimal('0'), u'valueB': u'2030.32', u'valueA': u'0.61'}
                ]
        },
    u'success': Decimal('1')
}
    '''
    if type(res) is not dict:
        raise Exception("The response is not a dict. %s" % pair)
    
    if res[u'success'] == decimal.Decimal('1'):
        # {"success":1,"return":{"CLR/RUB":"5.495"}}
        price = res[u'return'].get(pair)
        print (price)
        return [[decimal.Decimal(price), decimal.Decimal(1000)]], [[decimal.Decimal(price), decimal.Decimal(1000)]]
    
        #sell = res[u'return'][u'sell']
        #buy = res[u'return'][u'buy']
    else:
        raise Exception("error - getDepth_UpBit for %s" % pair)

    #print ("sell")
    sells = []
    pays = []
    for rec in sell:
        #print ("rank:",rec[u'rank'], rec[u'valueA'], rec[u'valueB'])
        sells.append([decimal.Decimal(rec[u'rank']), decimal.Decimal(rec[u'valueA'])])
    #print ("buy")
    for rec in buy:
        #print ("rank:",rec[u'rank'], rec[u'valueA'], rec[u'valueB'])
        pays.append([decimal.Decimal(rec[u'rank']), decimal.Decimal(rec[u'valueA'])])
    
    return sells, pays
