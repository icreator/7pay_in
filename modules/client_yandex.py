#!/usr/bin/env python
# coding: utf8
#from gluon import *
import urllib
import urllib2
import json
import time

from gluon import current

DOMEN = 'face2face'

def get_pars(edlr, edlr_acc):
    api_pars = json.loads( edlr.API )
    acc_pars = json.loads( edlr_acc.pkey )
    return api_pars, acc_pars, "%s:%s" % (edlr.name, edlr_acc.acc)

def get_balance(edlr, edlr_acc):
    api_pars, acc_pars, name = get_pars(edlr, edlr_acc)
    return YmGetBalanse(api_pars, edlr_acc.skey, name)

def pay(edlr, edlr_acc, pattern_id, acc, amo, pay_pars=None, testMake=None, testConfirm=None):
    api_pars, acc_pars, acc_name = get_pars(edlr, edlr_acc)
    #YmToPhone(api_pars, token, phone, amount, acc_name, test=None):
    res = YmToPhone(api_pars, edlr_acc.skey, acc, amo, acc_name, testMake)
    print '  YmToPhone:', res
    if res['status']!='success':
         res['method'] = 'request-payment'
         return res

    # тут все норм, ИДЕМ НА ПОДТВЕРЖДЕНИЕ
    res['pattern_id'] = pattern_id
    res = YmToPhoneConfirm(res, api_pars, edlr_acc.skey, testConfirm)
    res['method'] = 'process-payment'
    print '  YmToConfirm:', res
    return res

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

def YmToPhone(api_pars, token, phone, amount, acc_name, test=None):
    pars = {'pattern_id':u'phone-topup',
        'phone-number': phone,
        'amount': amount,
        'comment': '7pay to phone: %s' % phone,
        'message': current.T('оплата через портал '+DOMEN),
        #'test_payment': True,
        #'test_result': 'phone_unknown',
        }
    if test:
        pars['test_payment'] = True
        pars['test_result'] = test
    pars = urllib.urlencode(pars)
    #return pars
    rq = urllib2.Request(api_pars['URI_YM_API'] + '/request-payment', pars)
    rq.add_header('Authorization', 'Bearer ' + token)
    #return rq
    try:
        f = urllib2.urlopen(rq)
    except Exception as e:
        print 'YmToPhone ', acc_name, e
        return {'error': e, 'status':'unauthorized'}
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
    return r

def YmToPhoneConfirm(pars_in, api_pars, token, test=None):
    pars = {'pattern_id':u'phone-topup',
        'request_id': pars_in['request_id'],
        'money_source': 'wallet',
        #'test_payment': True,
        #'test_result': 'limit_exceeded',
        }
    if test:
        pars['test_payment'] = True
        pars['test_result'] = test
    pars = urllib.urlencode(pars)
    #return pars
    rq = urllib2.Request(api_pars['URI_YM_API'] + '/process-payment', pars)
    rq.add_header('Authorization', 'Bearer ' + token)
    #return rq
    f = urllib2.urlopen(rq)
    r = json.load(f)
    return r

def to_phone(edlr, edlr_acc, phone, amo):
    api_pars, acc_pars, acc_name = get_pars(edlr, edlr_acc)
    res = YmToPhone(api_pars, edlr_acc.skey, phone, amo, acc_name)
    # получили ответ
    if res['status']!='success': return res
    # если в ответе нет источника то уже ошибка
    res['error'] = 'no money_source'
    res['status'] = 'refused'
    if not 'money_source' in res: return res
    v = res['money_source']
    if not 'wallet' in v: return res
    v = v['wallet']
    if not 'allowed' in v: return res
    v = v['allowed']
    if v != 'true': return res

    # тут все норм, ИДЕМ НА ПОДТВЕРЖДЕНИЕ
    while True:
        res = YmToPhoneConfirm(res, api_pars, edlr_acc.skey)
        if res['status']!='in_progress':
             # платеж не а поцессе - выходим из проверки окончания платежа
             break
        # платеж в процессе - ожидаем и потом еще раз запросим
        print 'sleep'
        time.sleep(10)
    # платеж совершен или откланен
    if res['status']!='success':
         '''
         error	:	money_source_not_available
         status	:	refused
         '''
         return res
    ''' УСПЕХ!
balance	:
42.24
invoice_id	:
2000106905131
payment_id	:
434450183282000006
status	:
success
        '''
    return res
