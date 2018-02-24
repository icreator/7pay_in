#!/usr/bin/env python
# coding: utf8
import datetime
from decimal import Decimal

# TODO
# если валюта отключена и произошел возврат то баланс не изменяетс!!!

from gluon import current
T = current.T

TO_COIN_ID = 2

import db_common
import crypto_client
import rpc_erachain

#        if r.pay_ins.status in {'technical_error', 'payment_refused', 'currency_unused'}:

#
# на самом деле это не сервер - он не висит постоянно в памяти и не выполняется параллельно
# просто при приходе блока вызывчается curl со ссылкой на страницу проекта
# start /MIN curl http://127.0.0.1:8000/ipay3/tools/block_proc/%1/%2 -s >nul
# see !notify-curl.cmd in C:\web2py\applications\ipay4\wallets
# see bitcoin.conf and !notify.cmd in ./bitcoin

def log(db, mess):
    mess='BLK: %s' % mess
    print mess
    db.logs.insert(mess=mess)
def log_commit(db, mess):
    log(db,mess)
    db.commit()

# запуск пробный из тулсов:
#  /tools/block_proc/CLR
def b_p_db_update( db, conn, curr, xcurr, tab, curr_block):
    # сюда приходят все одиночные входы
    # поидее надо их всех запомнить
    token_system = None
    token_key = xcurr.as_token
    if token_key:
        token = db.tokens[token_key]
        token_system = db.systems[token.system_id]

    for rec in tab: #.iteritems():
        amo = Decimal(rec['amo'])
        acc = rec['acc']
        addr = rec['addr']
        txid=rec['txid']
        vout=rec['vout']
        time = rec['time']
        confs = rec['confs']
        #if len(acc)==0:
        #    # пропустим пустые а то они все будут подходить
        #    continue
        try:
            # for cyrilic - error
            print 'b_p_db_update:',curr.abbrev, 'acc:"%s"' % acc, ' unspent:',amo, 'txid:', txid, 'vout:',vout
        except:
            print 'b_p_db_update:',curr.abbrev, addr, ' unspent:',amo, 'txid:', txid, 'vout:',vout
        #print datetime.datetime.fromtimestamp(rec['time'])
        #print rec, '\n'
        if token_system:
            ## ASSET_KEY income > ASSET_KEY outcome : ADDRESS
            acc_tab = acc.split('>')
            if len(acc_tab) < 2:
                log(db, 'AS TOKEN not found on SPLIT ' + acc)
                continue

            token_key_in = acc_tab[0]
            try:
                token_key_in = int(token_key_in) # ASSET KEY in Erachain
            except Exception as e:
                log(db, 'income TOKEN not (int) ' + acc)
                continue
                
            xcurr_in = db_common.get_xcurr_by_system_token(db, token_system, token_key_in)
            curr_in = xcurr_in and db.currs[xcurr_in.curr_id]
            if not curr_in:
                log(db, 'income xCURR not found ' + acc)
                continue

            out_tab = acc_tab[1].split(':')
            if len(out_tab) < 2:
                log(db, 'AS TOKEN not found out_tab ' + acc)
                continue
            
            curr_out_name = out_tab[0]
            try:
                curr_out_key = int(curr_out_name) # ASSET KEY in Erachain
                print curr_out_key
                xcurr_out = db_common.get_xcurr_by_system_token(db, token_system, curr_out_key)
                curr_out = xcurr_out and db.currs[xcurr_out.curr_id]
            except Exception as e:
                curr_out, xcurr_out, e = db_common.get_currs_by_abbrev(db, curr_out_name)
            
            if not curr_out:
                log(db, 'AS TOKEN not found curr_out ' + acc)
                continue
                        
            deal_acc = db((db.deal_accs.deal_id == TO_COIN_ID)
                          & (db.deal_accs.curr_id == curr_out.id)
                          & (db.deal_accs.acc == out_tab[1])).select().first()
            if not deal_acc:
                deal_acc_id = db.deal_accs.insert(deal_id = TO_COIN_ID, curr_id = curr_out.id, acc = out_tab[1])
                
            deal_acc_addr = db((db.deal_acc_addrs.addr==addr)
                & (db.deal_acc_addrs.xcurr_id==xcurr_in.id)).select().first()
                        
            if not deal_acc_addr:
                deal_acc_addrs_id = db.deal_acc_addrs.insert(deal_acc_id = deal_acc_id, addr=addr, xcurr_id=xcurr_in.id)
                deal_acc_addr = db.deal_acc_addrs[ deal_acc_addrs_id ]
        else:
            deal_acc_addr = db((db.deal_acc_addrs.addr==addr)
                & (db.deal_acc_addrs.xcurr_id==xcurr.id)).select().first()

            # TODO
            if not deal_acc_addr:
                # такой адрес не в наших счетах
                if acc == '.main.' or acc == '.confirm.':
                    # если это приход на  главный адрес - например пополнения с обмена\
                    # то такую проводку пропустим
                    continue
                elif conn:
                    print 'unknown [%s] address %s for account:"%s"' % (curr.abbrev, addr, acc)
                    # если не найдено в делах то запомним в неизвестных
                    send_back(conn, curr, xcurr, txid,  amo)
                    print 'to return -> txid', txid
                    continue
                else:
                    print 'UNKNOWN deal:', rec
                    continue
        

        # теперь в таблице от unspent без повторов - так как там блок каждый раз новый
        trans = db((db.pay_ins.txid==txid) & (db.pay_ins.vout==vout)).select().first()
        if trans:
            # уже такая есть
            print 'txid+vout exist:', txid, vout
            continue

        if deal_acc_addr:
            addr_ret =  deal_acc_addr.addr_return
            if deal_acc_addr.unused and conn and addr_ret:
                # переводы на этоот адрес запрещены - тоже вернем его
                print 'UNUSED [%s] address %s for account:"%s"' % (curr.abbrev, addr, acc)
                # если не найдено в делах то запомним в неизвестных
                send_back(conn, curr, xcurr, txid,  amo, addr_ret)
                print 'to return -> txid', txid
                continue

        created_on = datetime.datetime.fromtimestamp(time)

        pay_id = db.pay_ins.insert( ref_ = deal_acc_addr.id,
            amount = amo, confs=confs,
            txid=txid, vout=vout,
            created_on = created_on
            )
        #print rec['time']
        # закатаем записи в стек чтобы быстро разообрать платежи по ордерам
        db.pay_ins_stack.insert(ref_=pay_id)

        # запомним сумму свободных монет на данном счету
        # потом именно столько можно перевести на главный счет
        incomed = deal_acc_addr.incomed
        if incomed: deal_acc_addr.incomed = incomed + amo
        else: deal_acc_addr.incomed = amo
        deal_acc_addr.update_record()

    # так как мы в фреймворке - тут само сохраняет db.commit()
    pass

    # сохраним теперь инфо что эти блоки обработали
    if token_system:
        pass
    else:
        xcurr.from_block = curr_block
        xcurr.update_record()

