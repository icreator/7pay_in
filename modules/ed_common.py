# coding: utf8

#from datetime import datetime
from decimal import Decimal
from gluon import current
import datetime

'''
общие процедуры для работы с диллерами фиата
'''
import db_common
import db_client
import ed_YD

PAY_LIM = 3777 # стандартное оограничение на один платеж
DAY_LIM_A = 3777
DAY_LIM_P = 33777
MON_LIM_A = 8777
MON_LIM_P = 73777

PAY_PARS = [{ "n": "id", "l": current.T("Идентификатор заказа или клиента:") }]
#[{"l": "номер заказа или клиента", "n": "order"}]
'''
PAY_PARS_P2P = [{ "n": "user", "l": "Код пользователя:"},
    { "n": "order", "l": "Код услуги, заказа:"}
    ]
'''
PAY_PARS_P2P = PAY_PARS

def log(db, mess):
    mess = 'EDc: %s' % mess
    print mess
    db.logs.insert(mess=mess)
def log_commit(db, mess):
    log(db,mess)
    db.commit()

#  закатать ошибку в базу
def dealer_deal_errs_add(db, dealer_deal, acc, err_mess):
    dealer_deal_err = db((db.dealer_deal_errs.dealer_deal_id == dealer_deal.id)
                 & (db.dealer_deal_errs.acc == acc)).select().first()
    if dealer_deal_err:
        dealer_deal_err.update_record( mess = err_mess )
    else:
        r_id = db.dealer_deal_errs.insert( dealer_deal_id = dealer_deal.id, acc = acc,
                                  mess = err_mess )

# сбросим ограничения если новый день или месяц
def limits_end(db, ed_acc):
    if not ed_acc.mon_limit or datetime.date.today().month != ed_acc.mon_limit:
        # если новый месяц то сбросим в ноль
        ed_acc.mon_limit = datetime.date.today().month
        ed_acc.mon_limit_sum = 0
        ed_acc.day_limit = datetime.date.today().day
        ed_acc.day_limit_sum = 0
        ed_acc.update_record()
        return
    if not ed_acc.day_limit or datetime.date.today().day != ed_acc.day_limit:
        # если новый день то сбросим в ноль
        ed_acc.day_limit = datetime.date.today().day
        ed_acc.day_limit_sum = 0
        ed_acc.update_record()

def limits_test(db, ed_acc, vol=33):
    if ed_acc.day_limit_sum < 0 or ed_acc.mon_limit_sum < 0:
        # уже предел настал
        return
    
    if ed_acc.limited:
        # если ограничение - то не более 10тыс в день и 40 тыс в мес
        #print 'ed_acc.day_limit_sum + vol:', ed_acc.day_limit_sum + vol
        if ed_acc.day_limit_sum + vol > DAY_LIM_A:
            return
        if ed_acc.mon_limit_sum + vol > MON_LIM_A:
            return
    else:
        #print 'ed_acc.day_limit_sum + vol:', ed_acc.day_limit_sum + vol
        # если НЕТ ограничения - то не более 10тыс в день и 40 тыс в мес
        if ed_acc.day_limit_sum + vol > DAY_LIM_P:
            return
        if ed_acc.mon_limit_sum + vol > MON_LIM_P:
            return

    return True

# выбрать счет с наибольшим резервом
# тут если приближается конец токена то используем его впервую очередб
def sel_acc_max(db, dealer, ecurr, vol, unlim=None):
    #print 'try sel_acc_max for vol:', vol, 'unlim:', unlim
    # в днях - 100 дней от окончания действия ключа
    expired = datetime.date.today() + datetime.timedelta(30)
    s = 0
    acc = None
    for ed_acc in db((db.dealers_accs.dealer_id == dealer.id)
             & (db.dealers_accs.ecurr_id == ecurr.id)
             ).select():
        if not ed_acc.used: continue

        #print ed_acc.acc, ed_acc.balance, ed_acc.day_limit_sum
        if not unlim:
            # сбросим лимиты если надо
            limits_end(db, ed_acc)
            # проверим на лимиты теперь - если превышен то пропустим
            if not limits_test(db, ed_acc, vol):
                #print 'limitted'
                continue

        bal = ed_acc.balance

        # если подходит дата окончания ключа
        # то если достаточно баланса - выберем сразу его
        if ed_acc.expired < expired and vol <= bal:
            return ed_acc

        if ed_acc.limited and vol < bal * Decimal(0.9):
            # если счет с лимитом то в первую очередь берем его
            # но баланса должно хватать для платежа + комиссия
            bal = bal * Decimal(3)

        #print 'new bal:',bal, 'new max bal for pay:', s
        if s < bal:
            s = bal
            acc = ed_acc
    return acc

