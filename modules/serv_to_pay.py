#!/usr/bin/env python
# coding: utf8
import sys
import random
from time import sleep
import json

import datetime
from decimal import Decimal

from gluon import current

import db_common
import db_client
import rates_lib
import gifts_lib
import partners_lib
import ed_common
import crypto_client
import clients_lib

TIME_DIFF_FOR_ORDERS = 1500 # sec, older to delete
USE_UNLIM=False

# по одному делу нельзя болье 60тыс в месяц платить
# тоесть когда комуто уже выплочено - там будет ограничение врублено
MAX_PAYMENT_IN_MONTH = 60000

volume_out_up_koeff = Decimal(1.2)

## statuses - wait refuse try
dealer_deal_NONE = None

def log(db, mess):
    print mess
    db.logs.insert(mess='PAY: %s' % mess)
def log_commit(db, mess):
    log(db,mess)
    db.commit()


#####################################################################################
# сначала удалим стек - чтобы ошибки ниже не создпвали 2-е выплаты
def get_pay_ins_recs(db, geted_pays):
    geted_pays_recs = []
    for id in geted_pays:
        st = db.pay_ins_stack[id]
        geted_pays_recs.append( db.pay_ins[st.ref_] )
        del db.pay_ins_stack[id]
    db.commit()
    return geted_pays_recs

# переданная запись не удаляется по del <запись> - видимо нет указания на таблицу
# status= True - этот вход будет возвращен обратно
def mark_pay_ins(db, geted_pays, status, status_mess='', to_refuse=None):
    for id in geted_pays:
        st = db.pay_ins_stack[id]
        st.update_record( in_proc = 0, to_refuse = to_refuse, tries = (st.tries or 0) + 1)
        pay_in = db.pay_ins[st.ref_]
        pay_in.update_record(status = status, status_mess = status_mess)

def check_order(db, order_stack_id):
    order_id = None # был ли использован заказ
    if order_stack_id:
        order_id = db.orders_stack[order_stack_id].ref_
        #print 'del order_stack_id:',order_stack_id
        # если был ордер, то удалим его из стека
        # оказывается если сюда передать готовую запись - удаления не будет
        del db.orders_stack[order_stack_id]
    return order_id