def get_incomed(db, erachain_url, erachain_addr, curr, xcurr, addr_in=None, from_block_in=None):
    
    tab = []
    curr_block = rpc_erachain.get_info(erachain_url)
    print curr_block
    if type(curr_block) != type(1):
        # кошелек еще не запустился
        print 'not started else'
        return tab, from_block # если переиндексация то возможно что и меньше

    from_block = from_block_in or xcurr.from_block
    if from_block:
        if not curr_block > from_block:
            print 'not curr_block > from_block', curr_block, from_block
            return tab, from_block # если переиндексация то возможно что и меньше
        print curr_block, from_block
        print curr.abbrev, from_block, erachain_addr
        tab = rpc_erachain.get_transactions(erachain_url, erachain_addr, from_block)
        if type(tab) == type({}):
            # ошибка
            log(db, 'listunspent %s' % l_Unsp)
            return tab, None

    else:
        # если нет еще номера обработанного блока
        # то и делать нечего - мол служба только запущена
        # на нее нет еще переводоов, хотя можно наоборот взять все входы
        xcurr.from_block = from_block = 1 # все входы со всеми подтверждениями берем
        xcurr.update_record()
        tab = rpc_erachain.get_transactions(erachain_url, erachain_addr)
        if type(tab) == type({}):
            # ошибка
            log(db, 'listunspent %s' % Unsp)
            return tab, None
    
    #print tab
    transactions = []
    for rec in tab:
        if rec['amount'] <= 0 or rec['action_key'] != 1:
            continue

        head = rec.get('head')
        if not head:
            acc = 'refuse:' + rec['creator']
        else:
            acc = ('%d' % rec['asset']) + '>' + head
                
        #print rec
        transactions.append(dict(
            amo = rec['amount'],
            txid=rec['signature'],
            vout=rec['sequence'],
            time = rec['timestamp'] * 0.001,
            confs = rec['confirmations'],
            addr = acc,
            acc = acc
                )
            )

    return transactions, curr_block

