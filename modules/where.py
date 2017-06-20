#!/usr/bin/env python
# coding: utf8
import datetime
import json

from gluon import current, URL, XML, A
T = current.T


import crypto_client
import db_common

def found_buys(db, addr):
    res = []
    if not addr or len(addr) < 6: return res
    #print addr
    no_addr = addr == "????--"
    expired = datetime.datetime.now() - datetime.timedelta(no_addr and 1 or 40, 0)
    for r in db(
               (no_addr or db.buys.addr==addr)
               ##& (db.buys.id == db.buys_stack.ref_)
               & (db.buys.created_on > expired)
               ).select(orderby=~db.buys.created_on):

        ##rec = r.buys
        #buys.buyer	buys.operation_id	buys.amount
        mess_in = '%s [%s] - op_id:%s %s' % (rec.amount, 'RUB', no_addr and '' or rec.operation_id, no_addr and rec.amo_out and round(rec.amount/rec.amo_out,8) or '')
        if rec.xcurr_id:
            xcurr = db.xcurrs[rec.xcurr_id]
            curr = xcurr and db.currs[xcurr.curr_id]
            abbrev = curr and curr.abbrev or '?'
        else:
            ## это пополнения из банков у которых еще не поределен адрес выхода
            abbrev = '???'
        st = rec.status
        st = st=='progress' and T('In progrress...') \
            or st=='addr waiting' and T('Awaiting the wallet assign') or st
        mess_out = rec.amo_out and '%s [%s] %s - txid:%s' % (rec.amo_out, abbrev, rec.created_on, rec.txid) or '0[%s] %s' % (abbrev, st)
        res.append({
            T('Вход'): mess_in,
            T('Выход'): mess_out,
            T('Затраты'): rec.tax_mess or '',
            })
    return res
#
# тут если адрес пуст или "" то не опрашивает кошельки и инфо показывает урезанную
# чтобы не было видно данных персональных
#

def found_unconfirmed(db, curr, xcurr, addr, pays):
    privat = not addr or len(addr) < 4
    if privat: return
    conn = crypto_client.conn(curr, xcurr)
    if not conn:
        #mess = curr.name + ' ' + T('no connection to wallet')
        #print mess
        #pays.append(mess)
        return
    #print xcurr.name
    addr_use = not (privat or addr == "????")

    confs_need = xcurr.conf
    curr_block = conn.getblockcount()
    if type(curr_block) != type(-1):
        pays.append(T('not started else...') + '%s' % curr_block )
        return
    from_block = xcurr.from_block
    if not from_block: return
    confMax = confs_need + curr_block - from_block - 1
    #print 'confMax:', confMax
    lUnsp = conn.listunspent(0, confMax)
    if type(lUnsp) != type([]):
        print 'ERROR: found_unconfirmed lUnsp:', lUnsp
        pays.append('ERROR: found_unconfirmed lUnsp')
        return
    txids_used = {}
    for r in lUnsp:
        #print '\n\n',r.get(u'amount'), r
        txid = r.get(u'txid')
        if not txid:
            print '\n found_unconfirmed GEN?', r
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
            if addr_use and income[u'address'] != addr: continue
            # далее только входы будут
            #print 'income:   ',income
            # CopperLark тут нету аккаунта и нет адреса
            # а у Litecoin есть сразу в записи unspent
            # запомним сумму монет на вывод
            amo = income[u'amount']
            mess_in = privat and '%s [%s]' % (amo, curr.abbrev) \
                or '%s [%s] txid:%s vout:%s' % (amo, curr.abbrev, txid, r[u'vout'])
            pays.append({ T('Вход'): mess_in,
                    T('Статус'): 'Подтверждений: %s, ожидаем еще %s. Время создания: %s'
                    % ( r[u'confirmations'], confs_need - r[u'confirmations'], datetime.datetime.fromtimestamp(ti[u'time'])),
                    })

