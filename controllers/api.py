# coding: utf8

session.forget(response)
time_exp = IS_LOCAL and 3 or 66

import datetime
from decimal import Decimal

import db_common
import db_client
import serv_to_buy

## ALLOW API from not local
response.headers['Access-Control-Allow-Origin'] = '*'

def help():
    redirect(URL('index'))

@cache.action(time_expire=time_exp, cache_model=cache.disk) #, vars=False, public=True, lang=True)
def index():
    response.title = T('Как начать принимать оплаты биткоинами на сайте')
    response.meta['keywords']=T('оплты биткоинами, платежи биткоинами, приём биткоинов, скрипт биткоин сайта')
    response.meta['description']=T('Организуй приём биткоинов на своём сайте, скрипт биткоин сайта')
    #  http://127.0.0.1:90/ipay/clients/api/get_rate?curr_in=BTC&curr_out=RUB&vol_in=0.23
    # https://7pay.in/ipay/clients/api/get_rate?curr_in=RUB&curr_out=BTC&vol_in=230
    return dict()


@cache.action(time_expire=time_exp, cache_model=cache.disk, vars=True, public=True, lang=False)
def rates():
    import time
    time.sleep(1)
    if 'wp' in request.args:
        # это переделать имена параметров под http://web-payment.ru/ стандарт
        WPnames = request.args.index('wp')
        deal_sel = WPnames and request.args(0) or request.args(1)
        WPnames = True
    else:
        deal_sel = request.args(0)
        WPnames = False
        
    #print deal_sel
    if deal_sel and deal_sel.upper() == 'HELP':
        return 'rates/[deal] - deal = PH_7RUB | TO_YDRUB | IN_YDRUB | TO_COIN | None - all'
    import rates_lib, db_client, ed_common
    rub_curr, x, ecurr_out = db_common.get_currs_by_abbrev(db,"RUB")
    ecurr_out_id = ecurr_out.id
    vol_rub = 1000
    res = []
    currs_in_max = {}
    currs_to_max = {}
    dealer_deal = None
    to_abbrev = 'PH_7RUB'
    if not deal_sel or deal_sel.upper() == to_abbrev:
        ## сначала длля телефона
        if TO_PHONE7_ID:
            deal = db.deals[ TO_PHONE7_ID ]
        else:
            deal = db(db.deals.name=='phone +7').select().first()
        dealer, dealer_acc, dealer_deal = ed_common.select_ed_acc(db, deal, ecurr_out)
        #print deal.name, 'dealer:', dealer_deal
        to_max = round(float(db_common.get_balance_dealer_acc( dealer_acc )), 8)

        for r in db((db.currs.id==db.xcurrs.curr_id)
                          & (db.currs.used==True)).select():
            curr_in = r.currs
            # теперь курс и мзду нашу найдем
            pr_b, pr_s, rate = rates_lib.get_average_rate_bsa(db, curr_in.id, rub_curr.id, None)
            if not rate: continue
            vol_out = vol_rub # в рублях
            in_max = curr_in.max_bal or 0
            if in_max>0:
                bal = db_client.curr_free_bal(curr_in)
                in_max = round(float(in_max - bal), 8)
            in_abbrev = curr_in.abbrev
            currs_in_max[ in_abbrev ] = in_max

            is_order = True
            vol_in, tax_rep = db_client.calc_fees_back(db, deal, dealer_deal, curr_in, rub_curr, vol_out,
                                               rate, is_order, note=0)
            ##rate = vol_out_new / vol_in
            '''
            <rates>
                <item>
                <from>PMEUR</from>
                <to>PMUSD</to>
                <in>1</in>
                <out>1.07</out>
                <amount>4322.79649</amount>
                <param>manual</param>
                <minamount>0 EUR</minamount>
                </item>
            '''
            if WPnames:
                item = { 'from': in_abbrev, 'to': to_abbrev,
                       'in': round(float(vol_in),8 ), 'out': vol_out,
                       'amount': to_max }
            else:
                item = { 'in': in_abbrev, 'to': to_abbrev,
                       'in_vol': round(float(vol_in),8 ), 'to_vol': vol_out,
                       'to_max': to_max }
            if in_max: item['in_max'] = in_max
            res.append(item)
    ###############
    ## теперь на ЯД кошелек
    to_abbrev = 'YDRUB'
    if not deal_sel or deal_sel.upper() == 'TO_YDRUB':
        if TO_WALLET_ID:
            deal = db.deals[ TO_WALLET_ID ]
        else:
            deal = db(db.deals.name=='BUY').select().first()
        dealer, dealer_acc, dealer_deal = ed_common.select_ed_acc(db, deal, ecurr_out)
        #print deal.name, 'dealer:', dealer_deal
        to_max = dealer_max = round(float(db_common.get_balance_dealer_acc( dealer_acc )), 8)
        for r in db((db.currs.id==db.xcurrs.curr_id)
                          & (db.currs.used==True)).select():
            curr_in = r.currs
            # теперь курс и мзду нашу найдем
            pr_b, pr_s, rate = rates_lib.get_average_rate_bsa(db, curr_in.id, rub_curr.id, None)
            if not rate: continue

            vol_out = vol_rub # в рублях
            is_order = True
            vol_in, tax_rep = db_client.calc_fees_back(db, deal, dealer_deal, curr_in, rub_curr, vol_out,
                                               rate, is_order, note=0)
            in_abbrev =  curr_in.abbrev
            if WPnames:
                item = { 'from': in_abbrev, 'to': to_abbrev,
                       'in': round(float(vol_in),8 ), 'out': vol_out,
                       'amount': to_max }
            else:
                item = { 'in': in_abbrev, 'to': to_abbrev,
                       'in_vol': round(float(vol_in),8 ), 'to_vol': vol_out,
                       'to_max': to_max }
            ## вытащим из кеша если он там есть
            in_max = currs_in_max.get( in_abbrev )
            if in_max == None:
                in_max = curr_in.max_bal or 0
                if in_max>0:
                    bal = db_client.curr_free_bal(curr_in)
                    in_max = round(float(in_max - bal), 8)
            if in_max: item['in_max'] = in_max
            res.append(item)

        ###### покупка через ЯДеньги
    if not deal_sel or deal_sel.upper() == 'IN_YDRUB':
        in_abbrev = 'YDRUB'
        if TO_BUY_ID:
            deal = db.deals[ TO_BUY_ID ]
        else:
            deal = db(db.deals.name=='BUY').select().first()
        # тут пустой %% dealer, dealer_acc, dealer_deal = ed_common.select_ed_acc(db, deal, ecurr_out)
        #print deal.name, 'dealer:', dealer_deal
        dealer_deal = None
        in_max = 57000 # у фиатного диллера одну покупку ограничим
        for r in db((db.currs.id==db.xcurrs.curr_id)
                          & (db.currs.used==True)).select():
            curr_out = r.currs
            vol_in = vol_rub # в рублях
            to_abbrev = curr_out.abbrev
            currs_to_max[ to_abbrev ] = to_max = round(float(db_client.curr_free_bal(curr_out)), 8)

            # теперь курс и мзду нашу найдем
            pr_b, pr_s, rate = rates_lib.get_average_rate_bsa(db, rub_curr.id, curr_out.id, None)
            if not rate: continue
            is_order = True
            vol_out, tax_rep = db_client.calc_fees(db, deal, dealer_deal, rub_curr, curr_out, vol_in,
                                               rate, is_order, note=0)
            if WPnames:
                item = { 'from': in_abbrev, 'to': to_abbrev,
                       'in': vol_in, 'out': round(float(vol_out),8 ),
                       'amount': to_max, 'in_max': in_max  }
            else:
                item = { 'in': in_abbrev, 'to': to_abbrev,
                       'in_vol': vol_in, 'to_vol': round(float(vol_out),8 ),
                       'to_max': to_max, 'in_max': in_max }
            res.append(item)

    #########
    # обмен крипты
    if not deal_sel or deal_sel.upper() == 'TO_COIN':
        if TO_COIN_ID:
            deal = db.deals[ TO_COIN_ID ]
        else:
            deal = db(db.deals.name=='to COIN').select().first()
        for r_in in db((db.currs.id==db.xcurrs.curr_id)
                          & (db.currs.used==True)).select():
            curr_in = r_in.currs
            in_abbrev = curr_in.abbrev
            vol_in = vol_rub * rates_lib.get_avr_rate_or_null(db, rub_curr.id, curr_in.id)
            vol_out = vol_rub # в рублях
            to_max = 0

            in_max = currs_in_max.get( in_abbrev )
            if in_max == None:
                in_max = curr_in.max_bal or 0
                if in_max>0:
                    bal = db_client.curr_free_bal(curr_in)
                    in_max = round(float(in_max - bal), 8)
            #print curr_in.abbrev, ' to RUB', vol_in
            for r_out in db((db.currs.id==db.xcurrs.curr_id)
                              & (db.currs.used==True)).select():
                curr_out = r_out.currs
                if curr_in.id == curr_out.id: continue
                # теперь курс и мзду нашу найдем
                pr_b, pr_s, rate = rates_lib.get_average_rate_bsa(db, curr_in.id, curr_out.id, None)
                if not rate: continue

                to_abbrev = curr_out.abbrev
                to_max = currs_to_max.get(to_abbrev, round(float(db_client.curr_free_bal(curr_out)), 8))
                # для каждого направление - свое дело

                is_order = True
                vol_out, tax_rep = db_client.calc_fees(db, deal, dealer_deal, curr_in, curr_out, vol_in,
                                                   rate, is_order, note=0)
            if WPnames:
                item = { 'from': in_abbrev, 'to': to_abbrev,
                       'in':round(float(vol_in),8), 'out': round(float(vol_out),8),
                       'amount': to_max }
            else:
                item = { 'in': in_abbrev, 'to': to_abbrev,
                           'in_vol':round(float(vol_in),8), 'to_vol': round(float(vol_out),8),
                           'to_max': to_max }
                if in_max: item['in_max'] = in_max
                res.append(item)
    return request.extension == 'html' and dict(
        h=DIV(BEAUTIFY({'rates': res}), _class='container')) or {'rates': res}


