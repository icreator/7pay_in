#!/usr/bin/env python
# coding: utf8
#import sys
#import random
#from time import sleep
#import json

if False:
    from gluon import *
    import db
    request = current.request
    response = current.response
    session = current.session
    cache = current.cache
    T = current.T

import datetime
from decimal import Decimal

from gluon import current
from gluon.contrib import simplejson as js

import common
import db_common
import db_client
import rates_lib
import ed_common
import crypto_client
import serv_to_pay
import ed_bal

#import ed_YD

TIME_DIFF_FOR_ORDERS = 1500 # sec, older to delete
deal_name = 'BUY'

def log(db, mess):
    mess = 'BUY: %s' % mess
    print mess
    db.logs.insert(mess=mess)
def log_commit(db, mess):
    log(db,mess)
    db.commit()

'''
def get_vol_in(db, curr_in, curr_out, volume_out, expired):
    s_b = False
    best_rate, pairs, taxs, efee = db_client.get_best_price_for_volume(
            db, curr_out.id, curr_in.id, volume_out, expired, s_b)
    if not best_rate:
        #print None
        return None, None, None

    #print best_rate, '1/r=', round(1/best_rate,8), pairs, '\n', taxs, efee
    #best_rate = 1/best_rate
    volume_in = volume_out * best_rate
    tax_mess = ''
    #print 'best_rate, volume_in:', best_rate, volume_in

    if volume_out:
        # возьмем таксы все
        deal = dealer_deal = None
        # там входной оброк не берется - так как он берется с заказов только
        # тоесть со входа фиата рубль не берется
        ## здесь не надо переворачивать - курс для продажи кррипты уже дан best_rate = 1/best_rate # обязательно перевернем
        #volume_out, tax_mess = db_client.use_fees_for_in(db, deal, dealer_deal, curr_in, curr_out, volume_in, best_rate)
        deal_fee = dealer_deal_fee = None
        #print volume_out, ' -> ', volume_in, best_rate
        volume_out2, tax_mess = db_client.use_fees_for_in(db, deal_fee, dealer_deal_fee, curr_in, curr_out, volume_in, 1/best_rate)
        #print volume_out2
        volume_in = volume_in * volume_out / Decimal(volume_out2)
        best_rate = volume_out / volume_in
    return volume_in, best_rate, tax_mess
'''

def buy_free(db, deal, curr_in, ecurr, volume_in, curr_out, xcurr, addr, token_system, conn, mess_in=None):
    volume_in = float(volume_in)
    print 'try buy_free %s [%s] -> %s %s' % (volume_in, curr_in.abbrev, curr_out.abbrev, addr)
    if not (token_system or conn):
        mess = 'buy_free [' + curr_out.name + '] not connection'
        print mess
        return { 'error': mess }, None

    ecurr_id = ecurr.id
    xcurr_id = xcurr.id
    _, _, best_rate = rates_lib.get_rate(db, curr_in, curr_out, volume_in)
    if not best_rate:
        mess = 'buy_free [' + curr_in.name + '] -> [' + curr_out.name + ']' + current.T(' - лучший КУРС не найден!')
        print mess
        return { 'error': mess }, None

    ##print best_rate, '1/r=', round(1/best_rate,8)
    # возьмем таксы все
    dealer_deal = None
    # там входной оброк не берется - так как он берется с заказов только
    # тоесть со входа фиата рубль не берется
    #deal_fee = dealer_deal_fee = None
    #volume_out, tax_mess = db_client.use_fees_for_in(db, deal_fee, dealer_deal_fee, curr_in, curr_out, volume_in, best_rate)
    is_order = True
    try:
        volume_out, tax_mess = db_client.calc_fees(db, deal, dealer_deal, curr_in, curr_out, volume_in, best_rate, is_order, note=1)
    except Exception as e:
        print 'buy_free error db_client.calc_fees %s' % e
        volume_out, tax_mess = volume_in * best_rate * 0.99, 'error in fees [%s], get rate 0.99' % e

    volume_out = common.rnd_8(volume_out)

    print 'buy_free', volume_in, curr_in.abbrev, '--> - tax - fee -->', volume_out, curr_out.abbrev, '\n mess:', tax_mess
    
    #log_commit(db, tax_mess)
    #################################################
    bal_free = db_client.curr_free_bal(curr_out)
    print 'buy_free \nsend:', volume_out, curr_out.abbrev, 'bal_free:', bal_free, addr
    

    if bal_free < volume_out:
        res = {'error': 'out off free funds', 'not_log': True}
        bal = None #curr_out.balance
        #log(db, res)
    else:
        # внутри там еще вычтется комиссия сети
        res, bal = crypto_client.send(db, curr_out, xcurr, addr, volume_out, conn, token_system)
        print 'buy_free RES:', res, bal
        log(db, res)
        #log(db, bal)
        if type(res) == type(u' '):
            # прошла транзакция, создадим массив инфо
            res = { 'txid': res }

        #if 'mess' in res: res['txid'] = res['mess']
        if res:
            err = res.get('error')
            if err:
                code = err.get('code')
                if code == -3:
                    # нехваватило монет - они еще не вернулись в кошелек
                    pass
            else:
                if res.get('mess'): volume_out = 0
                res['amo_out'] = volume_out
                res['tax_mess'] = tax_mess
    print res
    return res, bal

