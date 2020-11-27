#!/usr/bin/env python
# coding: utf8

#!/usr/bin/python2
import datetime

from gluon import current

import rpc_erachain
import rpc_ethereum_geth

T = current.T
cache = current.cache
#from gluon.cache import lazy_cache

from jsonrpc import ServiceProxy
### not worked yet (( from crypto_authproxy import AuthServiceProxy as ServiceProxy

ROUND_TO = 8

##import db_client

def log(db, mess):
    print mess
    db.logs.insert(mess='CRY: %s' % mess)
def log_commit(db, mess):
    log(db,mess)
    db.commit()


############ COMMON ################
def get_height(xcurr, token_system, conn=None):
    if xcurr.protocol == 'era':
        return rpc_erachain.get_height(token_system.connect_url)
    if xcurr.protocol == 'geth':
        return rpc_ethereum_geth.get_height(xcurr.connect_url)

def parse_tx_fields(xcurr, rec):
    if xcurr.protocol == 'era':
        return rpc_erachain.parse_tx_fields(rec)
    if xcurr.protocol == 'geth':
        return rpc_ethereum_geth.parse_tx_fields(rec)

def get_transactions(xcurr, token_system, from_block, conn=None):
    if xcurr.protocol == 'era':
        return rpc_erachain.get_transactions(token_system, from_block)
    if xcurr.protocol == 'geth':
        return rpc_ethereum_geth.get_transactions(xcurr, from_block)

###########

# покажем если был вызов а не из кэша
def conn_1(curr, xcurr, timeout=40):
    print 'try connect to ',curr.abbrev
    # def __init__(self, service_url, service_name=None, timeout=HTTP_TIMEOUT, connection=None):
    cn = ServiceProxy(xcurr.connect_url, None, timeout)
    #print cn
    blk = cn.getblockcount()
    print 'connected on block:', blk
    return cn

# тут если удача то надолго запомним
def conn_0(curr, xcurr, timeout=40):
    try:
        cn = cache.ram(curr.abbrev, lambda: conn_1(curr, xcurr, timeout), time_expire = 36000)
    except Exception as e:
        print curr.abbrev + ' conn except: %s' % current.CODE_UTF and str(e).decode(current.CODE_UTF,'replace') or str(e)
        cn = None
    if not cn:
        cache.ram.clear(curr.abbrev)
    return cn

# for bitcoin ver 12.0
def conn(curr, xcurr, cn=None):
    try:
        cn = cn or ServiceProxy(xcurr.connect_url, None, 60)
        cn.getblockcount()
        return cn
    except:
        return None

def connXcurr(xcurr, cn=None):
    try:
        cn = cn or ServiceProxy(xcurr.connect_url, None, 60)
        cn.getblockcount()
        return cn
    except:
        return None

# если нет связи то тоже запомним на небольшое время
def conn_v11(curr, xcurr, cn=None):
    # пока не подключимся - пробуем
    cn = cache.ram(curr.abbrev + '_0', lambda: conn_0(curr, xcurr, timeout), time_expire = 10)
    return cn


#@lazy_cache(curr.abbrev, time_expire=60, cache_model='ram')
def conn_old(curr, xcurr, inttime=30):
    cn = None
    #t1 = datetime.datetime.now()
    # запихаем результат функции в кэш на 1 часов - будет результат вызывыаться а не функция
    try:
        # короче тут сначала нужно получить связь! и только потом ее в кэш закатать
        # а если нету связи то без кэша
        #cn = ServiceProxy(xcurr.connect_url)
        #if cn:
        cn = cache.ram(curr.abbrev, lambda: ServiceProxy(xcurr.connect_url), time_expire = 3600)
    except Exception as e:
        print 'conn except: %s %s' % ( current.CODE_UTF and str(e).decode(current.CODE_UTF,'replace') or str(e), curr.abbrev)
        ##return
    #print datetime.datetime.now() - t1

    # если в кэше нет ничего или ошибка была то поновой без кжша возьмем
    try:
        cn = cn or ServiceProxy(xcurr.connect_url)
    except Exception as e:
        print 'conn except (ServiceProxy): %s %s' % ( current.CODE_UTF and str(e).decode(current.CODE_UTF,'replace') or str(e), curr.abbrev)
        return
    #print cnj
    #print cn.getblockcount(), cn

    try:
        cn.getblockcount()
        # это при переводах if xcurr.txfee: cn.settxfee(float(xcurr.txfee))
        #else: cn.settxfee(0.001)
        pass
    except Exception as e:
        print 'conn except (getblockcount): %s %s' % (current.CODE_UTF and str(e).decode(current.CODE_UTF,'replace') or str(e), curr.abbrev)
        return
    return cn