#@cache.action(time_expire=time_exp, cache_model=cache.disk, vars=True, public=True, lang=True)
def curr_get_info():
    import time
    time.sleep(1)

    curr_abbrev = request.args(0)
    if not curr_abbrev:
        return {"error": "empty curr - example: curr_get_info/btc" }
    curr_abbrev = curr_abbrev.upper()
    from db_common import get_currs_by_abbrev
    curr,xcurr,e = get_currs_by_abbrev(db, curr_abbrev)
    if not xcurr:
        return {"error": "invalid curr: " + curr_abbrev }
    
    token_system = None
    token_key = xcurr.as_token
    if token_key:
        token = db.tokens[token_key]
        token_system = db.systems[token.system_id]
    if token_system and token_system.name == 'Erachain':
        # UESE tokenSystem
        import rpc_erachain
        res = rpc_erachain.get_info(token_system.connect_url)
        res = {'height': res, 'balances': rpc_erachain.get_balances(token_system.connect_url, token_system.account),
               'from_block': token_system.from_block }
    else:
        from crypto_client import conn
        try:
            conn = conn(curr, xcurr)
            #return {'error': '%s' % conn}
        except:
            conn = None
        if not conn:
            return {'error': 'Connection to ' + curr_abbrev + ' wallet is lost. Try later'}
        #print conn
        try:
            #getblockchaininfo, getnetworkinfo, and getwalletinfo
            #res = conn.getinfo()
            res = conn.getnetworkinfo()
            #res = conn.getblockchaininfo()
            #res = conn.getwalletinfo() (!!!!) - дает ключи?
        #except Exception as e:
        except Exception, e:
            return {'error': 'Connection to ' + curr_abbrev + ' wallet raise error [%s]. Try later' % e}
    
    return res