## return True - это значит запись в стеке остается занятая в процессе - для дальнейших разборов вручную
def res_update(db, id, deal_id, res, bal, buy_rec, curr, xcurr, mess=None):
    in_proc = False
    if not res or 'error' in res:
        # перевода не произошло - запомним что надо потом его сделать
        buy_rec.status = 'wait'
        if res:
            err_mess = res.get('error_mess', res.get('error','err'))
            res_code = type(err_mess) == type({}) and err_mess.get('code') or 0
            if res_code:
                in_proc = True
                if res_code == -3:
                    buy_rec.status_mess = 'in progress [%s]' % res_code
                    in_proc = False # продолжим обработку этой записи в стеке
                elif res_code == -4:
                    # транзакция запуталась с выходами - выкнием ее из обработки так как она скорее всего выполнилась
                    # тоесть ее как в процессе оставляем
                    buy_rec.status_mess = 'in progress %s' % err_mess
                else:
                    buy_rec.status_mess = 'in progress %s' % err_mess
            else:
                buy_rec.status_mess = err_mess
        return in_proc
    # запомним инфо выплаты криптой
    if id: del db.buys_stack[id]
    buy_rec.status = res.get('mess', 'OK')
    buy_rec.txid = res.get('txid') or res.get('mess')
    #buy_rec.vout = res['vout']
    buy_rec.amo_out = res.get('amo_out')
    buy_rec.tax_mess = res['tax_mess']
    if mess:
        buy_rec.status_mess = mess

    curr.balance = bal # тут уже =reserve(conf)
    ###curr.balance = crypto_client.get_reserve(curr, xcurr, conn)
    curr.update_record()
    db_common.currs_stats_update(db, curr.id, deal_id, res.get('amo_out') or 0)

def get_credit(db, buys):
    buyers_credit = db(db.buyers_credit.acc == buys.buyer).select().first()
    if not buyers_credit: return buys.amount
    # это наш должник
    amo_get = buyers_credit.credit - buyers_credit.accepted
    if amo_get > buys.amount:
        # если средств недостаточно то возьмем только 5%
        amo_get = buys.amount * Decimal(0.05)
    buyers_credit.update_record( accepted = buyers_credit.accepted + amo_get)
    return buys.amount - amo_get

