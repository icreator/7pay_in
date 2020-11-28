#!/usr/bin/env python
# coding: utf8
#from gluon import *
import urllib
import urllib2
import json
import time

from gluon import current

DOMEN = 'face2face'

# получить инфо о параметрах тут
# https://money.yandex.ru/internal/mobile-api/get-showcase.xml?scid=4895

import common
import ed_common
import db_common

URL = 'https://qiwi.ru/'
URL_LOG = 'auth/login.action'
URL_LIST = 'user/report/list.action'
URL_STATE = 'user/payment/form/state.action'
ORL_FORM_TRANSF = 'ransfer/form.action'
	

def log(db, mess):
    print 'ed_YD - ', mess
    db.logs.insert(mess='YD: %s' % mess)
def log_commit(db, mess):
    log(db,mess)
    db.commit()
headers = { 'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'X-Requested-With': 'XMLHttpRequest'}


## выбррать способ связи
TTT = 'wcl'
TTT = 'lib'

def login(acc):

    data = dict( source='MENU', login = acc.deal_acc, password = acc.skey )
    if TTT == 'lib':
        h = urllib2.Request(URL + URL_LOG, urllib.urlencode(data), headers )
        r = urllib2.urlopen(h)
        r = json.load(r)
    elif TTT == 'wcl':
        from gluon.contrib.webclient import WebClient
        client = WebClient(URL, postbacks=True)
        client.post(URL_LOG, data=data, headers = headers )
        print client.status, client.text, '\n headers:', client.headers, '\n cookies: ', client.cookies, '\n sessions:', client.sessions
        r = json.loads(client.text)

    code = r.get('code')
    code = code and code.get('value')
    if not code or code != '7':
        return 'error on first request', r
        
    d = r.get('data')
    token = d and d.get('token')
    #deal_acc.update_record( pkey = token )
        
    data['loginToken'] = token
    
    if TTT == 'lib':
        h = urllib2.Request(URL + URL_LOG, urllib.urlencode(data), headers )
        r = urllib2.urlopen(h) # , URL_LOG + '?' + urllib.urlencode(data))
        r = json.load(r)
    elif TTT == 'wcl':
        client.post(URL_LOG, data=data, headers = headers )
        print client.status, client.text, '\n headers:', client.headers, '\n cookies: ', client.cookies, '\n sessions:', client.sessions
        r = json.loads(client.text)

    code = r.get('code')
    code = code and code.get('value')
    if not code or code != '0':
        return 'error on second request', r
    d = r.get('data')
    token = d and d.get('token')
    #deal_acc.update_record( pkey = token )
        
    return None, r

def get_balance(acc, TAG):
    data = dict( source='MENU', login = acc.deal_acc, password = acc.skey )
    if TTT == 'lib':
        r = urllib2.Request(URL + 'settings/account/main.action')
        r = urllib2.urlopen(r)
        r = r.read()
        r = TAG(r)
        el = r.elements('div.account_current_amount')
        bal = el[0][0]
        bal = bal.replace(',','.')
        bal = bal.replace(' ','')
        bal = float(bal)
        
    return None, bal

def get_history(acc, direction, from_dt, to_dt, TAG):
    data = dict(
        settings='true',
        conditions = dict(directions = direction),
        daterange = 'true',
        start = from_dt,
        finish = to_dt
    )
    if TTT == 'lib':
        h = urllib2.Request(URL + URL_LIST, urllib.urlencode(data) )
        r = urllib2.urlopen(h)
        r = r.read()
    
    r = TAG(r)
    r = r.elements('div[data-container-name=item]')
    '''
    <div class="reportsLine status_SUCCESS" data-container-name="item">
        <i class="icon icon_SUCCESS fa fa-check-circle"></i>
        <i class="icon icon_ERROR fa fa-times-circle"></i>
        <i class="icon icon_PROCESSED fa fa-clock-o"></i>

        <div class="DateWithTransaction">
	    <span class="date">
            01.02.2015
        </span>
	    <span class="time">
            10:28:24
        </span>
                <div class="transaction" data-action="item-extra" data-params="{&quot;data&quot;:{&quot;txn&quot;:5315416947}}">
                    <a class="more" href="#">
                        Информация
                    </a>
                </div>
        </div>
            <div class="IncomeWithExpend expenditure">
                <div class="cash">
                    3&nbsp;440,94
                    руб.
                </div>
                <div class="commission">
                        67,47
                        руб.
                </div>
                    <div class="operations">
                        <a class="cheque" href="/report/cheque.action?transaction=5315416947&amp;direction=OUT" target="_blank">
                            Распечатать чек
                        </a>
                    </div>
                
            </div>
        
        <div class="originalExpense">
	    <span>
            3&nbsp;373,47
            руб.
        </span>
        </div>

        <div class="ProvWithComment">
            <div class="provider">
                <span>ЖКУ (Москва)</span>
                <span class="opNumber">2321457502</span>
            </div>
            <div class="comment">26А-10</div>
        </div>
        <div class="clearBoth"></div>
        <div class="cashback-wrap">
            
        </div>
        <div class="clearBoth"></div>
        <div class="extra" data-container-name="item-extra">
            <div class="item">
                <span class="key">Транзакция:</span>
                <span class="value">999999900481932159</span>
            </div>
        </div>
    </div>
    '''
    trans = []
    for rec in r:
        dt = rec.element('div.DateWithTransaction')
        dd = dt.element('span.date')
        tt = dt.element('span.time')
        trans.append([dict(
                    date = dd[0][0],
                    time = tt[0][0],
                  )])
    #print r
    
    return None, trans

def get_balance__(edlr, edlr_acc):
    api_pars, acc_pars, name = get_pars(edlr, edlr_acc)
    return YmGetBalanse(api_pars, edlr_acc.skey, name)
def get_history__(edlr, edlr_acc, from_dt):
    pars_str = ""
    if from_dt: pars_str = '?from="%s"' % from_dt
    res = get_history_pars(edlr, edlr_acc, pars_str)
    return res

###############################
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
            #print dealer.name, dealer_acc.deal_acc, '- empty get_history_inputs_page = RES'
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
        acc_pars = json.loads( deal_acc )
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
        #print deal_acc, pay_pars, pars
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

    if True and not not_mod: # сейчас не добавлем все подряд
        id = None
        user_names = api_pars['acc_names']
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
        # теперь всем возможным параметрам присвоим этот ид
        for key in user_names:
            pars[key] = id

    #print 'PARS after make:', pars

def calc_contract_amount(res, db, deal, edlr_deal, api_pars, edlr_acc, acc, amo, acc_name, testMake, log_on, pars_in):
    contract_amount = res.get('contract_amount')
    #log(db, res)
    if contract_amount:
        contract_amount = float(contract_amount)
        if contract_amount == amo:
            # сумма не поменялась, значит выход с таким же значением
            return res
        # яндекс сконвертировал в другую валюту
        # - значит надо вычислить курс конвертации
        # и поновой запрос на платеж сделать
        rate = float(contract_amount) / amo
        amo_exch = round(amo / rate, 2) - 0.05 # за конвертацию еще себе + положим
        print 'RATE:', rate, amo_exch, amo, contract_amount
        for k in SUM_NAMES:
            #pars_in.get
            pass
        if pars_in:
            # в параметрах заданы суммы их так просто оттуда не выкурить поэтому выдадим ошибку
            # это только работает для платежей без тестовых параметров
            return { 'status': 'error', 'error': 'contract_amount = %s and pars_in: %s --> RES: %s' % ( contract_amount, pars_in, res) }
        res = YmTo(db, deal, edlr_deal, api_pars, edlr_acc.skey, acc, amo_exch, acc_name, testMake, log_on, pars_in)
        print 'calc_contract_amount RES:',res
        contract_amount = res.get('contract_amount')
        if not contract_amount: return res # тут какая-то ошибка вылезла
        contract_amount = float (contract_amount)
        if contract_amount > amo:
            return { 'status': 'error', 'error': 'contract_amount %s not equal input amo %s' % (contract_amount, amo)  }
        else:
            print 'contract_amount:',contract_amount, 'amo:', amo
            pass
    return res

# проверка правильности платежа
def pay_test(db, deal, edlr, edlr_acc, edlr_deal, acc, amo, log_on=None, pars_in=None):
    api_pars, acc_pars, acc_name = get_pars(edlr, edlr_acc)
    #log_on = True
    res = YmTo(db, deal, edlr_deal, api_pars, edlr_acc.skey, acc, amo, acc_name, None, log_on, pars_in)

    # если там идет конвертация а сумма выражена не в рублях
    # то пересчитаем по курсу ЯД
    res = calc_contract_amount(res, db, deal, edlr_deal, api_pars, edlr_acc, acc, amo, acc_name, None, log_on, pars_in)
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
    amo1 = res.get('contract_amount')
    
    res = YmToConfirm(res, api_pars, edlr_acc.skey, testConfirm)
    res['_acc_name'] = acc_name
    res['_acc'] = acc
    res['contract_amount'] = amo1
    #print "res.get('error'):", res.get('error')

    res['method'] = 'process-payment'
    if 'credit_amount' in res:
        sum1 = res['credit_amount']
        # тут процент просто вычисляем - так как есть данные о выходе
        tax = round((amo - sum1)/amo*100,1)
        res['tax'] = tax
        res['sum_taken'] = sum1 # списанные деньги
    elif bal1 and 'balance' in res:
        bal2 = res['balance']
        sum1 = bal1 - bal2
        amo = int(amo*100)*0.01
        #print sum1, amo, bal1, bal2
        tax = round((sum1 - amo)/amo*100,1)
        #print 'TAX:', tax
        if tax < 0: tax=0 # это тестовый платеж где баланс не меняется
        elif tax > 9: tax = 1 # есл вдруг было какоето изменение на счету не от этого платежа
        res['tax'] = tax
        res['sum_taken'] = sum1 # списанные деньги
    #print '  YmToConfirm:', res
    if log_on: log(db, 'YmToConfirm: %s' % res)
    return res

##########################################################################
def is_payment_for_buy(db, dealer_acc, info):
    #log(db, 'INFO %s' % json.dumps(info))
    '''
    amount	:
99.5
codepro	:
False
datetime	:
2013-11-14T13:47:27Z
details	:
CLR Cdv7iZEbvxYNte8T6WNgE5gq149WFqZ994
direction	:
in
message	:
CLR Cdv7iZEbvxYNte8T6WNgE5gq149WFqZ994
operation_id	:
875504095892034017
pattern_id	:
p2p
sender	:
410011949054154
status	:
success
title	:
Перевод от 410011949054154
    '''
    mess = None
    #log(db, json.dumps(info or ''))
    if not info:
        mess = 'income_YD: get_payment_info - NOT INFO'
    elif 'error' in info:
        mess = 'income_YD: get_payment_info - %s' % info['error']
    elif info['status'] != 'success':
        mess = 'income_YD: get_payment_info - NOT success'
    elif 'pattern_id' not in info:
        # платеж из АЛЬФА-БАНКА так приходит - без pattern
        # print info
        mess = 'not "pattern_id" in info'
    elif info['pattern_id'] != 'p2p':
        mess = 'income_YD: get_payment_info - NOT p2p'
    elif info.get('direction') != 'in':
        mess = 'income_YD: get_payment_info - direction not input'
    elif info.get('codepro'):
        # защита кодом - такие возвращаем назад
        mess = 'income_YD: get_payment_info - protected=True'
    elif not 'message' in info:
        # это нен аш платеж log(db, 'income_YD: get_payment_info - message=None' )
        mess = 'not mess'

    if mess:
        #log(db, mess)
        return None, mess

    buy_ = db( (db.buys.dealer_acc_id==dealer_acc.id)
                    & (db.buys.operation_id == info['operation_id'])
                    ).select().first()
    if buy_:
        # такая операция уже была выплочена
        mess = 'income_YD:  - operation_id %s already buyed' % info['operation_id']
        #log(db, mess)
        return None, mess

    abbrev, addr_0, addr = info['message'].partition(' ')
    print 'abbrev, addr_0, addr', abbrev, addr_0, addr
    if abbrev and not addr:
        addr = abbrev
        abbrev = db_common.get_currs_by_addr(db, addr, True)
        log(db, 'try use %s as ADDR' % addr)
        print abbrev, addr
    if not abbrev:
        mess = 'xcurr or wallet addr not in payments message [%s]' % info['message']
        log(db, mess)
        print mess
        return None, mess

    curr = xcurr = partner = None
    # это наж платеж - его в крипту перегнать надо
    # запомним это в базе чтобы если ошибка будет то потом попытаться еще раз
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
        return None, mess

    return { 'sender': info['sender'], 'operation_id': info['operation_id'],
            'amo': info['amount'], 'curr':curr, 'xcurr': xcurr, 'addr': addr,
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
            'comment': DOMEN+ u' to wallet: %s' % acc,
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
            'message': u'from ' + DOMEN, #current.T('from '+DOMEN),
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
        print 'ERROR YmTo ', acc_name, e
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
    if v != 'true': return r
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
            # или любая ошибка - повтор запроса - там должно выдать ОК
            #print 'YmToConfirm while EXEPTION:', e
            log(db, 'YmToConfirm while EXEPTION: %s' % e)

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
