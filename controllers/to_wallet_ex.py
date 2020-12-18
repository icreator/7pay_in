# coding: utf8

if False:
    from gluon import *
    import db
    request = current.request
    response = current.response
    session = current.session
    cache = current.cache
    T = current.T

#import copy
import datetime, time
import re

import common
#import db_common
#import ed_common
import db_client
#import crypto_client
import ed_common
import recl

import db_common
import rates_lib

response.logo2 = IMG(_src=URL('static','images/7P-33.png'), _width=256)

# берем только рубль
curr_out, x, ecurr_out = db_common.get_currs_by_abbrev(db,"RUB")#ecurr_out = db.ecurrs[ecurr_out_id]
ecurr_out_id = ecurr_out.id

deal_name = 'WALLET'
# найдем дело
deal = db(db.deals.name==deal_name).select().first()
if not deal: raise HTTP(200, T('ERROR: not found deal "%s"') % deal_name)

deal_id = deal.id

#MAX = deal.MAX

def u(h, url, cls='col-sm-4', onclick=None, style=''):
    return DIV(DIV(P(h, _class='btn_mc2'), _class='btn_mc1',
                   _style=style,
                   _onclick=onclick or "location.href='%s'" % url), _class='btn_mc ' + cls)
def ug(h, url, cls='col-sm-4', onclick=None, style=''):
    return DIV(DIV(P(h, _class='btn_mc2'), _class='btn_mc1g',
                   _style=style,
                   _onclick=onclick or "location.href='%s'" % url), _class='btn_mc ' + cls)

def get_e_bal(deal, dealer, dealer_acc):
    e_balance = db_common.get_balance_dealer_acc( dealer_acc )
    MAX = deal.MAX_pay or 1333
    if e_balance:
        #dealer_acc.balance = e_balance
        #dealer_acc.update_record()
        if e_balance < MAX*3:
             MAX = round(e_balance/3,0)
        if e_balance > 27777: e_balance = '>27777'
    return e_balance, MAX


# переходник для показа ссылкок и картинок в листингах
def download():
    return response.download(request,db)

response.title = DOMEN

ERRS={
    'err01':T('ОШИБКА: Проверьте номер телефона'),
    'err02':T('ОШИБКА: Слишком маленькая сумма платежа')
    }


