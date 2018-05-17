#!/usr/bin/env python
# coding: utf8
#from gluon import *
import datetime
# тут все в float -- from decimal import Decimal

ORDER_TIME = 600 # в сек жизни заказ на обмен
TRANS_TIME = 300 # в сек жизни заказ на обмен задержка создания транзакции
RATES_TIME = 3600 # в сек жизни курса с биржи

import db_common

# удалим из стека просроченные чтобы не мешались
def check_orders(db):
    dt_order = datetime.datetime.now() - datetime.timedelta(0, ORDER_TIME)
    for r in db(db.rate_orders_stack).select():
        if r.created_on < dt_order:
            # заказ на курс просрочен
            del db.rate_orders_stack[r.id]

def add_tax(db, in_id, out_id, b, s):
    return b,s
    ex_tax = db((db.exchg_taxs.curr1_id==in_id)
                & (db.exchg_taxs.curr2_id==out_id)).select().first()
    tax = (ex_tax and float(ex_tax.tax) or 0.5)*0.01
    if b: b = b * (1-tax)
    if s: s = s / (1-tax)
    return b, s

# rate for buy, sell, average or None
## in DB sell < buy
## but return AS s, b
def get_average_rate_bsa_1(db, in_id, out_id, expired, recursed=False):

    pair = db((db.exchg_pair_bases.curr1_id == in_id)
            & (db.exchg_pair_bases.curr2_id == out_id)
              ).select().first()

    avg = pair and pair.hard_price
    if avg:
        # если задан жесткий курс а не с биржи то
        avg = float(avg)
        b = avg*0.99
        s = avg/0.99
        ##print 'get as HARD', b,s
        return b, s, avg

    b = s = avg = None
    field =  "AVG(sp1) AS s, AVG(bp1) AS b "

    if expired:
        cond = "curr1_id=%s AND curr2_id=%s AND on_update > '%s'" % (in_id, out_id, expired)
    else:
        cond = "curr1_id=%s AND curr2_id=%s" % (in_id, out_id)

    qry ="SELECT " + field + \
 " FROM exchg_pairs \
 WHERE (%s) \
 GROUP BY curr1_id, curr2_id \
 ;" % cond
    #print qry
    rec = db.executesql(qry, as_dict=True)
    #print rec
    if len(rec)>0:
        rec = rec[0]
        b = s = avg = None
        ## here need REVERSE!
        if 'b' in rec: s = rec['b']
        if 's' in rec: b = rec['s']
        # если одно из низ ноне
        if b and s:
            avg = (b+s)/2
            return float(b), float(s), float(avg)
    
    # иначе возьмем старый курс и просто у него % на 5 увеличим
    if expired and not recursed:
        expired1 = expired + datetime.timedelta(0,RATES_TIME*30)
        b, s, avg = get_average_rate_bsa_1(db, in_id, out_id, expired1, True)
        if avg:
            avg = float(avg)
            b = avg*0.98
            s = avg/0.98

    return b, s, avg

def get_average_rate_bsa_2(db, in_id, out_id, expired):
    b=s=avg=None
    b,s,avg = get_average_rate_bsa_1(db, in_id, out_id, expired)
    if not b or not s:
        # поробуем обратный найти поиск
        b1,s1, avg = get_average_rate_bsa_1(db, out_id, in_id, expired)
        if b1 and s1:
            ## перевернем вход с выходом тоже
            b = 1/s1
            s = 1/b1
            avg = 1/avg
            #print 'get reverse rate:', b, s
    else:
        #print 'get direct rate:', b, s
        pass
    return b,s,avg

def get_average_rate_bsa(db, in_id, out_id, expired=None):
    if in_id == out_id: return 1,1,1
    # берем в расчет только недавние цены
    expired = expired or datetime.datetime.now() - datetime.timedelta(0,RATES_TIME)

    b,s,avg = get_average_rate_bsa_2(db, in_id, out_id, expired)
    if b and s:
        #print in_id,'->',out_id, b, s
        ##b,s = add_tax(db, in_id, out_id, b, s)
        return b, s, avg
    # иначе попробуем взять через Биткоин кросскурс
    btc, x, e = db_common.get_currs_by_abbrev(db,'BTC')
    b1,s1,avg1 = get_average_rate_bsa_2(db, in_id, btc.id, expired)
    b2,s2,avg2 = get_average_rate_bsa_2(db, btc.id, out_id, expired)
    if b1 and s1 and b2 and s2:
        #print in_id,'->BTC->',out_id, b1, s1, 'and', b2, s2
        # нашли кросскурс
        b = b1 * b2
        s = s1 * s2
        ##b, s = add_tax(db, in_id, out_id, b, s)
        return b, s, avg1*avg2

    btc, x, e = db_common.get_currs_by_abbrev(db,'USD')
    b1,s1,avg1 = get_average_rate_bsa_2(db, in_id, btc.id, expired)
    b2,s2,avg2 = get_average_rate_bsa_2(db, btc.id, out_id, expired)
    if b1 and s1 and b2 and s2:
        #print in_id,'->USD->',out_id, b1, s1, 'and', b2, s2
        # нашли кросскурс
        b = b1 * b2
        s = s1 * s2
        ##b, s = add_tax(db, in_id, out_id, b, s)
        return b, s, avg1*avg2
    return None, None, None

