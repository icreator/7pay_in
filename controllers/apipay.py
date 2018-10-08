# coding: utf8

session.forget(response)

## ALLOW API from not local
response.headers['Access-Control-Allow-Origin'] = '*'

time_exp = IS_LOCAL and 3 or 666

import datetime
from decimal import Decimal

import db_common
import db_client
import serv_to_buy

@cache.action(time_expire=time_exp, cache_model=cache.disk) #, vars=False, public=True, lang=True)
def index():
    return dict(
                get_currs = dict(url = "get_currs",
                                pars = dict(),
                                result = dict(
                                      icon_url = "URL for icons",
                                      in_ = dict(
                                            name = "Currency name for view",
                                            name2 = "Currency name for URI",
                                            may_pay = "[amount] - If exists - how many exchange may accept",
                                          ),
                                      out = dict(
                                            name = "Currency name for view",
                                            name2 = "Currency name for URI",
                                            bal = "free balance",
                                          ),
                                   )
                                ),
                get_rate = dict(url = "get_rate/[curr_in_id]/[curr_out_id]/[vol_in]?get_limits=1",
                                pars = dict(get_limits = "limits in result",
                                            curr_in_id = "income currency as digit No. or as Abbreviation. For example: 3 or BTC",
                                            curr_out_id = "outcome currency as digit No. or as Abbreviation",
                                            ),
                                result = dict(bal = "free balance for CURR_OUT inside exchange",
                                      addr_in = "cryptocurrency address for income",
                                      may_pay = "[amount] - If exists - how many exchange may accept CURR_IN?",
                                      volume_in = "amount You want to sell",
                                      volume_out = "amount You want to buy",
                                      base_rate = "middle rate of exchange",
                                      rate = "rate of this exchange",
                                      wrong = "message if rate not found"
                                   )
                                ),
                get_bals = dict(url = "get_bals/[curr_abbrev]",
                                pars = dict(curr_abbrev = "if set then balance for it currency only",
                                            ),
                                result = ""
                                   ),
                get_uri_in = dict(url = "get_uri_in/[deal_id]/[curr_in_id]/[curr_out_id]/[address_out]/[amount_in]",
                                pars = dict(deal_id = "for coins exchange use 2",
                                            curr_in_id = "income currency as digit No. or as Abbreviation. For example: 3 or BTC",
                                            curr_out_id = "outcome currency as digit No. or as Abbreviation. 3 - BTC, 9 - ERA, 10 - COMPU",
                                            address_out = "address for out",
                                            amount_in = "amount You want to sell (income)"
                                            ),
                                result = dict(bal = "free balance for CURR_OUT inside exchange",
                                      addr_in = "cryptocurrency address for income",
                                      uri = "URI for auto open wallet or generate QR-code",
                                      may_pay = "[amount] - If exists - how many exchange may accept CURR_IN?",
                                      volume_in = "amount You want to sell",
                                      volume_out = "amount You want to buy",
                                      wrong = "message if rate not found"
                                     )
                                   ),
                get_uri = dict(url = "get_uri/[deal_id]/[curr_in_id]/[curr_out_id]/[address_out]/[amount_out]",
                                pars = dict(deal_id = "for coins exchange use 2",
                                            curr_in_id = "income currency as digit No. or as Abbreviation. For example: 3 or BTC",
                                            curr_out_id = "outcome currency as digit No. or as Abbreviation. 3 - BTC, 9 - ERA, 10 - COMPU",
                                            address_out = "address for out",
                                            amount_out = "amount You want to buy (outcome)"
                                            ),
                                result = dict(bal = "free balance for CURR_OUT inside exchange",
                                      addr_in = "cryptocurrency address for income",
                                      uri = "URI for auto open wallet or generate QR-code",
                                      may_pay = "[amount] - If exists - how many exchange may accept CURR_IN?",
                                      volume_in = "amount You want to sell",
                                      volume_out = "amount You want to buy",
                                      rate = "rate of exchange",
                                      wrong = "message if rate not found"
                                     )
                                   ),
                history = dict(url = "history/[curr_out]/[account (or address)]",
                                exapmle = "history/COMPU/7PFRVswUdzWB7JYp9VJzfk9Qcnjh7eCVNY",
                                pars = dict(
                                            curr_out = "currency for out, for example: COMPU",
                                            account = 'account of DEAL (or address for deal "TO COIN"',
                                            ),
                                result = dict(
                                        unconfirmed = "payments wait confirmations",
                                        in_process = "payments in process", 
                                        done = "payments was done",
                                        deal = dict(id = "id", name = "name", MAX = "MAX"),
                                        deal_acc = dict(
                                            payed_month = "payed_month", 
                                            address = "address",
                                            payed = "total", 
                                            price = "price",
                                            message = "message for address"
                                            ),
                                     )
                                   )
                )