def pay():
# TODO тут на входе дело ловить а не валюту выхода

    #common.page_stats(db, response['view'])
    #print response['view'], ss, db_common.ip()

    response.title=T("Проверьте данные")
    ph = request.vars.get('phone')
    if not ph or len(ph)==0:
        redirect(URL('to_wallet','index',args=['err01']))
        return

    try:
        volume_out = float(request.vars['volume'])
        dealer_id = request.vars['dealer']
        dealer = db.dealers[dealer_id]
    except:
        time.sleep(333)
        raise HTTP('bee-bee-bee')

    dealer_acc = ed_common.sel_acc_max(db, dealer, ecurr_out, volume_out)
    if not dealer_acc:
        return dict(uri=T('Не найден акк-дилер для обмена, возможно превышены лимиты, просьба подождать до следующего дня или месяца'), addr=None)
    dealer_deal = db((db.dealer_deals.dealer_id == dealer.id)
        & (db.dealer_deals.deal_id == deal.id )
        ).select().first()
    if not dealer_deal:
        response.title=T("ОШИБКА")
        return dict(uri=T('Не найден дилер для дела:'), addr=None)

    # теперь проверку на правильность кошелька для дилера электронных платежей
    #dealer_acc
    # pay_test(deal, dealer, dealer_acc, dealer_deal, deal_acc, volume_out)
    res = ed_common.pay_test(db, deal, dealer, dealer_acc, dealer_deal, ph, deal.MIN_pay or dealer.pay_out_MIN or 20, False)
    if res['status']!='success':
        response.title=T("ОШИБКА")
        mess = 'error_description' in res and res['error_description'] or res['error'] or 'dealer error'
        mess = T('Платежная система %s отвергла платеж, потому что: %s') % (dealer.name, mess)
        return dict(uri= mess, addr=None)


    session.visitor_wallet = ph

    # найдем по имени крипту
    curr_in, xcurr_in, e = db_common.get_currs_by_abbrev(db, request.vars['curr_in'])
    if not xcurr_in:
        response.title=T("ОШИБКА")
        return dict(uri=T('Криптовалюта ') + request.vars['curr_in'] + T(' не найдена в базе данных.'), addr=None)

    token_system_in = None
    token_key_in = xcurr_in.as_token
    if token_key_in:
        token_in = db.tokens[token_key_in]
        token_system_in = db.systems[token_in.system_id]

    if token_system_in:
        addr_in = token_system_in.account
        deal_acc_id, deal_acc_addr = db_client.get_deal_acc_addr(db, deal_id, curr_out, ph, addr_in, xcurr_in)
    elif xcurr_in.protocol == 'geth':
        addr_in = xcurr_in.main_addr
        deal_acc_id, deal_acc_addr = db_client.get_deal_acc_addr(db, deal_id, curr_out, ph, addr_in, xcurr_in)
    else:
        # get new or old adress for payment
        x_acc_label = db_client.make_x_acc(deal, ph, curr_out.abbrev)
        # найдем ранее созданный адресс для этого телефона, этой крипты и этого фиата
        # сначала найтем аккаунт у дела
        deal_acc_id = db_client.get_deal_acc_id(db, deal, ph, curr_out)
        # теперь найдем кошелек для данной крипты
        deal_acc_addr = db_client.get_deal_acc_addr_for_xcurr(db, deal_acc_id, curr_in, xcurr_in, x_acc_label)
        if not deal_acc_addr:
            response.title=T("ОШИБКА")
            return dict(uri= T(' связь с кошельком ') + curr_in.name + T(' прервана.'), addr=None)

        #request.vars['deal_acc_addr']=deal_acc_addr
        addr_in = deal_acc_addr.addr

    request.vars['addr_in']=addr_in

    MIN = deal.MIN_pay or dealer.pay_out_MIN or 3
    if MIN > volume_out:
        u = URL('to_wallet','index',args=['err02']) #, vars={'l':deal.MIN_pay})
        redirect(u)
        return

    request.vars['e_bal'], MAX = get_e_bal(deal, dealer, dealer_acc)
    if volume_out > MAX: volume_out = MAX

    ###best_rate, pairs, taxs, ed_fee = db_client.get_best_price_by_volume_out(db, curr_in.id, curr_out.id, volume_out, dealer.id)
    # используем быстрый поиск курса по формуле со степенью на количество входа
    # только надо найти кол-во входа от выхода
    best_rate = pairs = taxs= ed_fee = None

    pr_b, pr_s, pr_avg = rates_lib.get_average_rate_bsa(db, curr_in.id, curr_out.id, None)
    #print pr_b, pr_s, pr_avg
    if pr_avg:
        vol_in = volume_out / pr_b
        #print vol_in, curr_in.abbrev, '-->', volume_out, curr_out.abbrev
        amo_out, _, best_rate = rates_lib.get_rate(db, curr_in, curr_out, vol_in)
        #best_rate = best_rate and 1/best_rate
        #print best_rate, 1/best_rate

    #print best_rate, pair
    if not best_rate:
        response.title=T("ОШИБКА")
        return dict(uri='[' + curr_in.name + '] -> [' + curr_out.name + ']' + T(' - лучшая цена не доступна.'), addr=None)
    # найдем цену без процентов - чтобы было не так страшно
    #best_rate_clear = best_rate / (1 - ed_fee)
    #for t in taxs:
    #    best_rate_clear = best_rate_clear / (1 - t['tax'])

    volume_in, rate_out, tax_info = db_client.get_fees_for_out(
        db, deal, dealer_deal, curr_in, curr_out, volume_out, best_rate, pairs, taxs, ed_fee)

    #print tax_info
    request.vars['dealer_name']=dealer.name
    request.vars['curr_out_name']=curr_out.abbrev
    request.vars['curr_in_name']=curr_in.abbrev
    request.vars['best_rate']=rate_out
    request.vars['best_rate_rev']=round(1.0/best_rate,8)
    request.vars['volume_in'] = volume_in
    request.vars['volume'] = volume_out

    # make tax and fee report for this RATE
    tax_rep = ''
    for ss in tax_info:
        tax_rep = tax_rep + ss
    request.vars['rate_report'] = tax_rep

    #deal = db(db.deals.name==deal_name).select().first()
    # new make order
    #print deal_acc_addr
    id = db.orders.insert(
        ref_ = deal_acc_addr.id,
        volume_in = volume_in,
        volume_out = volume_out,
        )
    # теперь стек добавим, который будем удалять потом
    db.orders_stack.insert( ref_ = id )
    request.vars['order'] = id

    uri, qr = common.uri_make( curr_in.name2, addr_in, {'amount':volume_in, 'label': db_client.make_x_acc_label(deal, ph, curr_out.abbrev)})


    return dict(uri=uri, addr=addr_in, qr=qr)

