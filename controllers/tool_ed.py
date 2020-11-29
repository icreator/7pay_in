# -*- coding: utf-8 -*-

if False:
    from gluon import *

    request = current.request
    response = current.response
    session = current.session
    cache = current.cache
    T = current.T
    import db

if not IS_LOCAL: raise HTTP(200, 'error')


from decimal import Decimal
import ed_common


# исправляем ошибку разбора по носеру заказа для покупки крипты
def try_buy_stack():
    if not request.args(0): return '/buys_stack.id'
    buy_st = db.buys_stack[ request.args(0) ]
    if not buy_st: return 'buy_stack rec not exist'
    buy = db.buys[ buy_st.ref_ ]
    
    mess = buy.addr
    xcurr, addr = ed_common.is_order_addr(db, mess)
    print xcurr
    if xcurr and not buy.xcurr_id:
        buy.update_record( xcurr_id = xcurr.id, addr = addr )
    return addr
    
# задаем парамеьры для яндекс
def set_pars_YD(dealer):
    acc = request.vars.acc
    h = CAT(
        DIV(
            LABEL('Account'),': ', INPUT(_name='acc', _value=acc or ''), ' - если аккаунта еще нет в БД - он добавится',
        _class='row '),
        DIV(
        LABEL('secret_response'),': ', INPUT(_name='secret_response'),' - If setted - will update [pkey] - CLIENT_ID is required too!',
            BR(),
        LABEL('CLIENT_ID'),': ', INPUT(_name='CLIENT_ID'),' - надо взять из ЯД - для подключения АПИ: ',
            A('Регистрация приложения', _href='https://money.yandex.ru/myservices/new.xml', _target='_blank'), BR(),
        _class='row gold-bgc'),
        )
    
    secret_response = request.vars.secret_response
    if dealer and acc:
        ed_acc = db((db.dealers_accs.dealer_id==dealer.id) & (db.dealers_accs.acc==acc)).select().first()
        if secret_response:
            from gluon.contrib import simplejson as js
            pars = js.dumps({"CLIENT_ID": request.vars.CLIENT_ID,
                "YM_REDIRECT_URI": "https://"+DOMEN+"/ed_YD/yandex_response",
                "SCOPE": "account-info operation-history operation-details payment-shop.limit(1,37777) payment-p2p.limit(1,37777)",
                "secret_response": secret_response})
            if ed_acc:
                ed_acc.update_record(pkey=pars)
                response.flash = 'updated'
            else:
                #ed_acc = db.dealers_accs[ db.dealers_accs.insert(dealer_id=dealer.id, pkey=pars) ]
                ed_acc = db.dealers_accs[ db.dealers_accs.insert(dealer_id=dealer.id, acc=acc, ecurr_id=request.vars.ecurr, pkey=pars) ]
                response.flash = 'added for ecurr_id ' + request.vars.ecurr
        db.commit()
        
        if ed_acc:
            import ed_YD
            api_pars, acc_pars, acc_name = ed_YD.get_pars(dealer, ed_acc)
            acc_pars['YM_REDIRECT_URI'] = acc_pars['YM_REDIRECT_URI'] + '/%s' % ed_acc.id
            ##return BEAUTIFY([api_pars, acc_pars, acc_name])
            redir_url = ed_YD.YmOauthRequestToken(api_pars, acc_pars)
            h += P(A(H3('For get API token - click it!'), _href = redir_url, _target='_blank'), BR())

        h += DIV(BEAUTIFY(ed_acc))
    return h

# настроить аккаунт для работы по АПИ
# так же можно добавить новый аккаунт
def set_pars_api():
    fields = dealer_id = request.vars.dealer
    if dealer_id:
        dealer = db.dealers[dealer_id]
        if dealer.name == 'Yandex':
            fields = set_pars_YD(dealer)
    h = CAT()
    eds = []
    for ed in db(db.dealers).select():
        eds.append(OPTION(ed.name, _value=ed.id))
    crs = []
    for r in db((db.ecurrs.curr_id==db.currs.id)
                & (db.currs.used==True)).select():
        crs.append(OPTION(r.currs.name, _value=r.ecurrs.id))
    h += DIV(
        DIV(
            P('Для ввода нового счета - задайте диллера, валюту, номер аккаунта, секрет для HTTP уведомлений и ИД приложения. Затем, когда аккаунт будет добавлен - нажмите на "Полусить АПИ токен"'),
        FORM(
            LABEL('Платежная служба?'),
            SELECT( eds,
                _class="blue-c", _name="dealer",
                ),' - для нее добавляем счет или обновляем его',BR(),
            LABEL('Валюта счета?'),
            SELECT( crs,
                _class="blue-c", _name="ecurr",
                ),
            fields or '', BR(),
            INPUT(_type='submit'),
            ),
        _class="row", _style="padding-bottom:10px;"),
        _class="container",
        )
    
    return dict(h=h)

