# coding: utf8
#
# http://web2py.com/examples/static/epydoc/web2py.gluon.dal-module.html

from datetime import datetime
from decimal import Decimal

STATUS_REFUSED = {'technical_error', 'payment_refused', 'currency_unused'}

'''
from gluon.dal import DAL, Field, Table
db = DAL("sqlite://storage.sqlite",
        #pool_size=1,
        #check_reserved=['all'],
# this keyword buil model on fly on load
        auto_import=True,
        folder="../databases")
#print db.tables
'''


def get_currs_by_abbrev(db, abbrev):
    curr = db(db.currs.abbrev == abbrev).select().first()
    xcurr = curr and db(db.xcurrs.curr_id == curr.id).select().first()
    ecurr = curr and db(db.ecurrs.curr_id == curr.id).select().first()
    return curr, xcurr, ecurr


def get_currs_by_addr(db, addr, abbrev_only=None):
    if not addr or len(addr) < 30 or len(addr) > 46: return None, None, None
    ch = addr[0:1]
    if ch == '1' or ch == '3':
        abbrev = 'BTC'
    elif ch == '7':
        abbrev = 'ERA'
    elif ch == 'L':
        abbrev = 'LTC'
    elif ch == 'X':
        abbrev = 'DASH'
    elif ch == 'C':
        abbrev = 'CLR'
    elif ch in 'D9A':
        abbrev = 'DOGE'
    elif ch == '4':
        abbrev = 'NVC'
    elif ch == 'P':
        abbrev = 'PPC'
    elif addr[0:2] == '0x':
        abbrev = 'ETH'
    else:
        # у догов 34 буквы и первая буква вообще разная
        abbrev = 'DOGE'
    if abbrev_only:
        return abbrev

    return get_currs_by_abbrev(db, abbrev)


#


###################################
# дело в том что баланс самого счета будет намного меньше баланса у дилера и меньше баланса на валюте
# поэтому нельзя напрмую вычетать депозиты из баланса счета - там всегда 0 будет
def get_balance_dealer_acc(dealer_acc):
    bal = 0
    # не учитываем тут более старшие балансы - только свой
    bal = float(dealer_acc.balance - (dealer_acc.deposit or 0))
    if bal < 0: bal = 0
    return round(bal, 2)


def get_balance_dealer(dealer):
    bal = float((dealer.balance or 0.0) - (dealer.deposit or 0.0) - (dealer.clients_deposit or 0.0))
    if bal < 0: bal = 0.0
    return round(bal, 2)


def get_balance_ecurr(ecurr):
    bal = float((ecurr.balance or 0.0) - (ecurr.deposit or 0.0) - (ecurr.clients_deposit or 0.0))
    if bal < 0: bal = 0.0
    return round(bal, 2)


def update_balances(curr, amount):
    amount = Decimal(amount)
    curr.balance = (curr.balance or Decimal('0.0')) + amount
    curr.update_record()


########################

# статитстика по среднему курсу обмена
def currs_stats_update(db, curr_id, deal_id, volume_out):
    currs_stats = db((db.currs_stats.curr_id == curr_id)
                     & (db.currs_stats.deal_id == deal_id)).select().first()
    if not currs_stats:
        if True:
            db.currs_stats.insert(curr_id=curr_id, deal_id=deal_id, average_=volume_out, count_=1)
        else:
            # on PostgreSQL rise ERROR
            db.currs_stats[0] = {
                'curr_id': curr_id,
                'deal_id': deal_id,
                'average_': volume_out,
                'count_': 1,
            }
    else:
        average = currs_stats.average_ or 0
        count = currs_stats.count_ or 0
        volume_out = Decimal(volume_out)
        currs_stats.average_ = count / (count + 1) * average + volume_out / (count + 1)
        currs_stats.count_ = count + 1
        currs_stats.update_record()


def get_exchg_pairs(db, id):
    return db(db.exchg_pairs.exchg_id == id).select()


# def commit(): db.commit()

def get_limits(db, exchg_id, curr_id):
    limits = db((db.exchg_limits.exchg_id == exchg_id) & (db.exchg_limits.curr_id == curr_id)).select().first()
    # print limits
    return limits


def store_rates(db, pair, sell, buy):
    pair.update_record(sp1=sell, bp1=buy, on_update=datetime.now())


def store_depts(db, pair, rec):
    # print rec
    pair.sp1 = rec[0][0][0]
    pair.sv1 = rec[0][0][1]
    pair.sp2 = rec[0][1][0]
    pair.sv2 = rec[0][1][1]
    pair.sp3 = rec[0][2][0]
    pair.sv3 = rec[0][2][1]
    pair.sp4 = rec[0][3][0]
    pair.sv4 = rec[0][3][1]
    pair.sp5 = rec[0][4][0]
    pair.sv5 = rec[0][4][1]

    pair.bp1 = rec[1][0][0]
    pair.bv1 = rec[1][0][1]
    pair.bp2 = rec[1][1][0]
    pair.bv2 = rec[1][1][1]
    pair.bp3 = rec[1][2][0]
    pair.bv3 = rec[1][2][1]
    pair.bp4 = rec[1][3][0]
    pair.bv4 = rec[1][3][1]
    pair.bp5 = rec[1][4][0]
    pair.bv5 = rec[1][4][1]

    # pair.update()
    pair.on_update = datetime.now()
    pair.update_record()
    db.commit()
    # print pair.uniq, "updated..."


def pay_err_store(db, dealer, dealer_acc, deal, acc, err):
    # запомним что такой платеж нужен комуто
    rec = db((db.deal_errs.dealer_id == dealer.id)
             & (db.deal_errs.dealer_acc == dealer_acc.acc)
             & (db.deal_errs.deal_id == deal.id)
             & (db.deal_errs.err == err)).select().first()
    if not rec:
        db.deal_errs.insert(dealer_id=dealer.id, dealer_acc=dealer_acc.acc,
                            deal_id=deal.id, count_=1, acc=acc, err=err)
    else:
        rec.count_ = rec.count_ + 1
        rec.acc = acc
        rec.update_record()


def gMIN(deal, dealer, min0=10):
    # для платежей криптой - любые суммы
    min1 = deal.MIN_pay or 0
    if min1 < 0: return 0
    min1 = int(min1 or min0)
    min2 = int(dealer and dealer.pay_out_MIN or min0)
    min_ = min2 > min1 and min2 or min1
    return int(min_ * 1.2) + 1


def gMAX(deal, dealer, max0=2777):
    # для платежей криптой - любые суммы
    max1 = deal.MAX_pay or 0
    if max1 < 0: return 0
    max1 = int(max1 or max0)
    ## нет у дилера макс пока max2 = int(dealer and dealer.pay_out_MAX or max0)
    max2 = max0
    max_ = max2 < max1 and max2 or max1
    return max_