def go2():
    dealer_id = request.args(0)
    if not dealer_id or not dealer_id.isdigit(): return T('Empty dealer_id')
    ecurr_id = request.args(1)
    if not ecurr_id or not ecurr_id.isdigit(): return T('Empty ecurr_id')
    dealer = db.dealers[ dealer_id ]
    if not dealer: return T('Empty dealer')
    ecurr = db.ecurrs[ ecurr_id ]
    if not ecurr: return T('Empty ecurr')
    curr_out = db.currs[ ecurr.curr_id ]
    if not curr_out: return T('Empty curr')
    
    #print request.vars
    best_rate = pairs = taxs = ed_fee = k = v = None
    for k, v in request.vars.iteritems():
        pass
    #return '%s: %s' % (k,v)
    # берем теперь наилучший аккаунт у этого диллера для нас
    volume_out = v and v.replace('.','').isdigit() and float(v) or 3
    dealer_acc = ed_common.sel_acc_max(db, dealer, ecurr, volume_out, not volume_out)
    if not dealer_acc:
        return T('Не найден акк-дилер для обмена, возможно превышены лимиты, просьба подождать до следующего дня или месяца')
    dealer_deal = db((db.dealer_deals.dealer_id == dealer.id)
        & (db.dealer_deals.deal_id == deal.id )
        ).select().first()
    if not dealer_deal:
        response.title=T("ОШИБКА")
        return T('Не найден дилер для дела:')
    
    h = CAT()
    
    MIN = deal.MIN_pay or dealer.pay_out_MIN or 3
    if MIN > volume_out:
        return T('ОШИБКА: Слишком маленькая сумма платежа')

    request.vars['e_bal'], MAX = get_e_bal(deal, dealer, dealer_acc)
    if volume_out > MAX:
        volume_out = float(MAX)

    _style='background-color: rgba(0, 0, 0, 0.25);'
    for rc in db(
                (db.xcurrs.curr_id == db.currs.id)
                & (db.currs.used==True)
                 ).select():
        #curr_in = db.currs[ xcurr.curr_id ]
        curr_in = rc.currs
        if not curr_in.used:
            hh = T('Not used')
        else:
            pr_b, pr_s, pr_avg = rates_lib.get_average_rate_bsa(db, curr_in.id, curr_out.id, None)
            #print pr_b, pr_s, pr_avg
            if pr_avg:
                vol_in = volume_out / pr_b
                #print vol_in, curr_in.abbrev, '-->', volume_out, curr_out.abbrev
                amo_out, _, best_rate = rates_lib.get_rate(db, curr_in, curr_out, vol_in)
                #best_rate = best_rate and 1/best_rate
                #print best_rate, 1/best_rate

            #print best_rate, pair
            if not best_rate:
                hh = CAT('[' + curr_in.name + '] -> [' + curr_out.name + ']' + T(' - лучшая цена не доступна.'))
            else:
                # найдем цену без процентов - чтобы было не так страшно
                #best_rate_clear = best_rate / (1 - ed_fee)
                #for t in taxs:
                #    best_rate_clear = best_rate_clear / (1 - t['tax'])

                volume_in, rate_out, tax_info = db_client.get_fees_for_out(
                    db, deal, dealer_deal, curr_in, curr_out, volume_out, best_rate, pairs, taxs, ed_fee)
                hh = CAT(DIV(
                        DIV(_class='col-md-1'),
                        ug(CAT(IMG(_src=URL('default','download', args=['db', curr_in.icon]),
                                  _width=64, _class='lst_icon', _alt=curr_in.name), ' ',
                              curr_in.name),
                          None,
                          'col-md-4 col-sm-5',
                          None,
                          #onclick="$('#%s').text('%s');ajax('%s', ['%s'], '%s')" % (tag, T('Working...'),url, curr.abbrev, tag),
                          #'background-color: rgba(19, 159, 24, 0.6);'
                          ),
                        DIV(T('For GET:'), ' ', volume_out, BR(),
                            T('To PAY:'), ' ', volume_in, BR(),
                            T('By RATE:'), ' ', rate_out,
                            _class='btn_mc col-sm-7'),
                        _class='row'),
                     DIV(tax_info, _class='small row'),
                     HR(),
                         )
                
                #hc = curr
        
        h += DIV(hh, _style=_style, _class='row')
    h += DIV(T('Max amount:'),' ', dealer_acc.balance)
    return h


