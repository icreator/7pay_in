#!/usr/bin/env python
# coding: utf8

if False:
    from gluon import *
    import db

    request = current.request
    response = current.response
    session = current.session
    cache = current.cache
    T = current.T

# from __future__ import print_function

from db_common import get_currs_by_addr
import datetime
from decimal import Decimal
import decimal
import db_common
import crypto_client

# TODO
# если валюта отключена и произошел возврат то баланс не изменяетс!!!

from gluon import current

T = current.T

TO_COIN_ID = 2


#        if r.pay_ins.status in {'technical_error', 'payment_refused', 'currency_unused'}:

#
# на самом деле это не сервер - он не висит постоянно в памяти и не выполняется параллельно
# просто при приходе блока вызывчается curl со ссылкой на страницу проекта
# start /MIN curl http://127.0.0.1:8000/ipay3/tools/block_proc/%1/%2 -s >nul
# see !notify-curl.cmd in C:\web2py\applications\ipay4\wallets
# see bitcoin.conf and !notify.cmd in ./bitcoin

def log(db, mess):
    mess = 'BLK: %s' % mess
    print mess
    db.logs.insert(mess=mess)


def log_commit(db, mess):
    log(db, mess)
    db.commit()


# запуск пробный из тулсов:
#  /tools/block_proc/CLR
def b_p_db_update(db, conn, curr, xcurr, token_system, token, tab, curr_block):
    # сюда приходят все одиночные входы
    # поидее надо их всех запомнить

    for rec in tab:  # .iteritems():
        amount = rec['amount']
        acc = rec['acc']
        recipient = rec['recipient']
        txid = rec['txid']
        vout = rec['vout']
        time = rec['timestamp']
        block = rec['block']
        confs = rec['confs']

        # if len(acc)==0:
        #    # пропустим пустые а то они все будут подходить
        #    continue

        if xcurr.main_addr and xcurr.main_addr == acc:
            # пропустим поступления на наш счет - например пополнение оборотных средств
            continue

        try:
            # for cyrilic - error
            print curr.abbrev, 'b_p_db_update - acc:"%s"' % acc, ' unspent:', amount, 'txid:', txid, 'vout:', vout
        except:
            print curr.abbrev, 'b_p_db_update', recipient, ' unspent:', amount, 'txid:', txid, 'vout:', vout
        # print datetime.datetime.fromtimestamp(rec['time'])
        # print rec, '\n'
        if token_system:
            ## ASSET_KEY income > ASSET_KEY outcome : ADDRESS
            acc_tab = acc.split('>')
            if len(acc_tab) < 2:
                log(db, curr.abbrev + ' AS TOKEN not found on SPLIT ' + acc)
                continue

            token_key_in = acc_tab[0]
            # INCOMED CURR - replace with CALCULATED
            xcurr = crypto_client.get_xcurr_by_system_token(db, token_system, token_key_in)
            curr = xcurr and db.currs[xcurr.curr_id]
            if not curr:
                log(db, curr.abbrev + ' income xCURR not found ' + acc)
                continue

            # print curr.abbrev, 'curr_in for SYSTEM: ', token_system.name

            out_tab = acc_tab[1].split(':')
            if len(out_tab) < 2:
                log(db, curr.abbrev  + ' AS TOKEN not found out_tab ' + acc)
                continue

            token_out = out_tab[0]
            recipient = out_tab[1]

            xcurr_out = crypto_client.get_xcurr_by_system_token(db, token_system, token_out)
            if not xcurr_out:
                log(db, curr.abbrev  + ' outcome xCURR not found ' + acc)
                continue

            curr_out = db.currs[xcurr_out.curr_id]
            if not curr_out:
                log(db, curr.abbrev + ' AS TOKEN not found curr_out ' + acc)
                continue

            # print curr.abbrev, 'as TOKEN curr_out: ', curr_out.abbrev

            deal_acc = db((db.deal_accs.acc == recipient)
                          & (db.deal_accs.curr_id == curr_out.id)).select().first()
            if not deal_acc:
                # print 'make deal_acc'
                deal_acc_id = db.deal_accs.insert(deal_id=TO_COIN_ID, acc=recipient, curr_id=curr_out.id)
                deal_acc_addr_id = db.deal_acc_addrs.insert(deal_acc_id=deal_acc_id, addr=token_system.account,
                                                            xcurr_id=xcurr.id)
                deal_acc_addr = db.deal_acc_addrs[deal_acc_addr_id]
            else:
                deal_acc_addr = db((db.deal_acc_addrs.deal_acc_id == deal_acc.id)
                                   & (db.deal_acc_addrs.xcurr_id == xcurr.id)).select().first()
                if not deal_acc_addr:
                    # print 'make deal_acc_addr'
                    deal_acc_addr_id = db.deal_acc_addrs.insert(deal_acc_id=deal_acc.id, addr=token_system.account,
                                                                xcurr_id=xcurr.id)
                    deal_acc_addr = db.deal_acc_addrs[deal_acc_addr_id]
                else:
                    deal_acc_addr_id = deal_acc_addr.id


        else:
            deal_acc_addr = db((db.deal_acc_addrs.addr == recipient)
                               & (db.deal_acc_addrs.xcurr_id == xcurr.id)).select().first()

            # TODO
            if not deal_acc_addr:
                # такой адрес не в наших счетах
                if conn:
                    print 'unknown [%s] address %s for account:"%s"' % (curr.abbrev, recipient, acc)
                    # если не найдено в делах то запомним в неизвестных
                    if False:
                        send_back(db, conn, token_system, curr, xcurr, txid, amount)
                    print curr.abbrev, 'skip? to return -> txid', txid
                    continue
                else:
                    print curr.abbrev, 'UNKNOWN deal:', rec
                    continue

        # теперь в таблице от unspent без повторов - так как там блок каждый раз новый
        if token_system:
            ## NOT use VOUT
            trans = db(db.pay_ins.txid == txid).select().first()
        else:
            trans = db((db.pay_ins.txid == txid) & (db.pay_ins.vout == vout)).select().first()
        if trans:
            # уже такая есть
            print curr.abbrev, 'txid+vout exist:', txid, vout
            continue

        if not token_system and deal_acc_addr:
            addr_ret = deal_acc_addr.addr_return
            if deal_acc_addr.unused and conn and addr_ret:
                # переводы на этоот адрес запрещены - тоже вернем его
                print 'UNUSED [%s] address %s for account:"%s"' % (curr.abbrev, recipient, acc)
                # если не найдено в делах то запомним в неизвестных
                send_back(db, conn, token_system, curr, xcurr, txid, amount, addr_ret)
                print curr.abbrev, 'to return -> txid', txid
                continue

        created_on = datetime.datetime.fromtimestamp(time)

        pay_id = db.pay_ins.insert(ref_=deal_acc_addr.id,
                                   amount=amount, block=block,
                                   txid=txid, vout=vout,
                                   created_on=created_on
                                   )
        # print rec['time']
        # закатаем записи в стек чтобы быстро разообрать платежи по ордерам
        db.pay_ins_stack.insert(ref_=pay_id)

        # запомним сумму свободных монет на данном счету
        # потом именно столько можно перевести на главный счет
        incomed = deal_acc_addr.incomed
        if incomed:
            deal_acc_addr.incomed = incomed + amount
        else:
            deal_acc_addr.incomed = amount
        deal_acc_addr.update_record()

    # так как мы в фреймворке - тут само сохраняет db.commit()
    pass

    # сохраним теперь инфо что эти блоки обработали
    if token_system:

        tokens_balances = crypto_client.get_assets_balances(xcurr, token_system)

        ##return '%s' % balances

        for token_rec in db(db.tokens.system_id == token_system.id).select():
            token_xcurr = db(db.xcurrs.as_token == token_rec.id).select().first()
            # print token_rec
            token_key = '%d' % token_rec.token_key
            if type(tokens_balances) == type({}) and token_key in tokens_balances:
                balance = tokens_balances.get(token_key)
                if balance:
                    balance = Decimal(balance[0][1])
            else:
                balance = Decimal(0)

            token_curr = db.currs[token_xcurr.curr_id]
            token_curr.balance = balance
            ### decimal.getcontext().prec = int(db.currs.balance.type.split(',')[1][:-1])
            token_curr.update_record()

            token_xcurr.from_block = curr_block
            token_xcurr.update_record()

        token_system.from_block = curr_block
        token_system.update_record()
    else:
        # баланс берем по обработанным только блокам
        balance = crypto_client.get_balance_xcurr(curr, xcurr, conn)  # conn.getbalance()
        curr.balance = balance
        curr.update_record()
        xcurr.from_block = curr_block
        xcurr.update_record()

    # после обработки блока сразу входы крипты обработаем
    # так как вых платеж может произойти тут надо сохранить
    db.commit()