# http://127.0.0.1:8000/shop/api/validate_addr.json/BTC/14qZ3c9WGGBZrftMUhDTnrQMzwafYwNiLt
def validate_addr():
    import time
    time.sleep(1)
    
    xcurr = None
    curr_abbrev = request.vars.get('curr')
    addr = request.vars.get('addr')
    if len(request.args) == 1:
        addr = request.args[0]
    if len(request.args) == 2:
        curr_abbrev = request.args[0]
        addr = addr or request.args[1]
        
    if not addr:
        return {'error':'need addr or curr_abbrev, example: /validate_addr.json/[addr] or /validate_addr.json/[curr_abbrev]/[addr]'}
        
    if addr and not curr_abbrev:
        from db_common import get_currs_by_addr
        curr, xcurr, _ = get_currs_by_addr(db, addr)

    if curr_abbrev:
        from db_common import get_currs_by_abbrev
        curr, xcurr, _ = get_currs_by_abbrev(db, curr_abbrev)
        
    
    if not xcurr:
        return {"error": "invalid curr_abbrev"}
    
    token_system_out = None
    token_key = xcurr.as_token
    if token_key:
        token = db.tokens[token_key]
        token_system = db.systems[token.system_id]

        import rpc_erachain
        curr_block = rpc_erachain.get_info(token_system.connect_url)
        if type(curr_block) != type(1):
            return {'error':'Connection to [%s] is lost, try later ' % curr.name}
        if rpc_erachain.is_not_valid_addr(token_system.connect_url, addr):
            return {'error':'address not valid for ' + curr.name + ' - ' + addr}

        return { 'curr': curr.abbrev, 'ismine': token_system.account == addr}
    else:
    
        from crypto_client import conn
        try:
            conn = conn(curr, xcurr)
        except:
            conn = None
        if not conn:
            return {'error':'Connection to [%s] is lost, try later ' % curr.name}
        
        valid = conn.validateaddress(addr)
        
        #import crypto_client
        #if crypto_client.is_not_valid_addr(conn, addr):
        #    return { 'error': 'address not valid for - ' + curr.abbrev}
    
        if not valid.get('isvalid'):
            return {"error": "invalid for [%s]" % curr.abbrev, 'mess': '%s' % valid}
        return { 'curr': curr.abbrev, 'ismine': valid.get('ismine'), 'mess': '%s' % valid }

