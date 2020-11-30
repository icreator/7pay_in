#!/usr/bin/env python
# coding: utf8

import datetime

from gluon import current, URL, XML, A
T = current.T
cache = current.cache

import crypto_client

def found_buys(db, buys, addr=None):
    if not addr or len(addr) < 6: return False
    #print addr
    no_addr = addr == "????--"
    expired = datetime.datetime.now() - datetime.timedelta(no_addr and 40 or 3, 0)
    for rec in db(
               (no_addr or db.buys.addr==addr)
               ##& (db.buys.id == db.buys_stack.ref_)
               & (not no_addr or db.buys.created_on > expired)
               ).select(orderby=~db.buys.created_on, limitby=(0, no_addr and 100 or 20)):

        ##buys.append(rec.buys)
        buys.append(rec)
    return no_addr


def found_unconfirmed_tokens_0(db, token_system):
    
    pays = []
    
    from_block = token_system.from_block
    if not from_block:
        mess = token_system.name + ': ' + T('not last block, please wait...')
        #print mess
        pays.append(mess)
        return
    
    confs_need = token_system.conf
    curr_block = crypto_client.get_height(None, token_system)
    if type(curr_block) != type(1):
        mess = token_system.name + ': ' + T('no connection to wallet')
        #print mess
        pays.append(mess)
        return

    confMax = confs_need + curr_block - from_block - 1
    #print 'confMax:', confMax

    lUnsp = crypto_client.get_unconf_incomes(token_system, token_system.account)
    if type(lUnsp) != type([]):
          mess = 'ERROR: found_unconfirmed lUnsp: %s' % lUnsp
          pays.append(mess)
          return
      
    for r in lUnsp:
        '''
          {
  "type_name":"SEND",
  "creator":"78JFPWVVAVP3WW7S8HPgSkt24QF2vsGiS5",
  "amount":"333.00000000",
  "signature":"ebfZ7saSLZSJxVneXK1dReTGNdgC1cKmYd1hNVsSpDbWh8YGSi65duJZ2LSCRSi23pKX4kEHEQKPykvUfY4Rg6X",
  "fee":"0.00010176",
  "type":31,
  "confirmations":-1,
  "version":0,
  "record_type":"SEND",
  "property2":128,
  "action_key":1,
  "property1":0,
  "size":159,
  "recipient":"7F9cZPE1hbzMT21g96U8E1EfMimovJyyJ7",
  "asset":1,
  "sub_type_name":"PROPERTY",
  "timestamp":1520158685079,
  "height":-1
}

        '''
        if u'amount' not in r:
            continue
        if r[u'type'] != 31:
            continue
        if r[u'action_key'] != 1:
            continue
                
        curr = db((db.tokens.system_id == token_system.id)
              & (db.tokens.token_key == r[u'asset'])
              & (db.xcurrs.as_token == db.tokens.id)
              & (db.currs.id == db.xcurrs.curr_id)).select().first()
        if not curr:
            return
        curr = curr.currs

        pays.append([dict(id = int(curr.id), abbrev = curr.abbrev),
                r[u'amount'], r[u'signature'], 0,
                #'Подтверждений: %s, ожидаем еще %s. Время создания: %s'
                r[u'confirmations'], int(confs_need - r[u'confirmations']),
                datetime.datetime.fromtimestamp(r[u'timestamp'] * 0.001),
                r[u'creator']
                    ])
    return pays

def found_unconfirmed_tokens(db, token_system):
    result = cache.ram(token_system.name + '_unc',
                lambda: found_unconfirmed_tokens_0(db, token_system), time_expire = 10)
    return result