def parse_line(db, mess, creator):
    if not mess:
        return None

    args = mess.split(':')
    # print 'parse_line:', mess, args

    arg1 = args[0].strip()
    if len(arg1) < 20:
        # as ABBREV
        curr_out, xcurr_out, _ = db_common.get_currs_by_abbrev(db, arg1)
        if xcurr_out:
            if len(args) > 1:
                addr = args[1].strip()
                if addr[0] == '[':
                    addr = addr[1:]
                if addr[-1] == ']':
                    addr = addr[:-1]
                return curr_out.abbrev + ':' + addr
            else:
                return curr_out.abbrev + ':' + creator

    # may be here only ADDRESS
    if len(arg1) > 30:
        curr_out, xcurr_out, _ = get_currs_by_addr(db, arg1)
        if xcurr_out:
            return curr_out.abbrev + ':' + arg1

    try:
        int(arg1)  ## is INTEGER?
        if len(args) > 1:
            addr = args[1].strip()
            if addr[0] == '[':
                addr = addr[1:]
            if addr[-1] == ']':
                addr = addr[:-1]
            return arg1 + ':' + addr
        else:
            return arg1 + ':' + creator
    except:
        pass


def make_rec(acc, rec, transactions):
    if not acc:
        acc = 'refuse:' + rec['creator']
    else:
        acc = ('%d' % rec['asset']) + '>' + acc

    rec['acc'] = acc

    transactions.append(rec)


