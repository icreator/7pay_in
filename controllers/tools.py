# coding: utf8

if False:
    from gluon import *
    request = current.request
    response = current.response
    session = current.session
    cache = current.cache
    T = current.T
    import db

##from __future__ import print_function

import socket
session.forget(response)

# vvv=True - включает секретную сессию и выдает страницу ошибки
def not_is_local(vvv=None):
    http_host = request.env.http_host.split(':')[0]
    remote_addr = request.env.remote_addr
    #http_host[7pay.in] remote_addr[91.77.112.36]
    #raise HTTP(200, T('appadmin is disabled because insecure channel http_host[%s] remote_addr[%s]') % (http_host, remote_addr))
    try:
        hosts = (http_host, socket.gethostname(),
                 socket.gethostbyname(http_host),
                 '::1', '127.0.0.1', '::ffff:127.0.0.1')
    except:
        hosts = (http_host, )

    if vvv and (request.env.http_x_forwarded_for or request.is_https):
        session.secure()

    if (remote_addr not in hosts) and (remote_addr not in TRUST_IP):
        #and request.function != 'manage':
        if vvv: raise HTTP(200, T('ERROR: not admin in local'))
        return True

import common
# запустим сразу защиту от внешних вызов
# тут только то что на локалке TRUST_IP in private/appconfig.ini
common.not_is_local(request)

import sys
import time
import crypto_client

from decimal import Decimal
import datetime
import json

def log(mess):
    print mess
    db.logs.insert(mess='CNT: %s' % mess)
def log_commit(mess):
    log(mess)
    db.commit()

# попробовать что-либо вида
def index():
    #err(1)
    return dict(message="hello from tools.py")

def del_logs():
    db.logs.truncate()
def del_site_stats():
    db.site_stats.truncate()

def qr():
    import common
    file_name = 'QR%s.png' % response.session_id # session.id
    path = 'static/temp--'
    common.QRcode('sdfsdf sd fds f', request.folder + path + '/' + file_name)
    img = IMG(_src=URL(path, file_name)) # а то тормозит и качество ухудшает), _width=124)
    return dict(img = img)

def clients_auto_collect():
    import clients_lib
    clients_lib.auto_collect(db)

def  get_balance_xcurr():
    if len(request.args) == 0:
        mess = 'len(request.args)==0'
        print mess
        return mess
    #import db_client
    import db_common
    import crypto_client
    curr, xcurr, e = db_common.get_currs_by_abbrev(db,request.args[0])
    if not xcurr: return 'xcurr not found'
    cn = crypto_client.connect(curr, xcurr)
    if not cn: return 'xcurr not connected'
    return crypto_client.get_balance_xcurr(curr, xcurr, cn) or 'None'

# get_unspents(conn, conf=None, vol=None, addrs=None, accs=None):
def get_unspents():
    if len(request.args) == 0:
        mess = 'len(request.args)==0'
        print mess
        return mess
    #import db_client
    import db_common
    import crypto_client
    curr, x, e = db_common.get_currs_by_abbrev(db,request.args[0])
    if not x: return 'xcurr not found'
    cn = crypto_client.connect(curr, x)
    if not cn: return 'xcurr not connected'
    vol = None
    conf = len(request.args)>1 and int(request.args[1]) or None
    tab, summ = crypto_client.get_unspents(cn, conf, vol)
    print tab, summ
    return '%s <br>%s' % (summ, BEAUTIFY(tab))


def retrans_rawtr():
    import crypto_client
    for xcurr in db(db.xcurrs).select():
        curr = xcurr.curr_id and db.currs[xcurr.curr_id]
        if not curr: continue
        cn = crypto_client.connect(curr, xcurr)
        if not cn: continue
        crypto_client.re_broadcast(db, curr, xcurr, token_system, cn)

# выдать запись из крипты или фиата
def get_acurr_rec_xe(db, id):
    #acurr = db(db.acurrs.id==id).select().first()
    acurr = db.acurrs[id]
    if db.xcurrs[acurr.xcurr_id].abbrev == '---':
        return db.ecurrs[acurr.ecurr_id], False # это фиатная валюта
    return db.xcurrs[acurr.xcurr_id], True # это крипта

