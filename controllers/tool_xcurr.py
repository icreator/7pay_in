# -*- coding: utf-8 -*-

if False:
    from gluon import *
    request = current.request
    response = current.response
    session = current.session
    cache = current.cache
    T = current.T
    import db

import common
# запустим сразу защиту от внешних вызов
# тут только то что на локалке TRUST_IP in private/appconfig.ini
common.not_is_local(request)

session.forget(response)

from decimal import Decimal
import db_common, crypto_client

def index(): return dict(message="hello from tool_xcurr.py")

def addrs():
    if not request.args(0):return '/EMC/[address]'
    curr, xcurr, e = db_common.get_currs_by_abbrev(db, request.args(0))
    if not xcurr: return 'xcurr not found'
    cn = crypto_client.connect(curr, xcurr)
    if not cn: return 'xcurr not connected'

    res = {}
    addr = request.args(1)
    if True or addr:
        #res = {'address': address , 'res': cn.getreceivedbyaddress(address) }
        res1 = cn.listaddressgroupings()
        res = {}
        i = 1
        cnt = cnt1 = 0
        for rr in res1:
            #res ['k%s' % i ] = r
            i += 1
            j = 1
            for r in rr:
                cnt += 1
                res ['i%s-j%s' % (i,j) ] = r
                j += 1
                # r = [address, amo, deal_acc]
                #print (r)
                if len(r) >2 :
                    cnt1 += 1
        res['1all'] = cnt
        res['1used'] = cnt1
    else:
        #res = cn.listreceivedbyaddress(0, True) # accs only
        #res = cn.listreceivedbyaccount(0, True)
        #res = cn.listaddress(0)
        #res = cn.listaccounts()
        #res = cn.getaddressesbyaccount('.main.')
        #res = cn.listtransactions('', 10, 0)

        # с минусом - это то что было отправлено комуто на их адрес !
        # а наш адрес в предыдущей транз смтреть
        # походу тут выдает с минусом только выходы на чужие адреса
        res1 = cn.listtransactions('',3333,0)
        res = []
        for k in res1:
            amo = Decimal(k['amount'])
            if amo >= 0:
                k['1getreceivedbyaddress'] = cn.getreceivedbyaddress(k['address'], 0)
                k['1getaccount'] = cn.getaccount(k['address'])
                res.append(k)
    
    
    return BEAUTIFY(res)

# test all ophranet transactions
def ophrans():
    if len(request.args) == 0:
        mess = 'len(request.args)==0 - [BTC]'
        return mess
    import db_common
    #import crypto_client
    curr, xcurr, e = db_common.get_currs_by_abbrev(db,request.args[0])
    conn = crypto_client.connect(curr, xcurr)
    h = CAT()
    cnt = 0
    for r in db((db.deal_acc_addrs.xcurr_id == xcurr.id)
                & (db.pay_ins.ref_ == db.deal_acc_addrs.id)).select():
        cnt += 1
        txid = r.pay_ins.txid
        #print (txid)
        if len(txid) > 60 and len(txid) < 70:
            res = conn.gettransaction(txid) # выдает только для кошелька
            if res:
                conf = res.get('confirmations')
                #print (conf)
                if conf > 2:
                    continue
            h += P(BEAUTIFY(r.pay_ins))
            h += P(BEAUTIFY(res))
            h += HR()
    return dict(h=CAT(H3('counter:', cnt),h))


# args:
# tools_xcurr/process_from/BTC/from_block
def process_from():
    session.forget(response)
    if len(request.args) < 2:
        mess = 'len(request.args)==0 need: tools_xcurr/process_from/BTC/12345'
        return mess

    import serv_block_proc

    return serv_block_proc.run_once(db, request.args[0], int(request.args[1]))