def found_unconfirmed_coins_0(db, curr, xcurr):
    #print curr.abbrev
    
    pays = []
    
    confs_need = xcurr.conf
    
    conn = crypto_client.connect(curr, xcurr)
    if not conn:
        mess = curr.name + ': ' + T('no connection to wallet')
        #print mess
        pays.append(mess)
        return

    #print xcurr.name

    try:
        curr_block = conn.getblockcount()
    except:
        mess = curr.name + ': ' + T('no blockcount connection to wallet')
        #print mess
        pays.append(mess)
        return
        
    #print curr_block
    if type(curr_block) != type(-1):
        pays.append(curr.name + ' not started else... curr block: %s' % curr_block )
        return
    from_block = xcurr.from_block
    if not from_block:
        mess = curr.name + ': ' + T('not last block, please wait...')
        #print mess
        pays.append(mess)
        return
    
    confMax = confs_need + curr_block - from_block - 1
    #print 'confMax:', confMax

    lUnsp = conn.listunspent(0, confMax)
    #print lUnsp
    if type(lUnsp) != type([]):
        mess = 'ERROR: found_unconfirmed lUnsp: %s' % lUnsp
        pays.append(mess)
        return
    txids_used = {}
    for r in lUnsp:
        #print '\n\n',r.get(u'amount'), r
        txid = r.get(u'txid')
        if not txid:
            mess = 'found_unconfirmed GEN [%s]?' % r
            pays.append(mess)
            continue
        if txid in txids_used:
            # обработанные транзакции пропустим
            continue
        txids_used[txid]=True #  запомним эту транзакцию
        ti = conn.gettransaction(txid)

        # тут массив - может быть несколько транзакций
        # может быть [u'category'] == u'receive' ИЛИ u'send'
        trans_details = ti['details']
        #print 'trans LEN:', len( trans_details ), 'trans_details:',trans_details
        #continue
        # так вот, в одной транзакции может быть несколько входов!
        # поэтому если есть выход - значит тут вход это сдача наша с вывода и такую
        # транзакцию пропускаем
        its_outcome = False
        for detail in trans_details:
            if detail[u'category'] == u'send':
                its_outcome = True
                # сдача тут
                #print 'outcome'
                break
        if its_outcome:
            continue

        for income in trans_details:
            if income[u'category'] != u'receive': continue
            #print income[u'address']
            
            # далее только входы будут
            #print 'income:   ',income
            # CopperLark тут нету аккаунта и нет адреса
            # а у Litecoin есть сразу в записи unspent
            pays.append([dict(id = curr.id, abbrev = curr.abbrev),
                income[u'amount'], txid, r[u'vout'],
                #'Подтверждений: %s, ожидаем еще %s. Время создания: %s'
                r[u'confirmations'], confs_need - r[u'confirmations'],
                datetime.datetime.fromtimestamp(ti[u'time']),
                income[u'address']
                    ])
            
    return pays

def found_unconfirmed_coins(db, curr, xcurr):
    result = cache.ram(curr.abbrev + '_unc',
                lambda: found_unconfirmed_coins_0(db, curr, xcurr), time_expire = 10)
    return result


# тут если адрес пуст или "" то не опрашивает кошельки и инфо показывает урезанную
# чтобы не было видно данных персональных
#