# conv DB to ACURRs
def conv_to_curr():
    return 'switch OFF'
    db.currs.truncate()
    for r in db(db.xcurrs).select():
        if r.abbrev == '---': continue
        curr_id = db.currs.insert(
            abbrev = r.abbrev,
            used = True,
            name = r.name,
            name2 = r.name2,
            icon = r.icon,
            xcurr_id = r.id
            )
        r.curr_id = curr_id
        r.update_record()
    for r in db(db.ecurrs).select():
        if r.abbrev == '---': continue
        curr_id = db.currs.insert(
            abbrev = r.abbrev,
            used = True,
            name = r.name,
            name2 = r.name,
            icon = r.icon,
            ecurr_id = r.id
            )
        r.curr_id = curr_id
        r.update_record()
    #return
    for r in db(db.deal_accs).select():
        e_id = r.ecurr_id
        a_id = db(db.currs.ecurr_id == e_id).select().first()
        r.curr_id = a_id.id
        r.update_record()

    import db_common
    for r in db(db.exchg_limits).select():
        xe_rec, _ = get_acurr_rec_xe(db, r.acurr_id)
        r.curr_id = xe_rec.curr_id
        r.update_record()

    for r in db(db.exchg_pairs).select():
        xe_rec, _ = get_acurr_rec_xe(db, r.acurr1_id)
        r.curr1_id = xe_rec.curr_id
        xe_rec, _ = get_acurr_rec_xe(db, r.acurr2_id)
        r.curr2_id = xe_rec.curr_id
        r.update_record()

    db.clients_balances.truncate()
    db.clients_trans.truncate()

    db.currs_stats.truncate()
    for r in db(db.xcurrs_stats).select():
        abbrev = db.xcurrs[r.xcurr_id].abbrev
        curr, x, e = db_common.get_currs_by_abbrev(db, abbrev)
        db.currs_stats.insert(
            curr_id = curr.id,
            deal_id = r.deal_id,
            average = r.average,
            count = r.count,
            )

    return 'Done'

def test_client_notify():
    import clients_lib
    note = db.clients_notifies[5]
    res = clients_lib.notify_one(db, note)


def test_buy_free():
    import serv_to_buy
    import db_common
    xcurr = db_common.get_xcurr_abr(db, "CLR")
    addr = u'CRjSDsfv5tLoe1ZWn59fjU5JrdH64vWo21'
    ecurr = db_common.get_ecurr_abr(db,"RUB")
    amo = 1
    res, bal = serv_to_buy.buy_free(db, ecurr, amo, xcurr, addr)
    print bal, res

# для проверки ошибок в покупке валюты - в ответ на яндекс запрос
def test_buy():
    # на какой наш счет шлем
    args = ['41001873409965']
    vars={"sender": "41001555269641", "label": "", "sha1_hash": "f42848463b1676f641338b48cff39870b95072d5", "currency": "643", "amount": "3.00", "notification_type": "p2p-incoming", "operation_id": "879591875976040017", "datetime": "2013-12-08T05:32:17Z", "codepro": "false"}
    redirect(URL('buy', 'income_YD', args=args, vars=vars))

#
# найти лучшую цену для пары и объема
# get_best_price_for_volume/NVC/RUB/10
def get_best_price_for_volume():
    if len(request.args) == 0:
        mess = 'len(request.args)==0'
        print mess
        return mess
    import db_client
    import db_common
    a_in, x, e = db_common.get_currs_by_abbrev(db,request.args[0])
    a_out, x, e = db_common.get_currs_by_abbrev(db,request.args[1])
    expired = datetime.datetime.now() - datetime.timedelta(5,600)
    s_b = len(request.args)<4 or request.args[3]=='sell'
    #s_b = not 3 in request.args or request.args[3]=='sell'
    print s_b
    print db_client.get_best_price_for_volume(db, a_in.id, a_out.id,
            float(request.args[2]), expired, s_b)

def depth0(e_id,pair):
    return sells, pays

# depth/1/ltc_rub = "UpBit ic"
# depth/2/ltc_rur - "BTC-e ic"
def depth():
    if len(request.args) == 0:
        mess = 'len(request.args)==0'
        print mess
        return mess
    import exch_client
    exchg = db.exchgs[request.args[0]]
    pair = request.args[1]
    exch_client.conn(exchg)
    sells, pays = exch_client.depth(exchg.name, pair)
    exch_client.conn_close(exchg)
    return dict(sells=sells, buy=pays)


