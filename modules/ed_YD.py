#!/usr/bin/env python
# coding: utf8
#from gluon import *
import urllib
import urllib2
#import json
from gluon.contrib import simplejson as json
import time

from gluon import current
DOMEN = current.DOMEN

# получить инфо о параметрах тут
# https://money.yandex.ru/internal/mobile-api/get-showcase.xml?scid=4895

import common
import ed_common
import db_common

import rates_lib

PAY_PARS = { 'id': { "n": "id" }}
#PAY_PARS_P2P = [{ "n": "user"}, { "n": "order"}]
PAY_PARS_P2P = PAY_PARS
SUM_NAMES = ['sum', 'netSum', 'redsum' ]


def log(db, mess):
    print 'ed_YD - ', mess
    db.logs.insert(mess='YD: %s' % mess)
def log_commit(db, mess):
    log(db,mess)
    db.commit()

def get_pars(edlr, edlr_acc):
    api_pars = json.loads( edlr.API )
    acc_pars = json.loads( edlr_acc.pkey )
    return api_pars, acc_pars, "%s:%s" % (edlr.name, edlr_acc.acc)

def get_balance(edlr, edlr_acc):
    api_pars, acc_pars, name = get_pars(edlr, edlr_acc)
    
    res = YmGetBalanse(api_pars, edlr_acc.skey, name)
    return res

def get_rate_to(db, dealer_deal):
    pay_pars_dealer = dealer_deal.template_ and json.loads(dealer_deal.template_) or ed_YD.PAY_PARS
    rate_to = pay_pars_dealer.get('rate_to')
    if not rate_to: return 1
    
    curr_in = db(db.currs.abbrev == 'RUB').select().first()
    curr_out = db(db.currs.abbrev == rate_to).select().first()
    _a, _b, _rate = rates_lib.get_average_rate_bsa(db, curr_in.id, curr_out.id, None)
    return _rate or 1

def get_history(edlr, edlr_acc, from_dt):
    pars_str = ""
    if from_dt: pars_str = '?from="%s"' % from_dt
    res = get_history_pars(edlr, edlr_acc, pars_str)
    return res

################################################################################
# короче тут выдается история с заданной даты или сначала
# если proccessed пропущен - вся история выдается по 30 записей на странице
# и потом в proccessed записывать дату-время последней обработанной транзакции
# тут записи в обратном порядке идут
# !!!тоесть если страниц несколько то нам выдадут последние платежи!!!!
# получается что нам надо искать последнюю страницу и с нее делать обработку
# а лучше все записи сначала собрать в массив
####################################################
# выдает одну страницу в 30 записей с заданной записи по времени первой транзакции
def get_history_inputs_page(edlr, edlr_acc, pars, next_rec ):
    print 'get_history_inputs_page next_rec:', next_rec
    if next_rec: pars['start_record'] = next_rec
    pars = urllib.urlencode(pars)
    #print pars
    res = get_history_pars(edlr, edlr_acc, pars)
    #print res
    return res
def get_history_inputs(edlr, edlr_acc, from_dt):
    tab = []
    pars = {
        'type': 'deposition',
        'details': 'true',
    }
    if from_dt: pars['from'] = from_dt
    next_rec = 0
    while True:
        #print 'next_rec:', next_rec
        res = get_history_inputs_page( edlr, edlr_acc, pars, next_rec )
        #print 'get_history_inputs_page res:', res
        if not res or 'operations' not in res:
            #print dealer.name, dealer_acc.acc, '- empty get_history_inputs_page = RES'
            break
        # сложим все записи с истории
        tab = tab + res['operations']
        next_rec  = 'next_record' in res and res['next_record']
        print 'next_rec:', next_rec, 'LEN:', len(res['operations'])
        if not next_rec: break

    # тут в обратной последовательности - надо отсортировать по возрастанию времени
    tab = sorted(tab, cmp=lambda x,y: cmp( x['datetime'], y['datetime']))
    return tab


def get_payment_info(edlr, edlr_acc, pay_id):
    api_pars, acc_pars, name = get_pars(edlr, edlr_acc)
    return YmGetPayInfo(api_pars, edlr_acc.skey, pay_id)