def get_avr_rate_or_null(db, curr_in_id, curr_out_id):
    if curr_in_id == curr_out_id:
        return 1

    pr_b, pr_s, pr_avg = get_average_rate_bsa(db, curr_in_id, curr_out_id)
    if pr_avg:
        return pr_avg

    return 0

#################
## вычисление по степени объема а не по стакану биржи ##################
#############################################################################
def get_pow_rate_par_1(db, curr_in, curr_out, rate_rev):
    # ищем прямой курс
    rate_par = db((db.exchg_pair_bases.curr1_id==curr_in.id)
                        & (db.exchg_pair_bases.curr2_id==curr_out.id)
                        ).select().first()
    if rate_par:
        return [float(rate_par.base_vol), float(rate_par.base_perc)]

    # ищем обратный
    rate_par_rev = db((db.exchg_pair_bases.curr1_id==curr_out.id)
                        & (db.exchg_pair_bases.curr2_id==curr_in.id)
                        ).select().first()
    if rate_par_rev:
        # перевернем кол-во по курсу
        return [float(rate_par_rev.base_vol)/rate_rev, float(rate_par_rev.base_perc)]
    return
    
def get_pow_rate_par(db, curr_in, curr_out, rate_rev, expired):
    #print curr_in.abbrev, '->>', curr_out.abbrev
    rate_par = get_pow_rate_par_1(db, curr_in, curr_out, rate_rev)
    #print rate_par
    if rate_par:
        return rate_par

    # попробуем крос курс BTC
    btc, x, e = db_common.get_currs_by_abbrev(db,'BTC')
    pr_b1, pr_s, pr_avg = get_average_rate_bsa(db, curr_in.id, btc.id, expired)
    rate_par1 = get_pow_rate_par_1(db, curr_in, btc, pr_b1) # курс для ->БТС берем
    #print 'rate_par1:',rate_par1, pr_b1
    pr_b2, pr_s, pr_avg = get_average_rate_bsa(db, btc.id, curr_out.id, expired)
    rate_par2 = get_pow_rate_par_1(db, btc, curr_out, pr_b2) # курс для <-БТС берем
    #print 'rate_par2:',rate_par2, pr_b2
    if rate_par1 and rate_par2:
        # нашли кросскурс
        return [(rate_par1[0]*rate_par2[0]/pr_b1)**0.5, rate_par1[1]+rate_par2[1]]

    # попробуем крос курс USD
    btc, x, e = db_common.get_currs_by_abbrev(db,'USD')
    pr_b1, pr_s, pr_avg = get_average_rate_bsa(db, curr_in.id, btc.id, expired)
    rate_par1 = get_pow_rate_par_1(db, curr_in, btc, pr_b1) # курс для ->БТС берем
    #print 'rate_par1:',rate_par1, pr_b1
    pr_b2, pr_s, pr_avg = get_average_rate_bsa(db, btc.id, curr_out.id, expired)
    rate_par2 = get_pow_rate_par_1(db, btc, curr_out, pr_b2) # курс для <-БТС берем
    #print 'rate_par2:',rate_par2, pr_b2
    if rate_par1 and rate_par2:
        # нашли кросскурс
        return [(rate_par1[0]*rate_par2[0]/pr_b1)**0.5, rate_par1[1]+rate_par2[1]]

# один раз для блока берем курсы валют чтобы сразу их учесть
def get_best_rates(db, curr_in, curr_out=None):
    rates = {}
    expired = datetime.datetime.now() - datetime.timedelta(0, RATES_TIME)
    for curr_out in db((db.currs.used==True)
            & (not curr_out or db.currs.id==curr_out.id)).select():
        if curr_out.id == curr_in.id:
            rates[curr_out.id] = [100000,0,1]
        else:
            pr_b, pr_s, pr_avg = get_average_rate_bsa(db, curr_in.id, curr_out.id, expired)
            #print curr_in.abbrev,'->',curr_out.abbrev, pr_b, pr_s, pr_avg
            if pr_b:
                rate_par = get_pow_rate_par(db, curr_in, curr_out, pr_b, expired)
                if rate_par: rates[curr_out.id] = [rate_par[0], rate_par[1], pr_b]

    return rates

