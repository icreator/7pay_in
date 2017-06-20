# coding: utf8

#!!!! ВНИМАНИЕ !!!
# некоторые АПИ у яндекса настроены на стрый callback - IPAY - надо там тоже править код!

#import copy
import json

import ed_common

def log(mess):
    print mess
    db.logs.insert(mess='BUY: %s' % mess)
def log_commit(mess):
    log(mess)
    db.commit()


'''
buy/income_YD/41001998296688?sender=41001000040&datetime=2013-11-17T17:54:05Z&label=&currency=643&amount=10.05&notification_type=p2p-incoming&test_notification=false&operation_id=test-notification&sha1_hash=71ffeff489a869d7e8975ccfa0dfb6c61b48dcdc&codepro=false

## без проверки кода-секретного в ЯД ответе - так как мы сами всю инфо с ЯД потом берем
buy/income_YD/410012175232158?&notification_type=p2p-incoming&operation_id=895318033202032017&sender=410011949054154

buy/income_YD/41001873409965?&notification_type=p2p-incoming&operation_id=963754923912060009&sender=410011314796164
buy/income_YD/41001873409965?operation_id=486931408464018008


чтобы глянуть номер транзакции
# http://127.0.0.1:8000/ipay/edealers/list_incoms/41001873409965/2015-06-06T06:08:19Z

при переводе еще параметр появился:
'operation_label': '1d1fc802-0001-5000-8000-00000bf82b77'

'''
Test_income_YD = None #True
## http://127.0.0.1:8000/ipay/buy/income_YD/410012107376992?operation_id=489576667705029008&amount=100
def income_YD():
  session.forget(response)

  #try:
  if True:
    args = request.args
    if not args or len(args)==0:
        # принудительно свой акк введем - иначе чего то ошибка на яндексе есди делать
        # https://7pay.in/ipay/buy/income_YD/41001555269641
        #args = [ '41001555269641' ]
        mess = 'len request.args==0 - ex: https://7pay.in/ipay/buy/income_YD/410012107376992?operation_id=489576667705029008&amount=100'
        log(mess)
        return mess

    # это для отладки у нас из строки боузера -по GET v = request.get_vars
    v = request.vars
    mess = 'income_YD -  request.vars: %s' % request.vars
    log(mess)
    if not v or len(v)<1:
        mess = 'ERROR: len(request.post_vars)<2 - /410012107376992?operation_id=489576667705029008&amount=100'
        log(mess)
        return mess

        #log(json.dumps(v))
    dealer = db(db.dealers.name == 'Yandex').select().first()
    if not dealer:
        mess = mess
        log( mess )
        return mess
    dealer_acc = db((db.dealers_accs.acc==args[0])
        & (db.dealers_accs.dealer_id == dealer.id)
        ).select().first()
    if not dealer_acc:
        mess =  'income_YD: %s dealer_acc %s not found' % (dealer.name, args[0])
        log(mess)
        return mess

    # раз сюда пришло значит баланс кошелька поменялся и надо его запомнить
    # причем сначала баланс возьмем а потом проверим есть ли такая запись ужке
    e_bal = ed_common.get_balance(dealer, dealer_acc )
        
    operation_id=v.get('operation_id')
    if not operation_id: return 'error 001 in pars ...'
    # запомним то что на аккаунте было телодвижение
    # если в общем списке транзакций уже есть такой op_id - то <0
    amo=v.get('amount')
    if not amo:
        info = ed_common.get_payment_info(dealer, dealer_acc, operation_id)
        # {u'status': u'refused', u'error': u'authorization_reject'}
        amo = info.get('amount')
        if not amo:
            mess = 'amount not found in info'
            if info.get(u'error') == u'authorization_reject':
                dealer_acc.used = False
                mess += ', authorization_reject for: ' + dealer_acc.acc
            return mess

    id_trans = ed_common.add_trans(db, dict(
                    dealer_acc_id=dealer_acc.id,
                    info= u'%s' % v, balance=e_bal, amo = amo,
                    op_id=operation_id
                    ))
    id_trans = operation_id != '489576667705029008' and id_trans or 0
    #print id_trans
    ## test on acc = 410012107376992 ? operation_id=='489576667705029008'
    if id_trans <0:
        # значит такая запись уже была внесена и обработана - выход
        mess =  'income_YD: id_trans = %s Ok X2' % id_trans
        log(mess)
        return 'OK x2 %s' % id_trans

    import ed_bal
    # сначала изменим все балансы - без лимитных балансов
    ed_bal.update(db, dealer_acc, amo, dealer, limited=False)
    # теперь обновим баланс - чтобы он не сбивался
    if e_bal:
        dealer_acc.update_record(balance = e_bal)
        print dealer_acc.acc,'ball updated:', e_bal

    #"secret_response":"CldjPZDx7qnpA+ZITT03htyk"
    '''
    u'expires - это значит платеж подвис - надо его принять - внести данные паспорта
при переводе еще параметр появился:
'operation_label': '1d1fc802-0001-5000-8000-00000bf82b77'
        {"sender": "41001000040", "datetime": "2013-11-17T17:54:05Z", "label": "", "currency": "643", "amount": "26.51", "notification_type": "p2p-incoming", "test_notification": "false", "operation_id": "test-notification", "sha1_hash": "71ffeff489a869d7e8975ccfa0dfb6c61b48dcdc", "codepro": "false"}
    '''
    '''
        post:
        amount	: 281.53
        codepro	:false
        currency	:	643
        datetime	:	2013-11-17T15:23:57Z
        label	:
        notification_type	:	p2p-incoming
        operation_id	:	test-notification
        sender	:	41001000040
        sha1_hash	:	2b23efbe77296e9447d537cc75925ac142823a93
        test_notification	:	true
    '''
    
    ### для того чтобы пополнения из банка срабатывали пропустим это
    if False and v['notification_type'] != 'p2p-incoming':
        mess = 'income_YD: NOT incoming'
        log(mess)
        return mess

    if v.get('test_notification'):
        mess = 'income_YD: this a TEST'
        log(mess)
        return mess
    # тут все рубли у яндекса if v.get('currency') != '643':
    #    log('income_YD: currency not RUB')
    #    return 'cuuu'
    if v.get('codepro') == 'true':
        # защита кодом - такие возвращаем назад
        mess = 'income_YD: protected=True'
        log( mess )
        return mess

    if Test_income_YD:
        ############# TEST #############
        # тут якобы все прогшло успешно надо только сделать платеж
        import db_common
        curr_out, xcurr_out, e = db_common.get_currs_by_abbrev(db,"LTC")
        info =  { 'sender': 'test 44505', 'operation_id': '8755040...892034017',
            'amo': 0.013, 'curr': curr_out, 'xcurr': xcurr_out,
            'addr': 'LYNJwquszE9dPihRDKpmzX3hZtxVkY1sv6', # оплата на сервисе 7З сотового моего
            'ecurr_abbrev':'RUB',
            }
    elif False: # отрубим проверку на секретный код так как мы все равно лезем потом на сервис ЯД и оттуда инфо получем
        acc_info = json.loads(dealer_acc.pkey)
        notification_secret = acc_info['secret_response']
        sss = '%s&%s&%s&%s&%s&%s&%s&%s&%s' % (
             v['notification_type'], operation_id, v['amount'], v['currency'],
             v['datetime'], v['sender'], v['codepro'], notification_secret, v['label'])
        import hashlib
        hhh = hashlib.sha1(sss).hexdigest()
        #print v['sha1_hash']
        #print hhh
        equ = v['sha1_hash'] == hhh
        #db.logs.insert(mess='%s \n%s \n%s' % (v['sha1_hash'], hhh, equ))
        if not equ:
            # хэш не совпал - это ненаш запрос
            log( 'not equ hash' )
            return 'notttt equ hash'
    else:
        #operation_id=875504095892034017
        info = ed_common.get_payment_info(dealer, dealer_acc, operation_id)
        log('ed_common.get_payment_info: %s' % info) #json.dumps(info))

    print 'buy:get_payment_info - ', info
    if not Test_income_YD:
        # наш ли это платеж?
        # если настроены уведомления но не настроины токен для АПИ
        # то = info = {'balance': None, 'error': HTTPError(), 'status': 'unauthorized'}
        if info.get('status') == 'unauthorized':
            mess =  'ERROR: API key unauthorized for ' + dealer.name + ':'+ dealer_acc.acc
            # v['notification_type'], operation_id, v['amount'], v['currency'],
            # v['datetime'], v['sender'], v['codepro'], notification_secret, v['label'])

            buy_id = db.buys.insert(
                dealer_acc_id = dealer_acc.id, # тут же валюта входа будет учтена автоматом
                buyer = v.get('sender'),
                status = 'error',
                status_mess = 'API unauthorized - ' + v.get('label','-'),
                operation_id = operation_id,
                amount = v.get('amount')
                )

            log(mess)
            return mess
        info, mess = ed_common.is_payment_for_buy(db, dealer, dealer_acc, info)
        if not info:
            log(mess)
            return mess

    # { 'sender': info['sder'], 'operation_id': info['operation_id'],
    #        'amo': info['amount'], 'xcurr': xcurr, 'addr': addr,
    #        'ecurr_abbrev':'RUB',
    #        }

    # это наж платеж - его в крипту перегнать надо
    # запомним это в базе чтобы если ошибка будет то потом попытаться еще раз
    #print info
    amo = info['amo']
    xcurr = info['xcurr']
    curr_out = info['curr']
    addr = info['addr']
    ecurr_abbrev = info['ecurr_abbrev'] # входящая фитаная валюта платиежа - может быть доллар
    
    buy_id = db.buys.insert(
            dealer_acc_id = dealer_acc.id, # тут же валюта входа будет учтена автоматом
            buyer = info.get('sender'),
            status = 'waiting',
            operation_id = operation_id,
            xcurr_id = xcurr and xcurr.id,
            addr=addr,
            amount = amo)

    # запомним что надо потом его сделать
    db.buys_stack.insert(ref_=buy_id)

  #except Exception as e:
  else:
    log(e)

  return 'OK'

## перенеправдения от старых версий сайта
def pay():
    redirect(URL('to_buy', 'index', args=request.args, vars=request.vars))
def to_pay():
    redirect(URL('to_buy', 'index', args=request.args, vars=request.vars))
def index():
    redirect(URL('to_buy', 'index', args=request.args, vars=request.vars))