''' тут надо преобразовать шаблон из дела в шаблон магазина для диллера
    Field('scid', length=50, unique=False),
    # тут шаблон по которму делать платеж у дилера
    # тоесть тут перврод имен параметров для данного дилера
    Field('template', 'text'),
    Field('grab_form', 'boolean', default=False, comment='use form from dealer site'),
    Field('p2p', 'boolean', default=False, comment='it p2p or partner shop'),
    Field('tax', 'decimal(4,2)', default = 1, comment='% комиссия дилера за это дело'),
'''
def make_pay_pars(deal, dlr_deal, api_pars, acc, amount, pars):
    # если тут счет как массив значит это счет и шаблон для сборки параметров
    #print 'make_pay_pars pars:', pars
    pay_pars = deal.template_
    if pay_pars and len(pay_pars)>0:
        pay_pars = json.loads(pay_pars)
    else:
        pay_pars = ed_common.PAY_PARS

    if dlr_deal.grab_form:
        not_mod = True
        '''
        # если форму с сайта дилера взяли то и параметры там не надо распаковывать
        acc_pars = json.loads( acc )
        # просто их добавим в общий набор параметров
        for k, v in acc_pars.iteritems():
            pars[k] = v
        '''
        # тут просто по порядку преобразуем из аккаунта нашего дела в их параметры
        acc_lst = json.loads(acc)
        pars.update( acc_lst )
    else:
        # тут надо распаковать строчку в счете на отдельные параметры
        dlr_template = dlr_deal.template_
        if dlr_template and len(dlr_template)>0:
            dlr_template = json.loads(dlr_template)
        else:
            dlr_template = PAY_PARS

        acc_str = acc
        #print acc, pay_pars, pars
        not_mod = None
        sum_names = dlr_template.get('_sum_names')
        #print 'dlr_template:', dlr_template
        calcs_ = dlr_deal.calcs_ or {}
        if len(calcs_)>0: pars['_calcs_'] = calcs_
        for p in pay_pars:
            #print p
            p_name = p.get('n')
            if not p_name: continue
            #print 'pay_pars p_name:',p_name
            # ищем в вычисляемых полях
            calc = calcs_.get(p_name)
            # тут параметры для счета
            if calc != None and not (type(calc) in [type(dict()), type({})]):
                # это строковое значение или число, то вычислим
                if calc == 'lm': val = common.last_month()
                elif calc == 'lm2': val = common.last_month2()
                elif calc == 'ly': val = common.last_year()
                elif calc == 'ly2': val = common.last_year2()
                elif len(calc)>0 and calc in pars:
                    # скопируем параметр уже созданный сюда
                    val = pars[ p[calc]]
                else:
                    #print p, type(p['calc'])
                    val = calc
            else:
                val, sep, acc_str = acc_str.partition(' ')

                #print dlr_template[p['n']]

            dlr_par = dlr_template.get(p_name)
            #print dlr_par
            if dlr_par:
                pars[ dlr_par['n']] = val

    #print 'PARS in make:', pars
    ## SKYPE - sum_round=4 !! - иначе округляется и курс обмена на ЕВРО не сходится
    sum_round =  dlr_template.get('sum_round', api_pars.get('sum_round'))
    if sum_round != None:
        amount = round(float(amount), sum_round)
    else:
        # в яндексе все округлять нафиг!
        amount = round(float(amount), 0)

    # преобразуем тут толпу разных парамеров у яндекса ко всем
    if sum_names:
        # если в шаблоне нужно только окнкретные имена сумм указывать
        # например за Билайн-интеренет - sum_names = ['sum', 'redsum']
        for sn in sum_names:
            calc = calcs_.get(sn)
            #print "%s", calc
            if calc != None:
                pars[sn] = calc
            else:
                pars[sn] = amount #int(amount)
        #print '_sums_names:', pars
    else:
        pars['sum'] = pars['netSum'] = pars['redsum'] = amount

    if 'comment' in pars: pars['FormComment'] = pars['comment']
    if 'FormComment' in pars: pars['comment'] = pars['FormComment']

    not_mod = 'not_mod' in dlr_template and True or not_mod # не добавлять все возможные ваоианты имени аккаунта
    if False and not not_mod: # сейчас не добавлем все подряд
        id = None
        user_names = api_pars['acc_names']
        #user_names = []
        #print pars
        for key in user_names:
            #print key
            if key in pars:
                id = pars[key]
                #print id, pars[key]
                break
        if not id:
            print 'ERROR - make_pay_pars - user id = None \n pay_pars:', pay_pars
            return
        # CustomerNumber и customerNumber - некорректно. В таком случае точно будет ошибка.
        if 'CustomerNumber' in pars and 'customerNumber' in user_names:
                ## тут массив а не список !! user_names.pop('customerNumber')
                print 'CustomerNumber in pars and customerNumber'
                pass
        elif 'customerNumber' in pars and 'CustomerNumber' in user_names:
                ## тут массив а не список !! user_names.pop('CustomerNumber')
                print 'customerNumber in pars and CustomerNumber'
                pass
        # теперь всем возможным параметрам присвоим этот ид
        for key in user_names:
            pars[key] = id

    #print 'PARS after make:', pars

