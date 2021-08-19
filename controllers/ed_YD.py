# coding: utf8

import common
# запустим сразу защиту от внешних вызов
if request.function != 'yandex_response':
    # кроме выдачи яндексом ответа с кодом
    if not IS_LOCAL:
        raise HTTP(503, 'error...')
# тут только то что на локалке

from decimal import Decimal
import datetime
import json

import ed_YD
dealer = db(db.dealers.name=='Yandex').select().first()

def log(mess):
    print (mess)
    db.logs.insert(mess='CNT: %s' % mess)
def log_commit(mess):
    log(mess)
    db.commit()


'''
http://127.0.0.1:8000/ipay/ed_YD/YmTo/3/3?acc=0000932298&sum=22.22
http://127.0.0.1:8000/ed_YD/YmTo/2/3345?acc=icreator@mail.ru&sum=22.22
/3653 - карта Тройка
acc_names": ["user", "PROPERTY1", "rapida_param1", "customerNumber", "CustomerNumber"]
 попробуем вручную получить ИД-платежа
'''
def YmTo():
    session.forget(response)
    if len(request.args) < 2:
        mess = '/[dealer_acc_id]/[deal_id]?deal_acc=ACC&amo=AMO'
        print (mess)
        return mess

    dealer_acc = db.dealers_accs[request.args(0)]
    dealer = dealer_acc and db.dealers[dealer_acc.dealer_id]
    deal = dealer and db.deals[request.args(1)]
    dealer_deal = deal and db((db.dealer_deals.deal_id == deal.id)
            & (db.dealer_deals.dealer_id == dealer.id)).select().first()
    if not dealer_deal: return 'NOT dealer_deal'
    
    acc = request.vars.get('deal_acc', '---???---')
    sum = request.vars.get('sum', '300.0')
    pars_in = {
        # acc_names": ["user", "PROPERTY1", "rapida_param1", "customerNumber", "CustomerNumber"]
        #'PROPERTY1': deal_acc,
        u'customerNumber': acc,
        # SUM_NAMES = ['sum', 'netSum', 'redsum' ]
        u'sum': sum,
        u'pattern_id': dealer_deal.scid,
        }
    test = log_on = None
    api_pars, acc_pars, acc_name = ed_YD.get_pars(dealer, dealer_acc)
    #def YmTo(db, deal, edlr_deal, api_pars, token, deal_acc, amount, acc_name, test=None, log_on=None, pars_in=None):
    res = ed_YD.YmTo(db, deal, dealer_deal, api_pars,
             dealer_acc.skey, acc,
             sum, acc_name, test, log_on, pars_in)
    return BEAUTIFY({'deal': deal.name, 'dealer_acc': dealer_acc.acc, 'pars_in': pars_in, 'res': res })

# попробуем вручную подтвердить ИД-платежа
## http://127.0.0.1:8000/ipay/ed_YD/YmToConfirm/2/1234535443154325432
def YmToConfirm():
    session.forget(response)
    if len(request.args) < 2:
        mess = '/[dealer_acc_id]/[request_id]'
        print (mess)
        return mess

    dealer_acc = db.dealers_accs[request.args(0)]
    dealer = db.dealers[dealer_acc.dealer_id]
    api_pars, acc_pars, acc_name = ed_YD.get_pars(dealer, dealer_acc)
    res = {
        'request_id': '%s' % request.args(1),
        }
    res = ed_YD.YmToConfirm(res, api_pars, dealer_acc.skey)
    return BEAUTIFY(res)

############################################
# тут запус из внешнего мира - чтобы запомнить сессию и в ней аккаунт для котрого
# ловим токен - все равно от яндекса ответ придет сюда
# https://7pay.in/ipay/ed_YD/get_yandex_token/41001875840125
# redirect :
# https://sp-money.yandex.ru/oauth/authorize?scope=account-info+operation-history+operation-details+payment-shop.limit%281%2C37777%29+payment-p2p.limit%281%2C37777%29&redirect_uri=http%3A%2F%2Fic-pool.cloudapp.net%2Fipay7%2Fed_YD%2Fyandex_response&response_type=code&client_id=9D8A0EDB2B7EB271527727F5DEFCE0B22599AAECEB4B0B7934E39525C914F4AF
## https://money.yandex.ru/myservices/new.xml
def get_yandex_token():
    if len(request.args) == 0:
        mess = CAT('len(request.args)==0',BR(),
            H4('Настройка аккаунта на Яндекс.Деньги'),
            UL('в настройках Yandex денег в Мои Приложения создать приложение БЕЗ 2-й аутинификации!!!'
               'задать там '+DOMEN+'+ https://'+DOMEN+' support@'+DOMEN,
               'задать redirect URL - https://'+DOMEN+'/ed_YD/yandex_response/410011949054154 - тонсть номер кашелька добавим',
               'получить ИД приложения - APP_ID',
                ),
            H4('Настройка записи в базе даннных'),
            UL(
                'set YM_REDIRECT_URI = "https://'+DOMEN+'/ed_YD/yandex_response" (acc_pars["YM_REDIRECT_URI"] = acc_pars["YM_REDIRECT_URI"] + "/%s" % edlr_acc.id)',
                'set CLIENT_ID = APP_ID',
               ),
          )
        return mess

    edlr_acc = db( db.dealers_accs.acc == request.args[0]).select().first()
    edlr = edlr_acc and db.dealers[edlr_acc.dealer_id]

    if not edlr: return 'not edlr or edlr_acc'

    api_pars, acc_pars, acc_name = ed_YD.get_pars(edlr, edlr_acc)
    print ( acc_name, ':', acc_pars)
    acc_pars['YM_REDIRECT_URI'] = acc_pars['YM_REDIRECT_URI'] + '/%s' % edlr_acc.id
    
    #return BEAUTIFY([api_pars, acc_pars, acc_name])
    
    redir_url = ed_YD.YmOauthRequestToken(api_pars, acc_pars)
    if True:
        redirect(redir_url)
    
    return BEAUTIFY([api_pars, acc_pars, acc_name, redir_url, 'for GO set to TRUUE if in script'])

## тут код промежуточный дается - настоящий по ззапросу получаем
## http://7pay.in/ipay/ed_YD/yandex_response?code=86...8
def yandex_response():
    
    h = ''
    edlr_acc_id = request.args(0)
    if not edlr_acc_id:
        h += '''not edlr_acc_id in request params'''
        return h

    code = request.vars.get('code')
    if not code:
        #raise HTTP(400, 'ERROR: not code')
        return 'ERROR: not code'

    edlr_acc = db.dealers_accs[edlr_acc_id]
    edlr = edlr_acc and db.dealers[edlr_acc.dealer_id]
    if not edlr: return 'response: edlr or edlr_acc is empty!'

    api_pars, acc_pars, acc_name = ed_YD.get_pars(edlr, edlr_acc)
    r = ed_YD.YmOauthRedirectHandler(api_pars, acc_pars, code)
    accessToken = r.get('access_token', '')
    if accessToken == '':
        return 'ERROR: %s' % r.get('error')

    from datetime import timedelta
    edlr_acc.update_record(
            skey = accessToken,
            expired = request.now + timedelta(1000) # три года
            )
    return '... received , expired: %s </br>new token: %s' % (edlr_acc.expired, accessToken)
