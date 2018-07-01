# coding: utf8

session.forget(response)

time_exp = IS_LOCAL and 3 or 666

import datetime
from decimal import Decimal

import db_common
import db_client
import serv_to_buy

@cache.action(time_expire=time_exp, cache_model=cache.disk) #, vars=False, public=True, lang=True)
def index():
    return dict(get_rate = dict(url = "get_rate/[curr_in_id]/[curr_out_id]/[vol_in]?get_limits=1",
                                pars = "get_limits - limits in result",
                                result = "j"),
                get_uri_out = dict(url = "get_uri_out/[deal_id]/[curr_in_id]/[curr_out_id]/[address_out]/[amount_out]",
                                pars = dict(deal_id = " - for coins exchange use 2",
                                            curr_in_id = " 3 - BTC, 10 - ERA",
                                            curr_out_id = " 3 - BTC, 10 - ERA",
                                            ),
                                result = dict(free_bal = "free balance for CURR_OUT inside exchange",
                                      addr_in = "cryptocurrency address for income",
                                      url_uri = "URI for auto open wallet or generate QR-code",
                                      lim_bal = "(False/True) - is limited on accept CURR_IN?",
                                      may_pay = "(0 or [amount]) - how namy echange may accept CURR_IN?",
                                      url_uri = " - URI for cryptocurrency wallet",
                                      volume_in = "- need to pay by client",
                                      volume_out = " - will be taken by client")
                                   ),
                get_uri = dict(url = "get_uri/[deal_id]/[curr_in_id]/[curr_out_id]/[address_out]/[amount_out]",
                                pars = dict(deal_id = " - for coins exchange use 2",
                                            curr_in_id = " 3 - BTC, 10 - ERA",
                                            curr_out_id = " 3 - BTC, 10 - ERA",
                                            ),
                                result = dict(free_bal = "free balance for CURR_OUT inside exchange",
                                      addr_in = "cryptocurrency address for income",
                                      url_uri = "URI for auto open wallet or generate QR-code",
                                      lim_bal = "(False/True) - is limited on accept CURR_IN?",
                                      may_pay = "(0 or [amount]) - how namy echange may accept CURR_IN?",
                                      url_uri = " - URI for cryptocurrency wallet",
                                      volume_in = "- need to pay by client",
                                      volume_out = " - will be taken by client")
                                   )
                )

def mess(error):
    return '{"error": "%s"}' % error


# get_rate/curr_in_id/curr_out_id/vol_in?get_limits=1
def get_rate():
    import rates_lib, common

    args = request.args
    ##print args, '\n', request.vars
    if len(args) < 2: return mess('err...')
    curr_id = args(0)
    curr_out_id = args(1)

    vol = args(2)
    if not vol or len(vol) > 20:
        return mess('error amount')
    
    try:
        vol = float(vol)
        curr_id = int(curr_id)
    except:
        return mess('digs...')
    
    curr_in = db.currs[ curr_id ]
    if not curr_in: return mess('curr...')
    xcurr_in = db(db.xcurrs.curr_id == curr_id).select().first()
    if not xcurr_in: return mess('xcurr...')

    if not curr_out_id: return mess('curr out id...')
    curr_out = db.currs[ curr_out_id ]
    if not curr_out: return mess('curr out...')
    xcurr_out = db(db.xcurrs.curr_id == curr_out.id).select().first()
    if not xcurr_out: return mess('xcurr out...')
    curr_out_abbrev = curr_out.abbrev

    vol_in = vol
    
    out_res = dict(
           volume_in = vol_in,
           curr_in = curr_in.abbrev,
           curr_out = curr_out.abbrev,
          )


    pr_b, pr_s, pr_avg = rates_lib.get_average_rate_bsa(db, curr_in.id, curr_out.id, None)
    if pr_avg:
        _, _, best_rate = rates_lib.get_rate(db, curr_in, curr_out, vol_in)
    else:
        best_rate = None

    if best_rate:

        is_order = False
        dealer_deal = None
        deal = db.deals[TO_COIN_ID]
        vol_out, mess_out = db_client.calc_fees(db, deal, dealer_deal, curr_in, curr_out, vol_in,
                                           best_rate, is_order=0, note=0, only_tax=0)
        ## vol_out - is Decimal
        vol_out = common.rnd_8(vol_out)
        rate_out = vol_out / vol_in
        
        out_res['vol_out'] = vol_out
        out_res['rate_out'] = rate_out
        
        if request.vars.get('get_limits'):
            lim_bal, may_pay = db_client.is_limited_ball(curr_in)
            free_bal = db_client.curr_free_bal(curr_out)

            out_res['lim_bal'] = lim_bal
            out_res['may_pay'] = may_pay
            out_res['free_bal'] = float(free_bal),


    return request.extension == 'html' and dict(
        h=DIV(BEAUTIFY(out_res), _class='container')) or out_res



# get URI for income exchanges
# https://127.0.0.1/apipay/get_uri/[deal_id]/[curr_in_id]/[curr_out_id]/[address_out]/[amount_out]
# http://face2face.cash/apipay/get_uri/2/3/10/7EP4bX6cauqYEa4F2CT13j8tC7LydPnNXq/33 - html
# http://face2face.cash/apipay/get_uri.json/2/3/10/7EP4bX6cauqYEa4F2CT13j8tC7LydPnNXq/33 - JSON

''' out parameters:
    free_bal - free balance for CURR_OUT inside exchange
    lim_bal (False/True) - is limited on accept CURR_IN?
    may_pay	(0 or [amount]) - how namy echange may accept CURR_IN?
    url_uri - URI for cryptocurrency wallet
    volume_in - need to pay by client
    volume_out - will be taken by client
'''