def found_pay_ins(db, curr_in, xcurr_in, addr, pays, amo_rest):
    # все зачтенные за последний месяц
    #xcurr = None
    # сначала выдадим все неоплоченные входы - они в стеке
    used = {}
    privat = not addr or len(addr) < 4
    no_addr = privat or addr == "????"
    for pay in db( (not privat)
               & (db.pay_ins.id == db.pay_ins_stack.ref_)
               & (db.pay_ins.ref_ == db.deal_acc_addrs.id)
               & (no_addr or db.deal_acc_addrs.addr==addr)
               ).select(orderby=~db.pay_ins.created_on):
        xcurr = db.xcurrs[pay.deal_acc_addrs.xcurr_id]
        if xcurr_in and xcurr_in.id != xcurr.id: continue
        curr_in = db.currs[xcurr.curr_id]

        deal_acc = db.deal_accs[pay.deal_acc_addrs.deal_acc_id]
        deal = db.deals[deal_acc.deal_id]
        deal_name = deal.name
        if not privat:
            # показать подробно мне
            deal_name = '%s %s' % (deal.name, deal_acc.acc)
        st = pay.pay_ins.status
        if st == 'returned':
            pay_out_info = T('Возвращен обратно')
        else:
            pay_out_info = T('НЕ ВЫПЛАЧЕН, статус: ') + (st or T('в обработке'))
        used[pay.pay_ins.id]=True
        mess_in = '%s [%s] %s -> %s' % (pay.pay_ins.amount, curr_in.abbrev, pay.pay_ins.created_on, deal_name)
        pays.append({
            T('Вход'): mess_in,
            T('Выход'): pay_out_info,
            })
    # теперь все выплаченные - их в стеке уже нет и тут глубина - 40 дней
    # если без адреса то только 1 сутки
    expired = datetime.datetime.now() - datetime.timedelta(no_addr and 1 or 40, 0)
    for pay in db(
               (no_addr or db.deal_acc_addrs.addr==addr)
               & (db.pay_ins.ref_ == db.deal_acc_addrs.id)
               & (db.pay_ins.created_on > expired)
               ).select(orderby=~db.pay_ins.created_on):
        if pay.pay_ins.id in used: continue
        #print pay
        xcurr = db.xcurrs[pay.deal_acc_addrs.xcurr_id]
        if xcurr_in and xcurr_in.id != xcurr.id: continue
        curr_in = db.currs[xcurr.curr_id]

        deal_acc = db.deal_accs[pay.deal_acc_addrs.deal_acc_id]
        deal = db.deals[deal_acc.deal_id]
        curr_out = db.currs[deal_acc.curr_id]
        dn_url = None
        if deal.name == 'phone +7':
            dn_url = URL('to_phone','index')
        elif deal.name == 'WALLET':
            dn_url = URL('to_wallet','index')
        else:
            dn_url = URL('more','to_pay', args=[deal.id])
        order_info = None
        if pay.pay_ins.order_id:
            order = db.orders[pay.pay_ins.order_id]
            order_info = T('№%s от %s, курс:%s') % (order.id, order.created_on, round(order.volume_out/order.volume_in,8))
        st = pay.pay_ins.status
        if st == 'returned':
            pay_out_info = T('Возвращен обратно')
        else:
            pay_out_info = T('НЕ ВЫПЛАЧЕН, статус: ') + (st or T('в обработке'))
        payout = rate = None
        if pay.pay_ins.payout_id:
            payout = db.pay_outs[pay.pay_ins.payout_id]
            if payout and payout.dealer_acc_id:
                #deal_acc = db.deal_accs[payout.ref_]
                #deal = db.deals[deal_acc.deal_id]
                dealer_acc = db.dealers_accs[payout.dealer_acc_id]
                #curr_out = db.currs[dealer_acc.curr_id]
                dealer = db.dealers[dealer_acc.dealer_id]
                dealer_deal = db((db.dealer_deals.deal_id == deal.id) & (db.dealer_deals.dealer_id == dealer.id)).select().first()
                #if dealer_deal.p2p and deal.name != 'WALLET':
                #    # если это выплата в магазин то переопределим ссылку
                #    dn_url = URL('to_shop','index')
                p_i = payout.vars or json.loads(payout.info or '{}')
                rate = round(payout.amount/payout.amo_in,8)
                amo_out = round(pay.pay_ins.amount * payout.amount/payout.amo_in, 2)
                #if not 'payment_id' in p_i: print payout.info, amo_out
                pay_out_info = T('%s [%s] -%s%s %s ') % ( amo_out, curr_out.abbrev, dealer_deal.tax, '%', payout.created_on )
                if not privat:
                    if 'payment_id' in p_i:
                        pay_out_info = pay_out_info + T('%s %s') % (p_i['payment_id'], p_i.get('invoice_id') or p_i.get('payee') )
                    else:
                        pay_out_info = pay_out_info + '%s' % p_i
        elif pay.pay_ins.clients_tran_id:
            # это выплатата клиенту
            cl_tr = db.clients_trans[pay.pay_ins.clients_tran_id]
            clnt = db.clients[cl_tr.client_id]
            amo_out = cl_tr.amo_in
            rate = None
            pay_out_info = ''
            if cl_tr.curr_in_id and cl_tr.curr_in_id != curr_in.id:
                # была конвертация
                pay_out_info = pay_out_info + '%s [%s] ' % (amo_out, curr_out.abbrev)
                #rate = cl_tr.amo_in
            pay_out_info = pay_out_info + T('зачтено')
            if privat:
                dn_url = URL('to_shop','index', args=[cl_tr.client_id])
            else:
                pay_out_info = pay_out_info + T(' транзакция №%s - %s') % (cl_tr.id, cl_tr.desc_)
                # to_shop/index/2?order=UUWZNTYIR&sum=0.02&curr_out=BTC
                vvv = {'order':deal_acc.acc, 'curr_out':curr_out.abbrev}
                if amo_rest: vvv['sum'] = amo_rest
                dn_url = URL('to_shop','index', args=[cl_tr.client_id],
                    vars=vvv)

        if not order_info and rate:
            order_info = T('текущий курс:%s') % round(rate,8)
        deal_name = deal.name
        if not privat:
            deal_name = '%s %s' % (deal.name, deal_acc.acc)
        deal_name = XML(A(deal_name, _href=dn_url))
        rec_vals = {
            T('Вход'): '%s [%s] %s' % (pay.pay_ins.amount, curr_in.abbrev, pay.pay_ins.created_on),
            T('Для'): deal_name,
            T('Заказ'): order_info,
            T('Выход'): pay_out_info,
            }
        if payout:
            if payout.amo_gift and payout.amo_gift > 0:
                rec_vals[T('Подарок')] = T('Вы получили дополнительно %s [%s]') % (payout.amo_gift, curr_out.abbrev)
            if payout.amo_partner and payout.amo_partner > 0:
                rec_vals[T('Партнёрские')] = T('Вы получили дополнительно %s [%s]') % (payout.amo_partner, curr_out.abbrev)


        pays.append(rec_vals)