def sel_acc_max_for_balance(db, dealer, ecurr, vol, unlim=None):
    #print 'try sel_acc_max for vol:', vol, 'unlim:', unlim
    # в днях - 100 дней от окончания действия ключа
    s = 0
    acc = None
    koeff = Decimal(0.9)
    for ed_acc in db((db.dealers_accs.dealer_id == dealer.id)
             & (db.dealers_accs.ecurr_id == ecurr.id)
             ).select():
        if not ed_acc.used: continue
        bal = ed_acc.balance
        if vol and vol > bal * koeff:
            continue

        #print ed_acc.acc, ed_acc.balance, ed_acc.day_limit_sum
        if not unlim:
            # сбросим лимиты если надо
            limits_end(db, ed_acc)
            # проверим на лимиты теперь - если превышен то пропустим
            if not limits_test(db, ed_acc, vol):
                #print 'limitted'
                continue


        if ed_acc.limited and vol < bal * koeff:
            # если счет с лимитом то в первую очередь берем его
            # но баланса должно хватать для платежа + комиссия
            bal = bal * Decimal(3)

        #print 'new bal:',bal, 'new max bal for pay:', s
        if s < bal:
            s = bal
            acc = ed_acc
    return acc

# выбрать счет с наименьшим резервом
# для пополнения
def sel_acc_min(db, dealer, ecurr, vol, unlim=None):
    #min = db.dealers_accs.balance.max()
    #print db().select(max).first()[max]
    s = 999999
    acc = None
    
    # в днях - 40 дней от окончания действия ключа
    expired = datetime.date.today() + datetime.timedelta(40)

    for ed_acc in db((db.dealers_accs.dealer_id == dealer.id)
             & (db.dealers_accs.ecurr_id == ecurr.id)
             ).select(orderby=db.dealers_accs.balance):
        if not ed_acc.used: continue

        # если подходит дата окончания ключа то прекратим пополнение этого счета
        if ed_acc.expired < expired:
            #print ed_acc.expired, ' < ', expired
            continue
        if ed_acc.reserve_MAX and ed_acc.reserve_MAX + 555 < ed_acc.balance:
            continue

        if not unlim:
            #print 'test limits'
            # сбросим лимиты если надо
            limits_end(db, ed_acc)
            # проверим на лимиты теперь - если превышен то пропустим
            if not limits_test(db, ed_acc, vol): continue

        bal = ed_acc.balance

        if ed_acc.limited:
            ## если счет мелкий то типа на нем баланс большой уже
            if vol > PAY_LIM:
                ## если счет мелкий то типа на нем баланс большой уже
                bal *= 7
            else:
                bal *= 4

            
        if s > bal:
            s = bal
            acc = ed_acc
    return acc

# найти диллера через кого будем платить и счет с наибольшим резервом у него
def select_ed_acc(db, deal, ecurr, vol=33, unlim=None):
    result = None, None, None
    vol = Decimal(1.1) * Decimal(vol)
    #print vol, type(vol)
    # сначала возьмем те у кого баланс больше чем нужно максимально
    for ed_acc in db(
               (db.dealer_deals.deal_id == deal.id)
             & (db.dealers_accs.dealer_id == db.dealers.id)
             & (db.dealers_accs.used == True)
             & (db.dealers_accs.ecurr_id == ecurr.id)
             & (db.dealers_accs.reserve_MAX > 0)
         #    & (db.dealers_accs.reserve_MAX < MON_LIM_A)
             & (db.dealers_accs.reserve_MAX < db.dealers_accs.balance)
             & (db.dealers_accs.balance > vol)
             ).select():
        print 'get as max_reserve > balance', ed_acc.dealers_accs.acc
        return ed_acc.dealers, ed_acc.dealers_accs, ed_acc.dealer_deals

    l = []
    # по всем диллерам
    for dealer_deal in db(db.dealer_deals.deal_id == deal.id).select():
        dealer = db.dealers[dealer_deal.dealer_id]
        #print dealer.name
        # теперь выберем аккант наш у диллера где больше всего деннег
        acc = sel_acc_max(db, dealer, ecurr, vol, unlim)
        if acc:
            # счет нашелся
            print 'added for search:', acc.acc
            l.append([dealer, acc, dealer_deal])

    print l
    # теперь из найденных счетов выберем с наименьшей комиссией
    tax = 100
    for t in l:
        print '  t[2].tax:', t[2].tax
        if tax > t[2].tax:
            tax = t[2].tax
            result = t[0], t[1], t[2]

    return result