### parse commands:
# add: SIGNATURE1 SIGNATURE2 ... - add that TX to payment
def parse_mess(acc, lines, xcurr, token_system, rec, transactions):
    if not lines:
        return

    for line in lines:
        try:
            command = line.split(':')
            if len(command) > 1:
                if command[0].strip().lower() == 'add':
                    ## ADD transactions without payments details to that payment
                    ## need
                    for txid in command[1].strip().split(' '):
                        txid = txid.strip()
                        if not txid:
                            continue

                        # see this TX in DB and set DETAILS
                        pay_in = db(db.pay_ins.txid == txid).select().first()
                        if pay_in:
                            # already assigned
                            continue

                        recAdded = crypto_client.get_tx_info(xcurr, token_system, txid)
                        recAdded = crypto_client.parse_tx_fields(xcurr, token_system, recAdded)

                        if not recAdded or 'creator' not in recAdded or recAdded['creator'] != rec['creator']:
                            # set payment details only for this creator records
                            continue

                        # make record INCOME from Erachain TRANSACTION
                        make_rec(acc, recAdded, transactions)

        except Exception as e:
            mess = 'COMMAND: %s - %s' % (line, e)
            log(db, mess)


def get_incomed(db, curr, xcurr, token_system, from_block_in=None):
    tab = []
    chain_height = crypto_client.get_height(xcurr, token_system)
    print curr.name, 'chain_height:', chain_height
    if type(1) != type(chain_height):
        # кошелек еще не запустился
        print curr.name, 'not started else'
        return tab, from_block_in

    from_block = from_block_in or token_system and token_system.from_block or xcurr.from_block
    if from_block:
        if not chain_height > from_block:
            print curr.name, 'not chain_height > from_block', chain_height, from_block, 'return []'
            return tab, from_block  # если переиндексация то возможно что и меньше
        print curr.name, from_block, '-->', chain_height
        tab, chain_height = crypto_client.get_transactions(xcurr, token_system, from_block)

        if chain_height is None:
            return [], None

    else:
        # если нет еще номера обработанного блока
        # то и делать нечего - мол служба только запущена
        # на нее нет еще переводоов, хотя можно наоборот взять все входы
        if token_system:
            token_system.from_block = from_block = 1  # все входы со всеми подтверждениями берем
            token_system.update_record()
        else:
            xcurr.from_block = from_block = 1  # все входы со всеми подтверждениями берем
            xcurr.update_record()

        tab, chain_height = crypto_client.get_transactions(xcurr, token_system, from_block)

        if chain_height is None:
            return [], None

    print curr.name, chain_height, '\n', tab

    transactions = []
    for rec in tab:

        rec = crypto_client.parse_tx_fields(xcurr, token_system, rec)
        # print 'after parse_tx_fields: ', rec

        message = rec.get('message')
        if not message:
            continue

        lines = message.strip().split('\n')

        acc = parse_line(db, lines[0].strip(), rec.get('creator'))
        if not acc:
            continue

        # make record INCOME from Erachain TRANSACTION
        make_rec(acc, rec, transactions)

        if len(lines) > 1:
            parse_mess(acc, lines[1:], xcurr, token_system, rec, transactions)

    return transactions, chain_height