# найдем все входы одиночные
# на выходе массив по входам
def b_p_proc_unspent( db, conn, curr, xcurr, addr_in=None, from_block_in=None ):
    # проверим непотраченные монеты на адресах,
    # которые созданы для приема крипты
    #
    # тут ограничиваем просмотр входящих неизрасходованных
    # транзакций по подтверждениям с учетом номера обработанного блока
    #
    tab = []
    # макс подтв так чтобы не брать уже обработанные
    curr_block = conn.getblockcount()
    from_block = from_block_in or xcurr.from_block
    print curr_block
    if type(curr_block) != type(1):
        # кошелек еще не запустился
        print 'not started else'
        return tab, from_block # если переиндексация то возможно что и меньше
    sumUnsp = None
    sumChange = None

    if from_block:
        if not curr_block > from_block:
            #print 'not curr_block > from_block', curr_block, from_block
            return tab, from_block # если переиндексация то возможно что и меньше
        #print curr_block, from_block
        confLast = curr_block - from_block - 1
        confMax = xcurr.conf + confLast
        #print curr.abbrev, 'confMax:', confMax
        l_Unsp = conn.listunspent(xcurr.conf, confMax)
        if type(l_Unsp) == type({}):
            # ошибка
            log(db, 'listunspent %s' % l_Unsp)
            return tab, None
        # теперь для вновь появившихся сгенерированных
        # они появлюяются в unspent через 120 подтверждений
        conf_gen = xcurr.conf_gen or 120
        if conf_gen < confMax:
            # если с подтверждения больше чем подт_генерации то сдвинем их
            conf_gen = confMax + 1
        l_generate = conn.listunspent( conf_gen, conf_gen + confLast)
        #if curr.abbrev=='BTC' and curr_block > 277423:
        #    log(db, 'curr_block %s \n conf_gen: %s .. %s =  l_generate \n %s' % (curr_block, conf_gen, conf_gen + confLast, l_generate))
        #lUnsp.update(l_generate)
        lUnsp = l_Unsp + l_generate

    else:
        # если нет еще номера обработанного блока
        # то и делать нечего - мол служба только запущена
        # на нее нет еще переводоов, хотя можно наоборот взять все входы
        xcurr.from_block = from_block = 1 # все входы со всеми подтверждениями берем
        xcurr.update_record()
        lUnsp = conn.listunspent(xcurr.conf)
        if type(lUnsp) == type({}):
            # ошибка
            log(db, 'listunspent %s' % Unsp)
            return tab, None

    for r in lUnsp:
        # выдает входящие транзакции причем те что не израсходовались
        # берем только подтвержденные нами и только входы - у них нет выходов в транзакции
        # иначе это сдача от выхода

        acc = r.get(u'account')
        if acc and acc == '.main.': continue # свои проводки не проверяем
            
        amo = r[u'amount']
        #print '\n\n',amo, r
        #continue

        txid = r[u'txid']
        ti = conn.gettransaction(txid)

        # тут массив - может быть несколько транзакций
        # может быть [u'category'] == u'receive' ИЛИ u'send'
        trans_details = ti['details']
        # так вот, в одной транзакции может быть несколько входов!
        # поэтому если есть выход - значит тут вход это сдача наша с вывода и такую
        # транзакцию пропускаем
        #if True or len(trans_details)>1:
        # оказывается и с 1м есть выход в деталях - сдачи может и не быть
        its_outcome = False
        for detail in trans_details:
            if detail[u'category'] == u'send':
                its_outcome = True
                # сдача тут
                break
        if its_outcome:
            #print 'its_outcome'
            sumChange = sumChange and sumChange + amo or amo
            continue

        amo = r[u'amount']
        vout = r[u'vout']
        addr = r.get(u'address')
        if not addr:
            # если адреса нет то берем его из рав-транзакции
            rawtr = conn.getrawtransaction(txid, 1)
            vouts = rawtr[u'vout']
            trans = vouts[vout]
            #print trans
            addr = trans[u'scriptPubKey'][u'addresses'][0]

        if addr_in and addr_in != addr: continue
        if not acc:
            acc = conn.getaccount(addr)
        #print acc, addr
        #print amo, txid, vout

        sumUnsp = sumUnsp and sumUnsp + amo or amo
        tab.append({'acc': acc, 'amo': amo,
            'confs': r[u'confirmations'],
            # запомним данные для поиска потом
            'txid':txid, 'vout': vout,
            'addr': addr,
            'time':ti[u'time']})

    sumUnsp = sumUnsp or 0
    sumChange = sumChange or 0
    sumFull = sumUnsp + sumChange
    #print '\n\nsumUnsp:',sumUnsp, '  sumChange:',sumChange, ' SUM:',sumFull
    return tab, curr_block

