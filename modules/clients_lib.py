#!/usr/bin/env python
# coding: utf8
from time import sleep
Test = None

DOMEN = 'face2face'

from decimal import Decimal
import datetime
#from gluon import *
import urllib
import httplib
import json

import db_common

def log(db, mess):
    print mess
    db.logs.insert(mess='CNT: %s' % mess)
def log_commit(db, mess):
    log(db,mess)
    db.commit()

def get_trans(db, client, order_id):
    return db((db.clients_trans.client_id == client.id)
              & (db.clients_trans.order_id == order_id)).select()
def get_bal(db, client, curr):
    xw = db((db.clients_balances.client_id == client.id)
            & (db.clients_balances.curr_id == curr.id)).select().first()
    return xw and xw.bal or None
def update_bal(db, client, curr, amo):
    xw = db((db.clients_balances.client_id == client.id)
            & (db.clients_balances.curr_id == curr.id)).select().first()
    if not xw:
        id = db.clients_balances.insert(
                client_id = client.id,
                curr_id = curr.id,
                bal = 0,
                )
        xw = db.clients_balances[id]
    xw.bal = xw.bal + Decimal(amo)
    xw.update_record()

    curr.clients_deposit = curr.clients_deposit + Decimal(amo)
    curr.update_record()

    db.commit()
    return xw.bal
def mem_output(db, client, order_id, amo, curr, desc):
    # изменим баланс валют на счетах клиента
    bal = update_bal(db, client, curr, -amo)
    clients_trans_id = db.clients_trans.insert(
        client_id = client.id,
        order_id = order_id,
        curr_out_id = curr.id,
        amo_out = amo,
        desc_ = desc,
        )

    return clients_trans_id, bal


# тут только транзакцию входа, а не обменна обрабатываем
# поэтому тут выходная валюта - чисто для учета магазина
# если есть валюта выхода - то значит входящая конвертируется в выходящую
# и балансы изменяются для выходяще - входящая по 0м
# если задан deal_acc_id то создаем уведомление на заказ платежа
def mem_input(db, client, order_id, amo, curr, desc, deal_acc = None):
    # изменим баланс валют на счетах клиента
    clients_trans_id = db.clients_trans.insert(
        client_id = client.id,
        order_id = order_id,
        curr_in_id = curr.id,
        amo_in = amo,
        desc_ = desc,
        )
    bal = update_bal(db, client, curr, amo)

    # и запомним чтонадо сообщить об этом нашему клиенту через HTTP
    client_notify_id = db.clients_notifies.insert(
            clients_tran_id = clients_trans_id,
            )
    if deal_acc:
        # и если задан заказ то уведомление на него запомним
        id = db.deal_accs_notifies.insert( deal_acc_id = deal_acc.id, client_id = client.id )
        # поидее тут же надо послать уведомление?
        notify_one_acc(db, db.deal_accs_notifies[id], client, deal_acc)
        
    return clients_trans_id, bal

def notify_one(db, note):
    #print note
    tries = note.tries or 0
    #print 'tries:', tries

    if tries > 6: return
    if tries > 0:
        tmin = note.created_on
        dt_old = datetime.datetime.now() - datetime.timedelta(0, 60*2**tries)
        #print datetime.timedelta(0, 60*2**tries), ' - ', dt_old
        if note.created_on > dt_old:
            #print 'till wail'
            return

    # сюда пришло значит время пришло послать уведомление
    clients_tran = db.clients_trans[note.clients_tran_id]
    client = db.clients[clients_tran.client_id]
    if not client.note_url: return
    curr = db.currs[clients_tran.curr_in_id]
    amo = clients_tran.amo_in
    #http://localhost/tobitrent/distrib_parts.php?id_min=%s&summ=%s&xcurr=%s&txid=%s&data=%s&desc=mining_income
    #https://bitrent.in/index.php?fc=module&module=annone&controller=validation&ref=%s&summ=%s&curr=1&curr_abbr=%s&trans=%s-7pay&date=%s
    f = r = None
    try:
        info = json.loads(clients_tran.desc_)
    except Exception as e:
        info = clients_tran.desc_
    print info
    '''
    type(info)==type(' ') and info or 'desc' in info and info['desc'] or '',
    'txid' in info and info['txid'] or '',
    'vout' in info and info['vout'] or '',
    '''
    try:
        url_rersp = client.note_url % (clients_tran.order_id, amo,
        curr.abbrev, clients_tran.id, clients_tran.created_on,
        'inp',
        )
    except Exception as e:
        url_rersp = client.note_url
        
    log(db, '%s' % url_rersp)
    try:
        f = urllib.urlopen(url_rersp)
        r = f.read()
    except Exception as e:
        print e
    print f and f.getcode()
    if not f or f.getcode() != 200:
        log(db, '%s %s' % (f.getcode(), r))
        note.tries = tries + 1
        note.update_record()
    else:
        print 'notify_one deleted'
        del db.clients_notifies[note.id]
    note.update_record()
    return r