# сделаем платеж електр.денег с заданнного аккаунта диллера
# и запомним все в базе
# если есть order_stack_id - то и его удалим
def make_edealer_payment(db, geted_pays,  curr_in, xcurr, curr_out, ecurr, vol_in, volume_out, deal_acc_addr, rate, order_stack_id=None, dealer=None, dealer_acc=None, dealer_deal=None):
    #print 'try payout rub:', vol_in, curr_in.abbrev, volume_out , curr_out.abbrev, deal_acc_addr.addr, '\n', geted_pays
    # заодно проверим не занята ли база is loocked
    # сейчас копим на счету услуги if volume_out>13:
    #    # но это не для мелких платежей
    #    log_commit( db, 'try payout: make_edealer_payment %s[%s] -> %s[%s] %s \n geted_pays: %s' % ( vol_in, curr_in.abbrev, volume_out, curr_out.abbrev, deal_acc_addr.addr, geted_pays))
    #return

    ## проверим запасы - если есть ограничение по баласу то откажем в выплатах
    max_bal = Decimal(curr_in.max_bal or 0)
    ##print 'types:', type(curr_in.balance), type(curr_in.deposit)
    ## float - Decimal - хотя в базе поле описано как ДЕЦИМАЛ
    bal_dep = Decimal(curr_in.balance or 0) - Decimal(curr_in.deposit or 0)
    if max_bal and max_bal > 0 and max_bal - bal_dep < 0: ##vol_in: тут уже в баланс упал вход
        mark_pay_ins(db, geted_pays, 'wait', current.T('Превышен запас монет: %s + %s > %s') % (bal_dep, vol_in, max_bal))
        db.commit()
        return

    deal_acc = db.deal_accs[deal_acc_addr.deal_acc_id]
    deal = db.deals[deal_acc.deal_id]

    in_proc = random.randint(1, 99999)
    desc = []
    for id in geted_pays:
        inp_stk = db.pay_ins_stack[id]
        # запомним что мы обрабатываем этот вход
        inp_stk.update_record( in_proc = in_proc )
        inp_rec = db.pay_ins[inp_stk.ref_]
        desc.append({ 'txid': inp_rec.txid, 'vout': inp_rec.vout})
    # сохраним базу - чтобы все процессы видели что мы обрабатываем записи стека
    db.commit()
    #print 'make_edealer_payment', deal_acc.acc, volume_out, curr_out.abbrev, '%s' % desc
    #  теперь ждем чтобы записи в базк записались
    # - так чтобы пораллельно их не обработали
    sleep(1)
    pay_error = None # если мы не заплатили то не вносить изменения баланса и пр

    # если уже идет обработка стека то выход
    # и она не наша
    for id in geted_pays:
        inp_stk = db.pay_ins_stack[id]
        if inp_stk.in_proc and inp_stk.in_proc != in_proc:
            # если этот вход в стеке уже вобработке то удалим его
            # нет просто выход нажмем - чтобы не было свалки обработки входов
            log(db, ' input_stack.in_proc == True : return' )
            return

    print '\ntry payout:', vol_in, curr_in.abbrev, '-->', volume_out, curr_out.abbrev, deal_acc_addr.addr, '\n', 'geted_pays:', geted_pays
    #log(db, '%s %s %s %s %s %s %s %s %s' % ('try payout:', vol_in, curr_in.abbrev, '-->', volume_out, curr_out.abbrev, deal_acc_addr.addr,  ' - geted_pays:', geted_pays))

    if ecurr:
        MIN = deal.MIN_pay
    else:
        xcurr_out = db(db.xcurrs.curr_id == curr_out.id).select().first()
        MIN = (xcurr_out.txfee or curr_out.fee_in or curr_out.fee_out) * 10

    #log(db, 'volume_out %s, MIN %s' % (volume_out, MIN))

    if volume_out <= 0 or MIN > 0 and volume_out < MIN:
        print volume_out, ' <<< ', MIN
        #Теперь добавляем к переплате на счет услуги
        # так как в volume_out есть вычета абсолютные мзды то оно меньше нуля
        if order_stack_id:
            # если есть заказ на курс то по этому курсу
            volume_out = vol_in * rate
            print 'volume_out by ORDER', order_stack_id, rate, ' ->', volume_out
        else:
            # иначе возьмем просто по курсу без абсолютных добавок
            if ecurr and not dealer_deal:
                volume_out = vol_in * rate
                # лимиты диллера не учитываем
                dealer, dealer_acc, dealer_deal = ed_common.select_ed_acc(db, deal, ecurr, volume_out, unlim=USE_UNLIM)
            # и возьмем таксу без fee
            # тут берем без учета что еще на нас начислит диллер за эту услугу (учет в ed_common.pay)
            volume_out, _ = db_client.calc_fees(db, deal, dealer_deal_NONE, curr_in, curr_out, vol_in, rate,
                                            is_order=None,
                                            note=None, only_tax=1)
            print 'volume_out by TAX', volume_out
        print 'add to_pay', volume_out
        deal_acc.update_record( to_pay = (deal_acc.to_pay or 0)  + volume_out )
        pay_ins_recs=get_pay_ins_recs(db, geted_pays)
        # и запомним на что потратили входы
        for pay_in in pay_ins_recs:
            ## None pay_in.payout_id = pay_out_id
            if pay_in.amount == vol_in:
                volume_out_it = volume_out
            else:
                volume_out_it = round(float(volume_out * pay_in.amount / vol_in),8)
            pay_in.status = 'added'
            pay_in.status_mess = volume_out_it
            ## Njne еще не определили заказ  pay_in.order_id = order_id # запомним использованный заказ
            pay_in.update_record()
        db.commit()
        return

    client = db(db.clients.deal_id==deal.id).select().first()
    if client:
        # это наш клиент- магазин, у него не делаем перебор
        # и не делаем платеж вообще, а учитываем его просто в своей базе
        print 'make_edealer_payment ist my CLIENT:', deal.id, 'client:',client
        # здесь валюта выходя есть авлюта входа для клиента - так как он
        # вообще не должен знать чем нам пользователь наш заплатил
        clients_tran_id, client_bal = clients_lib.mem_input(db, client, deal_acc.acc, volume_out, curr_out, '%s' % desc)
        #mark_pay_ins(db, geted_pays, 'client', 'client_trans: %s' % clients_tran_id)
        res = None
        order_id = check_order(db, order_stack_id)
        # и запомним на что потратили входы
        # удалим все взятые входы крипты для этого вывода
        # имеено ТУТ чтобы ошибки ниже уже не повлияли на ошибочный повторный вывод
        # а то иногда ошибки ниже не дают запомнить что мы уже выплатили все тут
        pay_ins_recs=get_pay_ins_recs(db, geted_pays)
        for pay_in in pay_ins_recs:
            print 'clients_tran_id:', clients_tran_id
            pay_in.clients_tran_id = clients_tran_id
            pay_in.status = 'ok'
            pay_in.order_id = order_id # запомним использованный заказ
            pay_in.update_record()
        db.commit()
    else:

        # здесь выплаты только электронными деньгами
        gift_amo = 0
        if deal_acc.gift_amount and deal_acc.gift_amount >0 and deal_acc.gift_pick > 0:
            # если есть подарок у аккаунта то его включим
            gift_amo = Decimal(deal_acc.gift_amount < deal_acc.gift_pick and deal_acc.gift_amount or deal_acc.gift_pick)
            ##print type(Decimal(0.3)), type(volume_out)
            if gift_amo > Decimal(0.3) * volume_out: gift_amo = Decimal(0.3) * volume_out
            rrr = random.randint(1, 100)
            # вероятность берем
            # сделаем случайны подарок - чем меньше сумма остатка тем меньше вероятность подарка
            pick_ver = gifts_lib.pick_ver(deal_acc.gift_amount, gift_amo)
            if rrr > int(pick_ver * 100):
                gift_amo = 0
                #print 'NOT lucky'
            else:
                # подарок выпал
                deal_acc.gift_amount = deal_acc.gift_amount - gift_amo
                deal_acc.gift_payed = deal_acc.gift_payed and deal_acc.gift_payed + gift_amo or gift_amo
        #print 'gift_amo:', gift_amo

        # проверим бонус патртнера - если он больше 100 то выплатим его
        partner_sum = Decimal(deal_acc.partner_sum or 0)
        if partner_sum: ## тут разные валюты и разные значения! and partner_sum > current.PARTNER_MIN:
            #print 'PARTNER -> deal_acc.partner_sum:', partner_sum
            deal_acc.partner_sum = 0
            deal_acc.partner_payed = (deal_acc.partner_payed or 0) + partner_sum
        else:
            # Сбросим а то оно прибавится ниже
            partner_sum = 0

        amo_to_pay = Decimal(deal_acc.to_pay or 0)
        add_vol = gift_amo + partner_sum + amo_to_pay

        volume_out_full = volume_out + add_vol

        # тут ищем акккаунт с еще не превышенным лимитом на платежи и максим балансом среди разных диллеров
        if ecurr:
            # это фиат с аккаунтами разными у диллера
            ##dealer_acc = None ## тут могут добавиться на счету недоплаты! поэтому новый нужно выбрать счет диллера
            if dealer_acc and dealer_acc.balance > volume_out_full:
                print 'preselected dealer_acc:', dealer_acc.acc, dealer_acc.balance
            else:
                dealer, dealer_acc, dealer_deal = ed_common.select_ed_acc(db, deal, ecurr, volume_out_full, unlim=USE_UNLIM)
                if dealer_acc:
                    print 'select_ed_acc -> dealer_acc:', dealer_acc.acc, dealer_acc.balance
                else:
                    mark_pay_ins(db, geted_pays, 'try', (dealer and dealer.name or 'dealer=None') + ': dealer_acc not found')
                    db.commit()
                    print 'ERROR: make_edealer_payment - dealer_acc=', dealer_acc, 'deal id:', deal.id, 'ecurr id:', ecurr.id
                    return

            balance = dealer_acc.balance
            if not balance:
                balance = ed_common.get_balance(dealer, dealer_acc )
                if not balance or balance < 0:
                    mark_pay_ins(db, geted_pays, 'wait', dealer.name + ': balance=None')
                    db.commit()
                    print 'ERROR: make_edealer_payment - not balance', dealer_acc
                    return
            #print 'make_edealer_payment', dealer.name, ':', dealer_acc.acc, 'balance:', balance

            ###############################################################
            # теперь надо посмотреть насколько превышен лимит платежа за месяц для этого аккаунта этого дела
            if not deal_acc.payed_month_num or datetime.date.today().month != deal_acc.payed_month_num:
                # если новый месяц то сбросим в ноль
                deal_acc.payed_month_num = datetime.date.today().month
                deal_acc.payed_month = 0

            if deal.is_shop:
                # для сайтов и обмена - без изменения величины оплаты так как там жесткая величина
                over_turns = 0
            else:
                over_turns = (deal_acc.payed_month or 0) / (deal.MAX_pay or 777 )

            if over_turns > 5:
                volume_out_full = volume_out_full * Decimal(0.98) # если превышение боле чем в 6 раза то 2% себе сразу
            elif over_turns > 4:
                volume_out_full = volume_out_full * Decimal(0.99) # если превышение боле чем в 4 раза то 1% себе сразу
            elif over_turns > 3:
                volume_out_full = volume_out_full * Decimal(0.995) # если превышение боле чем в 2 раза то 0.5% себе сразу
            elif over_turns > 2:
                volume_out_full = volume_out_full * Decimal(0.9925) # если превышение боле чем в 1 раза то 0.25% себе сразу

        else:
            # это обмен на другую крипту
            # тут баланс просто у крипты берем
            balance = db_client.curr_free_bal(curr_out)

        ######################################################
        print 'volume_out_full > balance', volume_out_full, balance
        if volume_out_full > balance:
            if len(geted_pays)==1:
                pay_error = 'out of balance'
                res = {'error': pay_error}
                #print pay_error, volume_out_full, balance, curr_out.abbrev
            else:
                for id in geted_pays:
                    p_i_s = db.pay_ins_stack[id]
                    pay_in = db.pay_ins[p_i_s.ref_]
                    vol_in_one = pay_in.amount
                    volume_out_one = vol_in_one / vol_in * volume_out
                    # размарозим вход - чтобы его могли обработать
                    p_i_s.update_record( in_proc = False )
                    db.commit()
                    # тут dealer_acc, dealer_deal не передаем - там новые берем
                    make_edealer_payment(db, [id],  curr_in, xcurr, curr_out, ecurr, vol_in_one, volume_out_one, deal_acc_addr, rate, order_stack_id)
                return
        elif ecurr:
            # надо проверить величину выплат в месяц - не более 60тыс можно
            # только для фиата
            if deal_acc.payed_month and deal_acc.payed_month + volume_out_full > MAX_PAYMENT_IN_MONTH:
                # переплата - включаем задержку
                pay_error = 'monthly_limit_60_exceeded'
                res = {'status':'wait', 'error':'wait', 'error_description': pay_error}
            else:
                ####################
                #res = {'status':'success', 'balance': 123, 'payment_id': 'sldkflsfj3', 'invoice_id': '78676654',
                #    'sum_taken': volume_out_full}
                #res = {'status':'testedd', 'error':'test', 'error_description':'tst_descr', }
                log_on = None # None - log some, False - notg, True - log all
                res = ed_common.pay(db, deal, dealer, dealer_acc, dealer_deal, deal_acc.acc,
                            volume_out_full, log_on )
                log( db, 'PAYed ecurr - res: %s' % res)
        else:
            # сюда пришло значит баланса хватает и это на выходе криптовалюта
            dealer_acc = None
            ## ыше уже задали xcurr_out = db(db.xcurrs.curr_id == curr_out.id).select().first()
            res, bal = crypto_client.send(db, curr_out, xcurr_out, deal_acc.acc, volume_out_full)
            #print bal, res
            if bal:
                curr_out.update_record( balance = bal )
            if type(res) == type(u' '):
                # прошла транзакция, создадим массив инфо
                res = { 'payment_id': res, 'status': 'success' }
            log( db, 'PAYed xcurr - res: %s' % res)

        ####################
        if not res or 'error' in res or res.get('status') != 'success':
            ## res = { 'status': 'error', 'error':'so_small','error_description': '%s < txfee %s' % (amo, txfee) }
            # платежа не произошло - выход
            pay_error = res.get('error_description')
            if not pay_error or pay_error == u'':
                pay_error = res.get('error', 'dealer error')
            elif ecurr:
                # только для фиата с дилерами
                if pay_error == 'limit_exceeded':
                    # тут превышен лимит в день или даже в месяц - надо брать другой счет
                    # причем сумму в месяц не меняем - чтобы знать сколько в месяц прошло
                    dealer_acc.day_limit = datetime.date.today().day
                    dealer_acc.day_limit_sum = -dealer_acc.day_limit_sum
                    dealer_acc.update_record()
                elif pay_error == 'monthly_limit_60_exceeded':
                    # тут превышен лимит в день или даже в месяц - надо брать другой счет
                    # причем сумму в месяц не меняем - чтобы знать сколько в месяц прошло
                    dealer_acc.mon_limit = datetime.date.today().month
                    dealer_acc.mon_limit_sum = -dealer_acc.mon_limit_sum
                    dealer_acc.update_record()
                elif pay_error == 'not_enough_funds':
                    # баланс кошелька поменялся - видимо вручную политили с него
                    balance = ed_common.get_balance(dealer, dealer_acc )
                    dealer_acc.update_record(balance = balance or 0)
                else:
                    ed_common.dealer_deal_errs_add(db, dealer_deal, deal_acc.acc, '%s' % res)

            # нельзя менять так как не будет возврата pay_error = pay_error + ' (%s ... %s)' % (round(volume_out_full,2), dealer_acc.acc[-5:])
            if pay_error=='technical_error' or pay_error=='payment_refused':
                mark_pay_ins(db, geted_pays, 'try', pay_error)
            elif 'Unknown operator for phone' in pay_error:
                ## Unknown operator for phone-number=PhoneNumber{79016661485 (RU)}
                ## тут сразу возврат и написать туда чтобы оператора нашел сам
                pay_error = 'Unknown operator. Please find this operator in list of services'
                mark_pay_ins(db, geted_pays, 'refuse', pay_error, to_refuse=True)
                pass
            else:
                mark_pay_ins(db, geted_pays, 'wait', pay_error)
            db.commit()
            print 'serv to pay **** - ERROR: make_edealer_payment ', pay_error, 'RES:', res
            return

        # удалим все взятые входы крипты для этого вывода
        # имеено ТУТ чтобы ошибки ниже уже не повлияли на ошибочный повторный вывод
        # а то иногда ошибки ниже не дают запомнить что мы уже выплатили все тут
        # запомним платеж фиата
        amo_taken = Decimal(res.get('sum_taken', volume_out_full))
        pay_out_id = db.pay_outs.insert(
             ref_ = deal_acc.id, # за какое дело и за какого клиента
             dealer_acc_id = dealer_acc and dealer_acc.id, # с какого моего аккаунта дилера оплачено
             amount = volume_out,
             amo_taken = amo_taken,
             amo_to_pay = amo_to_pay,
             amo_in = vol_in,
             amo_gift = gift_amo,
             amo_partner = partner_sum,
             created_on = datetime.datetime.now(),
             #info=json.dumps({'payment_id'res['payment_id'], 'invoice_id': res['invoice_id'] })
             #info = res and json.dumps(res) or None
             vars = res,
             ## возможно что нет выплаты - то добавим ссобщение об ошибке
             txid = res.get('payment_id', pay_error),
             )
        order_id = check_order(db, order_stack_id)
        # тут внутри commit сразу
        pay_ins_recs=get_pay_ins_recs(db, geted_pays)
        # и запомним на что потратили входы
        for pay_in in pay_ins_recs:
            pay_in.payout_id = pay_out_id
            pay_in.status = 'ok'
            pay_in.status_mess = pay_in.status_mess and ('(%s)' % pay_in.status_mess) or ''
            pay_in.order_id = order_id # запомним использованный заказ
            pay_in.update_record()
        db.commit()

        # тут же в ответе приходит новый баланс
        # запомним суммарно по этому счету
        if ecurr:
            if res and 'balance' in res: dealer_acc.balance = Decimal(res['balance'])
            # лимиты дневные - месячные подправим
            dealer_acc.day_limit_sum = dealer_acc.day_limit_sum + amo_taken
            dealer_acc.mon_limit_sum = dealer_acc.mon_limit_sum + amo_taken
            dealer_acc.update_record()
            #print 'payed, new balance:', dealer_acc.balance
            # сразу таксу дилера на это дело запомним
            tax = res.get('tax')
            # причем только если они еще не заданы вообще
            # и число использований меньше 3
            if not dealer_deal.tax and dealer_deal.fee and tax and dealer_deal.taken and dealer_deal.taken < 3:
                # для ПРИН английское имя только чтобы ошибок конверт не было
                print 'dealer new TAX:', deal.name2, tax
                # если уже много раз использовано то не изменяем таксу - мож она вручную уже выставлена
                dealer_deal.tax = tax
            dealer_deal.taken += 1
            dealer_deal.update_record()

        # теперь надо заплатить нашему партнеру
        # если это дело партнерам оплачивается
        if deal_acc.gift and not deal.not_gifted: # and not deal_acc.partner: # andl en(deal_acc.gift) > 5:
            try:
                partners_lib.calc(db, deal, curr_out, deal_acc, volume_out)
            except:
                print 'except partners_lib.calc(db, deal, curr_out, deal_acc, volume_out)'

        # запомним месячную выплату - ее надо ограничивать
        deal_acc.payed_month = deal_acc.payed_month and deal_acc.payed_month + volume_out or volume_out

        # запомним всего оплачено по этому заказу - и для клиентов тоже
        deal_acc.payed = deal_acc.payed and deal_acc.payed + volume_out or volume_out
        # надо запомнить если недоплатили или переплатили
        #print res
        #print 'deal_acc.to_pay = volume_out_full - amo_taken'
        #print deal_acc.to_pay, volume_out_full, amo_taken
        try:
            # дадим на следующий платеж ему от нас 0,5%!
            #   TO_COIN_ID != deal.id
            add_bonus = 0
            deal_tax = deal.tax
            if deal_tax and deal_tax > 0:
                ##if deal.id == TO_COIN_ID:
                ##    add_bonus = 0.001
                if deal_tax >1.9:
                    add_bonus = 0.005
                elif deal_tax >0.9:
                    add_bonus = 0.002
                else:
                    add_bonus = 0.001
                add_bonus = Decimal(add_bonus) * volume_out_full
            ## найденнный бонус начислим или как партнерские или как подарок
            if deal_acc.partner:
                deal_acc.partner_sum = (deal_acc.partner_sum or 0) + add_bonus
            else:
                deal_acc.gift_amount = (deal_acc.gift_amount or 0) + add_bonus
                ## и если кусочек меньше намного то увеличим кусочек
                if deal_acc.gift_pick * 7 < deal_acc.gift_amount:
                    deal_acc.gift_pick = deal_acc.gift_amount / 7

            deal_acc.to_pay = volume_out_full - amo_taken
        except:
            print 'deal_acc.to_pay = volume_out_full - amo_taken:', type(deal_acc.to_pay), type(volume_out_full), type(amo_taken)

    deal_acc.update_record()

    # запомниим статисткиу по делу
    count = deal.count_ or 0
    average = deal.average_ or 0
    if volume_out: deal.average_ = count/( count + 1 ) * average + volume_out/( count + 1 )
    deal.count_ = count + 1
    deal.update_record()

    ####################

    # заплмним сатиститку для крипты по этому делу
    if volume_out: db_common.currs_stats_update(db, curr_in.id, deal.id, volume_out)

    # обновим балансы дилеров и валюты
    # поидее это в ed_common YD_ все проходит
    ##if not client: db_common.update_balances(curr_out, -amo_taken, dealer)

    #if gift_amo and gift_amo > 0:
    #    print 'gift_amo', gift_amo
    #print 'Payed!'
    log(db, 'Payed! geted_pays: %s' % geted_pays)
    db.commit()