############################################################
def index():

    response.title=T("Перевод криптоденег в электронные деньги")

    if session.visitor_date_log:
        d_diff = datetime.datetime.today() - session.visitor_date_log
        if d_diff.seconds > 1200:
            session.visitor_date_log = None
            session.visitor_wallet = '-'


    h = CAT()

    for ecurr_out in db(db.ecurrs).select():
        curr = db.currs[ ecurr_out.curr_id ]
        hh = CAT(H3(IMG(_src=URL('default','download', args=['db', curr.icon]), _width=42, _height=42, _class='lst_icon', _id='lst_icon%s' % id),
                curr.name,' ',
                INPUT(_name=curr.abbrev, _value='123'),
                ))
        for r in db(
                 (db.dealers_accs.ecurr_id==ecurr_out.id)
                 & (db.dealers_accs.used == True)
                 & (db.dealers.id == db.dealers_accs.dealer_id)
                 & (db.dealers.used == True)
                 & (db.dealer_deals.dealer_id == db.dealers.id)
                 & (db.dealer_deals.deal_id == deal.id)
                ).select(db.dealers.ALL, groupby=db.dealers.id):
            
            min = 10
            dealer_acc = ed_common.sel_acc_max(db, r.dealers, ecurr_out, 0, True)
            bal, max = get_e_bal(deal, r.dealers, dealer_acc)

            _id = r.dealers.id
            tag = 'tag%s' % _id
            url = URL('to_wallet2', 'go2', args=[curr.id, _id])
            st = 'display: table-cell; vertical-align: middle;'
            fee = curr.fee_out
            tax = r.dealer_deals.tax + curr.tax_out
            
            hh += DIV(
                    u(r.dealers.name,
                          #URL('to_wallet2', 'go1', args=[curr.id, r.dealers.id]),
                          None,
                          'col-sm-5',
                      onclick="$('#%s').text('%s');ajax('%s', ['%s'], '%s')" % (tag, T('Working...'),url, curr.abbrev, tag)),
                    DIV(T('Min / Max'), ': ', min, ' / ', max, BR(),
                        T('Is:'), ' ', bal, BR(),
                        T('Fee & Tax'), ' - ', fee, ' & ', tax,'%',
                        _class='btn_mc col-sm-5'),
                    _class='row')
            hh += DIV(_id=tag, _class='row')
        h += hh

    return dict(h = h)

    if len(dd)==0:
        response.subtitle=T("ОШИБКА: Нет подходящих работников!")
        return dict( vars = None)

    ed_sel = SELECT(dd, value='1', _name='dealer')

    volume_out = float(100)
    pairs = db_client.get_xcurrs_for_deal(db, volume_out, curr_out, deal, None)

    vars = {
            'phone': session.visitor_wallet or None,
            #'mess' = request.args,
            'MIN': deal.MIN_pay or 3,
            'MAX': deal.MAX_pay or 1333,
            'ed_sel': ed_sel,
            'last_visit': session.visitor_date_log
            }
    wallet = None
    if request.vars:
        vn = 'sum'
        if vn in request.vars:
            vars[vn] = request.vars[vn]
        vn = 'wallet'
        if vn in request.vars:
            wallet = request.vars[vn]
            vars[vn] = wallet
            if not ed_name:
                response.subtitle=T("ОШИБКА: Не задано имя системы электронных денег для данного кошелька %s!") % wallet
                return dict( vars = None)

        vn = 'mess'
        if 'mess' in request.vars:
            vars[vn] = request.vars[vn]

    title1 = wallet and T('Оплата на %s') % ed_name  or T('Ваш кошелек')
    wallet = wallet or session.visitor_wallet or None
    if wallet: response.title = title1 + ':' + wallet[:3] + '****' + wallet[-3:]

    #print request.args
    if len(request.args)>0: response.flash = ERRS[request.args[0]]

    _, reclams = recl.get(db,2)

    # тут балансы у разных диллеров vars['e_bal'] = get_e_bal(deal, dealer, dealer_acc)

    return dict(reclams=reclams, vars=vars, xcurrs_list=pairs)