# балансы не трогает
def add_trans(db, pars):
    # при одновременном вызове закатывает двойные записи 964365557832024009
    tr = db((db.dealers_accs_trans.dealer_acc_id==pars['dealer_acc_id'])
            & (db.dealers_accs_trans.op_id==pars['op_id'])).select().first()
    if tr: return -tr.id # уже такая есть
    print 'ed_common - add_trans ADD pars %s' % pars
    tr_last=db(db.dealers_accs_trans.dealer_acc_id==pars['dealer_acc_id']).select().last()
    bal_last = tr_last and tr_last.balance or Decimal(0)
    pars['diff'] = float(bal_last) - float(pars.get('balance') or 0) + float(pars.get('amo') or 0)
    return db.dealers_accs_trans.insert(**pars)

###################################
# дело в том что баланс самого счета будет намного меньше баланса у дилера и меньше баланса на валюте
# поэтому нельзя напрмую вычетать депозиты из баланса счета - там всегда 0 будет
def get_balance(dealer, dealer_acc ):
    bal = 0
    if dealer.name == 'Yandex':
        bal = ed_YD.get_balance(dealer, dealer_acc )
        # тут нет db на входе !!! log(db, 'get_balance: %s' % bal)
        bal = bal.get('balance', 0)

    return bal

# взять возможную сумму платежа по ограничениям счета
def get_lim_bal(db, dealer):
    #dealer_acc = db.dealers_accs[request.args(0)]

    bal = 0
    accs = []
    for acc in db((db.dealers_accs.dealer_id == dealer.id)
            & (db.dealers_accs.used == True)).select():
        v = acc.balance
        if acc.day_limit_sum < 0 or acc.mon_limit_sum <0:
            # если уже предел настал то 0
            continue

        if acc.limited:
            vd = DAY_LIM_A - acc.day_limit_sum
            vm = MON_LIM_A - acc.mon_limit_sum
        else:
            vd = DAY_LIM_P - acc.day_limit_sum
            vm = MON_LIM_P - acc.mon_limit_sum
        if v > vd:
            v = vd
        if v > vm:
            v = vm

        if v> 0:
            bal += v
            accs.append([v, acc])
    return bal, accs

def update_balances(db, dealer, dealer_acc, amount):
    amount = Decimal(amount)
    dealer.balance = (dealer.balance or Decimal('0.0')) + amount
    dealer.update_record()
    dealer_acc.balance = (dealer_acc.balance or Decimal('0.0')) + amount
    dealer_acc.update_record()
    ecurr = db.ecurrs[dealer_acc.ecurr_id]
    curr = db.currs[ecurr.curr_id]
    curr.balance = (curr.balance or Decimal('0.0')) + amount
    curr.update_record()

#########################################


def pay_test(db, deal, dealer, dealer_acc, dealer_deal, acc, volume_out, log_on=None, pars_in=None):
    volume_out = round(volume_out,2)
    if dealer.name == 'Yandex':
        res = ed_YD.pay_test(db, deal, dealer, dealer_acc, dealer_deal,
            acc, volume_out, log_on, pars_in)
    else:
        res = {'status':'refused', 'error':'no dealer', 'error_description': dealer.name + ' not scripted', }

    if res.get('error'):
        try:
            db_common.pay_err_store(db, dealer, dealer_acc, deal, acc, res.get('error'))
        except Exception as e:
            log(db, e)
        pass

    return res