# выдать резервы только с учкетом проверенного блока на вход -
# так чтобы нельзя было
# перевести еще неучтенные монеты со входов UNSPENT
def get_reserve(curr, xcurr, cn=None):
    if not cn:
        cn = conn(curr,xcurr)
    if not cn:
        return
    curr_block = cn.getblockcount()
    conf = curr_block - xcurr.from_block + xcurr.conf
    #print conf
    tab, sum_Full = get_unspents(cn, conf)
    #print sum_Full
    return sum_Full

def get_tx_info(conn, xcurr, token_system, txid):
    if xcurr.protocol == 'era':
        import rpc_erachain
        return rpc_erachain.get_tx_info(token_system, txid)

    elif xcurr.protocol == 'geth':
        import rpc_ethereum_geth
        return rpc_ethereum_geth.get_tx_info(xcurr.connect_url, txid)

    elif not conn:
        conn = connXcurr(xcurr)
        if not conn:
            return None

    res = None
    try:
        res = conn.gettransaction(txid)
    except Exception as e:
        res = {'error': e}
        pass
    return res

def trans_exist(conn, txid):
    res = None
    #try:
    if True:
        # здесь нельзя делать отлов ошибок связи
        # иначе выдаст что нет транзакции хотять неизвестно - просто вязи небыло
        #res = conn.getrawtransaction(txid,1) # все выдает
        res = conn.gettransaction(txid) # выдает только для кошелька
        res = res and res.get('details')
    #except Exception as e:
    else:
        ###res = { 'error': e }
        pass
    return res

def is_not_valid_addr(cc, addr):
    try:
        valid = cc.validateaddress(addr)
    except:
        return

    if not valid.get('isvalid') or valid.get('ismine'):
        return True

# bal = reserve(conf)
# внутри еще вычтется комиссия сети
### нет - комсу теперь не включаем?
def send(db, curr, xcurr, addr, amo, conn_in=None, token_system = None, token = None):

    if xcurr.as_token:
        if token == None:
            token = db.tokens[xcurr.as_token]
        if token_system == None:
            token_system = db.systems[token.system_id]

    if token_system:
        import rpc_erachain
        return rpc_erachain.send(db, curr, xcurr, addr, amo, token_system, token)

    cc = conn_in or conn(curr, xcurr)
    if not cc: return {'error':'unconnect to [%s]' % curr.abbrev }, None
    try:
        valid = cc.validateaddress(addr)
    except:
        return {'error':'unconnect to [%s]' % curr.abbrev }, None
    if not valid or 'isvalid' in valid and not valid['isvalid'] or 'ismine' in valid and valid['ismine']:
        return {'error':'invalid [%s] address' % curr.abbrev }, None
    amo = round(float(amo),8)
    if True:
        txfee = round(float(xcurr.txfee or 0), 8)
    else:
        txfee = 0
    # reserve - то что уже учтено нами и это можно отослать дальше
    reserve =  get_reserve(curr, xcurr, cc)
    if amo + txfee > reserve:
        return {'error':'out off reserve:[%s]' % reserve }, None
    # проверим готовность базы - is lock - и запишем за одно данные
    log_commit(db, 'try send: %s[%s] %s' % (amo, curr.abbrev, addr))
    cc.settxfee( txfee )
    if amo > txfee * 2:
        #if True:
        try:
            #to_send_amo = int((amo - txfee) * 100000000) - txfee already included in get_RATE from db.currs
            to_send_amo = int(amo * 100000000)
            to_send_amo = float(to_send_amo) / 100000000.0

            print 'res = cc.sendtoaddress(addr, amo)', to_send_amo
            res = cc.sendtoaddress(addr, to_send_amo)
            print "SENDed? ", res
        #else:
        except Exception as e:
            ##return {'error': (current.CODE_UTF and str(e).decode(current.CODE_UTF,'replace') or str(e)) + ' [%s]' % curr.abbrev }, None
            return {'error': ('%s' % e) + ' [%s]' % curr.abbrev }, None
    else:
        # тут mess для того чтобы обнулить выход и зачесть его как 0
        res = { 'mess':'< txfee', 'error':'so_small', 'error_description': '%s < txfee %s' % (amo, txfee) }

    bal = get_reserve(curr, xcurr, cc)
    return res, bal