def calc_contract_amount(res, db, deal, edlr_deal, api_pars, edlr_acc, acc, amo, acc_name, testMake, log_on, pars_in):
    # это взятая с нас сумма
    contract_amount = res.get('contract_amount')
    ## там внутри параметр на сумму поменяли перед запросом, поэтому берем внутреннюю сумму
    if not res.get('_pars'):
        return { 'status': 'error', 'error': res }
    
    sum_amount = res['_pars'].get('sum', res.get('netSum', amo))
    print 'in calc_contract_amount - sum_amount, contract_amount', sum_amount, contract_amount
    #log(db, res)
    if not contract_amount:
        # если нет значит сумма таже
        return res

    contract_amount = float(contract_amount)
    if contract_amount == sum_amount:
        # сумма не поменялась, значит выход с таким же значением
        return res
    if contract_amount > sum_amount * 0.95 and contract_amount < sum_amount * 1.05:
        # небольшая НАценка - мы ее там в to_pay в долг закатаем
        return res
    # яндекс сконвертировал в другую валюту
    # - значит надо вычислить курс конвертации
    # и поновой запрос на платеж сделать
    # recursion
    amo_old = sum_amount
    rate = contract_amount / sum_amount * 1.03 # за конвертацию еще себе + положим
    sum_amount = round( amo_old / rate, 6)
    log(db, 'calc_contract_amount get a RATE: rate: %s, amo_new: %s, sum_amount: %s, contract_amount: %s'
        % (rate, sum_amount, amo_old, contract_amount))
    #for k in SUM_NAMES:
    #    #pars_in.get
    #    pass
    if pars_in:
        # в параметрах заданы суммы их так просто оттуда не выкурить поэтому выдадим ошибку
        # это только работает для платежей без тестовых параметров
        mess = 'contract_amount = %s and pars_in: %s --> RES: %s' % ( contract_amount, pars_in, res)
        print 'calc_contract_amount error -', mess
        return { 'status': 'error', 'error': mess }
        
    # платеж с новым значением - с обменом уже
    res = YmTo(db, deal, edlr_deal, api_pars, edlr_acc.skey, acc, sum_amount, acc_name, testMake, log_on, pars_in)
    log(db,'calc_contract_amount RES: %s' % res)
    contract_amount = res.get('contract_amount')
    if not contract_amount:
        log(db, 'calc_contract_amount ERROR - not [contract_amount]')
        return res # тут какая-то ошибка вылезла
    contract_amount = float (contract_amount)
    if contract_amount > amo_old * 1.05:
        return { 'status': 'error', 'error': 'contract_amount %s not equal input amo %s' % (contract_amount, amo_old)  }
    else:
        log(db, 'contract_amount: contract_amount: %s, amo: %s' % (contract_amount, amo_old))
        pass
    
    res['credit_amount'] = sum_amount
    return res

# проверка правильности платежа
def pay_test(db, deal, edlr, edlr_acc, edlr_deal, acc, amo, log_on=None, pars_in=None):
    api_pars, acc_pars, acc_name = get_pars(edlr, edlr_acc)
    log_on = False
    
    '''
    rate_to = get_rate_to(db, edlr_deal)
    print 'rate_to:', rate_to
    if rate_to != 1:
        amo_to_rate = round(amo * rate_to, 2) or 1.0
    else:
        amo_to_rate = amo
    '''
    res = YmTo(db, deal, edlr_deal, api_pars, edlr_acc.skey, acc, amo, acc_name, None, log_on, pars_in)
    print 'resYmTo res:', res
    
    # если там идет конвертация а сумма выражена не в рублях
    # то пересчитаем по курсу ЯД
    res = calc_contract_amount(res, db, deal, edlr_deal, api_pars, edlr_acc, acc, amo, acc_name, None, log_on, pars_in)
    print 'calc_contract_amount res:', res
    
    if False and 'contract' in res:
        ss = res['contract']
        ss = ss.encode('utf8')
        ss = str(ss).decode('utf8')
        print 'TEST\n', ss
    #print 'TEST  YmTo:', res
    ''' нетестовый запрос не работает с тестовым подтвердением (
    if res['status']!='success':
         res['method'] = 'request-payment'
         return res

    # запустим теперь подтверждение в тестовом режиме
    res = YmToConfirm(res, api_pars, edlr_acc.skey, 'success')
    '''
    return res