def mess(error):
    return '{"error": "%s"}' % error


# get_currs
def get_currs():
    import db_client

    out_res = {'icon_url': URL('static', 'images/currs'), 'in': {}, 'out': {}}
    
    for r in db(
             (db.currs.used == True)
             & (db.currs.id == db.xcurrs.curr_id)
             ).select(orderby=~db.currs.uses):
        free_bal = db_client.curr_free_bal(r.currs)
        lim_bal, may_pay = db_client.is_limited_ball(r.currs)

        out_res['in'][r.currs.abbrev] = { 'id': int(r.currs.id),
                                           'name': r.currs.name, 'name2': r.currs.name2,
                                          'icon':  r.currs.abbrev + '.png'}
        if lim_bal > 0:
            out_res['in'][r.currs.abbrev]['may_pay'] = float(may_pay)

        out_res['out'][r.currs.abbrev] = { 'id': int(r.currs.id), 'bal': float(free_bal),
                                           'name': r.currs.name, 'name2': r.currs.name2,
                                          'icon':  r.currs.abbrev + '.png'}

    
    return request.extension == 'html' and dict(
        h=DIV(BEAUTIFY(out_res), _class='container')) or out_res


# get_bals/[curr]
def get_bals():
    import db_client

    abbrev = request.args(0)

    out_res = {}
    for r in db(
             (db.currs.used == True)
             & (db.currs.id == db.xcurrs.curr_id)
             & (not abbrev or db.currs.abbrev == abbrev)
             ).select(orderby=~db.currs.uses):
        free_bal = db_client.curr_free_bal(r.currs)
        
        if abbrev:
            return free_bal

        out_res[r.currs.abbrev] = float(free_bal)
    
    return request.extension == 'html' and dict(
        h=DIV(BEAUTIFY(out_res), _class='container')) or out_res

# get_rate/curr_in_id/curr_out_id/vol_in?get_limits=1
def get_rate():
    import db_client, rates_lib, common

    args = request.args
    vars = request.vars
    ##print args, '\n', request.vars
    if len(args) < 2:
        if len(vars) < 2:
            return mess('err...')
    
    curr_id = args(0) or vars.get('curr_in')
    if not curr_id or len(curr_id) > 20:
        return mess('error curr_out')
    curr_out_id = args(1) or vars.get('curr_out')
    if not curr_out_id or len(curr_out_id) > 20:
        return mess('error curr_out_id')

    vol_in = args(2) or vars.get('vol_in')
    if not vol_in or len(vol_in) > 20:
        return mess('error amount')
    
    out_res = rates_lib.get_rate_for_api(db, curr_id, curr_out_id, vol_in,
                                         deal = db.deals[current.TO_COIN_ID], get_limits = vars.get('get_limits'))

    if 'free_bal' in out_res:
        out_res['bal'] = out_res.pop('free_bal')

    if 'rate_out' in out_res:
        out_res['rate'] = out_res.pop('rate_out')

    if 'curr_in_rec' in out_res:
        out_res.pop('curr_in_rec')
        del out_res['curr_out_rec']

    if 'lim_bal' in out_res:
        if out_res['lim_bal'] == 0:
            out_res.pop('may_pay')
        else:
            out_res['may_pay'] = float(out_res['may_pay'])
            
        out_res.pop('lim_bal')
        

    return request.extension == 'html' and dict(
        h=DIV(BEAUTIFY(out_res), _class='container')) or out_res


