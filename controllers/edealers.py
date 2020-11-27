# coding: utf8
import socket
from decimal import Decimal

# vvv=True - включает секртную сессию и выдает страницу ошибки
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

    if (remote_addr not in hosts) and (remote_addr != "127.0.0.1"):
        #and request.function != 'manage':
        if vvv: raise HTTP(404, T('ERROR 0432'))
        return True
    
import json
import ed_YD
import serv_to_buy

def log(mess):
    print mess
    db.logs.insert(mess='BUY: %s' % mess)
    db.commit()


# edealers/list_twiced/2905 - from id
# по id: 2905 - 26634.00 в пролете у меня
### для того чтобы добавить утраты в базу покупателей - rewrite_credits = True
def buys_twiced():
    not_is_local(True)
    # всегда с обновлением в базу так как то что уже возвращено не сбрасывается тут
    rewrite_credits = False
    if rewrite_credits:
        for r in db(db.buyers_credit).select():
            if r.un_rewrite: continue
            r.update_record(credit=0)
    
    start_id = request.args(0) or 0
    h = CAT()
    i = 0
    amo_full = amo_gain = amo_lose = Decimal(0)
    # все что уже были оплачены
    buyers = {}
    checked = []
    for r in db(db.buys.id > start_id).select():
        if r.id in checked:
            # уже обработали ее
            continue
        amo_full += r.amount
        # ищем дуплированные
        r_rs = db((db.buys.operation_id == r.operation_id)
                 & (db.buys.buyer == r.buyer)
                 & (db.buys.id != r.id)
                    ).select()
        if not r_rs: continue

        checked.append(r.id)
        if r.status != 'OK':
            h += H5(' STATUS: %s' % r.status)
        print r.id, r.amount, 'status:', r.status
        i += 1
        r.tax_mess=''
        h += DIV(H3(B('#%s status: %s %s' % (r.id, r.status, r.created_on))), B('%s' % r))
        for r_r in r_rs:
            checked.append(r_r.id)
            amo = r_r.amount
            if r_r.status != 'OK':
                h += DIV(H3('!!!!! rec.id: ', r_r.id, ' !!!!!!'))
            buyers[r_r.buyer] = buyers.get(r_r.buyer, Decimal(0)) + amo
            h += DIV('%s: %s - %s' % (r_r.status, amo, r_r.txid))
            amo_lose += amo
        #if i > 5: break

    if rewrite_credits:
        h += H3('list of payers')
        for p, amo in buyers.iteritems():
            h += DIV(p, ': ', amo)
            buyers_credit = db(db.buyers_credit.acc == p).select().first()
            if buyers_credit.un_rewrite: continue
            if buyers_credit:
                buyers_credit.update_record(credit = buyers_credit.credit + amo)
            else:
                db.buyers_credit.insert(acc = p, credit = amo)

    for bc in db(db.buyers_credit).select():
        amo_gain += bc.accepted
        
    return dict(h = DIV(H3("всего: ",amo_full,", потеряно: ",amo_lose,
                           ", взвращено:", amo_gain,
                   ", доля утаты - возврата: ",round( float((amo_lose-amo_gain)/amo_full)*100.0, 2)), h, _class='container'))


# edealers/list_twiced/23 - from id
# поиск двойных выплат на один вход крипты - по txid
def pay_outs_twiced():
    not_is_local(True)
    start_id = request.args(0) or 0
    h = CAT()
    i = 0
    for r in db(db.pay_outs.id > start_id).select():
        # ищем дуплированные
        r_rs = db((db.pay_outs.txid == r.txid)
                 & (db.pay_outs.id != r.id)
                    ).select()
        if r_rs:
            print r
            i += 1
            h += DIV(H3(B('%s' % r.id)), B('%s' % r))
            for r_r in r_rs:
                h += DIV('%s' % r_r)
            if i > 5: break

    return dict(h = DIV(h, _class='container'))

## 'in', '01.01.2014', '01.01.2016'
def qiwi_hist():
    if len(request.args) == 0:
        return 'use qiwi_hist/79169172019/in/01.01.2014/01.01.2016'
    ecurr = db.ecurrs[2]
    dealer = db(db.dealers.name == 'QIWI' ).select().first()
    if not dealer.used: return 'QIWI unusable'
    import ed_common
    acc = db((db.dealers_accs.acc==request.args(0))
             & (db.dealers_accs.dealer_id == dealer.id)).select().first()
    if not acc: return 'not that QIWI deal_acc'
    import ed_QIWI
    err, res = ed_QIWI.get_history(acc, request.args(1), request.args(2), request.args(3), TAG)
    if err:
        return dict( error=err, result = res)
    return DIV( res )


# qiwi_bal/79169172019
def qiwi_bal():
    if len(request.args) == 0:
        return 'use qiwi_bal/79169172019'
    ecurr = db.ecurrs[2]
    dealer = db(db.dealers.name == 'QIWI' ).select().first()
    if not dealer.used: return 'QIWI unusable'
    
    import ed_common
    acc = db((db.dealers_accs.acc==request.args(0))
             & (db.dealers_accs.dealer_id == dealer.id)).select().first()
    if not acc: return 'not that QIWI deal_acc'
    
    import ed_QIWI
    err, res = ed_QIWI.get_balance(acc, TAG)
    if err:
        return dict( error=err, result = res)
    return res

def qiwi_log():
    if len(request.args) == 0:
        return 'use qiwi_log/79169172019'
    ecurr = db.ecurrs[2]
    dealer = db(db.dealers.name == 'QIWI' ).select().first()
    if not dealer.used: return 'QIWI unusable'
    
    import ed_common
    #vol = 100.1
    #deal_acc = ed_common.sel_acc_max(db, dealer, ecurr, vol)
    acc = db((db.dealers_accs.acc==request.args(0))
             & (db.dealers_accs.dealer_id == dealer.id)).select().first()
    if not acc: return 'not is QIWI deal_acc'
    
    import ed_QIWI
    err, res = ed_QIWI.login(acc)
    if err:
        return dict( error=err, result = res)
    return res