# тут если параметры уже собраны то задаем pay_pars['grab_form']=True
#
def pay(db, deal, edlr, edlr_acc, edlr_deal, acc, amo, testMake=None, testConfirm=None, log_on=None, pars_in=None):
    api_pars, acc_pars, acc_name = get_pars(edlr, edlr_acc)
    res = YmTo(db, deal, edlr_deal, api_pars, edlr_acc.skey, acc, amo, acc_name, testMake, log_on, pars_in)
    if False and 'contract' in res:
        # тут выдает кодировку для нашего компа и надо ее преобразовать для корректногой печати
        # тут кодировки такой нет
        #ss = res['contract']
        #ss = ss.encode('utf8')
        #ss = str(ss).decode('utf8')
        #print ss
        pass
    if log_on: log(db, ' YmTo RES: %s' % res)

    # если там идет конвертация а сумма выражена не в рублях
    # то пересчитаем по курсу ЯД
    res = calc_contract_amount(res, db, deal, edlr_deal, api_pars, edlr_acc, acc, amo, acc_name, testMake, log_on, pars_in)

    if res.get('status') !='success':
        res['method'] = 'request-payment'
        return res

    # тут все норм, ИДЕМ НА ПОДТВЕРЖДЕНИЕ
    # запомним баланс до платежа чтобы вычислить %% диллера после того как платеж пройдет
    bal1 = res.get('balance')
    ## если нет credit_amount - значит это оплатат сотового или еще что где нет таксы
    sum_taken = res.get('contract_amount', amo) # то что с нас списали
    '''
    u'credit_amount': 80.35, 'tax': 0.5, 'contract_amount': 80.75, 
    '''
    res = YmToConfirm(res, api_pars, edlr_acc.skey, testConfirm)
    ## это такса вниз - минус которую получил уже получатель
    sum_getted = res.get('credit_amount', amo)

    tax_out = tax = 0
    if sum_taken != amo:
        # тут процент просто вычисляем - так как есть данные о выходе
        tax = round((sum_taken - amo)/amo*100, 2)
    if sum_getted != amo:
        # тут процент просто вычисляем - так как есть данные о выходе
        tax_out = round((amo - sum_getted)/amo*100, 2)

    res['tax'] = tax
    res['tax_out'] = tax_out
    res['_acc_name'] = acc_name
    res['_acc'] = acc
    res['sum_taken'] = sum_taken
    res['sum_getted'] = sum_getted
    res['method'] = 'process-payment'

    #print '  YmToConfirm:', res
    if log_on: log(db, 'YmToConfirm: %s' % res)
    return res

##########################################################################
def is_payment_for_buy_from_bank(db, dealer_acc, info):
    '''
с КАРТЫ банковской:
amount	:	250.0
datetime	:	2015-03-18T19:00:08Z
details	:	Пополнение с банковской карты, операция №3bdfe536d0d12ec019f922ee11ba6787e3e806d7 Комиссия: 49,00 руб.
direction	:	in
message	:	BTC 155WMmtMbiL9ZpXcZbS5r5EjJSxt7xjQun
operation_id	:	480020408341068008
status	:	success
title	:	Пополнение с банковской карты
type	:	deposition

********* с банка:
amount	:	5000.0
datetime	:	2015-06-06T06:14:16Z
details	:	АЛЬФА-БАНК, пополнение счета в Яндекс.Деньгах, платеж №E040606150000744
direction	:	in
operation_id	:	486886456889020008
status	:	success
title	:	АЛЬФА-БАНК, пополнение
type	:	deposition
for return - { 'sender': info['sender'], 'operation_id': info['operation_id'],
            'amo': info['amount'], 'curr':curr, 'xcurr': xcurr, 'addr': addr,
            'ecurr_abbrev':'RUB', 'partner': partner,
            }, None
    '''
    dets = info['details']
    ## будем искать номер
    trr = dets.find(u'№')
    if not trr:
        return 'not found reference number in details (№)'
    trr = dets[trr+1:]
    trr2 = trr.find(u' ')
    trr = trr[:trr2]
    title = info['title']
    title_id = title.find(u',')
    if title_id: title = title[:title_id]
    info['sender'] = trr + u' ' + title
    mess = info.get('message')
    info['pattern_id'] = mess and 'card' or 'bank'
    ### - НЕЛЬЗЯ - там дальше по сообщению разбор адреса и валюты
    ### поэтому если сообщениеп пустое то просто как платеж их банка будет
    ###info['message'] = mess or info['details']
    