#
# найдем телефон по делу, сделаем проплату и удалим стек платежей и отметимся сумммой в деле
def make_edealer_free_payment(db,
            curr_in,
            xcurr,
            #account,
            deal_acc_addr,
            geted_pays, amo):
    # возьмем дело для этой валюты и этого акка
    # имя акка + валюта входа должно быть уникальным (выходная валютта в имени аккаунта)
    r = db.deal_accs[deal_acc_addr.deal_acc_id]
    if not r:
        print 'ERROR: (make_edealer_free_payment) "deal_accs" not found - ', curr_in.abbrev, deal_acc_addr, amo
        mark_pay_ins(db, geted_pays, 'refuse', current.T('"deal_accs[%s]" не найден') % deal_acc_addr.deal_acc_id)
        db.commit()
        return

    if not r.acc:
        print 'ERROR: (make_edealer_free_payment) "deal_accs.acc" = None ', curr_in.abbrev, deal_acc_addr, amo
        mark_pay_ins(db, geted_pays, 'refuse', 'deal_accs[%s].acc=None' % deal_acc_addr.deal_acc_id)
        db.commit()
        return
    deal = db.deals[r.deal_id]
    if not deal:
        print 'ERROR: (make_edealer_free_payment) "deal" = None ', curr_in.abbrev, deal_acc_addr, amo
        mark_pay_ins(db, geted_pays, 'refuse', 'deal[%s]=None' % r.deal_id)
        db.commit()
        return

    volume_in = amo
    #log( db, 'make free-pay for deal_acc: %s %s[%s]' % ( r.acc, volume_in, curr_in.abbrev))

    curr_out = db.currs[r.curr_id]
    ecurr = dealer = dealer_acc = dealer_deal = None # у клиентов тут Ноне

    client = db(db.clients.deal_id == deal.id).select().first()
    if client:
        pass #dealer = None
    else:
        # тут только фиат на выходе
        ecurr = db(db.ecurrs.curr_id==curr_out.id).select().first()

    # курс реальный берем - чем больше тем ниже
    s_b = True
    d_e = None # перевод с биржи на диллера
    # так как у нас тут неизвестно количестыво на выходе а есть
    # количество на входе, то надо обратную операцию:
    # поменяем in out s_b
    pr_b, pr_s, pr_avg = rates_lib.get_average_rate_bsa(db, curr_in.id, curr_out.id, None)
    if not pr_avg:
        mark_pay_ins(db, geted_pays, 'wait', 'best rate not found!')
        db.commit()
        log(db,  '%s[%s] -> [%s] - best rate not found!' % ( amo, curr_in.abbrev, curr_out.abbrev))
        return
    volume_out, _, best_rate = rates_lib.get_rate(db, curr_in, curr_out, amo)
    best_rate = Decimal(best_rate)
    volume_out = Decimal(volume_out)
    if client:
        pass
    else:
        if ecurr:
            # теперь нам известен объем на выходе - найдм диллера
            dealer, dealer_acc, dealer_deal = ed_common.select_ed_acc(db, deal, ecurr, volume_out, unlim= USE_UNLIM)
        # тут добавляем еще мизерный оброк себе в карман = 1 рубль например:
        # и оброк с конкретнгого дела
        is_order = True
        try:
            # тут берем без учета что еще на нас начислит диллер за эту услугу (учет в ed_common.pay)
            volume_out, mess = db_client.calc_fees(db, deal, dealer_deal_NONE, curr_in, curr_out, amo, best_rate, is_order, note=0)
        except Exception as e:
            print 'PAY error db_client.calc_fees', e
            volume_out, mess = amo * best_rate, 'error in fees'

        #log_commit(db, mess)
    #print volume_in, volume_out, best_rate, '=', volume_in * best_rate

    ##print 'volume_in:', type(volume_in), 'volume_out:', type(volume_out)
    #################################################
    # оплатить и обновить базу
    # тут уже берем dealer_acc, dealer_deal
    make_edealer_payment(db, geted_pays, curr_in, xcurr, curr_out, ecurr, volume_in, volume_out, deal_acc_addr, best_rate, None, dealer, dealer_acc, dealer_deal)
    #################################################