# get_in/deal_id/curr_in_id/curr_out_id/addr/vol_in
def get_uri_out():
    import rates_lib, common

    args = request.args
    ##print args, '\n', request.vars
    if len(args) < 2: return mess('err...')
    deal_id = args(0)
    curr_id = args(1)
    curr_out_id = args(2)
    addr_out = args(3)
    if not deal_id.isdigit() or not curr_id.isdigit():
        return mess('dig...')

    vol = args(4)
    if not vol or len(vol) > 20:
        return mess('error amount')
    
    try:
        vol = float(vol)
        curr_id = int(curr_id)
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
    
    curr_in = db.currs[ curr_id ]
    if not curr_in: return mess('curr...')
    xcurr_in = db(db.xcurrs.curr_id == curr_id).select().first()
    if not xcurr_in: return mess('xcurr...')

    if not curr_out_id: return mess('curr out id...')
    curr_out = db.currs[ curr_out_id ]
    if not curr_out: return mess('curr out...')
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
                return mess('Connection to [%s] id lost, try lates ' % curr_out_name)
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
                return mess('Connection to [%s] id lost, try lates ' % curr_out_name)
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
            return mess('Connection to [%s] id lost, try lates ' % curr_in_name)

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
        vol_in = rate_out = tax_rep = None

    _, url_uri = common.uri_make( curr_in.name2, addr_in, {'amount':vol_in, 'label': db_client.make_x_acc_label(deal, addr_out, curr_out_abbrev)})

    curr_in_abbrev = curr_in.abbrev
    
    #
    lim_bal, may_pay = db_client.is_limited_ball(curr_in)

    free_bal = db_client.curr_free_bal(curr_out)
    if token_system_in:
        addr_out_full = (token_system_out and ('%d' % token_out.token_key) or curr_out.abbrev) + ':' + addr_out
    else:
        addr_out_full = addr_out

    out_res = dict(curr_out_abbrev = curr_out_abbrev, addr_out = addr_out, volume_out = vol_out,
                   free_bal = float(free_bal),
                   curr_in_name = curr_in_name, volume_in = vol_in, curr_in_abbrev= curr_in_abbrev, addr_in = addr_in,
                   lim_bal = lim_bal, may_pay = may_pay,
                   url_uri= url_uri
                  )
    if token_system_in:
        out_res['addr_out_full'] = addr_out_full
    
    return request.extension == 'html' and dict(
        h=DIV(BEAUTIFY(out_res), _class='container')) or out_res


# get URI for income exchanges
# https://127.0.0.1/apipay/get_uri/[deal_id]/[curr_in_id]/[curr_out_id]/[address_out]/[amount_out]
# http://face2face.cash/apipay/get_uri/2/3/10/7EP4bX6cauqYEa4F2CT13j8tC7LydPnNXq/33 - html
# http://face2face.cash/apipay/get_uri.json/2/3/10/7EP4bX6cauqYEa4F2CT13j8tC7LydPnNXq/33 - JSON

''' out parameters:
    free_bal - free balance for CURR_OUT inside exchange
    lim_bal (False/True) - is limited on accept CURR_IN?
    may_pay	(0 or [amount]) - how namy echange may accept CURR_IN?
    url_uri - URI for cryptocurrency wallet
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
    curr_id = args(1)
    curr_out_id = args(2)
    addr_out = args(3)
    if not deal_id.isdigit() or not curr_id.isdigit():
        return mess('dig...')

    vol = args(4)
    if not vol or len(vol) > 20:
        return mess('error amount')
    
    try:
        vol = float(vol)
        curr_id = int(curr_id)
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
    
    curr_in = db.currs[ curr_id ]
    if not curr_in: return mess('curr...')
    xcurr_in = db(db.xcurrs.curr_id == curr_id).select().first()
    if not xcurr_in: return mess('xcurr...')

    if not curr_out_id: return mess('curr out id...')
    curr_out = db.currs[ curr_out_id ]
    if not curr_out: return mess('curr out...')
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
                return mess('Connection to [%s] id lost, try lates ' % curr_out_name)
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
                return mess('Connection to [%s] id lost, try lates ' % curr_out_name)
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
            return mess('Connection to [%s] id lost, try lates ' % curr_in_name)

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

    _, url_uri = common.uri_make( curr_in.name2, addr_in, {'amount':volume_in, 'label': db_client.make_x_acc_label(deal, addr_out, curr_out_abbrev)})

    curr_in_abbrev = curr_in.abbrev
    
    #
    lim_bal, may_pay = db_client.is_limited_ball(curr_in)

    free_bal = db_client.curr_free_bal(curr_out)
    if token_system_in:
        addr_out_full = (token_system_out and ('%d' % token_out.token_key) or curr_out.abbrev) + ':' + addr_out
    else:
        addr_out_full = addr_out

    out_res = dict(curr_out_abbrev = curr_out_abbrev, addr_out = addr_out, volume_out = volume_out,
                   free_bal = float(free_bal),
                   curr_in_name = curr_in_name, volume_in = volume_in, curr_in_abbrev= curr_in_abbrev, addr_in = addr_in,
                   lim_bal = lim_bal, may_pay = may_pay,
                   url_uri= url_uri
                  )
    if token_system_in:
        out_res['addr_out_full'] = addr_out_full
    
    return request.extension == 'html' and dict(
        h=DIV(BEAUTIFY(out_res), _class='container')) or out_res