# адрес выплат вручную по вводу от клиента
def is_payment_for_buy(db, dealer_acc, info):
    #log(db, 'INFO %s' % json.dumps(info))
    '''
amount	:99.5
u'expires - это значит платеж подвис - надо его принять - внести данные паспорта

codepro	:False
datetime	:2013-11-14T13:47:27Z
details	:CLR Cdv7iZEbvxYNte8T6WNgE5gq149WFqZ994
direction	:in
message	:CLR Cdv7iZEbvxYNte8T6WNgE5gq149WFqZ994
operation_id	:875504095892034017
pattern_id	:p2p
sender	:410011949054154
status	:success
title	:Перевод от 410011949054154
    '''
    mess = is_bank = None
    #log(db, json.dumps(info or ''))
    if not info:
        mess = 'income_YD: get_payment_info - NOT INFO'
    elif 'error' in info:
        mess = 'income_YD: get_payment_info - %s' % info['error']
    elif info['status'] != 'success':
        mess = 'income_YD: get_payment_info - NOT success'
    elif info.get('direction') != 'in':
        mess = 'income_YD: get_payment_info - direction not input'
    elif info.get('codepro'):
        # защита кодом - такие возвращаем назад
        mess = 'income_YD: get_payment_info - protected=True'
    elif False and info.get('expires'):
        ## у платежжа который пропихнули ве равно остается этот параметр (
        mess = 'income_YD: get_payment_info - expires: %s' % info.get('expires')
    elif 'pattern_id' not in info:
        # платеж из АЛЬФА-БАНКА так приходит - без pattern
        # print info
        if info.get('type') == 'deposition':
            # это пополнение кошелька из банка
            # если там нет ошибок то в INFO положим новые данные
            #print info
            mess = is_payment_for_buy_from_bank(db, dealer_acc, info)
            if not mess:
                is_bank = True
            #print 'is_payment_for_buy_from_bank: \n', mess or info
        else:
            mess = 'not "pattern_id" in info'
    elif info['pattern_id'] != 'p2p':
        mess = 'income_YD: get_payment_info - NOT p2p'
    elif not 'message' in info:
        # это нен аш платеж log(db, 'income_YD: get_payment_info - message=None' )
        mess = 'not mess'

    if mess:
        #log(db, mess)
        return None, mess

    '''
    buy_ = db( (db.buys.dealer_acc_id==dealer_acc.id)
                    & (db.buys.operation_id == info['operation_id'])
                    ).select().first()
    if buy_:
        # такая операция уже была выплочена
        mess = 'income_YD:  - operation_id %s already buyed' % info['operation_id']
        #log(db, mess)
        return None, mess
    '''

    curr = xcurr = partner = addr = None
    info_message = info.get('message')
    ##if info_message and not is_bank:
    if info_message:
        ss = info_message
        ss = ss.encode('utf8') ## иначе русские буквы при печати ошибку делают
        ##ss = str(ss).decode('cp1251')
        #print ss
        abbrev, addr_0, addr = ss.partition(' ')
        print 'abbrev=%s\naddr_0=%s\naddr=%s' % (abbrev, addr_0, addr)

        if abbrev and not addr:
            xcurr, addr = ed_common.is_order_addr(db, abbrev)
            if not xcurr:
                addr = abbrev
                abbrev = db_common.get_currs_by_addr(db, addr, True)
                log(db, 'try use %s as ADDR' % addr)
                #print abbrev, addr
            if not abbrev:
                mess = 'xcurr or wallet addr not in payments message [%s]' % info['message']
                log(db, mess)
                #print mess
                return None, mess

        # это наж платеж - его в крипту перегнать надо
        # запомним это в базе чтобы если ошибка будет то потом попытаться еще раз
        if not xcurr:
            if len(abbrev)==3:
                # это абревиатура крипты
                curr, xcurr, e = db_common.get_currs_by_abbrev(db, abbrev)
            elif len(abbrev)==5:
                # это код партнера
                curr, xcurr, e = db_common.get_currs_by_addr(db, addr)
                partner = abbrev

        if not xcurr:
            mess = 'income_YD: xcurr [%s] not found or adr[%s] invalid' % (abbrev, addr)
            log(db, mess)
            ##return None, mess
            pass ## а пусть все платежи отражаются в необработанных
    else:
        # тут нет адреса в примечании к платежу
        # вручную его запросим у пользоваеля
        pass

    ##print xcurr
    return { 'sender': info['sender'], 'operation_id': info['operation_id'],
            'amo': info['amount'], 'curr':curr, 'xcurr': xcurr, 'addr': addr and addr.strip() or None,
            'ecurr_abbrev':'RUB', 'partner': partner,
            }, None