# обработать все сотавшиеся платежи
def proc_free_payments(db, curr_in, xcurr, used_pays):
    # сначала найдем группы по аккаунту - валюте
    for grp in db((db.pay_ins_stack.ref_==db.pay_ins.id)
        & (db.pay_ins.ref_ == db.deal_acc_addrs.id )
        & (db.deal_acc_addrs.xcurr_id == xcurr.id)
        ).select(groupby=(db.deal_acc_addrs.id)):
        #print grp #.payments.xcurr_id, grp.payments.account
        #continue
        # теперь для группы
        # тут уже валюта выбрана, дело и аккаунт пользователя тоже
        grp_deal_acc = db.deal_accs[ grp.deal_acc_addrs.deal_acc_id ]
        ecurr = db(db.ecurrs.curr_id == grp_deal_acc.curr_id).select().first()
        if ecurr:
            # если на выходе фиат то проверим на превышение одного платежа
            curr_out = db.currs[ grp_deal_acc.curr_id]
            grp_deal = db.deals[ grp_deal_acc.deal_id ]
            fee_curr = db.currs[ grp_deal.fee_curr_id]
            geted_pays = [grp.pay_ins_stack.id]
            print 'curr out:', curr_out.abbrev, ' fee_curr:', fee_curr.abbrev, 'grp_deal.MAX_pay:', grp_deal.MAX_pay
            pr_b, pr_s, pr_avg = rates_lib.get_average_rate_bsa(db, curr_in.id, curr_out.id, None)
            if not pr_avg:
                print 'proc_free_payments - rates None'
                mark_pay_ins(db, geted_pays, 'wait', 'best rate not found!')
                # нет курса валют - пропустим
                continue
            pr_b, pr_s, pr_avg_fee = rates_lib.get_average_rate_bsa(db, curr_out.id, fee_curr.id, None)
            if not pr_avg_fee:
                print 'proc_free_payments - rates None for pr_avg_fee'
                mark_pay_ins(db, geted_pays, 'wait', 'best rate for fee not found!')
                # нет курса валют - пропустим
                continue
            rate_out = Decimal(pr_avg * pr_avg_fee)
            print pr_avg, pr_avg_fee, rate_out

        geted_pays = []
        amo = 0
        for pay in db((db.pay_ins_stack.ref_==db.pay_ins.id)
              & (db.pay_ins.ref_ == db.deal_acc_addrs.id )
              & (db.deal_acc_addrs.id == grp.deal_acc_addrs.id)
              ).select():
            # если он еще не обрабатывается паралельно
            if pay.pay_ins.status in db_common.STATUS_REFUSED or pay.pay_ins_stack.to_refuse:
                # этот вход мы отвергаем - ее выслать надо назад
                # он будет возвращен обратно
                continue
            if pay.pay_ins_stack.in_proc or pay.pay_ins_stack.id in used_pays:
                # если этот платеж уже по заказам пытались выплатиьть
                # но у него видимо ошибка, то не платим тут
                continue
            print 'income:', pay.deal_acc_addrs.addr, pay.pay_ins.amount
            amo = amo + Decimal(pay.pay_ins.amount)
            geted_pays.append(pay.pay_ins_stack.id)
            if ecurr and amo * rate_out > grp_deal.MAX_pay:
                # если за раз уже много набралось и общая сумма платежа выше нормы - прекратить сборку
                break

        #print amo, geted_pays
        if amo > 0 :
            make_edealer_free_payment(db,
                curr_in, xcurr,
                #grp.payments.account,
                grp.deal_acc_addrs,
                geted_pays, amo)