def send_back(conn, curr, xcurr, txid, amount, to_addr=None):
    # такой платеж возвращаем
    sender_addr = to_addr or crypto_client.sender_addr(conn, txid)
    print 'return to sender_addr:', sender_addr
    if not sender_addr: return
    amo = round(float (amount - xcurr.txfee * 2), 8)
    if amo > 0:
        print 'send_back:', curr.abbrev, amo, sender_addr
        txid = conn.sendtoaddress(sender_addr, amo )
        try:
            # может быть ошибка прри конвертации в ASCII
            print txid
        except:
            pass
        return txid
    else:
        return 'so small to return - wipe'
    return

def return_refused(db, curr, xcurr, conn):
    # возвраты
    for r in db((db.pay_ins_stack.ref_ == db.pay_ins.id)
                 & (db.pay_ins.ref_ == db.deal_acc_addrs.id)
                 & (db.deal_acc_addrs.xcurr_id == xcurr.id)
                 ).select():
        #print r
        ##STATUS_REFUSED = {'technical_error', 'payment_refused', 'currency_unused', 'refuse'}
        ##if r.pay_ins.status in db_common.STATUS_REFUSED or r.pay_ins_stack.to_refuse:
        if r.pay_ins.status == 'refuse' or r.pay_ins_stack.to_refuse:
            # такой платеж возвращаем
            # причем если адрес возврата уже задан в записи то возьмем его
            if True:
                txid = send_back(conn, curr, xcurr,  r.pay_ins.txid,
                     r.pay_ins.amount, r.deal_acc_addrs.addr_return)
            else:
                txid='probe1'
            #print txid
            to_delete_from_stack = True # удалить из стека чтобы 2 раза не отправлять
            if txid and type({}) == type(txid):
                # {u'id': 1, u'result': None, u'error': {u'message': u'Insufficient funds', u'code': -6}}
                err = txid.get('error')
                print "return_refused - err.get('error'):", err
                if err and err[u'code'] == -6:
                    # не хватает монет - ничего не делаем
                    print "to_delete_from_stack=False - Insufficient funds', u'code': -6"
                    to_delete_from_stack = False
                    r.pay_ins.status = 'wait return'
                    r.pay_ins.status_mess = 'Insufficient funds'
            else:
                try:
                    # из-за ошибки конвертации в ASCII 
                    # 'ascii' codec can't decode byte 0xd0 in position 17: ordinal not in range(128)
                    r.pay_ins.status = 'returned'
                    if r.pay_ins.status_mess:
                        ##status_mess = r.pay_ins.status_mess + '. txid: %s' % txid
                        status_mess = 'txid: %s' % txid
                    else:
                        status_mess = 'txid: %s' % txid
                    r.pay_ins.status_mess = status_mess
                except:
                    r.pay_ins.status = 'returned'
                    r.pay_ins.status_mess = 'txid: %s' % txid

            if to_delete_from_stack:
                # если нет вообще отк ошелькка связи то удалим - так как там походу что-то не то
                print 'try del pay_ins_stack[%s]: txid= %s' % (r.pay_ins_stack.id, txid)
                del db.pay_ins_stack[r.pay_ins_stack.id]
            r.pay_ins.update_record()
            db.commit()