def found_unconfirmed(db, curr, xcurr, addr, pays):
    #print curr.abbrev
    
    confs_need = xcurr.conf
    
    token_system = None
    token_key = xcurr.as_token
    if token_key:
        token = db.tokens[token_key]
        token_system = db.systems[token.system_id]

    if token_system:
        curr_block = crypto_client.get_height(xcurr, token_system)
        if type(curr_block) != type(1):
            mess = curr.name + ': ' + T('no connection to wallet')
            #print mess
            pays.append(mess)
            return
        

    else:
        conn = crypto_client.connect(curr, xcurr)
        if not conn:
            mess = curr.name + ': ' + T('no connection to wallet')
            #print mess
            pays.append(mess)
            return
        #print xcurr.name

        try:
            curr_block = conn.getblockcount()
        except:
            mess = curr.name + ': ' + T('no blockcount connection to wallet')
            #print mess
            pays.append(mess)
            return
        
    #print curr_block
    if type(curr_block) != type(-1):
        pays.append(curr.name + ' not started else... curr block: %s' % curr_block )
        return
    from_block = xcurr.from_block
    if not from_block:
        mess = curr.name + ': ' + T('not last block, please wait...')
        #print mess
        pays.append(mess)
        return

    confMax = confs_need + curr_block - from_block - 1
    #print 'confMax:', confMax
    if token_system:
        lUnsp = crypto_client.get_unconf_incomes(xcurr, token_system, token_system.account)
        if type(lUnsp) != type([]):
            mess = 'ERROR: found_unconfirmed lUnsp: %s' % lUnsp
            pays.append(mess)
            return
        for r in lUnsp:
            '''
            {
    "type_name":"SEND",
    "creator":"78JFPWVVAVP3WW7S8HPgSkt24QF2vsGiS5",
    "amount":"333.00000000",
    "signature":"ebfZ7saSLZSJxVneXK1dReTGNdgC1cKmYd1hNVsSpDbWh8YGSi65duJZ2LSCRSi23pKX4kEHEQKPykvUfY4Rg6X",
    "fee":"0.00010176",
    "type":31,
    "confirmations":-1,
    "version":0,
    "record_type":"SEND",
    "property2":128,
    "action_key":1,
    "property1":0,
    "size":159,
    "recipient":"7F9cZPE1hbzMT21g96U8E1EfMimovJyyJ7",
    "asset":1,
    "sub_type_name":"PROPERTY",
    "timestamp":1520158685079,
    "height":-1
  }

            '''
            if u'amount' not in r: continue
            
            # filter for
            if addr and addr != r[u'creator']:
                continue
            
            txid = r[u'signature']
            pays.append([
                    curr, r[u'amount'], txid, 0,
                    #'Подтверждений: %s, ожидаем еще %s. Время создания: %s'
                    r[u'confirmations'], confs_need - r[u'confirmations'],
                    datetime.datetime.fromtimestamp(r[u'timestamp'] * 0.001),
                    r[u'creator']
                        ])

    else:
        lUnsp = conn.listunspent(0, confMax)
        #print lUnsp
        if type(lUnsp) != type([]):
            mess = 'ERROR: found_unconfirmed lUnsp: %s' % lUnsp
            pays.append(mess)
            return
        txids_used = {}
        for r in lUnsp:
            #print '\n\n',r.get(u'amount'), r
            txid = r.get(u'txid')
            if not txid:
                mess = 'found_unconfirmed GEN [%s]?' % r
                pays.append(mess)
                continue
            if txid in txids_used:
                # обработанные транзакции пропустим
                continue
            txids_used[txid]=True #  запомним эту транзакцию
            ti = conn.gettransaction(txid)

            # тут массив - может быть несколько транзакций
            # может быть [u'category'] == u'receive' ИЛИ u'send'
            trans_details = ti['details']
            #print 'trans LEN:', len( trans_details ), 'trans_details:',trans_details
            #continue
            # так вот, в одной транзакции может быть несколько входов!
            # поэтому если есть выход - значит тут вход это сдача наша с вывода и такую
            # транзакцию пропускаем
            its_outcome = False
            for detail in trans_details:
                if detail[u'category'] == u'send':
                    its_outcome = True
                    # сдача тут
                    #print 'outcome'
                    break
            if its_outcome:
                continue

            for income in trans_details:
                if income[u'category'] != u'receive': continue
                #print addr, income[u'address']
                if addr and income[u'address'] != addr: continue
                # далее только входы будут
                #print 'income:   ',income
                # CopperLark тут нету аккаунта и нет адреса
                # а у Litecoin есть сразу в записи unspent
                ##pay_in = db(db.deal_acc_addrs.addr = addr).select().first()
                pays.append([
                    curr, income[u'amount'], txid, r[u'vout'],
                    #'Подтверждений: %s, ожидаем еще %s. Время создания: %s'
                    r[u'confirmations'], confs_need - r[u'confirmations'],
                    datetime.datetime.fromtimestamp(ti[u'time']),
                    income[u'address']
                        ])

    # TEST
    if False:
        pays.append([
            curr, 23, 'c7ea40601335a754e42b3a09f20386b1617448873882d654bdcb09bad3e920fd', 2,
            0, confs_need - 0,
            datetime.datetime.now()
                ])