# get URI for income exchanges
# http://127.0.0.1:8000/apipay/get_uri_in/[deal_id]/[curr_in_id]/[curr_out_id]/[address_out]/[amount_in]
# http://face2face.cash/apipay/get_uri_in/2/3/10/7EP4bX6cauqYEa4F2CT13j8tC7LydPnNXq/33 - html
# http://face2face.cash/apipay/get_uri_in.json/2/3/10/7EP4bX6cauqYEa4F2CT13j8tC7LydPnNXq/33 - JSON
# http://127.0.0.1:8000/ipay3_free/apipay/get_uri_in/2/9/3/39b83inCcbcpTKZWQXEwTaSe5d8kVEh4vC/0.1 - not my!
 

''' out parameters:
    bal - free balance for CURR_OUT inside exchange
    may_pay    [amount] - If exists - how namy echange may accept CURR_IN?
    uri - URI for cryptocurrency wallet
    volume_in - need to pay by client
    volume_out - will be taken by client
'''

# get_uri_in/deal_id/curr_in_id/curr_out_id/addr/vol_in
def get_uri_in():
    import rates_lib, common

    args = request.args
    ##print args, '\n', request.vars
    if len(args) < 2: return mess('err...')
    deal_id = args(0)

    curr_id = args(1) or vars.get('curr_in')
    if not curr_id or len(curr_id) > 20:
        return mess('error curr_in')
    try:
        curr_id = int(curr_id)
        curr_in = db.currs[ curr_id ]
        if not curr_in:
            return mess('curr in id...')
    except:
        curr_in = db(db.currs.abbrev == curr_id).select().first()
        curr_id = curr_in.id
        if not curr_in:
            return mess('curr in id...')
        curr_id = curr_in.id

    curr_out_id = args(2) or vars.get('curr_out')
    if not curr_out_id or len(curr_out_id) > 20:
        return mess('error curr_out')
    try:
        curr_out_id = int(curr_out_id)
        curr_out = db.currs[ curr_out_id ]
        if not curr_out:
            return mess('curr out id...')
    except:
        curr_out = db(db.currs.abbrev == curr_out_id).select().first()
        if not curr_out:
            return mess('curr out id...')
        curr_out_id = curr_out.id

    
    addr_out = args(3)

    #if not deal_id.isdigit() or not curr_id.isdigit():
    #    return mess('dig...')

    vol = args(4)
    if not vol or len(vol) > 20:
        return mess('error amount')
    
    try:
        vol = float(vol)
    except:
        return mess('digs...')

    if not addr_out:
        return mess('error address')

    try:
        if len(addr_out) < 25 or len(addr_out) > 40:
            return mess('error address')
    except:
        return mess('error address')

    deal = db.deals[ deal_id ]
    if not deal: return mess('deal...')
    
    xcurr_in = db(db.xcurrs.curr_id == curr_id).select().first()
    if not xcurr_in: return mess('xcurr...')

    xcurr_out = db(db.xcurrs.curr_id == curr_out.id).select().first()
    if not xcurr_out: return mess('xcurr out...')
    curr_out_abbrev = curr_out.abbrev
    curr_out_name = curr_out.name

    token_system_in = None
    token_key_in = xcurr_in.as_token
    if token_key_in:
        token_in = db.tokens[token_key_in]
        token_system_in = db.systems[token_in.system_id]
        import rpc_erachain

    token_system_out = None
    token_key_out = xcurr_out.as_token
    if token_key_out:
        token_out = db.tokens[token_key_out]
        token_system_out = db.systems[token_out.system_id]
        import rpc_erachain
        
    #print request.application[-5:]
    if request.application[:-3] != '_dvlp':
        # conflicts to call if from [ipay3_dvlp]  - wallet not in connection...
        if token_system_out:
            curr_block = rpc_erachain.get_info(token_system_out.connect_url)
            if type(curr_block) != type(1):
                return mess('Connection to [%s] is lost, try later ' % curr_out_name)
            if rpc_erachain.is_not_valid_addr(token_system_out.connect_url, addr_out):
                return mess('address not valid for ' + curr_out_name + ' - ' + addr_out)
            
            pass
        else:
            import crypto_client
            try:
                cc = crypto_client.conn(curr_out, xcurr_out)
            except:
                cc = None
            if not cc:
                return mess('Connection to [%s] is lost, try later ' % curr_out_name)
            if crypto_client.is_not_valid_addr(cc, addr_out):
                return mess('address not valid for - ' + curr_out_name + ' - ' + addr_out)

    curr_in_name = curr_in.name
    
    if token_system_in:
        deal_acc_id, deal_acc_addr = rpc_erachain.get_deal_acc_addr(db, deal_id, curr_out, addr_out, token_system_in.account, xcurr_in)
        addr_in = token_system_in.account
        pass
    else:
        x_acc_label = db_client.make_x_acc(deal, addr_out, curr_out_abbrev)
        deal_acc_id = db_client.get_deal_acc_id(db, deal, addr_out, curr_out)
        deal_acc_addr = db_client.get_deal_acc_addr_for_xcurr(db, deal_acc_id, curr_in, xcurr_in, x_acc_label)
        if not deal_acc_addr:
            return mess('Connection to [%s] is lost, try later ' % curr_in_name)

        addr_in = deal_acc_addr.addr
        

    deal_acc = db.deal_accs[deal_acc_id]
    vol_in = vol

    # fast search of RATE first
    # 
    pr_b, pr_s, pr_avg = rates_lib.get_average_rate_bsa(db, curr_in.id, curr_out.id, None)
    if pr_avg:
        amo_out, _, best_rate = rates_lib.get_rate(db, curr_in, curr_out, vol_in)
    else:
        best_rate = None

    if best_rate:
        is_order = False
        dealer_deal = None
        vol_out, mess_out = db_client.calc_fees(db, deal, dealer_deal, curr_in, curr_out, vol_in,
                                           best_rate, is_order, note=0)

        ## vol_out - is Decimal
        vol_out = common.rnd_8(vol_out)
        rate_out = vol_out / vol_in

        # new make order
        order_id = db.orders.insert(
            ref_ = deal_acc_addr.id,
            volume_in = vol_in,
            volume_out = vol_out,
            )
        db.orders_stack.insert( ref_ = order_id )
    else:
        vol_out = rate_out = tax_rep = None

    _, uri = common.uri_make( curr_in.name2, addr_in, {'amount':vol_in, 'label': db_client.make_x_acc_label(deal, addr_out, curr_out_abbrev)})

    curr_in_abbrev = curr_in.abbrev
    
    #
    lim_bal, may_pay = db_client.is_limited_ball(curr_in)

    free_bal = db_client.curr_free_bal(curr_out)
    if token_system_in:
        addr_out_full = (token_system_out and ('%d' % token_out.token_key) or curr_out.abbrev) + ':' + addr_out
    else:
        addr_out_full = addr_out

    out_res = dict(curr_out_abbrev = curr_out_abbrev, addr_out = addr_out, volume_out = vol_out,
                   bal = float(free_bal / 2), rate = rate_out,
                   curr_in_name = curr_in_name, volume_in = vol_in, curr_in_abbrev= curr_in_abbrev, addr_in = addr_in,
                   uri= uri
                  )
    if lim_bal > 0:
        out_res['may_pay'] = float(may_pay / 2)
    
    if not vol_out:
        out_res['wrong'] = 'rate not found'

    if token_system_in:
        out_res['addr_out_full'] = addr_out_full
    
    return request.extension == 'html' and dict(
        h=DIV(BEAUTIFY(out_res), _class='container')) or out_res