import serv_to_pay
import serv_to_buy
import clients_lib
def run_once(db, abbrev):
    ss = ''
    curr, xcurr, e = db_common.get_currs_by_abbrev(db, abbrev)
    if not xcurr:
        mess = "ERROR:" + abbrev + " in db.xcurrs not exist"
        ss = ss + '%s<br>' % mess
        print mess
        return ss
    tab = e = conn = None
    
    token_system = None
    token_key = xcurr.as_token #
    if token_key:
        token = db.tokens[token_key]
        token_system = db.systems[token.system_id]

        erachain_addr = token_system.account
        erachain_rpc = token_system.connect_url

        addr_in= None #'4V6CeFxAHGVTM5wYKhAbXwbXsjUW5Bazdh'
        from_block_in = 68600
        tab, curr_block = get_incomed(db, erachain_rpc, erachain_addr, curr, xcurr, addr_in, from_block_in)
        print 'tab:   ',tab
        ##return
        b_p_db_update(db, None, curr, xcurr, tab, curr_block)
        # баланс берем по обработанным только блокам
        ###balance = crypto_client.get_reserve(curr, xcurr, conn) #conn.getbalance()
        balances = rpc_erachain.get_balances(erachain_rpc, erachain_addr)
        if type(balances) == type([]):
            for token_rec in db(db.tokens.system_id == token_system.id).select():
                print token_rec.token_key
                balance = balances[token_rec.token_key][0][1]
                token_xcurr = db(db.xcurrs.as_token == token_rec.id).seletc().first()
                token_curr = db.currs[token_xcurr.curr_id]
                token_curr.balance = balance
                print token_curr.balance
                token_curr.update_record()
        else:
            print balances
        # после обработки блока сразу входы крипты обработаем
        # так как вых платеж может произойти тут надо сохранить
        db.commit()
        pass
    else:
        conn = crypto_client.conn(curr, xcurr)
        if conn:
            #try:
            if True:
                addr_in= None #'4V6CeFxAHGVTM5wYKhAbXwbXsjUW5Bazdh'
                from_block_in = None #65111
                tab, curr_block = b_p_proc_unspent(db, conn, curr, xcurr, addr_in, from_block_in)
                #print 'tab:   ',tab
                #return
                b_p_db_update(db, conn, curr, xcurr, tab, curr_block)
                # баланс берем по обработанным только блокам
                balance = crypto_client.get_reserve(curr, xcurr, conn) #conn.getbalance()
                curr.balance = balance
                curr.update_record()
                # после обработки блока сразу входы крипты обработаем
                # так как вых платеж может произойти тут надо сохранить
                db.commit()
            else:
            #except Exception as e:
                db.rollback()
                mess = 'b_p_proc_unspent ERROR: %s' % e
                ss = ss + '%s<br>' % mess
                log_commit(db, mess)
        else:
            mess = curr.name + " no connection to wallet"
            ss = ss + '%s<br>' % mess
            print mess

    #return

    ''' ВНИМАНИЕ!! если внутри ошибка произойдет то
    запись стека будет помечена номером процесса и по второму разу не будет обработана
    Тоесть если выплата на ЯДеньги уже прошла а потом ошибка случилась
    то из стека она не уберетс
    поэтому если в СТЕКЕ есть записи с номерами процесса - скорее всего они уже оплатились рублями!!!
    Тут можно убирать TRY - это на запись номера процесса не влияет
    '''
    ### надо TRY врубать чтобы ошибка от коннекта к кошелькам не сыпалась и не обрубала проход по всем валютам
    #try:
    if True:
        # оплатить входы крипты фиатом
        serv_to_pay.proc_xcurr(db, curr, xcurr)
        db.commit()
    #except Exception as e:
    else:
        db.rollback()
        mess = 'serv_to_pay.proc_xcurr: %s' % e
        ss = ss + '%s<br>' % mess
        log_commit(db, mess)

    if conn:
        try:
        #if True:
            # если есть отвергнутиые платежи то вернем их
            return_refused(db, curr, xcurr, conn)
            db.commit()
        except Exception as e:
            db.rollback()
            mess = 'return_refused: %s' % e
            ss = ss + '%s<br>' % mess
            log_commit(db, mess)

        if True: # не важно есть входы или нет - там может стек невыплоченных быть or tab and len(tab)>0:
            # если есть приход фиата то попробовать продать крипту - может там не хватило баланса
            #try:
            if True:
                serv_to_buy.proc_ecurr(db, curr, xcurr, conn)
                db.commit()
            else:
            #except Exception as e:
                db.rollback()
                mess = 'serv_to_buy.proc_ecurr: %s' % e
                ss = ss + '%s<br>' % mess
                log_commit(db, mess)

        try:
            # если есть транзакции не включенные еще в блок
            crypto_client.re_broadcast (db, curr, xcurr, conn)
            db.commit()
        except Exception as e:
            db.rollback()
            mess = 're_broadcast: %s' % e
            ss = ss + '%s<br>' % mess
            log_commit(db, mess)

    # если
    try:
        clients_lib.notify(db)
        db.commit()
    except Exception as e:
        db.rollback()
        mess =  'clients_lib.notify: %s' % e
        ss = ss + '%s<br>' % mess
        log_commit(db, mess)

    if len(ss)==0: ss='OK'
    return ss