##########################################################################
##########################################################################
# Fill in this consts your values
# client_id for your application from yandex.money
#CLIENT_ID = ''
#OAUTH2 = ''

# at this URL should be YmOauthRedirectHandler,
# and the same URL should be configured for your
# application at yandex.money
#YM_REDIRECT_URI = ''
#YM_REDIRECT_URI = 'http://ic-pool.cloudapp.net/ipay/edealers/yandex_responce'

# http://i-pay.in
#CLIENT_ID = 'E9B54B67BF1E8CCEBE68CD184E86F5B09C1A3ED00B95236B878C9FAAD5FCD13F'
#YM_REDIRECT_URI = 'http://i-pay.in/edealers/yandex_response'

# http://ic-pool.cloudapp.net/ipay -
#CLIENT_ID = '3FAAFA1A38961AD37B6EB620337ACFCA4A240297740C53785CA465122D853E34'
#YM_REDIRECT_URI = 'http://ic-pool.cloudapp.net/ipay/edealers/yandex_response'

#CLIENT_ID = 'A9051A7E17FC30EF7E35CD14D736DB6B5456C51B6ABD794C0D0EA56A54CBD945'
#OAUTH2 = 'B58E677E9EB656DADE838842CBAED4AAC7B93E422E79CA8AB496564E5347897F4F623B30A34055913092EA1A5B6CAC3F0969F431EB355DE665471CB4BE572563'

# for example 'account-info', see API docs for more options
# те клманды которые разрешаем в этом АПИ
#SCOPE = 'account-info operation-history operation-details payment-shop.limit(1,33333) money-source("wallet")'

# Links for full version of yandex.money.
#URI_YM_API = 'https://money.yandex.ru/api'
#URI_YM_AUTH = 'https://sp-money.yandex.ru/oauth/authorize'
#URI_YM_TOKEN = 'https://sp-money.yandex.ru/oauth/token'

# это нужно вызвать для получания токена на мой аккаунт
# этот токен потом надоо сохранить - он везде для доступа к АПИ нужен
def YmOauthRequestToken(api_pars, acc_pars) :
    """ At first step, send your user browser to yandex.money.
        User will authorize token generation, then she will be redirected
        to your Oauth redirect handler, specified in YM_REDIRECT_URI and
        in the app description at yandex.money.
    """
    data = {'client_id' : acc_pars['CLIENT_ID'], 'response_type' : 'code',
            'redirect_uri' : acc_pars['YM_REDIRECT_URI'], 'scope' : acc_pars['SCOPE']}
    # Make a platform specific redirect to
    #  (URI_YM_AUTH + '?' + urllib.urlencode(data))
    #redirect()
    return api_pars['URI_YM_AUTH'] + '?' + urllib.urlencode(data)


def YmOauthRedirectHandler(api_pars, acc_pars, code):
    """ Oauth redirect handler. User browser will be redirected here at
        second step of Oauth.
        Requests access token in exchange for request token (code)
        provided be yandex.money as the redirect parameter. """
    #print 'CODE', code
    data = {'client_id' : acc_pars['CLIENT_ID'], 'grant_type' : 'authorization_code',
            'redirect_uri' : acc_pars['YM_REDIRECT_URI'], 'code' : code}
    f = urllib.urlopen(api_pars['URI_YM_TOKEN'], urllib.urlencode(data))
    r = json.load(f)
    return r