# get URI for income exchanges
# https://127.0.0.1/apipay/get_uri/[deal_id]/[curr_in_id]/[curr_out_id]/[address_out]/[amount_out]
# http://face2face.cash/apipay/get_uri/2/3/10/7EP4bX6cauqYEa4F2CT13j8tC7LydPnNXq/33 - html
# http://face2face.cash/apipay/get_uri.json/2/3/10/7EP4bX6cauqYEa4F2CT13j8tC7LydPnNXq/33 - JSON
# http://127.0.0.1:8000/ipay3_free/apipay/get_uri/2/9/3/39b83inCcbcpTKZWQXEwTaSe5d8kVEh4vC/0.1 - not my!

''' out parameters:
    bal - free balance for CURR_OUT inside exchange
    may_pay    [amount] - If exists - how namy echange may accept CURR_IN?
    uri - URI for cryptocurrency wallet
    volume_in - need to pay by client
    volume_out - will be taken by client
'''

# get_uri/deal_id/curr_in_id/curr_out_id/addr/vol_out
def get_uri():
    import rates_lib, common

    args = request.args
    ##print args, '\n', request.vars
    if len(args) < 2: return mess('err...')
    deal_id = args(0)

    curr_id = args(1) or vars.get('curr_in')
    if not curr_id or len(curr_id) > 20:
        return mess('error curr_in')
    try:
        curr_id = int(curr_id)
        curr_in = db.currs[ curr_id ]
        if not curr_in:
            return mess('curr in id...')
    except:
        curr_in = db(db.currs.abbrev == curr_id).select().first()
        curr_id = curr_in.id
        if not curr_in:
            return mess('curr in id...')
        curr_id = curr_in.id

    curr_out_id = args(2) or vars.get('curr_out')
    if not curr_out_id or len(curr_out_id) > 20:
        return mess('error curr_out')
    try:
        curr_out_id = int(curr_out_id)
        curr_out = db.currs[ curr_out_id ]
        if not curr_out:
            return mess('curr out id...')
    except:
        curr_out = db(db.currs.abbrev == curr_out_id).select().first()
        if not curr_out:
            return mess('curr out id...')
        curr_out_id = curr_out.id

    
    addr_out = args(3)

    #if not deal_id.isdigit() or not curr_id.isdigit():
    #    return mess('dig...')

    vol = args(4)
    if not vol or len(vol) > 20:
        return mess('error amount')
    
    try:
        vol = float(vol)
    except:
        return mess('digs...')

    if not addr_out:
        return mess('error address')

    try:
        if len(addr_out) < 25 or len(addr_out) > 40:
            return mess('error address')
    except:
        return mess('error address')

    deal = db.deals[ deal_id ]
    if not deal: return mess('deal...')
    
    xcurr_in = db(db.xcurrs.curr_id == curr_id).select().first()
    if not xcurr_in: return mess('xcurr...')

    xcurr_out = db(db.xcurrs.curr_id == curr_out.id).select().first()
    if not xcurr_out: return mess('xcurr out...')
    curr_out_abbrev = curr_out.abbrev
    curr_out_name = curr_out.name

    token_system_in = None
    token_key_in = xcurr_in.as_token
    if token_key_in:
        token_in = db.tokens[token_key_in]
        token_system_in = db.systems[token_in.system_id]
        import rpc_erachain

    token_system_out = None
    token_key_out = xcurr_out.as_token
    if token_key_out:
        token_out = db.tokens[token_key_out]
        token_system_out = db.systems[token_out.system_id]
        import rpc_erachain
        
    #print request.application[-5:]
    if request.application[:-3] != '_dvlp':
        # conflicts to call if from [ipay3_dvlp]  - wallet not in connection...
        if token_system_out:
            curr_block = rpc_erachain.get_info(token_system_out.connect_url)
            if type(curr_block) != type(1):
                return mess('Connection to [%s] is lost, try later ' % curr_out_name)
            if rpc_erachain.is_not_valid_addr(token_system_out.connect_url, addr_out):
                return mess('address not valid for ' + curr_out_name + ' - ' + addr_out)
            
            pass
        else:
            import crypto_client
            try:
                cc = crypto_client.conn(curr_out, xcurr_out)
            except:
                cc = None
            if not cc:
                return mess('Connection to [%s] is lost, try later ' % curr_out_name)
            if crypto_client.is_not_valid_addr(cc, addr_out):
                return mess('address not valid for - ' + curr_out_name + ' - ' + addr_out)

    curr_in_name = curr_in.name
    
    if token_system_in:
        deal_acc_id, deal_acc_addr = rpc_erachain.get_deal_acc_addr(db, deal_id, curr_out, addr_out, token_system_in.account, xcurr_in)
        addr_in =  token_system_in.account
        pass
    else:
        x_acc_label = db_client.make_x_acc(deal, addr_out, curr_out_abbrev)
        deal_acc_id = db_client.get_deal_acc_id(db, deal, addr_out, curr_out)
        deal_acc_addr = db_client.get_deal_acc_addr_for_xcurr(db, deal_acc_id, curr_in, xcurr_in, x_acc_label)
        if not deal_acc_addr:
            return mess('Connection to [%s] is lost, try later ' % curr_in_name)

        addr_in = deal_acc_addr.addr
        

    deal_acc = db.deal_accs[deal_acc_id]
    volume_out = vol

    # fast search of RATE first
    # 
    pr_b, pr_s, pr_avg = rates_lib.get_average_rate_bsa(db, curr_in.id, curr_out.id, None)
    if pr_avg:
        vol_in = volume_out / pr_b
        amo_out, _, best_rate = rates_lib.get_rate(db, curr_in, curr_out, vol_in)
    else:
        best_rate = None

    if best_rate:
        is_order = True
        dealer_deal = None
        # first add TAX
        txfee = float(xcurr_out.txfee or 0.0001)
        volume_out += txfee
        volume_in, mess_in = db_client.calc_fees_back(db, deal, dealer_deal, curr_in, curr_out, volume_out,
                                           best_rate, is_order, note=0)

        volume_in = common.rnd_8(volume_in)
        rate_out = volume_out / volume_in

        # new make order
        order_id = db.orders.insert(
            ref_ = deal_acc_addr.id,
            volume_in = volume_in,
            volume_out = volume_out,
            )
        db.orders_stack.insert( ref_ = order_id )
    else:
        volume_in = rate_out = tax_rep = None

    _, uri = common.uri_make( curr_in.name2, addr_in, {'amount':volume_in, 'label': db_client.make_x_acc_label(deal, addr_out, curr_out_abbrev)})

    curr_in_abbrev = curr_in.abbrev
    
    #
    lim_bal, may_pay = db_client.is_limited_ball(curr_in)

    free_bal = db_client.curr_free_bal(curr_out)
    if token_system_in:
        addr_out_full = (token_system_out and ('%d' % token_out.token_key) or curr_out.abbrev) + ':' + addr_out
    else:
        addr_out_full = addr_out

    out_res = dict(curr_out_abbrev = curr_out_abbrev, addr_out = addr_out, volume_out = volume_out,
                   bal = float(free_bal / 2), rate = rate_out,
                   curr_in_name = curr_in_name, volume_in = volume_in, curr_in_abbrev= curr_in_abbrev, addr_in = addr_in,
                   uri = uri
                  )
    if lim_bal > 0:
        out_res['may_pay'] = float(may_pay / 2)

    if not volume_in:
        out_res['wrong'] = 'rate not found'

    if token_system_in:
        out_res['addr_out_full'] = addr_out_full
    
    return request.extension == 'html' and dict(
        h=DIV(BEAUTIFY(out_res), _class='container')) or out_res