# по отловленным входам
# сделать платежи фиата
def to_pay():
    print 'to_pay'
    from serv_to_pay import run_once
    run_once(db)

# отлов входящих платежей с 0-1-2 подтверждениями и закатываем их
# в стек платежей с датой-временем нахождения
def check_new_inputs():
    print 'check_new_inputs'
    from serv_new_inputs import run_once
    run_once(db)

############################################
# ВНИМАНИЕ! эта страница вызывается из клиентов-кощельков
# по адресу на портал
# start /B /LOW /MIN curl http://127.0.0.1:8000/ipay/tools/block_proc/%1/%2 -s >>!notify_log.txt
# args:
# tools/block_proc/LTC
###@cache.action(time_expire=10, cache_model=cache.ram, vars=True)
def block_proc():
    print 'block_proc runned'
    #return 'stoped'
    session.forget(response)
    if len(request.args) == 0:
        mess = 'len(request.args)==0'
        print mess
        return mess
    import serv_block_proc
    abbrev = request.args[0]
    #bhash = len(request.args) > 1 and request.args[1] or None
    print 'block_proc', abbrev
    #return abbrev
    return serv_block_proc.run_once(db, abbrev)

def block_proc_test():
    try:
        block_proc()
    except Exception as e:
        db.rollback()
        log('tools - block_proc: %s' % e)


# отправить на апбит Розе и Ис ларки
# http://127.0.0.1:8000/ipay8/tools/send_to_many/CLR?CGk6Q3cx7qNEzAoWx2YnMNm2xvTQKEaYun=0.1&CdYGrbTZNhgYKh5gghYY6mFWr9pmGbEedY=0.13
# http://127.0.0.1:8000/ipay8/tools/send_to_many/LTC?Lc7nSnWdhp1RU9kCDZS8gRCV1WBAMupkYy=0.01
# Lc7nSnWdhp1RU9kCDZS8gRCV1WBAMupkYy
# vars: {address:amount, ...}
def send_to_many():
    import db_common
    import crypto_client
    curr, xcurr, ecurr = db_common.get_currs_by_abbrev(db, request.args[0])
    if not curr or not xcurr: raise HTTP(503, 'ERROR: xcurr [%s] not found' % request.args[0] )

    if not request.vars or len(request.vars)==0: HTTP(500, 'list ={}' )

    res = crypto_client.send_to_many(curr, xcurr, request.vars)
    print res
    return '%s' % res


def send_to_main(conn, xcurr, acc_from, amo):
    mess = "to send %s from deal_acc:"% amo +acc_from +" to " + xcurr.main_addr
    print 'try', mess
    try:
        conn.sendfrom( acc_from, xcurr.main_addr, amo)
    except Exception as e:
        if e.error['code']==-4:
            # если не хватает на комиссию то уменьшим сумму и повторим
            print 'tax -0.01'
            send_to_main(conn, xcurr, acc_from, amo * 0.97)
            return
        print e.error
        return e.error
    #print mess


# попробуем вручную получить ИД-платежа и его подтвердить
# https://sp-money.yandex.ru/check.xml?request-id=3734353838393737305f323535613763306161373966333461383833613238303266623630316132383264666535353665625f3332333937303939
# http://127.0.0.1:8000/ipay10/tools/YmToConfirm/2/111
def YmToConfirm():
    import ed_YD
    session.forget(response)
    if len(request.args) < 2:
        mess = '/[dealer_acc_id]/[request_id]'
        print mess
        return mess

    dealer_acc = db.dealers_accs[request.args(0)]
    dealer = db.dealers[dealer_acc.dealer_id]
    api_pars, acc_pars, acc_name = ed_YD.get_pars(dealer, dealer_acc)
    res = {
        'request_id': '%s' % request.args(1),
        }
    res = ed_YD.YmToConfirm(res, api_pars, dealer_acc.skey)
    return BEAUTIFY(res)