def get_xaddress_by_label(conn, label, protocol='btc'):

    addrs = conn.getaddressesbyaccount(label)

    if addrs:
        return addrs[0]
    return conn.getnewaddress(label)

# открыть те что в списке
def unlocks(conn, tab=None):
    if not tab: tab = conn.listlockunspent() # все закрытые откроем
    conn.lockunspent(True, tab)

# закрыть все входы, чтобы при переносе монет они не трогались
def locks(conn):

    lu = conn.listunspent(0)
    ll = []
    for u in lu:
        ll.append({u'txid':u[u'txid'], u'vout':u[u'vout']})
    try:
        conn.lockunspent(False, ll)
    except Exception as e:
        print e,
        print e.error

# найти адрес того кто выслал их
def sender_addr(conn, token_system, tr):

    if token_system:
        import rpc_erachain
        return rpc_erachain.get_tx_info(token_system, tr)['creator']
    elif not conn:
        return None

    tr_info = conn.getrawtransaction(tr,1)
    vins =  tr_info and 'vin' in tr_info and tr_info['vin']
    if not vins:
        #res.append({ 'tr_info.vins': 'None'})
        # тут может быть приход с добвтого блока - тогда тоже будет пусто!
        print 'ERROR: sender_addr - tr_in_info:', tr_in_info
        print 'RUN "crypto WALLET.exe"  -reindex -txindex'
        return
    vin = vins[0]
    txid = vin['txid']
    vout = vin['vout']
    tr_in_info = conn.getrawtransaction(txid,1)

    if 'error' in tr_in_info:
        print 'ERROR: sender_addr - tr_in_info:', tr_in_info
        print 'RUN "crypto WALLET.exe"  -reindex -txindex'
        return
    vin = vins[0]
    txid = vin['txid']
    vout = vin['vout']
    tr_in_info = conn.getrawtransaction(txid,1)

    if 'error' in tr_in_info:
        print 'ERROR: sender_addr - tr_in_info:', tr_in_info
        print 'RUN "crypto WALLET.exe"  -reindex -txindex'
        return
    sender = tr_in_info[u'vout'][vout][u'scriptPubKey'][u'addresses']
    return sender[0]

# выдать неиспользованные входы - для создания транзакции вручную
# наберем входы на данный баланс и для данного адреса
# addrs = [...]
def get_unspents(conn, conf_from=None, vol=None, addrs=None, accs=None):
    conf_from = conf_from == None and 1 or conf_from # если на входе 0 то не менять
    sumFull = sumReceive = sumChange = sumGen = 0.0
    tab = []
    lUnsp = conn.listunspent(conf_from)
    #print conf_from, conn.getbalance(), lUnsp
    # обработка со старых начинаем
    lUnsp.sort(key=lambda r: r[u'confirmations'], reverse=True)
    for unsp in lUnsp:
        #print 'conf:', unsp[u'confirmations'], ' amo:', unsp[u'amount'], 'vout:',unsp[u'vout']
        txid = unsp['txid']
        ti = conn.gettransaction(txid)
        trans_details = ti['details']

        vout = unsp[u'vout']
        if accs:
            kk = u'account'
            tx_acc = unsp.get(kk)
            if tx_acc not in accs: continue
        if addrs:
            kk = u'address'
            tx_addr = unsp.get(kk)
            if tx_addr not in addrs: continue


        amo = float(unsp[u'amount'])
        #print '\n\n confirmations:',unsp[u'confirmations'], 'amo:',amo, unsp

        #print '   DETAILS', trans_details
        categ = ''

        its_change = None
        for detail in trans_details:
            if detail[u'category'] == u'send':
                # если тут хоть один выход встретился - значит это сдача
                # и она тут как вход
                sumChange = sumChange + amo
                its_change = True
                categ = 'change'
                break

        if not its_change:
            # если это не сдача то смотрим еще категорию "сгенерировано"
            its_generate = False
            for detail in trans_details:
                if detail[u'category'] == u'generate':
                    # сюда пришлоесли монета сгенерирована - ждем больше подтверждений
                    its_generate = True
                    categ = 'generate'
                    break

            if its_generate:
                sumGen = sumGen + amo
            else:
                categ = 'receive'
                sumReceive = sumReceive + amo


        sumFull = sumChange + sumGen + sumReceive
        tab.append({ 'txid':txid, 'vout':vout,
                     'category': categ, 'amo': amo
                     })
        #print '   appended... as', categ
        if vol and vol < sumFull: break

    #sumFull = sumFull + sumChange + sumGen + sumReceive
    #print sumFull, 'change:', sumChange, 'gen:',sumGen, 'receive:',sumReceive
    return tab, sumFull