# найдем все входы одиночные
# на выходе массив по входам
def b_p_proc_unspent(db, conn, curr, xcurr, addr_in=None, from_block_in=None):
    # проверим непотраченные монеты на адресах,
    # которые созданы для приема крипты
    #
    # тут ограничиваем просмотр входящих неизрасходованных
    # транзакций по подтверждениям с учетом номера обработанного блока
    #
    tab = []
    # макс подтв так чтобы не брать уже обработанные
    chain_height = conn.getblockcount()
    from_block = from_block_in or xcurr.from_block
    print curr.name, 'chain_height:', chain_height
    if type(1) != type(chain_height):
        # кошелек еще не запустился
        print curr.name, 'not started else'
        return tab, from_block  # если переиндексация то возможно что и меньше
    sumUnsp = None
    sumChange = None

    if from_block:
        if not chain_height > from_block:
            print curr.name, 'not chain_height > from_block', chain_height, from_block
            return tab, from_block  # если переиндексация то возможно что и меньше
        print curr.name, chain_height, from_block
        confLast = chain_height - from_block - 1
        confMax = xcurr.conf + confLast
        # print curr.name, 'confMax:', confMax
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
        l_generate = conn.listunspent(conf_gen, conf_gen + confLast)
        # if curr.abbrev=='BTC' and chain_height > 277423:
        #    log(db, 'chain_height %s \n conf_gen: %s .. %s =  l_generate \n %s' % (chain_height, conf_gen, conf_gen + confLast, l_generate))
        # lUnsp.update(l_generate)
        lUnsp = l_Unsp + l_generate

    else:
        # если нет еще номера обработанного блока
        # то и делать нечего - мол служба только запущена
        # на нее нет еще переводоов, хотя можно наоборот взять все входы
        xcurr.from_block = from_block = 1  # все входы со всеми подтверждениями берем
        xcurr.update_record()
        lUnsp = conn.listunspent(xcurr.conf)
        if type(lUnsp) == type({}):
            # ошибка
            log(db, 'listunspent %s' % lUnsp)
            return tab, None

    for r in lUnsp:
        # выдает входящие транзакции причем те что не израсходовались
        # берем только подтвержденные нами и только входы - у них нет выходов в транзакции
        # иначе это сдача от выхода

        acc = r.get(u'account')
        if acc and xcurr.main_addr and xcurr.main_addr == acc:
            # свои проводки не проверяем
            continue

        amount = r[u'amount']
        # print curr.name, '\n\n',amount, r
        # continue

        txid = r[u'txid']
        ti = conn.gettransaction(txid)

        # тут массив - может быть несколько транзакций
        # может быть [u'category'] == u'receive' ИЛИ u'send'
        trans_details = ti['details']
        # так вот, в одной транзакции может быть несколько входов!
        # поэтому если есть выход - значит тут вход это сдача наша с вывода и такую
        # транзакцию пропускаем
        # if True or len(trans_details)>1:
        # оказывается и с 1м есть выход в деталях - сдачи может и не быть
        its_outcome = False
        for detail in trans_details:
            if detail[u'category'] == u'send':
                its_outcome = True
                # сдача тут
                break
        if its_outcome:
            # print curr.name, 'its_outcome'
            sumChange = sumChange and sumChange + amount or amount
            continue

        amount = r[u'amount']
        vout = r[u'vout']
        recipient = r.get(u'address')
        if not recipient:
            # если адреса нет то берем его из рав-транзакции
            rawtr = conn.getrawtransaction(txid, 1)
            vouts = rawtr[u'vout']
            trans = vouts[vout]
            # print curr.name, trans
            recipient = trans[u'scriptPubKey'][u'addresses'][0]

        if addr_in and addr_in != recipient:
            continue
        if not acc:
            acc = conn.getaccount(recipient)
        # print curr.name, acc, addr
        # print curr.name, amount, txid, vout

        sumUnsp = sumUnsp and sumUnsp + amount or amount
        tab.append({'acc': acc, 'amount': Decimal(amount),
                    'block': chain_height,
                    'confs': r[u'confirmations'],
                    # запомним данные для поиска потом
                    'txid': txid, 'vout': vout,
                    'recipient': recipient,
                    'timestamp': ti[u'time']})

    sumUnsp = sumUnsp or 0
    sumChange = sumChange or 0
    sumFull = sumUnsp + sumChange
    # print curr.name, '\n\nsumUnsp:',sumUnsp, '  sumChange:',sumChange, ' SUM:',sumFull
    return tab, chain_height