def pay_test_to_mosenergo():
    import ed_YD
    deal_acc=db.deal_accs[264]
    deal = db.deals[deal_acc.deal_id]
    dealer_acc = db.dealers_accs[deal.dealers_acc_id]
    dealer = db.dealers[dealer_acc.dealer_id]
    # тут ели параметры уже собраны то задаем pay_pars['grab_form']=True
    pay_pars = { # 62959 069 02 199 6
        'grab_form': 1 }
    acc = '''{
        "rapida_param1": 6295906902,
        "PROPERTY1": "62959",
        "PROPERTY2": "069",
        "PROPERTY3": "02",
        "rapida_param2": 9,
        "PROPERTY4": 9,
        "rapida_param3": 13,
        "PROPERTY5": 13,
        "rapida_param4": 199,
        "PROPERTY6": 199,
        "rapida_param5": 6,
        "PROPERTY7": 6,
        "rapida_param6": 0,
        "PROPERTY8": 0,
        "rapida_param7": 0,
        "PROPERTY9": 0,

        "regionId": 77,
        "PROPERTY10": 77,
        "rapida_param8": 77
        }'''

    acc = '''{
        "PROPERTY1": 6295906902,
        "rapida_param1": "62959",
        "rapida_param2": "069",
        "rapida_param3": "02",

        "regionId": 77,
        "PROPERTY2": 77,
        "rapida_param4": 77,

        "mes": 9,
        "PROPERTY3": 9,
        "rapida_param5": 9,

        "god": 2013,
        "PROPERTY4": 2013,
        "rapida_param6": 2013,

        "kod1": 6,
        "PROPERTY5": 6,
        "rapida_param7": 6,

        "kod2": 199,
        "PROPERTY6": 199,
        "rapida_param8": 199,

        "previousValue": 0,
        "PROPERTY7": 0,
        "rapida_param9": 0,

        "currentValue": 0,
        "PROPERTY8": 0,
        "rapida_param10": 0,

        "end": 0

        }'''

    print acc
    res = ed_YD.pay(deal, dealer, dealer_acc, 4895, acc, 22, pay_pars)
    print res
    return res

# попробуем вручную получить ИД-платежа и его подтвердить
# https://sp-money.yandex.ru/check.xml?request-id=3734353838393737305f323535613763306161373966333461383833613238303266623630316132383264666535353665625f3332333937303939
def pay_test_to_mosenergo_confirm():
    import ed_YD
    deal_acc=db.deal_accs[264]
    deal = db.deals[deal_acc.deal_id]
    dealer_acc = db.dealers_accs[deal.dealers_acc_id]
    dealer = db.dealers[dealer_acc.dealer_id]
    api_pars, acc_pars, acc_name = ed_YD.get_pars(dealer, dealer_acc)
    res = {
        'request_id': '3734353838393737305f323535613763306161373966333461383833613238303266623630316132383264666535353665625f3332333937303939',
        }
    res = ed_YD.YmToConfirm(res, api_pars, dealer_acc.skey)


def payouts_stats():
    # pay_outs.amount created_on
    d = {}
    ss = 0
    for po in db(db.pay_outs).select():
        da = db.deal_accs[ po.ref ]
        dl = db.deals[ da.deal_id ]
        if dl.name not in d: d[dl.name] = 0
        d[dl.name] = d[dl.name] + round(float(po.amount),2)
        ss = ss + po.amount
    d['!TOTAL'] = float(ss)
    return BEAUTIFY(d)

def to_mysql():
    import convert_db
    return convert_db.to_mysql(db, db_old)


def pay_err_store():
    import db_common
    res = { 'error': 'eeee' }
    dealer_id = dealer_acc = deal_id = acc = 2
    db_common.pay_err_store(db, dealer_id, dealer_acc, deal_id, acc, res.get('error'))

def json_try():
    ll='[\
{ "n": "reg", "l": "Код региона (77-Москва, 50-Моск.обл.)", "ln":2, "f": "%d" },\
{ "n": "deal_acc", "l": "Номер лицевого счета по квитанции (10 цифр)", "ln":10, "f": "%d" },\
{ "n": "cod", "l": "Код платежа. (желательно 6 - корректирующий)",  "v": 6, "f": "%d" },\
{ "n": "PP", "l": "Код РР", "ln":3, "v": 199, "f": "%d" },\
{ "n": "m", "l": "Месяц", "calc": "lm", "hidden":"1" },\
{ "n": "y", "l": "Год",  "calc": "ly2", "hidden":"1" }\
]'
    ff = json.loads(ll)
    #for rr in ff:
    #    print
    #    for (k,v) in rr.iteritems():
    #        print k,v
    return BEAUTIFY(ff)