# вычислить комисиию за длинну транзакции
def calc_txfee(cn, lus, sends, fee_in):
    tx_str = cn.createrawtransaction (lus, sends)
    #print 'len(tx_str):',len(tx_str), fee_in
    return fee_in*(round(len(tx_str)/1000, 0) + 1)

def send_to_many(db, curr, xcurr, sends_in, tx_fee_in=None, conn_in=None):
    if len(sends_in)==0: return
    # тут надоп роверить баланс клиента
    vol = 0.0
    sends = {}
    for (k,v) in sends_in.iteritems():
        v = round(float(v),ROUND_TO)
        vol = vol + v
        # отловим повторы в списке и ссумируем их
        # хотя поидее они уже там из списка просуммированы
        sends[k] = (sends.get(k) or 0.0) + v # converted to float

    cn = conn_in or conn(curr,xcurr)
    if not cn:
        return {'error': 'ERROR: connection to wallet [%s] is broken' % curr.abbrev }

    #print 'wallet balance:', cn.getbalance()
    res = None
    addr=None
    conf = xcurr.conf
    # наберем входы неиспользованные на этот объем монет
    lus, amo_u = get_unspents(cn, conf, vol, addr)
    #print lus
    transFEE = calc_txfee(cn, lus, sends, float(tx_fee_in or xcurr.txfee or 0.0001))
    #print transFEE

    # reserve - то что уже учтено нами и это можно отослать дальше
    reserve =  get_reserve(curr, xcurr, cn)
    if vol + transFEE > reserve:
        return {'error':'out off reserve:[%s]' % reserve }, None

    # заново наберем чтобы комиссию включить
    lus, amo_u = get_unspents(cn, conf, vol + transFEE, addr)

    # теперь надо остаток перевести себе за минусом комиссиии платежа
    my_change = round(amo_u - vol - transFEE, 8)
    #print vol, '+ my_change:', my_change, len(lus), len(sends), amo_u
    if my_change < 0:
        return { 'error': 'ERROR: my_change %s < 0 ! wallet balance: %s - %s - fee %s' % (my_change, amo_u, vol, transFEE) }
    if my_change > 0:
        # тут остается сдача, поэтому
        # добавим наш адрес для возврата сдачи, остальное уйдет как комиссия за транзакцию
        ### если на старый адресс пихать или даже брать новый
        # то баланс в кошельке до подтверждения блока будет в неподтвержденных!
        # тут надо использовать

        change_addr = xcurr.main_addr
        #print change_addr, '=', my_change
        sends[change_addr] = my_change

    tx_str = cn.createrawtransaction (lus, sends)
    if type(tx_str) == type( {} ):
        #print tx_str
        return { 'error': 'ERROR: createrawtransaction res= %s' % (tx_str) }

    #return '%s' % transFEE

    #print '\n\n [%s]' % cn.decoderawtransaction(tx_str)

    # провеим нне залочена ло база данных и заодно запомним платеж в логах
    if db: log_commit(db,'try crypto_client.send_to_many %s: %s' % (curr.abbrev, sends_in))

    res = cn.signrawtransaction( tx_str )
    #print 'signrawtransaction:', res
    if u'error' in res or not res[u'complete']:
        return { 'error': 'ERROR: signrawtransaction %s' % (res[u'error']) }
    # транзакция успешно подписана - можем отправить ее в сеть

    tx_hex = res[u'hex'] # запомним ее - вдруг сеть не включила в блок
    res = cn.sendrawtransaction( tx_hex )
    #print type(res)
    #log('sendrawtransaction: %s' % res)
    if type(res) != type(u' '):
        return { 'error': 'ERROR: sendrawtransaction %s' % (res) }

    return { 'txid': res, 'tx_hex': tx_hex, 'txfee': transFEE }

def re_broadcast (db, curr, xcurr, cn=None):
    return # поидее наш кошелек сам все делает
    cn = cn or conn(curr,xcurr)
    if not cn: return

    ok_conf = 6
    for r in db((db.xcurrs_raw_trans.xcurr_id==xcurr.id)
                & (db.xcurrs_raw_trans.confs < ok_conf)).select():

        tx = cn.getrawtransaction (r.txid,1)
        confs = tx.get('confirmations')
        if confs>0:
            r.confs = confs
            r.update_record()
            continue
        print 're_broadcast:', tx
        #log(db, tx)
        res = cn.signrawtransaction(tx[u'hex'])
        print res