# по умолчанию ссылка для ответа
## http://site_url/to_shop_response/from_7pay_in?order=[order_id]
def try_note_url(client, deal_acc):
    note_url = client.note_url
    if not note_url or len(note_url)<2:
         deal = db.deals[deal_acc.deal_id]
         note_url = deal.url or 'http://%s' % (deal.name2 or deal.name)
         note_url = note_url + '/to_shop_response/from_'+DOMEN
    url_rersp = note_url + '?order=%s' % deal_acc.acc
    log(db, '%s' % url_rersp)
    try:
        # пошлем запрос ничего во твет не ждем
        urllib.urlopen(url_rersp)
        #f = urllib.urlopen(url_rersp)
        #print f and f.getcode()
        #r = f.read()
    except Exception as e:
        print e

def notify_one_acc(db, note, client=None, deal_acc=None):
    #print note
    tries = note.tries or 0
    #print 'tries:', tries

    if tries > 10: return
    if tries > 0:
        # это ненулевое уведомление значит еще проверку на вермя делаем
        tmin = note.created_on
        dt_old = datetime.datetime.now() - datetime.timedelta(0, 30*2**tries)
        #print datetime.timedelta(0, 60*2**tries), ' - ', dt_old
        if note.created_on > dt_old:
            #print 'till wail'
            return

    # сюда пришло значит время пришло послать уведомление
    deal_acc = deal_acc or db.deal_accs[note.deal_acc_id]
    client = client or db.clients[note.client_id]
    try_note_url(client, deal_acc)
    note.tries = tries + 1
    note.update_record()
    return

def notify(db):
    for note in db(db.clients_notifies).select():
        notify_one(db, note)
    for note in db(db.deal_accs_notifies).select():
        notify_one_acc(db, note)

    db.commit()


# запуск как сервера
def serv_notify(db, interval=None):
    interval = interval or 66
    print __name__, ' interval:', interval

    while True:
        try:
            notify(db)
        except Exception as e:
            print 'ERROR:', __name__, e
            
        if Test: break
        sleep(interval)

def auto_collect(db):
    print '\nAUTO_COLLECT'
    for xcurr in db(db.xcurrs).select():
        curr = db.currs[xcurr.curr_id]
        if not curr.used: continue
        print curr.abbrev
        cn = crypto_client.connect(curr, xcurr)
        if not cn: continue
        
        addrs = {}
        # берем заданные крипту и все балансы по ней
        for cl_bal in db(db.clients_balances.curr_id == curr.id).select():
            if not (cl_bal.bal and cl_bal.bal >0): continue
            
            client = db.clients[cl_bal.client_id]
            # берем только клиентов с автовыплатой
            if not client.auto_collect: continue
            print client.email, cl_bal.bal
            # locket db
            cl_xwallet = db((db.clients_xwallets.client_id == client.id)
                            & (db.clients_xwallets.xcurr_id == xcurr.id)).select().first()
            if not cl_xwallet: continue
            
            addr = cl_xwallet.addr
            if not addr or len(addr) < 20:
                print 'not valid addr:', addr
                continue
            
            valid = cn.validateaddress(addr)
            if not valid or 'isvalid' in valid and not valid['isvalid'] or 'ismine' in valid and valid['ismine']:
                print 'not valid addr:', addr, valid
                continue
            print 'add bal:', cl_bal.bal
            addrs[addr] = round( float( cl_bal.bal ), 8 )
        #print addrs
        if len(addrs)==0:continue
        # теперь надо выплату сделать разовую всем за раз
        # отлько таксу здесь повыше сделаем чтобы быстро перевелось
        #{ 'txid': res, 'tx_hex': tx_hex, 'txfee': transFEE }
        res = crypto_client.send_to_many(curr, xcurr, addrs, 3*float(xcurr.txfee or 0.0001), cn )
        if not res or 'txid' not in res:
            print res
            return
        # деньги перевелись нужно зачесть это каждому
        txid = res['txid']
        # поидее надо запомнить что было перечисление
        # а то вдруг база залочена
        # проверим это
        log(db,'txid:%s for addrs:%s' % (txid, addrs))
        ti = cn.gettransaction(txid)
        trans_details = ti['details']
        vout = 0
        for trans in trans_details:
            addr = trans[u'address']
            # значение с минусом - поменяем его на +
            amo = - trans[u'amount']
            print amo, addr
            rec = db((db.clients_xwallets.xcurr_id == xcurr.id)
                    & (db.clients_xwallets.addr == addr)
                    & (db.clients.id == db.clients_xwallets.client_id)
                    ).select().first()
            if not rec:
                # это адрес сдачи - пропустим его
                continue
            order_id = None
            client = rec.clients
            # тут балансы все обновляются и сохраняются
            clients_trans_id, bal_new = mem_output(db, client, order_id, amo, curr,
                '{"txid": "%s", "vout": %s}' % (txid, vout))
            print 'bal new:', bal_new
            vout = vout + 1

    # тут не надо же сохранять - уже сохранилось в mem_output
    #### db.commit()