def deals_used():
    tt = SQLFORM.smartgrid (db.deals,
        #fields = ['name', 'used', 'my_client', 'wants', '_count', '_average', 'fee'],
        #fields00 = [db.deals.name, db.deals.used, db.deals.my_client, db.deals.wants, db.deals.count_,
        #     db.deals.average_, db.deals.fee,
        #     db.deal_accs.acc, db.deal_accs.payed, db.deal_accs.payed_month, db.deal_accs.partner_sum ,db.deal_accs.gift_payed,
        #     db.deal_errs.err, db.deal_errs.count_],
        #orderby=~db.deals.wants,
        links_in_grid=False,
        )
    return locals()

def out_txid():
    for r in db(db.pay_outs).select():
        v = r.info
        if v:
            try:
                v = json.loads(v)
                r.update_record(vars = v)
                r.update_record( txid = v.get('payment_id') or None )
            except Exception as e:
                print e
                r.update_record(vars = '"%s"' % v)


                
# api/tx_info.json/BTC/ee4ddc65d5e3bf133922cbdd9d616f89fc9b6ed11abbe9a040dac60eb260df23
# api/tx_info.html/BTC/ee4ddc65d5e3bf133922cbdd9d616f89fc9b6ed11abbe9a040dac60eb260df23
def tx_info():
    session.forget(response)

    txid = request.args(1)
    if not txid:
        return {'error':"need txid: /tx_info.json/[curr]/[txid]"}
    curr_abbrev = request.args(0)
    import db_common
    curr,xcurr,e = db_common.get_currs_by_abbrev(db, curr_abbrev)
    if not xcurr:
        return {"error": "invalid curr:  /tx_info.json/[curr]/[txid]"}

    import crypto_client

    token_system = conn = None
    if xcurr.protocol == 'era':
        token_key = xcurr.as_token
        token = db.tokens[token_key]
        token_system = db.systems[token.system_id]
        res = dict(result=crypto_client.get_tx_info(xcurr, token_system, txid, conn))
        return res

    res = crypto_client.get_tx_info(xcurr, token_system, txid, conn)
    return res

# api/tx_senders/BTC/ee4ddc65d5e3bf133922cbdd9d616f89fc9b6ed11abbe9a040dac60eb260df23
def tx_senders():
    session.forget(response)
    txid = request.args(1)
    if not txid:
        #raise HTTP(501, {"error": "empty pars"})
        return {'error':"need txid: /tx_senders.json/[curr]/[txid]"}
    curr_abbrev = request.args(0)
    import db_common
    curr, xcurr, e = db_common.get_currs_by_abbrev(db, curr_abbrev)
    if not xcurr:
        return {"error": "invalid curr"}
    
    token_system = None
    token_key = xcurr.as_token
    if token_key:
        token = db.tokens[token_key]
        token_system = db.systems[token.system_id]
        res = dict(result=crypto_client.sender_addrs(conn, token_system, txid))
        return res

    import crypto_client
    conn = crypto_client.connect(curr, xcurr)
    if not conn:
        return {"error": "not connected to wallet"}
    res = dict(result=crypto_client.sender_addrs(conn, token_system, txid))
    return res



## если какая то транзакция была пропущена - в АНСПЕНТ не попала так как была уже израсходована
## то проверить - была ли она обработана и если нет то обработать
## check_txid/BTC/4c921268aa59a182f7268c211d9facdce5445d2306638b398cf1e7d8880a9266
##
def check_txid():
    from cp_api import check_txid
    return check_txid(db, request)

def datetime():
    import datetime
    return 'request.now = %s <br> datetime.datetime.now() = %s' % (request.now, datetime.datetime.now())

def parse_mess(mess):
    args = mess.strip().split(':')
    #print args
    import db_common
    curr_out, xcurr_out, e = db_common.get_currs_by_abbrev(db, args[0].strip())
    if xcurr_out:
        if len(args) > 1:
            addr = args[1].strip()
            return curr_out.name + ':' + addr
        else:
            token_key = xcurr_out.as_token
            if token_key:
                token = db.tokens[token_key]
                token_system = db.systems[token.system_id]
                return curr_out.name + ':' + 'as RECIPIENT'

def probe_mess():
    
    acc = parse_mess(request.vars.get('head'))
    if not acc:
        acc = parse_mess(request.vars.get('message'))
        
    return acc