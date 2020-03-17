# coding: utf8

import rates_lib
import datetime

session.forget(response)

if not IS_LOCAL: raise HTTP(200, T('ERROR'))

# попробовать что-либо вида
def index():
    #err(1)
    return dict(message="hello from tools.py")

def serv_rates():
    if not request.args(0): return 'serv_rates/exchgs.id'
    exchg = db(db.exchgs.id==request.args(0)).select().first()
    if not exchg: return 'exchg not found'
    import serv_rates
    return BEAUTIFY(serv_rates.get_from_exch(db, exchg))

def get_best_rates():
    if not request.args(0): return 'get_best_rates/RUB'
    curr_in = db(db.currs.abbrev==request.args(0)).select().first()
    rates = rates_lib.get_best_rates(db, curr_in, curr_out=None)
    #print rates
    h = CAT()
    for i, r in rates.iteritems():
        #print i,r
        h += DIV(
            db.currs[i].abbrev,' base: ',r[0],' tax: ', r[1],' rate:', r[2], ' - 1/rate:', 1/r[2] if r[2] else 0
            )
    return dict(h=h)
#
# найти лучшую цену для пары и объема
# get_best_price_for_volume/NVC/RUB/10
def get_best_price_for_volume():
    if len(request.args) == 0:
        mess = 'len(request.args)==0'
        print mess
        return mess
    import db_client
    import db_common
    a_in, x, e = db_common.get_currs_by_abbrev(db,request.args[0])
    a_out, x, e = db_common.get_currs_by_abbrev(db,request.args[1])
    expired = datetime.datetime.now() - datetime.timedelta(5,600)
    s_b = len(request.args)<4 or request.args[3]=='sell'
    #s_b = not 3 in request.args or request.args[3]=='sell'
    print s_b
    print db_client.get_best_price_for_volume(db, a_in.id, a_out.id,
            float(request.args[2]), expired, s_b)

# выдать лучшуу цену нв объем
# best_price/sell/LTC/RUB/123
def best_price():
    if len(request.args) == 0:
        mess = 'len(request.args)==0'
        print mess
        return mess
    import db_client
    import db_common

    s_b = None
    if request.args[0] == 'sell': s_b = True
    _in = request.args[1]
    _out = request.args[2]
    volume_in = request.args[3]
    x,e,acurr_in = db_common.get_currs_by_abbrev(db,_in)
    x,e,acurr_out = db_common.get_currs_by_abbrev(db,_out)
    expired = datetime.datetime.now() - datetime.timedelta(2,60)
    dealer_id = None
    d_e = None
    best_rate, pair = db_client.get_best_price_for_volume(
        db, acurr_in.id, acurr_out.id, float(volume_in), expired, s_b, dealer_id, d_e)
    res = best_rate and "%s, 1/X = %s" % (best_rate, 1/best_rate) or best_rate
    print res, pair
    return res

# выдает список для вычисления курса по степени объема
# http://127.0.0.1:8000/ipay/tools/get_rate_powers/BTC
def get_rate_powers():
    if len(request.args) == 0:
        mess = 'len(request.args)==0'
        print mess
        return mess
    import rates_lib
    curr_in = db(db.currs.abbrev==request.args[0]).select().first()
    best_rates = rates_lib.get_best_rates(db, curr_in)
    res = ''
    for v in best_rates:
        res = res + '[%s]->[%s]=' % (curr_in.abbrev,db.currs[v].abbrev) + '%s' % best_rates[v]  + '<br>'
    return res

#
def get_rate():
    if len(request.args) <2:
        mess = 'len(request.args)==0 - [pay_in]/[pay_out]/[amo]'
        print mess
        return mess
    import rates_lib
    import db_common
    curr_in, x, e = db_common.get_currs_by_abbrev(db,request.args[0])
    curr_out, x, e = db_common.get_currs_by_abbrev(db,request.args[1])
    amo = float( len(request.args)>2 and request.args[2] or 1 ) / 10
    res = ''
    for i in range(1,4):
        amo = amo*10
        amo_out, rate_order, rate = rates_lib.get_rate(db, curr_in, curr_out, amo)
        res = res + '%s[%s] -> %s[%s] x%s /%s <br>' % (amo, curr_in.abbrev, amo_out, curr_out.abbrev, rate, rate and 1/rate or 0)
    return res

# tools/get_best_rate/1/20
def get_best_rate():
    if len(request.args) == 0:
        mess = 'len(request.args)==0 - [pay_in]/[amo]'
        print mess
        return mess
    import rates_lib
    pay_in = db.pay_ins[request.args[0]]
    shop_order_addr = db.shop_order_addrs[pay_in.shop_order_addr_id]
    shop_order = db.shop_orders[shop_order_addr.shop_order_id]
    xcurr_in = db.xcurrs[shop_order_addr.xcurr_id]
    curr_in = db.currs[xcurr_in.curr_id]
    curr_out = db.currs[shop_order.curr_id]
    amo = float(request.args[1])
    amo_out, rate_order, rate = rates_lib.get_rate(db,
        curr_in, curr_out, amo, pay_in.created_on, shop_order_addr)
    return '%s[%s] -> %s[%s] x%s /%s' % (amo, curr_in.abbrev, amo_out, curr_out.abbrev, rate, 1/rate)
