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
    return dict()

def mess(error):
    return '{"error": "%s"}' % error

# get URI for income exchanges
# https://127.0.0.1/apipay/get_uri/[deal_id]/[curr_in_id]/[curr_out_id]/[address_out]/[amount_out]
def get_uri():
    import rates_lib, common
    # /deal_id/curr_in_id/curr_out_id/addr/vol

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
        # чето конфликт если из ipay3_dvlp вызывать то кошелек на ipay3 не коннектится
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

    try:
        session.toCoin = curr_out_abbrev
        session.toCoinA = addr_out
    except:
        print 'to_coin session error .toCoinA:', type(addr_out), addr_out

    try:
        session.vol = vol
    except:
        print 'to_coin session error .vol:', type(vol), vol

    curr_in_name = curr_in.name
    
    if token_system_in:
        deal_acc_id, deal_acc_addr = rpc_erachain.get_deal_acc_addr(db, deal_id, curr_out, addr_out, token_system_in.account, xcurr_in)
        addr_in =  token_system_in.account
        pass
    else:
        x_acc_label = db_client.make_x_acc(deal, addr_out, curr_out_abbrev)
        # найдем ранее созданный адресс для этого телефона, этой крипты и этого фиата
        # сначала найтем аккаунт у дела
        deal_acc_id = db_client.get_deal_acc_id(db, deal, addr_out, curr_out)
        # теперь найдем кошелек для данной крипты
        deal_acc_addr = db_client.get_deal_acc_addr_for_xcurr(db, deal_acc_id, curr_in, xcurr_in, x_acc_label)
        if not deal_acc_addr:
            return mess('Connection to [%s] id lost, try lates ' % curr_in_name)

        addr_in = deal_acc_addr.addr
        

    deal_acc = db.deal_accs[deal_acc_id]
    volume_out = vol

    # используем быстрый поиск курса по формуле со степенью на количество входа
    # только надо найти кол-во входа от выхода
    pr_b, pr_s, pr_avg = rates_lib.get_average_rate_bsa(db, curr_in.id, curr_out.id, None)
    if pr_avg:
        vol_in = volume_out / pr_b
        amo_out, _, best_rate = rates_lib.get_rate(db, curr_in, curr_out, vol_in)
    else:
        best_rate = None

    if best_rate:
        is_order = True
        dealer_deal = None
        # сначала открутим обратную таксу
        txfee = float(xcurr_out.txfee or 0.0001)
        volume_out += txfee
        volume_in, mess_in = db_client.calc_fees_back(db, deal, dealer_deal, curr_in, curr_out, volume_out,
                                           best_rate, is_order, note=0)
        ## теперь таксы для человека получим и должна та же цифра выйти
        vol_out_new, tax_rep = db_client.calc_fees(db, deal, dealer_deal, curr_in, curr_out, volume_in,
                                           best_rate, is_order, note=1)
        vol_out_new = common.rnd_8(vol_out_new)
        if common.rnd_8(volume_out) != vol_out_new:
            print 'to_phone error_in_fees: volume_out != vol_out_new', volume_out,  vol_out_new

        volume_in = common.rnd_8(volume_in)
        rate_out = volume_out / volume_in

        # new make order
        order_id = db.orders.insert(
            ref_ = deal_acc_addr.id,
            volume_in = volume_in,
            volume_out = volume_out,
            )
        # теперь стек добавим, который будем удалять потом
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