def send_back(db, conn, token_system, curr, xcurr, txid, amount, to_addr=None):
    # такой платеж возвращаем
    if True:
        return 'backWard denied by service'

    sender_addr = to_addr or crypto_client.sender_addr(xcurr, token_system, txid, conn)
    print curr.name, 'return to sender_addr:', sender_addr
    if not sender_addr: return
    amo = round(float(amount - xcurr.txfee * 2), 8)
    if amo > 0:

        print curr.name, 'send_back:', amo, sender_addr
        if True:
            res, bal = crypto_client.send(db, curr, xcurr, sender_addr, amo)
            log(db, 'send_back - res: %s' % res)
            if bal:
                curr.update_record(balance=bal)
            if type(res) == type(u' '):
                # прошла транзакция, создадим массив инфо
                return res
        else:
            txid = conn.sendtoaddress(sender_addr, amo)
            try:
                # может быть ошибка при конвертации ASCII
                print curr.name, txid
            except:
                pass
            return txid

        txid = conn.sendtoaddress(sender_addr, amo)
        try:
            # может быть ошибка прри конвертации в ASCII
            print curr.name, txid
        except:
            pass
        return txid
    else:
        return 'so small to return - wipe'
    return


def return_refused(db, curr, xcurr, conn, token_system):
    # возвраты
    for r in db((db.pay_ins_stack.ref_ == db.pay_ins.id)
                & (db.pay_ins.ref_ == db.deal_acc_addrs.id)
                & (db.deal_acc_addrs.xcurr_id == xcurr.id)
                ).select():
        # print curr.name, r
        ##STATUS_REFUSED = {'technical_error', 'payment_refused', 'currency_unused', 'refuse'}
        ##if r.pay_ins.status in db_common.STATUS_REFUSED or r.pay_ins_stack.to_refuse:
        if r.pay_ins.status == 'refuse' or r.pay_ins_stack.to_refuse:
            # такой платеж возвращаем
            # причем если адрес возврата уже задан в записи то возьмем его
            if True:
                txid = send_back(db, conn, token_system, curr, xcurr, r.pay_ins.txid,
                                 r.pay_ins.amount, r.deal_acc_addrs.addr_return)
            else:
                txid = 'probe1'
            # print curr.name, txid
            to_delete_from_stack = True  # удалить из стека чтобы 2 раза не отправлять
            if txid and type({}) == type(txid):
                # {u'id': 1, u'result': None, u'error': {u'message': u'Insufficient funds', u'code': -6}}
                err = txid.get('error')
                print curr.name, "return_refused - err.get('error'):", err
                if err and err[u'code'] == -6:
                    # не хватает монет - ничего не делаем
                    print curr.name, "to_delete_from_stack=False - Insufficient funds', u'code': -6"
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
                print curr.name, 'try del pay_ins_stack[%s]: txid= %s' % (r.pay_ins_stack.id, txid)
                del db.pay_ins_stack[r.pay_ins_stack.id]
            r.pay_ins.update_record()
            db.commit()