##############################################################
### API CALLS
#############################################################
def YmGetBalanse(api_pars, token, acc_name):
    """ Make an API call - requests account info """
    rq = urllib2.Request(api_pars['URI_YM_API'] + '/account-info', '')
    rq.add_header('Authorization', 'Bearer ' + token)
    try:
        f = urllib2.urlopen(rq)
    except Exception as e:
        print 'YmGetBalanse ', acc_name, e
        return {'error': e, 'status':'unauthorized', 'balance': None}
    r = json.load(f)
    #print r.get('balance')
    return r #.get('balance')

def get_history_pars(edlr, edlr_acc, pars):
    api_pars, acc_pars, name = get_pars(edlr, edlr_acc)
    token = edlr_acc.skey
    """ Make an API call - requests account info """
    rq = urllib2.Request(api_pars['URI_YM_API'] + '/operation-history', pars)
    rq.add_header('Authorization', 'Bearer ' + token)
    try:
        f = urllib2.urlopen(rq)
    except Exception as e:
        print 'get_incoms %s \n PARS: %s' % (e, pars)
        return {'error': e, 'status':'unauthorized', 'get_incoms': None}
    r = json.load(f)
    #print r.get('balance')
    return r #.get('balance')


def YmGetPayInfo(api_pars, token, pay_id):
    """ Make an API call - requests account info """
    rq = urllib2.Request(api_pars['URI_YM_API'] + '/operation-details', 'operation_id=%s' % pay_id)
    rq.add_header('Authorization', 'Bearer ' + token)
    try:
        f = urllib2.urlopen(rq)
    except Exception as e:
        print 'YmGetPayInfo ', pay_id, e
        return {'error': e, 'status':'unauthorized', 'balance': None}
    r = json.load(f)
    #print r.get('balance')
    return r #.get('balance')
#import logging