# для данной крипты найдем невыплаченные покупки ее и попробуем выплатить
def proc_ecurr(db, curr, xcurr, token_system, conn):

    print 'serv_to_buy proc_ecurr'
    if not (token_system or conn):
        mess = '[' + curr.name + '] not connection'
        print mess
        return # { 'error': mess }, None
    # найдем дело
    deal = db(db.deals.name==deal_name).select().first()
    if not deal:
        log(db, T('ERROR: not found deal "%s"') % deal_name)
        return
    op_ids = [] # для удаления двойных записей
    ## берем только те что еще не в обработке
    recs = db((db.buys_stack.ref_==db.buys.id)
                 & (db.buys_stack.in_proc == False)
                 & (db.buys.xcurr_id==xcurr.id)
                 & (db.dealers_accs.id==db.buys.dealer_acc_id)
                 & (db.ecurrs.id==db.dealers_accs.ecurr_id)
                 ).select()
    ## сначала их пометим что они уже в процессе
    for rec in recs:
        rec.buys_stack.update_record(in_proc = True)
    db.commit()

    for rec in recs:
        curr_in = db.currs[rec.ecurrs.curr_id]
        curr_out = db.currs[xcurr.curr_id]
        if not db.buys_stack[rec.buys_stack.id]:
            # если запись уже удалена была то пропустим
            continue
        
        if rec.buys.operation_id in op_ids:
            del db.buys[ rec.buys.id ]
            ## каскадное удаление сделает del db.buys_stack[ rec.buys_stack.id ]
            db.commit()
            log(db, 'proc_ecurr - rec.buys.operation_id already processed: %s' % rec.buys.operation_id)
            continue
            
        op_ids.append( rec.buys.operation_id)

        # если этот чел с нашего сервиса поимел что-то раньше то уменьшим ему выплату
        volume_in_cred = get_credit(db, rec.buys)
        if volume_in_cred != rec.buys.amount:
            mess = 'cred**%s' % volume_in_cred
        else:
            mess = None

        res, bal = buy_free(db, deal, curr_in, rec.ecurrs, float(volume_in_cred), curr_out, xcurr, rec.buys.addr, token_system, conn)
        # запомним результат и апдейт балансов сделаем
        # тут же удаляет стек
        in_proc = res_update(db, rec.buys_stack.id, deal.id, res, bal, rec.buys, curr_out, xcurr, mess)
        rec.buys_stack.update_record(in_proc = in_proc)
        rec.buys.update_record()
        db.commit()
        if res and 'not_log' in res: pass
        else: log(db, 'proc_ecurr: %s' % res)
    pass


# по всем аккаунтом диллеров пройдемся чтобы историю платежей проверить
# - вдруг чего не выплачено
# задаем в теле скрипта:
# only_list (=None - значит с записью в БД)
# from_dt 
    # = '2013-12-29T10:42:33Z'
    # = '0' - всю историю
    # = None - берет с БД нашей последнюю дату опроса
    # = 'same' - взяь дату из нашей базы