def histoty_result(db, r):
    curr_out = db.currs[r.deal_accs.curr_id]
    pay_in = r.pay_ins

    result = dict(
        curr_in = dict(abbrev = r.currs.abbrev, id = r.currs.id),
        curr_out = dict(abbrev = curr_out.abbrev, id = curr_out.id),
        acc = r.deal_accs.acc,
        amount_in = float(pay_in.amount),
        confitmations = pay_in.confs,
        txid = pay_in.txid,
        created = pay_in.created_on
        )

    if pay_in.status: result['stasus'] = pay_in.status
    if pay_in.status_mess: result['status_mess'] = pay_in.status_mess
    if pay_in.order_id:
        result['order_id'] = pay_in.order_id
        order = db.orders[pay_in.order_id]
        result['order_rate'] = round(float(order.volume_in / order.volume_out), 10)

    return result

def history():

    if len(request.args) == 1:
        acc = request.args(0)
        if not acc or len(acc) > 200:
            return mess('wrong account. Use ABBREV/ACCOUNT')
            
        curr, xcurr, _, = db_common.get_currs_by_addr(db, acc)
        if not xcurr:
            return mess('Use ABBREV/ACCOUNT')
        
        curr_out_abbrev = curr.abbrev
    elif len(request.args) == 2:
        curr_out_abbrev = request.args(0)
        if not curr_out_abbrev or len(curr_out_abbrev) > 10: return mess('wrong currency ABBREV. Use ABBREV/ACCOUNT')
        acc = request.args(1)
        if not acc or len(acc) > 200: return mess('wrong account. Use ABBREV/ACCOUNT')
    else:
        return mess('Use ABBREV/ACCOUNT')
    

    deal_acc = db((db.deal_accs.acc == acc)
          & (db.deal_accs.curr_id == db.currs.id)
          & (db.currs.abbrev == curr_out_abbrev)
          ).select().first()
    if not deal_acc:
        return mess('Deal ACCOUNT not found. Use ABBREV/ACCOUNT')

    deal_acc = deal_acc.deal_accs
    deal = db.deals[ deal_acc.deal_id ]

    from pytz import utc, timezone
    from time import mktime

    import where3

    ############ UNCONFIRMED ############
    pays_unconf = []

    ## found income ADDRS
    ## not TOKENS system
    for r in db((db.currs.used)
            & (db.currs.id == db.xcurrs.curr_id)
            & (db.deal_acc_addrs.deal_acc_id == deal_acc.id)
            & (db.xcurrs.id == db.deal_acc_addrs.xcurr_id)
          ).select():
        
        if r.xcurrs.as_token > 0:
            continue
        
        xcurr_in = r.xcurrs
        curr_in = r.currs
        addr = r.deal_acc_addrs.addr
        
        pays_unconf_curr = []
        where3.found_unconfirmed_coins(db, curr_in, xcurr_in, pays_unconf_curr)
        for item in pays_unconf_curr:
            if item[8] == addr:
                pays_unconf.append(pays_unconf_curr)

    ## SSE all TOKEN SYSTEMS
    for token_system in db(db.systems).select():
        
        #addr = None # r.account
        #token = db(db.tokens.system_id == r.id).select().first()
        #xcurr_in = db(db.xcurrs.as_token == token.id).select().first()
        #curr_in = db.currs[xcurr_in.curr_id]
        
        # add ALL incomes
        where3.found_unconfirmed_tokens(db, token_system, pays_unconf)
        

    ####################### IN PROCCESS ##############
    in_proc = []
    for r in db( 
               (db.pay_ins_stack.ref_ == db.pay_ins.id)
               & (db.pay_ins.ref_ == db.deal_acc_addrs.id)
               & (db.deal_acc_addrs.deal_acc_id == deal_acc.id)
               & (db.deal_accs.id == deal_acc.id)
               & (db.xcurrs.id == db.deal_acc_addrs.xcurr_id)
               & (db.currs.id == db.xcurrs.curr_id)
               ).select(orderby=~db.pay_ins.created_on):
        
        result = histoty_result(db, r)
        
        in_proc.append(result)

    expired = datetime.datetime.now() - datetime.timedelta(40, 0)
    done = []
    for r in db(
           (db.pay_ins.ref_ == db.deal_acc_addrs.id)
           & (db.deal_acc_addrs.deal_acc_id == deal_acc.id)
           & (db.deal_accs.id == deal_acc.id)
           & (db.xcurrs.id == db.deal_acc_addrs.xcurr_id)
           & (db.currs.id == db.xcurrs.curr_id)
           & (db.pay_ins.created_on > expired)
           ).select(orderby=~db.pay_ins.created_on):

        if db(db.pay_ins.id == db.pay_ins_stack.ref_).select().first():
            continue

        result = histoty_result(db, r)

        pay_in = r.pay_ins
        if pay_in.payout_id:
            pay_out = db.pay_outs[pay_in.payout_id]

            if pay_out:
                pay_put_result = dict(amo_gift = float(pay_out.amo_gift),
                     amo_in = float(pay_out.amo_in),
                     amo_partner = float(pay_out.amo_partner),
                     amo_taken = float(pay_out.amo_taken),
                     amo_to_pay = float(pay_out.amo_to_pay),
                     amount = float(pay_out.amount),
                     created_on = pay_out.created_on,
                     created_ts = mktime(utc.localize(pay_out.created_on).utctimetuple()),
                     id = pay_out.id,
                     info = pay_out.info,
                     status = pay_out.status,
                     tax_mess = pay_out.tax_mess,
                     txid = pay_out.txid,
                     vars = pay_out.vars
                     )

                if pay_out.dealer_acc_id:
                    #deal_acc = db.deal_accs[pay_out.ref_]
                    #deal = db.deals[deal_acc.deal_id]
                    pay_put_result['dealer_acc'] = dealer_acc = db.dealers_accs[pay_out.dealer_acc_id]
                    #curr_out = db.currs[dealer_acc.curr_id]
                    pay_put_result['dealer'] = db.dealers[dealer_acc.dealer_id]
                    #rec_vals['dealer_deal'] = db((db.dealer_deals.deal_id == deal.id)
                    #      & (db.dealer_deals.dealer_id == dealer.id)).select().first()
            
                result['pay_out'] = pay_put_result
                
        elif pay_in.clients_tran_id:
            # это выплатата клиенту
            cl_tr = db.clients_trans[pay_in.clients_tran_id]
            client = db.clients[cl_tr.client_id]
            result['client'] = dict(id = client.id, transaction = pay_in.clients_tran_id)
        
        done.append(result)
            
    deal_res = dict(id = deal.id, name = deal.name,
         MAX = float(deal.MAX_pay))
    
    import gifts_lib
    if 'to COIN' in deal.name:
        rnd = 8
    else:
        rnd = 2
    deal_acc_mess = XML(gifts_lib.adds_mess(deal_acc, PARTNER_MIN, T, rnd))

    deal_acc_res = dict(id = deal_acc.id, name = deal_acc.acc,
            to_pay = float(deal_acc.to_pay or Decimal(0)),
            payed_month = float(not deal.is_shop and deal_acc.payed_month or Decimal(0)),
            payed = float(deal_acc.payed or Decimal(0)), price = float(deal_acc.price or Decimal(0)),
            gift_amount = float(deal_acc.gift_amount),
            gift_payed = float(deal_acc.gift_payed),
            gift_pick = float(deal_acc.gift_pick),
            curr_out_id = deal_acc.curr_id,
            message = deal_acc_mess
            )
    
    #print 'pays:', pays
    out_res = dict(deal = deal_res, deal_acc = deal_acc_res, 
        unconfirmed = pays_unconf, in_process = in_proc, done = done
        )

    return request.extension == 'html' and dict(
        h=DIV(BEAUTIFY(out_res), _class='container')) or out_res