@cache.action(time_expire=time_exp*10, cache_model=cache.disk)
def get_rates():
    session.forget(response)
    return { 'error': 'please use /rates/to_ydrub or rates/help API call instead'}

@cache.action(time_expire=time_exp*10, cache_model=cache.disk)
def get_buy_rates():
    session.forget(response)
    return { 'error': 'please use /rates/in_ydrub or rates/help API call instead'}

@cache.action(time_expire=IS_LOCAL and 5 or 300, cache_model=cache.ram, public=False, lang=False)
def rates3():
    session.forget(response)
    curr_out = db(db.currs.abbrev == 'BTC').select().first()
    if not curr_out: return 'curr_out [BTC] not found'

    currs_list = ['BTC', 'LTC', 'DASH', 'ERA', 'COMPU']
    import rates_lib
    btc_rates = []
    for r in rates_lib.top_line(db, curr_out, currs_list):
        btc_rates.append(r)

    curr_out = db(db.currs.abbrev == 'USD').select().first()
    if not curr_out: return 'curr_out [USD] not found'

    usd_rates = []
    for r in rates_lib.top_line(db, curr_out, currs_list):
        usd_rates.append(r)

    curr_out = db(db.currs.abbrev == 'RUB').select().first()
    if not curr_out: return 'curr_out [RUB] not found'

    rub_rates = []
    for r in rates_lib.top_line(db, curr_out, currs_list):
        rub_rates.append(r)
    
    return dict( btc = btc_rates, usd = usd_rates, rub = rub_rates)

# адес тут должен быть точный
def for_addr():
    session.forget(response)
    addr = request.vars and request.vars.get('addr')
    #print addr
    if not addr or len(addr) < 24: return dict(pays=T('ошибочный адрес [%s]') % addr)

    pays = where.found_buys(db, addr)
    if len(pays)>0:
        return dict(pays=pays)

    pays=[]
    # все еще не подтвержденные
    curr, xcurr, _, = db_common.get_currs_by_addr(db, addr)
    #print curr, '\n', xcurr
    if not curr or not curr.used: return dict(pays=T('ошибочный адрес по первой букве [%s]') % addr)
    where.found_unconfirmed(db, curr, xcurr, addr, pays)


    where.found_pay_ins(db, curr, xcurr, addr, pays, None)
    if len(pays)==0: pays = T('Входов не найдено...')
    return dict(pays=pays)