def proc_history(db, only_list=None, ed_acc=None, from_dt_in=None):
    deal = db(db.deals.name==deal_name).select().first()
    ss = []
    for dealer_acc in db(db.dealers_accs).select():
        if ed_acc:
            if ed_acc != dealer_acc.acc:
                # если задан на входе аккаунт и это не он
                continue
        else:
            ss += [dealer_acc.acc]
            print '\n', dealer_acc.acc
            # если перебо всех, то пропустим неиспользуемые
            if not dealer_acc.used:
                # если счет не используется
                ss += [' unused']
                print ' unused'
                continue
        if not dealer_acc.skey:
            # если ключ доступа не задан
            print ' unused skey'
            continue
        dealer = db.dealers[dealer_acc.dealer_id]
        if not dealer.used:
            print ' dealer unused'
            continue
        #ecurr=db.ecurrs[dealer_acc.ecurr_id]
        if only_list:
            ss1 = '%s : %s' % (dealer.name, dealer_acc.acc)
            ss += [ss1]
            print '\n', ss1

        # from_dt_in - не трогаем так как в цикле его можно переопределить и будет ошибка для других аккаунтов!!
        if from_dt_in == 'same' or not from_dt_in:
            # обязательно нужно разделить иначе при путой даде буде 'same' брать
            from_dt = dealer_acc.from_dt or '0'
        else:
            from_dt = from_dt_in

        ss1 = 'try get_history_inputs from dt: %s' % from_dt
        print ss1
        if only_list:
            ss += [ss1]

        # тут всегда будет выдавать последнюю запись взода рублей
        tab = ed_common.get_history_inputs(dealer, dealer_acc, from_dt )
        #tab = sorted(tab, key='datetime')
        #print 'len(tab)', len(tab)
        #if only_list: ss += [tab]

        print 'result TABLE'
        dt_last = None
        ss += ['*** INCOMS ***']
        ssr = ['****']
        for rec in tab:
            ss += ssr
            ssr = ['*** ***']
            #print rec
            # запомним время последней обработанной транзакции
            if True or not dt_last:
                # вроде теперь в прямом порядке
                # ---------
                # тут записи в обратном порядке идут
                # поэтому надо время у первой записи взять сразу
                dt_last = rec['datetime']
            if rec['status']!='success': continue
            op_id = 'operation_id' in rec and rec['operation_id']
            if not op_id: continue
            print  'proc_history', rec['datetime']

            if only_list:
                if u'sender' not in rec:
                    #for (k, v ) in rec.iteritems():
                        #if type(v) == type(u''):
                            #v = v.decode('utf8')
                            #v = v.decode('ascii')
                            #rec[k] = v

                    ss1 = rec
                    #print rec.get('title').encode('utf-8')
                else:
                    ss1 = dict( sender=rec['sender'], amount=rec['amount'], dt=rec['datetime'], mess=rec['message'], op_id=rec['operation_id'])
                print ss1
                ssr += [ss1]

            buy_rec = db( (db.buys.dealer_acc_id==dealer_acc.id)
                    & (db.buys.operation_id== op_id)
                    ).select().first()
            if buy_rec:
                # если такая операция длля этого аккаунта уже есть то пропустим
                if only_list:
                    ss1 = 'its in buys'
                    ssr += [ss1]
                
                continue
            
            #info = ed_common.get_payment_info( dealer, dealer_acc, op_id )
            info = rec
            #print info
            # запомним то что на аккаунте было телодвижение
            bal = float(info.get('balance') or dealer_acc.balance or 0)
            amo=info.get('amount', 0)
            id_trans = ed_common.add_trans(db,dict(dealer_acc_id=dealer_acc.id,
                    info='%s' % info, balance=bal, amo=amo, vars=info,
                    op_id=op_id))
            # id_trans УЖЕ ПРОВЕРЕНО ВЫШЕ НА ПОВТОР
            # это новая транзакция - надо балансы сдвинуть
            # сначала изменим все балансы - без лимитных балансов
            # поидее тут все записи - приход - так что баланс ++
            ed_bal.update(db, dealer_acc, amo, dealer, limited=False)
            # теперь обновим баланс - чтобы он не сбивался
            if bal:
                dealer_acc.update_record(balance = bal)
                print dealer_acc.acc,'ball updated:', bal

            info, mess = ed_common.is_payment_for_buy(db, dealer, dealer_acc, info)
            if not info:
                # это не наш платеж - пропустим
                #log(db, mess)
                if only_list:
                    ss1 = 'NOT is_payment_for_buy: %s' % mess
                    ssr += [ss1]
                continue
            # тут наш вход - надо его запомнить в базу ....
            # хотя можно без коммита - так как тут нет выплат
            # и номер обработанной транзакции тоже не сохранится
            ##amo = info['amo']
            xcurr = info['xcurr']
            addr = info['addr']

            ss1 = 'ADDED: %s xcurr.id:%s %s %s' % ( amo, xcurr and xcurr.id, addr, rec['datetime'])
            if not only_list:
                buy_id = db.buys.insert(
                    dealer_acc_id = dealer_acc.id,
                    buyer = info['sender'],
                    operation_id = op_id,
                    xcurr_id = xcurr and xcurr.id,
                    addr=addr,
                    amount = amo,
                    ## если неопределена крипта выхода то ожидаем
                    status = xcurr and addr and 'progress' or 'addr waiting',
                    )
                db.buys_stack.insert(ref_=buy_id)
                print ss1
            else:
                ssr += [ss1]

        ss += ssr

        if dt_last:
            # если записи новые были то обновим
            dealer_acc.from_dt = dt_last
        dealer_acc.update_record()
        if only_list:
            ss1 = 'processed to: %s' % dealer_acc.from_dt
        else:
            db.commit()

    return ss

from time import sleep
Test = None

def serv_proc_history(db, interval=None):
    interval = interval or 666
    print __name__, ' interval:', interval

    while True:
        try:
            proc_history(db)
        except Exception as e:
            print 'ERROR:', __name__, e

        if Test: break
        sleep(interval)