# тут ели параметры уже собраны то задаем edlr_deal.grab_form==True
def YmTo(db, deal, edlr_deal, api_pars, token, acc, amount, acc_name, test=None, log_on=None, pars_in=None):
    if edlr_deal.scid == 'phone-topup':
        if False and len (acc) == 11 and acc[0:1] == '7': ph = acc[1:]
        else: ph = acc
        #print ph
        pars = {'pattern_id': edlr_deal.scid,
            'phone-number': ph,
#            'PROPERTY1': ph[0:3],
#            'PROPERTY2': ph[3:],
            'amount': amount,
            'comment': DOMEN + u' to phone: %s' % acc,
            'message': u'from ' + DOMEN,
            #'test_result': 'phone_unknown',
            }
    elif edlr_deal.scid == 'p2p':
        #return {'error': 'p2p not support', 'status':'p2p not support'}
        pars = { 'pattern_id': edlr_deal.scid,
            'to': acc,
            'amount': amount,
            'comment': DOMEN + u' to wallet: %s' % acc,
            'message': u'from ' + DOMEN,
            }
    elif edlr_deal.p2p:
        # это подключенный к нам магазин через яндекс кошелек
        # тут закодируем счет пользователя
        id_name = DOMEN + u': %s' % acc
        pars = { 'pattern_id': 'p2p',
            'to': edlr_deal.scid,
            'amount': amount,
            'title': id_name,
            'label': id_name,
            'comment': id_name,
            'message': id_name
            }
        #pars['label'] = pars['message']
    else: # это магазин и там иднтификатор
        #print type(deal)
        if type(deal) == type(''): name = deal
        else: name = deal.name #.decode('utf8') #'cp1251')
        #print name
        pars = {'pattern_id': edlr_deal.scid,
            'comment': DOMEN + ' to %s for [%s]' % (name, acc),
            'message': u'from ' + DOMEN, #current.T('from ' + DOMEN),
            #'test_result': 'shop_unknown',
            }
        # добавим параметры из шаблона магазина
        if not pars_in:
            make_pay_pars(deal, edlr_deal, api_pars, acc, amount, pars)
            pars['label'] = pars['message']
            pars['title'] = pars['message']

        #print pars
        #if 'user' not in pars:
        #    return {'error': 'user=None', 'status':'user not setted'}

    if test:
        pars['test_payment'] = True
        pars['test_result'] = test

    if 'test_result' in pars: pars['test_payment'] = True

    #print pars_in
    pars = pars_in or pars

    # если заданы комисии то сразу их введем
    fees = pars.get('_calcs_')
    fees = fees and fees.get('_fees')
    if fees:
        amo = float(pars['sum'])
        # <fee a="0.02" c="30" netAmount="netSum"/>
        # "_fees": { "a": "0.02", "c": "30", "netAmount": "netSum"}
        a = float(fees.get('a',0))
        c = float(fees.get('c',0))
        fee = amo * a
        if fee < c: fee = c
        pars[fees['netAmount']] = amo - fee

    # сохраним параметры без примечаний и сообщений для ЛОГа
    pars_uncomment = pars.copy()
    for k in ['comment', 'FormComment', 'message', 'title', 'label']:
        pars_uncomment.pop(k, None)
    pars = urllib.urlencode(pars)
    #print 'PARS:',pars
    #return pars
    rq = urllib2.Request(api_pars['URI_YM_API'] + '/request-payment', pars)
    rq.add_header('Authorization', 'Bearer ' + token)
    #print rq
    #logging.Logger.debug(rq)
    try:
        f = urllib2.urlopen(rq)
    except Exception as e:
        print 'ERROR YmTo ', acc_name, e,
        print 'e.errno, e.strerror:', e.errno, e.strerror
        ## была такая ошибка а потом нормально заплтило - но pay_ins - в процессе остался TODO - сделать игнорирование такой ошибки - на повтор
        ## res={'_acc': '79092111110', '_acc_name': 'Yandex:410012071750033', 'error': URLError(error(10054, 'An existing connection was forcibly closed by the remote host'),), 'status': 'Exception'}
        return {'error': e, 'status':'Exception', '_acc_name':acc_name, '_acc':acc}
    r = json.load(f)
    ''' данные ан выходе
    почемуто пишет успех но денег то на счете нету!
balance	:	49.24
contract	:
Оплата услуг сотовой связи МТС   Реквизиты платежа:   Cумма платежа: 12345.00 RUB Телефон: 9169172019 Номер транзакции: 2000106896738
money_source	:
request_id	:
3731303332363133385f623537333864323962616438633061396637383733393965396131323937343639326231373332305f3332333937303939
status	:	success
==============================================
     если послать сумму в балансе то выдает:
money_source	:	wallet	:	allowed	:	true
================================
при ошибках есть
     error:
     '''
    # получили вроде полож ответ
    # но проверим источник выплаты
    r['_acc_name'] = acc_name
    r['_acc'] = acc
    r['_pars'] = pars_uncomment

    # удалим лишние комменты
    if log_on != False: log(db, 'pars_uncomment:%s --> res:%s' % (pars_uncomment, r))

    if r['status']!='success':
        return r
    # если в ответе нет источника то уже ошибка
    r['error'] = 'no money_source'
    r['status'] = r.get('status') or 'refused'
    if not 'money_source' in r: return r
    v = r['money_source']
    if not 'wallet' in v: return r
    v = v['wallet']
    if not 'allowed' in v: return r
    v = v['allowed']
    if not v or v == 'false': return r
    # ошибки нет - то что надо выбрано для выплаты
    r['error'] = None
    r['status'] = 'success'
    if log_on != False: print 'YmTo - success!', acc, amount, '\n'
    return r

def YmToConfirm(pars_in, api_pars, token, test=None):
    pars = {
#        'pattern_id': pars_in['pattern_id'],
        'request_id': pars_in['request_id'],
        'money_source': 'wallet',
        #'test_payment': True,
        #'test_result': 'limit_exceeded',
        }
    if test:
        pars['test_payment'] = True
        pars['test_result'] = test

    pars = urllib.urlencode(pars)
    print 'YmToConfirm PARS:', pars
    rq = urllib2.Request(api_pars['URI_YM_API'] + '/process-payment', pars)
    rq.add_header('Authorization', 'Bearer ' + token)
    #return rq
    while True:
        # платеж в процессе - ожидаем и потом еще раз запросим
        try:
            f = urllib2.urlopen(rq)
            r = json.load(f)
            print 'YmToConfirm while status not in_proggress - res:', r
            if r['status']!='in_progress':
                 # платеж не а поцессе - выходим из проверки окончания платежа
                 break
        except Exception as e:
            from gluon import current
            # или любая ошибка - повтор запроса - там должно выдать ОК
            #print 'YmToConfirm while EXEPTION:', e
            log(current.db, 'YmToConfirm while EXEPTION: %s' % e)
            pass

        time.sleep(20)
        pass
    ''' если УСПЕХ!
balance	:
42.24
invoice_id	:
2000106905131
payment_id	:
434450183282000006
status	:
success
        '''

    return r