#@cache.action(time_expire=request.is_local and 5 or 30, cache_model=cache.disk,
#              vars=True, public=True, lang=True)
def deals_does():

    addr = request.args(0) or request.vars.addr
    if addr and len(addr) > 40: addr = None

    import where3
    pays = []

    deal_acc_addr = db(db.deal_acc_addrs.addr == addr).select().first()
    if not deal_acc_addr:
        return mess('Deals not found')
    xcurr_in = db.xcurrs[deal_acc_addr.xcurr_id ]
    curr_in = db.currs[ xcurr_in.curr_id ]
    deal_acc = db.deal_accs[ deal_acc_addr.deal_acc_id]
    curr_out = db.currs[ deal_acc.curr_id ]
    deal = db.deals[ deal_acc.deal_id ]
    payed_month = not deal.is_shop and deal_acc.payed_month or Decimal(0)
    MAX = deal.MAX_pay
    payed = deal_acc.payed or Decimal(0)
    price = deal_acc.price
    order_id = deal_acc.acc
    amo_rest_url = None
    client = db(db.clients.deal_id == deal.id).select().first()
    if client:
        curr_out = db.currs[deal_acc.curr_id]
        vvv = {'order':order_id, 'curr_out':curr_out.abbrev}

        if price and price >0 and price - payed > 0:
            # еще надо доплатить
            vvv['sum'] = price - payed
        amo_rest_url=A(T('Доплатить'), _href=URL('to_shop','index', args=[client.id],
            vars=vvv))

    import gifts_lib
    if 'to COIN' in deal.name:
        rnd = 8
    else:
        rnd = 2
    adds_mess = XML(gifts_lib.adds_mess(deal_acc, PARTNER_MIN, T, rnd))

    pays_unconf = []
    where3.found_unconfirmed(db, curr_in, xcurr_in, addr, pays_unconf)
    #print 'pays_unconf:', pays_unconf

    pays_process=[]
    where3.found_pay_ins_process(db, addr, pays_process)

    pays=[]
    where3.found_pay_ins(db, addr, pays)
    #print 'pays:', pays
    return dict( pays_unconf=pays_unconf, pays_process=pays_process, pays=pays,
        payed_month=payed_month, MAX=MAX, addr=addr,
        payed=payed, price=price, order_id=order_id, amo_rest_url=amo_rest_url,
        adds_mess = adds_mess,
        curr_in = curr_in, deal_acc = deal_acc,
        curr_out = curr_out, deal = deal, privat = False,
        )

    # сюда пришло значит ищес общий список
    pays_process=[]
    where3.found_pay_ins_process(db, addr, pays_process)
    pays=[]
    privat = where3.found_pay_ins(db, addr, pays)

    pays_unconf = []
    if not privat:
        # если мне то и все неподтв
        # все еще не подтвержденные
        for xcurr_in in db(db.xcurrs).select():
            curr_in = db.currs[xcurr_in.curr_id]
            if not curr_in or not curr_in.used: continue
            where3.found_unconfirmed(db, curr_in, xcurr_in, None, pays_unconf)

    return dict( adds_mess = None, pays_unconf=pays_unconf, pays_process=pays_process, addr = None, pays=pays, privat = privat)

def deals_wait():
    addr = request.args(0) or request.vars.addr
    if addr and len(addr) > 40: addr = None

    import where3
    pays = []


    # сюда пришло значит ищес общий список
    pays_process=[]
    where3.found_pay_ins_process(db, addr, pays_process)
    pays=[]
    privat = where3.found_pay_ins(db, addr, pays)

    pays_unconf = []
    if not privat:
        # если мне то и все неподтв
        # все еще не подтвержденные
        for xcurr_in in db(db.xcurrs).select():
            curr_in = db.currs[xcurr_in.curr_id]
            if not curr_in or not curr_in.used: continue
            where3.found_unconfirmed(db, curr_in, xcurr_in, None, pays_unconf)

    return dict( adds_mess = None, pays_unconf=pays_unconf, pays_process=pays_process, addr = None, pays=pays, privat = privat)