import serv_to_pay
import serv_to_buy
import clients_lib


def run_once(db, abbrev, from_block_in=0):
    ss = ''
    curr, xcurr, e = db_common.get_currs_by_abbrev(db, abbrev)
    if not xcurr:
        mess = "ERROR:" + abbrev + " in db.xcurrs not exist"
        ss = ss + '%s<br>' % mess
        print mess
        return ss

    conn = None

    token_key = xcurr.as_token
    token = token_key and db.tokens[token_key]
    token_system = token and db.systems[token.system_id]

    if token_system:

        tab, curr_block = get_incomed(db, curr, xcurr, token_system, from_block_in)

        if curr_block == None:
            return 'connection lost'

        b_p_db_update(db, None, curr, xcurr, token_system, token, tab, curr_block)

    else:
        conn = crypto_client.connect(curr, xcurr)
        if conn:
            # try:
            if True:
                addr_in = None  # '4V6CeFxAHGVTM5wYKhAbXwbXsjUW5Bazdh'
                tab, curr_block = b_p_proc_unspent(db, conn, curr, xcurr, addr_in, from_block_in)
                # print curr.name, 'tab:   ',tab
                # return
                b_p_db_update(db, conn, curr, xcurr, token_system, token, tab, curr_block)
            else:
                # except Exception as e:
                db.rollback()
                mess = 'b_p_proc_unspent ERROR: %s' % e
                ss = ss + '%s<br>' % mess
                log_commit(db, mess)
        else:
            mess = curr.name + " no connection to wallet"
            ss = ss + '%s<br>' % mess
            print curr.name, mess

    # return

    ''' ВНИМАНИЕ!! если внутри ошибка произойдет то
    запись стека будет помечена номером процесса и по второму разу не будет обработана
    Тоесть если выплата на ЯДеньги уже прошла а потом ошибка случилась
    то из стека она не уберетс
    поэтому если в СТЕКЕ есть записи с номерами процесса - скорее всего они уже оплатились рублями!!!
    Тут можно убирать TRY - это на запись номера процесса не влияет
    '''
    ### надо TRY врубать чтобы ошибка от коннекта к кошелькам не сыпалась и не обрубала проход по всем валютам
    # try:
    if True:
        # запускаем обработку выплат
        if token_system:
            for token_rec in db(db.tokens.system_id == token_system.id).select():
                token_xcurr = db(db.xcurrs.as_token == token_rec.id).select().first()
                token_curr = db.currs[token_xcurr.curr_id]
                serv_to_pay.proc_xcurr(db, token_curr, token_xcurr)
                return_refused(db, token_curr, token_xcurr, conn, token_system)
                db.commit()
        else:
            serv_to_pay.proc_xcurr(db, curr, xcurr)
            db.commit()
    # except Exception as e:
    else:
        db.rollback()
        mess = 'serv_to_pay.proc_xcurr: %s' % e
        ss = ss + '%s<br>' % mess
        log_commit(db, mess)

    if conn or token_system:
        try:
            # if True:
            # если есть отвергнутиые платежи то вернем их
            return_refused(db, curr, xcurr, conn, token_system)
            db.commit()
        except Exception as e:
            db.rollback()
            mess = 'return_refused: %s' % e
            ss = ss + '%s<br>' % mess
            log_commit(db, mess)

        if True:  # не важно есть входы или нет - там может стек невыплоченных быть or tab and len(tab)>0:
            # если есть приход фиата то попробовать продать крипту - может там не хватило баланса
            # try:
            if True:
                serv_to_buy.proc_ecurr(db, curr, xcurr, conn)
                db.commit()
            else:
                # except Exception as e:
                db.rollback()
                mess = 'serv_to_buy.proc_ecurr: %s' % e
                ss = ss + '%s<br>' % mess
                log_commit(db, mess)

        try:
            # если есть транзакции не включенные еще в блок
            crypto_client.re_broadcast(db, curr, xcurr, token_system, conn)
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
        mess = 'clients_lib.notify: %s' % e
        ss = ss + '%s<br>' % mess
        log_commit(db, mess)

    if len(ss) == 0: ss = 'OK'
    return ss