# http://127.0.0.1:8000/ipay3_dvlp/tool_ed/update/11/-500
def update_bal():
    if len(request.args) < 2:
        return ' dealer_acc = db.dealers_accs[ request.args(0) ] + amount = -500'
    import ed_bal
    dealer_acc = db.dealers_accs[ request.args(0) ]
    ed_bal.update(db, dealer_acc, request.args(1), None, limited=True)

# показать балансы счетов для диллера ИД с ограничениями
def get_limited():
    if len(request.args) ==0: return ' dealer = db.dealers[ request.args(0) ] '
    import ed_bal
    dealer = db.dealers[ request.args(0) ]
    bal, accs = ed_bal.get_limited(db, dealer)
    h = CAT(
        'PAY_LIM:', ed_bal.PAY_LIM, # стандартное оограничение на один платеж
        ' DAY_LIM_A:', ed_bal.DAY_LIM_A,
        ' DAY_LIM_P:', ed_bal.DAY_LIM_P,
        ' MON_LIM_A:', ed_bal.MON_LIM_A,
        ' MON_LIM_P:', ed_bal.MON_LIM_P
        )
    for r in accs:
        acc = r[1]
        h += DIV(
            'limit balance:', r[0],BR(),
            acc.acc, ' full bal:',acc.balance, ' day_lim_sum:',acc.day_limit_sum, ' mon_lim_sum;', acc.mon_limit_sum,
            _class='row')
    return dict(h = DIV(B(bal),BR(), h, _class='container'))

def index():
    return dict()

######################################################
# ipay
def get_ebalance():
    if len(request.args) == 0:
        mess = 'get_ebalance/[dealer_acc_id]'
        return mess
    import ed_common
    dealer_acc = db.dealers_accs[ request.args[0]]
    dealer = db.dealers[ dealer_acc. dealer_id ]
    res = ed_common.get_balance(dealer, dealer_acc )
    print type(res), res
    return 'type:%s - %s' % (type(res), res)

# 410012107376992/
def is_payment_for_buy():
    if len(request.args) <2: return '/acc/op_id - /410012107376992/..'
    acc = request.args(0)
    dealer_acc = db(db.dealers_accs.acc==acc).select().first()
    if not dealer_acc: return 'ed_acc not founf'
    dealer = db.dealers[ dealer_acc.dealer_id]
    op_id = request.args(1)
    import ed_common
    info = ed_common.get_payment_info(dealer, dealer_acc, op_id )
    info1, mess = ed_common.is_payment_for_buy(db, dealer, dealer_acc, info, test=True)
    return mess and BEAUTIFY({'mess': mess, 'info': info}) or BEAUTIFY({'info': info, 'info1': info1})

def pay_test_to_phone():
    import ed_common
    phone = '79169172019' # берем аккаунт и дело для моего телефона
    deal_acc = db(db.deal_accs.acc==phone).select().first()
    deal = db.deals[deal_acc.deal_id]
    dealer_acc = db.dealers_accs[6]
    dealer = db.dealers[dealer_acc.dealer_id]
    dealer_deal = db(
        (db.dealer_deals.dealer_id==dealer.id)
        & (db.dealer_deals.deal_id==deal.id)
        ).select().first()
    # послали запрос на операцию
    #pay(edlr, edlr_acc, pattern_id, deal_acc, amo, pay_pars, testMake, testConfirm):
    # если задан другой телефон то платеж ему сделаем
    phone = len(request.args) == 0 and phone or request.args[0]
    res = ed_common.pay(deal, dealer, dealer_acc, dealer_deal, phone, 13)
    print res
    return res