def get_refs(db, pay):
    xcurr = db.xcurrs[pay['deal_acc_addrs'].xcurr_id]
    deal_acc = db.deal_accs[pay['deal_acc_addrs'].deal_acc_id]
    deal = db.deals[deal_acc.deal_id]
    return dict( xcurr = xcurr,
            curr_in = db.currs[xcurr.curr_id],
            deal_acc = deal_acc,
            deal = deal,
            curr_out = db.currs[deal_acc.curr_id]
            )

# addr если не задан то надо для всех искать свои дела и прочее
# те что еще в обработке
def found_pay_ins_process(db, addr, pays):
    # все зачтенные за последний месяц
    #xcurr = None
    if addr == "????":
        privat = addr != "????"
        addr = None
    elif addr:
        privat = False
    else:
        privat = True

    # сначала выдадим все неоплоченные входы - они в стеке
    for pay in db( (not privat or (addr!=None and len(addr)>29))
               & (db.pay_ins.id == db.pay_ins_stack.ref_)
               & (db.pay_ins.ref_ == db.deal_acc_addrs.id)
               & (not addr or db.deal_acc_addrs.addr == addr)
               ##& (not addr or db.deal_acc_addrs.xcurr_id == xcurr_in.id)
               ).select(orderby=~db.pay_ins.created_on):
        pay_in = pay.pay_ins
        rec_vals = addr and dict() or get_refs(db, pay)
        rec_vals['pay_in'] = pay_in
        rec_vals['pay_in_stack'] = pay.pay_ins_stack
        #print pay.pay_ins.status
        pays.append(rec_vals)

# addr если не задан то надо для всех искать свои дела и прочее
def found_pay_ins(db, addr, pays):
    # все зачтенные за последний месяц
    if addr == "????":
        privat = False
        addr = None
    elif addr:
        privat = False
    else:
        privat = True
    
    # теперь все выплаченные - их в стеке уже нет и тут глубина - 40 дней
    if addr:
        # для адреса за 60 дней
        expired = datetime.datetime.now() - datetime.timedelta(privat and 40 or 100, 0)
        recs = db(
               (db.deal_acc_addrs.addr==addr)
               & (db.pay_ins.ref_ == db.deal_acc_addrs.id)
               & (db.pay_ins.created_on > expired)
               ).select(orderby=~db.pay_ins.created_on)
    else:
        # если без адреса то только 3 сутки и < 20 последних
        expired = datetime.datetime.now() - datetime.timedelta(privat and 3 or 30, 0)
        recs = db(
               (db.pay_ins.ref_ == db.deal_acc_addrs.id)
               & (db.pay_ins.created_on > expired)
               ).select(orderby=~db.pay_ins.created_on, limitby=(0, privat and 20 or 100))
    for pay in recs:
        pay_in = pay.pay_ins
        if db(pay_in.id == db.pay_ins_stack.ref_).select().first(): continue
        rec_vals = addr and dict() or get_refs(db, pay)
        rec_vals['pay_in'] = pay_in

        if pay_in.order_id:
            rec_vals['order'] = db.orders[pay_in.order_id]

        if pay_in.payout_id:
            pay_out = db.pay_outs[pay_in.payout_id]
            rec_vals['pay_out'] = pay_out
            if pay_out and pay_out.dealer_acc_id:
                #deal_acc = db.deal_accs[pay_out.ref_]
                #deal = db.deals[deal_acc.deal_id]
                rec_vals['dealer_acc'] = dealer_acc = db.dealers_accs[pay_out.dealer_acc_id]
                #curr_out = db.currs[dealer_acc.curr_id]
                rec_vals['dealer'] = db.dealers[dealer_acc.dealer_id]
                #rec_vals['dealer_deal'] = db((db.dealer_deals.deal_id == deal.id)
                #      & (db.dealer_deals.dealer_id == dealer.id)).select().first()
        elif pay_in.clients_tran_id:
            # это выплатата клиенту
            cl_tr = db.clients_trans[pay_in.clients_tran_id]
            rec_vals['client'] = db.clients[cl_tr.client_id]

        pays.append(rec_vals)

    return privat