# на входе нужен список курсов:
# best_rates = { 'curr1': { 'curr2':[base_vol, base_perc, base_rate] } }
# best_rates = { 'BTC': { 'BTC':[1, 0, 1] } } # здесь всегда 1 будет
# best_rates = { 'BTC': { 'LTC':[0.1, 0.5, 0.033] } } # за <0.1 БТС 0,5% за 0,3 - 1%; 0,9-1,5%; 2.7-2%
# best_rates = { 'BTC': { 'RUB':[0.1, 0.4, 30000] } } # за <0.1 БТС 0,4% за 0,3 - 0.8%; 0,9-1,2%; 2.7-1.6%
def get_best_rate(best_rates, curr_out, amo):
    rate_pars = best_rates.get(curr_out.id)
    if not rate_pars:
        return 0
    base_vol = rate_pars[0] # объем базовый
    base_perc = rate_pars[1] # процент с объема
    base_rate = rate_pars[2] # процент с объема
    power_perc = 0
    for pow in range(0,10):
        power_perc = pow
        vol = base_vol*3**pow
        #print vol, amo
        if vol > amo:
            break
    power_perc = power_perc + 1
    perc = power_perc*base_perc
    #print 'POWER:', power_perc, ' ->:', perc,'%'
    best_rate = base_rate * (1 - perc*0.01)
    return best_rate

# ищем заказ на курс, попути удаляем если он просрочен
# заказов может быть много и платежей разных - списком
def get_rate_order_for_trans(db, shop_order_addr_id, amo):
    dt_order = datetime.datetime.now() - datetime.timedelta(0, ORDER_TIME)
    ro = None
    for r in db((db.rate_orders_stack.ref_id == db.rate_orders.id)
                & (db.rate_orders.ref_id == shop_order_addr_id)
                ).select(orderby=~db.rate_orders_stack.created_on):
        if r.rate_orders_stack.created_on < dt_order:
            # заказ на курс просрочен
            del db.rate_orders_stack[r.rate_orders_stack.id]
            continue

        # проверим сколько уже использовано по заказу
        used_amo = float(r.rate_orders.used_amo) or 0
        if used_amo + amo > r.rate_orders.volume_in:
            continue
        r.rate_orders.update_record(used_amo = used_amo + amo)
        #print 'get_rate_order_for_trans  r.rate_orders:',  r.rate_orders
        return r.rate_orders
    return None

# надо взять курс или с заказа на обмен или по объему с бирж
# а если нету то взять курс вычесленный по степени от объема
def get_amo_out(db, rates, shop_order_addr, curr_out, amo, created_on):
    amo_out = rate_order = None
    # если время транзакции не поздно, тогда только заказ на обмен используем
    dt_trans = datetime.datetime.now() - datetime.timedelta(0, TRANS_TIME)
    if created_on and created_on > dt_trans:
        # тут же найдем заказ на курс для данной транзакции
        rate_order = shop_order_addr and get_rate_order_for_trans(db, shop_order_addr.id, amo) or None
        #print 'get_amo_out - RATE by rate_order:',rate_order
    if rate_order:
        rate = rate_order.volume_out / rate_order.volume_in
        amo_out = rate*amo
    else:
        ## и покажем обратный курс
        #print 'get_amo_out - RATES:', curr_out.abbrev,':',rates, rates.get(curr_out.id) and 1/rates[curr_out.id][2] or None
        rate = get_best_rate(rates, curr_out, amo)
        if rate:
            amo_out = rate*float(amo)
    return amo_out, rate_order, rate

# надо взять курс или с заказа на обмен или по объему с бирж
# а если нету то взять курс вычесленный по степени от объема
def get_rate(db, curr_in, curr_out, amo_in=None, created_on=None, shop_order_addr=None):
    if curr_in.id == curr_out.id:
        return amo_in, None, 1.0
    if not amo_in: amo_in = 0.0
    #print '%s[%s] -> [%s]' % (amo_in, curr_in.abbrev, curr_out.abbrev)
    rates = get_best_rates(db, curr_in, curr_out)
    return get_amo_out(db, rates, shop_order_addr, curr_out, amo_in, created_on)

def top_line(db, curr, filter=[]):
    h = []
    curr_in_id = curr.id
    for r in db((db.currs.used==True)
                & (db.currs.id==db.xcurrs.curr_id)).select():
        if len(filter)>0 and r.currs.abbrev not in filter: continue
        curr_out_id = r.currs.id
        if curr_out_id == curr_in_id: continue
            
        b, s, avg = get_average_rate_bsa(db, curr_in_id, curr_out_id)
        if avg > 0:
            rate = 1/avg
            if rate > 1000: rate = int(rate)
            elif rate >10: rate = round(rate,2)
            elif rate >0.1: rate = round(rate,4)
            else: rate = round(rate,6)
            h.append([rate,r.currs.abbrev])

    return h