# http://127.0.0.1:8000/ipay/tools/pay_test_YD?pattern_id=1856&sum=15&PROPERTY1=0897468952&rapida_param1=0897468952&redsum=15
# платеж с заданными параметрами
# redsum=15&PROPERTY1=0897468952&sum=15&pattern_id=1856&rapida_param1=0897468952 - такие на входе
def pay_test():
    session.forget(response)
    import db_common
    import ed_common
    scid = request.vars.get('pattern_id')
    curr, xcurr, ecurr= db_common.get_currs_by_abbrev(db,'RUB')
    dealer_deal = db((db.dealer_deals.scid==scid)
            & (db.dealer_deals.dealer_id==dealer.id)).select().first()
    deal = db.deals[dealer_deal.deal_id]
    print deal.name
    dealer, dealer_acc, d_ = ed_common.select_ed_acc(db, deal, ecurr)
    print dealer_acc.acc, dealer_acc.balance
    vol = float(request.vars.get('sum') or request.vars.get('redsum') or 13)

    acc = '---???---'
    res = ed_common.pay_test(db, deal, dealer, dealer_acc, dealer_deal, acc, vol, True, request.vars)
    print res
    return BEAUTIFY(res)


def pay_test_to_deal():
    if not request.args(0): return '/deal_id - 46 (skype) / summ?acc=_'
    session.forget(response)
    import db_common
    import ed_common
    
    deal = db.deals[request.args(0)]
    dealer = db.dealers[1]
    curr, xcurr, ecurr= db_common.get_currs_by_abbrev(db,'RUB')
    dealer_deal = db((db.dealer_deals.deal_id==deal.id)
            & (db.dealer_deals.dealer_id==dealer.id)).select().first()
    #deal = db.deals[dealer_deal.deal_id]
    print deal.name
    dealer, dealer_acc, d_ = ed_common.select_ed_acc(db, deal, ecurr)
    print dealer_acc.acc, dealer_acc.balance
    
    vol = float(request.args(1) or 100)
    
    acc = request.vars.get('acc')
    res = ed_common.pay_test(db, deal, dealer, dealer_acc, dealer_deal, acc, vol, True, None)
    print res
    return BEAUTIFY(res)

# оплатить с заданного дилера с заданного акка диллера, по делу, на аккаунт дела - сумму
# http://127.0.0.1:8000/ipay/tools/pay_to_deal/Yandex/410012175232158?deal=WALLET&acc=410011949054154&sum=5
def pay_to_deal():
    if len(request.args) == 0:
        mess = 'andex/410012175232158?deal=WALLET&acc=410011949054154&sum=5'
        return mess

    import ed_common
    dealer = db(db.dealers.name==request.args[0]).select().first()
    dealer_acc = db((db.dealers_accs.dealer_id==dealer.id)
            & (db.dealers_accs.acc==request.args[1])).select().first()

    deal = db(db.deals.name==request.vars['deal']).select().first()
    acc = request.vars['acc']
    #deal_acc = db((db.deal_accs.deal_id==deal.id)
    #              & (db.deal_accs.acc==acc)).select().first()

    dealer_deal = db(
        (db.dealer_deals.dealer_id==dealer.id)
        & (db.dealer_deals.deal_id==deal.id)
        ).select().first()
    # послали запрос на операцию
    #pay(edlr, edlr_acc, pattern_id, deal_acc, amo, pay_pars, testMake, testConfirm):
    # если задан другой телефон то платеж ему сделаем
    res = ed_common.pay(db, deal, dealer, dealer_acc, dealer_deal, acc, float(request.vars['sum']))
    print res
    return BEAUTIFY(res)

# найти счет диллера с котрого будем платить
def edealer_acc_max():
    if len(request.args) == 0: return 'edealer_acc_max/edealer/amo'
    dealer = db.dealers[request.args(0) or 1]
    if not dealer: return 'dealer not found'
    vol = int(request.args(1) or 333)
    # берем только рубль
    import db_common, ed_common
    curr, x, ecurr = db_common.get_currs_by_abbrev(db,"RUB")
    import ed_common
    dealer_acc = ed_common.sel_acc_max(db, dealer, ecurr, vol)
    h = DIV(
        H3(dealer.name),' -> ', vol,
        BEAUTIFY(dealer_acc),
    )
    return dict(h = h)

# найти счет диллера на котрый будем принимть фиат
def edealer_acc_min():
    if len(request.args) == 0: return 'edealer_acc_min/edealer/amo'
    dealer = db.dealers[request.args(0) or 1]
    if not dealer: return 'dealer not found'
    vol = int(request.args(1) or 333)
    # берем только рубль
    import db_common, ed_common
    curr, x, ecurr = db_common.get_currs_by_abbrev(db,"RUB")
    import ed_common
    dealer_acc = ed_common.sel_acc_min(db, dealer, ecurr, vol)
    h = DIV(
        H3(dealer.name),' <- ', vol,
        BEAUTIFY(dealer_acc),
    )
    return dict(h = h)

