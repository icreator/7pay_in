# coding: utf8

#from datetime import datetime
from decimal import Decimal
#from gluon import current
import datetime

'''
общие процедуры для работы с диллерами фиата - баллансами счетов
'''
import db_common

PAY_LIM = 3777 # стандартное оограничение на один платеж
DAY_LIM_A = 8777
DAY_LIM_P = 23777
MON_LIM_A = 8777
MON_LIM_P = 47777

def log(db, mess):
    mess = 'EDc: %s' % mess
    print (mess)
    db.logs.insert(mess=mess)
def log_commit(db, mess):
    log(db,mess)
    db.commit()


def limits_test(db, ed_acc, vol=33):
    if ed_acc.limited:
        # если ограничение - то не более 10тыс в день и 40 тыс в мес
        if ed_acc.day_limit_sum + vol > DAY_LIM_A:
            return
        if ed_acc.mon_limit_sum + vol > DAY_LIM_P:
            return
    else:
        # если НЕТ ограничения - то не более 10тыс в день и 40 тыс в мес
        if ed_acc.day_limit_sum + vol > MON_LIM_A:
            return
        if ed_acc.mon_limit_sum + vol > MON_LIM_P:
            return

    return True

# выбрать счет с наибольшим резервом
# тут если приближается конец токена то используем его впервую очередб
def sel_acc_max(db, dealer, ecurr, vol, unlim=None):
    # в днях - 100 дней от окончания действия ключа
    expired = datetime.date.today() + datetime.timedelta(100)
    s = 0
    acc = None
    for ed_acc in db((db.dealers_accs.dealer_id == dealer.id)
             & (db.dealers_accs.ecurr_id == ecurr.id)
             ).select():
        if not ed_acc.used: continue

        if not unlim:
            # сбросим лимиты если надо
            limits_end(db, ed_acc)
            # проверим на лимиты теперь - если превышен то пропустим
            if not limits_test(db, ed_acc, vol):
                print ('limitted')
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

        if s < bal:
            s = bal
            acc = ed_acc
    return acc

# выбрать счет с наименьшим резервом
# для пополнения
def sel_acc_min(db, dealer, ecurr, vol, unlim=None):
    #min = db.dealers_accs.balance.max()
    #print (db().select(max).first()[max])
    s = 999999
    acc = None
    
    # в днях - 100 дней от окончания действия ключа
    expired = datetime.date.today() + datetime.timedelta(100)

    for ed_acc in db((db.dealers_accs.dealer_id == dealer.id)
             & (db.dealers_accs.ecurr_id == ecurr.id)
             ).select(orderby=db.dealers_accs.balance):
        if not ed_acc.used: continue

        # если подходит дата окончания ключа то прекратим пополнение этого счета
        if ed_acc.expired < expired:
            #print (ed_acc.expired, ' < ', expired)
            continue

        if not unlim:
            #print ('test limits')
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
    l = []
    # по всем диллерам
    for dealer_deal in db(db.dealer_deals.deal_id == deal.id).select():
        dealer = db.dealers[dealer_deal.dealer_id]
        #print (dealer.name)
        # теперь выберем аккант наш у диллера где больше всего деннег
        acc = sel_acc_max(db, dealer, ecurr, vol, unlim)
        if acc:
            # счет нашелся
            l.append([dealer, acc, dealer_deal])

    #print (l)
    # теперь из найденных счетов выберем с наименьшей комиссией
    tax = 100
    for t in l:
        if tax > t[2].tax:
            tax = t[2].tax
            result = t[0], t[1], t[2]

    return result

###################################
# возьмем баланс возможный для операций
def get_max(db, dealer, limited=False):
    bal, accs = get_limited(db, dealer)
    return bal, accs
    
    

# взять возможную сумму платежа по ограничениям счета
# и список аккков у диллера у которых есть еще запас по балансу с учетоа ограничений
# проверка в http://127.0.0.1:8000/ipay3_dvlp/tool_ed/get_limited/1
def get_limited(db, dealer):
    bal = 0
    accs = []
    for acc in db((db.dealers_accs.dealer_id == dealer.id)
            & (db.dealers_accs.used == True)).select():
        v = acc.balance
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

# изменить балансы + балансы лимитные если платеж по лимиту
def update(db, dealer_acc, amount, dealer=None, limited=None):
    dealer = dealer or db.dealers[ dealer_acc.dealer_id ]
    amount = Decimal(amount)
    dealer.update_record(balance = Decimal(dealer.balance or 0) + amount)
    dealer_acc.balance = Decimal(dealer_acc.balance or 0) + amount
    if limited:
        # и лимиты не забудем
        dealer_acc.day_limit_sum = Decimal(dealer_acc.day_limit_sum or 0) + abs(amount)
        dealer_acc.mon_limit_sum = Decimal(dealer_acc.mon_limit_sum or 0) + abs(amount)
    dealer_acc.update_record()

    ecurr = db.ecurrs[dealer_acc.ecurr_id]
    curr = db.currs[ecurr.curr_id]
    curr.update_record(balance = Decimal(curr.balance or 0) + amount)