# TODO если платеж по заказу, но была ошибка у дилепа и он не прошел
# то он останется и пойдет в свободные платежи без заказанного курса
####
# после того как обработали блок крипты
# идем сюда и смотрим входы и если есть то проплачиваем
# всем записям обрабатываем присваиваем номер процесса чтобы по 2 раза из не обработать и сразу сохраняем
def proc_xcurr(db, curr_in, xcurr):
    print '\nto_pay', curr_in.abbrev
    # обработаем ордера для такой крипты (входы)
    # если ордер устарел - удалим его
    dt_order = datetime.datetime.now() - datetime.timedelta(0, TIME_DIFF_FOR_ORDERS)
    # неудаляет таблицу одну из зароса ( db((db.orders_stack.ref_==db.orders.id) & (db.orders.created_on < dt_order)).delete(db.orders_stack)
    # поэтому удалим в цикле из стека старые
    for rec in db(db.orders_stack).select():
        order = db.orders[rec.ref_]
        if order.created_on < dt_order:
            #print 'deleted' rec.id
            del db.orders_stack[rec.id]

    if not curr_in.used:
        # если валюта не используется то всем входам сделаем currency_unused - по нему будет возврат
        for r in db((db.pay_ins_stack.ref_ == db.pay_ins.id)
                 & (db.pay_ins.ref_ == db.deal_acc_addrs.id)
                 & (db.deal_acc_addrs.xcurr_id == xcurr.id)
                 ).select():
            r.pay_ins.status = 'currency_unused'
            r.pay_ins.update_record()
        return
    dt_trans = datetime.datetime.now() - datetime.timedelta(0,400)
    used_pays={}
    #deleted = None
    for r in db((db.orders_stack.ref_==db.orders.id)
        & (db.orders.ref_==db.deal_acc_addrs.id)
        & (db.deal_acc_addrs.xcurr_id==xcurr.id)
        ).select():
        #print '\n ORDER:',r

        # здесь будет время создания транзакции а не когда у нее подтвержлдения случились
        # поэтому задержку даем максимум 5 минут = 5х60
        # для оставшихся ордеров найдем платежи
        #print 'ORDER: ',r.orders.volume_in, 'TO PHONE:', r.deal_acc_addrs.xcurr_id, r.deal_acc_addrs.addr
        # для данного ордера (аккаунт+валюта) все записи в стеке с датой под ордер
        geted_pays = []
        amo = 0
        for pay in db((db.pay_ins_stack.ref_ == db.pay_ins.id)
                & (db.pay_ins.ref_ == r.deal_acc_addrs.id ) # платеж к нашему адресу относится
                & (db.pay_ins.created_on > dt_trans) # платеж не устарел для Закакза
                ).select():
            if pay.pay_ins.status in db_common.STATUS_REFUSED or pay.pay_ins_stack.to_refuse:
                # этот вход мы отвергаем - ее выслать надо назад
                # он будет возвращен обратно
                continue
            #print 'found PAY for order:', pay.pay_ins.amount
            id = pay.pay_ins_stack.id
            # если он еще не обрабатывается параллельно
            if pay.pay_ins_stack.in_proc or id in used_pays: continue
            amo1 = amo + Decimal(pay.pay_ins.amount)
            if amo1 > r.orders.volume_in: break
            amo = amo1
            geted_pays.append(id)
            used_pays[id] = True
            #print 'summ:', amo

        # собрали нужную сумму на этот ордер
        if amo == 0:
            # если нет платежей то пропустим
            continue

        rate = Decimal(r.orders.volume_out) / Decimal(r.orders.volume_in)
        if amo < r.orders.volume_in:
            # если количвество входа не равно тому что в заказе
            #print 'order RATE for new vol_out:', rate
            volume_out = amo * rate
        else:
            volume_out = Decimal(r.orders.volume_out)
        #print 'serv_to_pay.proc_xcurr amo:', amo, 'volume_out:', volume_out

        deal_acc = db.deal_accs[r.deal_acc_addrs.deal_acc_id]
        curr_out = db.currs[deal_acc.curr_id]
        ecurr = db(db.ecurrs.curr_id == curr_out.id).select().first()
        ##deal = db.deals[deal_acc.deal_id]

        # сделаем платеж и базу обновим
        # тут надо ордер-стек тоже передать туда на удаление
        make_edealer_payment(db, geted_pays,  curr_in, xcurr, curr_out, ecurr, amo, volume_out, r.deal_acc_addrs, rate, r.orders_stack.id, dealer=None, dealer_acc=None, dealer_deal=None)

    # все оставшиеся палатежи в стеке для этой крипты (входы)
    proc_free_payments(db, curr_in, xcurr, used_pays)

    # это после каждого платежа сохраняет db.commit()