def select_ed_acc():
    import db_common
    import ed_common
    deal_id = request.args(0)
    if not deal_id: return '/[deal_id]/[vol_out_full]/[limited]'
    deal = db.deals[deal_id]
    print deal.name
    curr = db.currs[ deal.fee_curr_id ]
    ecurr = db(db.ecurrs.curr_id == curr.id).select().first()
    volume_out_full = Decimal(request.args(1) or 0)
    limited = request.args(2)
    dealer, dealer_acc, d_ = ed_common.select_ed_acc(db, deal, ecurr, volume_out_full, limited)
    if not dealer_acc:
        return 'dealer_acc=None'
    print dealer_acc.acc, dealer_acc.balance
    h = CAT(H1(deal.name,' : ', curr.abbrev),
            dealer_acc.acc,': ', dealer_acc.balance, ' day_limit_sum:', dealer_acc.day_limit_sum,
            ' mon_limit_sum:', dealer_acc.mon_limit_sum,' reserve_MAX:', dealer_acc.reserve_MAX,
           )
    return dict(h=h)

# узнать сколько всего можно сейчас перевести с учетом ограничений
def get_lim_bal():
    if len(request.args) == 0:
        mess = 'len(request.args)==0'
        print mess
        return mess
    import ed_common
    dealer = db.dealers[request.args[0]]
    if not dealer: return 'dealer not found'

    bal, accs = ed_common.get_lim_bal(db, dealer)
    h = CAT(H3(dealer.name),
            H4(bal),
            BEAUTIFY( accs )
            )
    return dict(h = h)

### http://127.0.0.1:8000/ipay/edealers/get_payment_info/41001873409965/480020408341068008
def get_payment_info():
    if len(request.args) == 0:
        mess = '/edealers/get_payment_info/41001873409965/[op_id]'
        #print mess
        return mess
    ed_acc = request.args(0)
    op_id = request.args(1)
    dealer_acc = db(db.dealers_accs.acc==ed_acc).select().first()
    dealer = db.dealers[ dealer_acc.dealer_id ]
    
    import ed_common
    
    info = ed_common.get_payment_info(dealer, dealer_acc, op_id)
    info['REQUEST.now'] =request.now
    return info

# ппробовать найти все не выплоченные - на входе аккаунт у диллера - пооидее он уникальный
# задаем в теле скрипта:
# only_list (=None - значит с записью в БД)
# from_dt 
    # = '2013-12-29T10:42:33Z'
    # = '0' - всю историю
    # = None - берет с БД нашей последнюю дату опроса
    # = 'same' - взяь дату из нашей базы
# и вызываем:
# http://127.0.0.1:8000/ipay/edealers/list_incoms/41001875840125
# http://127.0.0.1:8000/ipay/edealers/list_incoms/41001873409965/2015-06-06T06:08:19Z
def list_incoms():
    if len(request.args) == 0:
        mess = '/edealers/list_incoms/41001873409965?from=same or 2015-06-06T06:08:19Z'
        #print mess
        return mess

    import serv_to_buy
    ed_acc = request.args(0)
    only_list = None
    only_list = True
    #from_dt = 'same'
    #from_dt = '2014-01-20T16:06:19Z' # 'same'
    from_dt = request.vars.get('from') or '2015-06-06T06:08:19Z'
    mess = serv_to_buy.proc_history(db, only_list, ed_acc, from_dt)
    return BEAUTIFY(mess)


def get_edealers_for_to_wallet():
    if len(request.args) == 0: return 'get_edealers_for_to_wallet/[ecurr_out_id=1]/[deal_id=15]/ed_name=None'
    ecurr_out = db.ecurrs[ request.args(0) ]
    curr_out = db.currs[ ecurr_out.curr_id ]
    deal = db.deals[ request.args(1) ]
    ed_name = request.args(2)
    limit_bal, inp_dealers = ed_common.get_edealers_for_to_wallet(db, deal, curr_out, ecurr_out.id, ed_name)
    return BEAUTIFY({'limit_bal':limit_bal, 'inp_dealers': inp_dealers })