# здесь ведем учет что диллер еще начислит на нас сверху
# поэтому уменьшаем сумму платежа
def pay(db, deal, dealer, dealer_acc, dealer_deal, acc, volume_out_full, log_on=None, pars_in=None):
    fee_curr = db.currs[ deal.fee_curr_id ]
    curr_out, x, ecurr_out = db_common.get_currs_by_abbrev(db,"RUB")
    if fee_curr.id == curr_out.id:
        fee_rate = 1
    else:
        import rates_lib
        fee_rate = Decimal(rates_lib.get_avr_rate_or_null(db, fee_curr.id, curr_out.id))
    ## проверка тут http://127.0.0.1:8000/ipay3_dvlp/tool_deal/fees/BTC/4049/100/1
    volume_out, _ = db_client.dealer_deal_tax_add(db, None, fee_rate, dealer_deal, '', Decimal(volume_out_full), '')
    volume_out = round(float(volume_out),2)

    if dealer.name == 'Yandex':
        res = ed_YD.pay(db, deal, dealer, dealer_acc, dealer_deal,
            acc, volume_out, None, None, log_on, pars_in)
        if res['status'] == u'refused' and res.get('error') == u'authorization_reject':
            # авторизация кончилась - надо этот счет выключить
            print 'pay - authorization_reject for', dealer_acc.acc
            dealer_acc.update_record( used = False)
            #print 'authorization_reject'
    else:
        res = {'status':'refused', 'error':'no dealer', 'error_description': dealer.name + ' not scripted', }

    if res and res['status']=='success':
        sum_taken = res.get('sum_taken')
        # платеж прошел и было взято с нас, запомним
        if log_on != False:
            print 'ed_common pay() res:', res
        add_trans(db, dict(dealer_acc_id=dealer_acc.id,
                    info='%s' % res,
                    vars = res,
                    balance=res.get('balance'),
                    amo=-sum_taken,
                    op_id=res.get('payment_id')))

        update_balances(db, dealer, dealer_acc, -sum_taken) #, res.get('balance'))
    else:
        try:
            db_common.pay_err_store(db, dealer, dealer_acc, deal, acc, res.get('error'))
        except Exception as e:
            log(db, e)
        pass


    return res

# платеж для клиентов - учесть уменьшение депозита клиентов
def client_pay(db, deal, dealer, dealer_acc, dealer_deal, acc, volume_out, ecurr):
    res = pay(db, deal, dealer, dealer_acc, dealer_deal, acc, volume_out)
    if not res or 'error' in res or res['status']!='success':
        return res

    dealer.clients_deposit = (dealer.clients_deposit or Decimal('0.0')) - volume_out
    dealer.balance = (dealer.balance or Decimal('0.0')) - volume_out
    ecurr.clients_deposit = (ecurr.clients_deposit or Decimal('0.0')) - volume_out
    ecurr.balance = (ecurr.balance or Decimal('0.0')) - volume_out
    return res

def get_payment_info(dealer, dealer_acc, pay_id ):
    if dealer.name == 'Yandex':
        return ed_YD.get_payment_info(dealer, dealer_acc, pay_id )

# test - not seek in DB
def is_order_addr(db, mess, test=None ):
    vs = mess.split('7pb')
    #print vs
    if len(vs)==2:
        order_id = vs[1]
        #print 'is_order_addr 7pb +', order_id
        if order_id.isdigit():
            #print 'is_order_addr isdigits', order_id
            order = db.addr_orders[ order_id ]
            if order:
                #print 'is_order_addr order',  order.addr
                xcurr = db.xcurrs[ order.xcurr_id ]
                addr = order.addr
                return xcurr, addr and addr.strip()
        else:
            print 'is_payment_for_buy -  orderId:', order_id
    return None, None

# test - not seek in DB
def is_payment_for_buy(db, dealer, dealer_acc, info, test=None ):
    buy = not test and db( (db.buys.dealer_acc_id==dealer_acc.id)
                    & (db.buys.operation_id == info['operation_id'])
                    ).select().first()
    if buy:
        # такая операция уже была выплочена
        mess = 'is_payment_for_buy:  - operation_id %s already buyed. Status: [%s]' % (info['operation_id'], buy.status)
        #log(db, mess)
        return None, mess

    if dealer.name == 'Yandex':
        return ed_YD.is_payment_for_buy(db, dealer_acc, info)
def get_history(db, dealer, dealer_acc, from_id ):
    if dealer.name == 'Yandex':
        return ed_YD.get_history(dealer, dealer_acc, from_id)
def get_history_inputs(dealer, dealer_acc, from_dt ):
    if dealer.name == 'Yandex':
        return ed_YD.get_history_inputs(dealer, dealer_acc, from_dt)

def get_edealers_for_to_wallet(db, deal, curr_out, ecurr_out_id, ed_name=None):
    inp_dealers = []
    limit_bal = None
    for edealer in db((db.dealers.used == True)
                 & (not ed_name or db.dealers.name == ed_name)).select():
        #print edealer.name
        limit_bal = 0
        MAX = MIN = db_common.gMIN(deal, edealer)
        MAX = deal.MAX_pay or 1777
        limit_bal, accs = get_lim_bal(db, edealer)
        if MAX * 3 > limit_bal:
            MAX = limit_bal / 4
        inp_dealers.append([edealer.id, (edealer.name, curr_out.abbrev, limit_bal, MIN, MAX)])
    return limit_bal, inp_dealers
