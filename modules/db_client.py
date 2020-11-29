# coding: utf8

if False:
    from gluon import *
    import db

    request = current.request
    response = current.response
    session = current.session
    cache = current.cache
    T = current.T

from gluon import current

T = current.T

DOMEN = 'face2face'

from datetime import datetime, timedelta
from decimal import Decimal

import common
from db_common import *
import crypto_client
import rates_lib


## проверим запасы - если есть ограничение по баласу то откажем в выплатах
def is_limited_ball(curr_in):
    max_bal = Decimal(curr_in.max_bal or 0)
    bal_dep = Decimal(curr_in.balance or 0) - Decimal(curr_in.deposit or 0)
    if max_bal and max_bal > 0:
        limit = max_bal - bal_dep
        if limit < 0:
            limit = 0
        return max_bal, limit
    return 0, 0


def make_x_acc(deal, acc, curr_out_abbrev):
    # это имя аккаунта в моем кошельке какое будет
    return '[%s] [%s] [%s]' % (deal.name2, acc, curr_out_abbrev)


def make_x_acc_label(deal, acc, curr_out_abbrev):
    # это имя аккаунта в кошельке клиента - чтобы ему было понятней
    return DOMEN + ' -> [%s] [%s] [%s]' % (deal.name2, acc, curr_out_abbrev)


# old def get_deal_acc_id_for_deal_and_acc(db, deal, deal_acc, acurr):
# создаем заказ длля данного дела с заданной суммой заказа
def get_deal_acc_id(db, deal, acc, curr_out, price=None):
    if not acc or len(acc) < 3: return
    # найдем аккаунт для данного дела или создадим
    # если пустой аккаунт в записи то его почему-то находит ((
    import time
    # чтобы народ нас не ДОСИЛ - задержку
    time.sleep(0.5)
    deal_acc = None
    for rec in db((db.deal_accs.deal_id == deal.id)  # для данного дела
                  & (db.deal_accs.acc == acc)  # есть такой аккаунт
                  & (db.deal_accs.curr_id == curr_out.id)
                  ).select():
        if len(rec.acc) < 3: continue
        deal_acc = rec
        ##print 'get_deal_acc_id found:', deal_acc.id, deal_acc.acc, curr_out.id
        break

    if deal_acc:
        deal_acc_id = deal_acc.id
    else:
        time.sleep(1)
        deal_acc_id = db.deal_accs.insert(deal_id=deal.id, acc=acc, curr_id=curr_out.id, price=price)
        ##print 'insert new - deal_acc_id:', deal_acc_id
    return deal_acc_id


def get_deal_acc_addr(db, deal_id, curr_out, acc, addr, xcurr_in):
    deal_acc = db((db.deal_accs.deal_id == deal_id)
                  & (db.deal_accs.curr_id == curr_out.id)
                  & (db.deal_accs.acc == acc)).select().first()
    if not deal_acc:
        deal_acc_id = db.deal_accs.insert(deal_id=deal_id, curr_id=curr_out.id, acc=acc)
    else:
        deal_acc_id = deal_acc.id

    deal_acc_addr = db((db.deal_acc_addrs.addr == addr)
                       & (db.deal_acc_addrs.xcurr_id == xcurr_in.id)).select().first()

    if not deal_acc_addr:
        deal_acc_addrs_id = db.deal_acc_addrs.insert(deal_acc_id=deal_acc_id, addr=addr, xcurr_id=xcurr_in.id)
        deal_acc_addr = db.deal_acc_addrs[deal_acc_addrs_id]

    return deal_acc_id, deal_acc_addr


def get_deal_acc_addr_for_xcurr(db, deal_acc_id, curr, xcurr, x_acc_label):
    # найдем адрес крипты для данного аккаунта дела или создадим
    deal_acc_addr = db((db.deal_acc_addrs.deal_acc_id == deal_acc_id)
                       & (db.deal_acc_addrs.xcurr_id == xcurr.id)
                       ).select().first()
    if deal_acc_addr:
        ##print 'get_deal_acc_addr_for_xcurr found:', 'deal_acc_id:', deal_acc_id, 'xcurr_id:', xcurr.id, '>>', deal_acc_addr.id, deal_acc_addr.addr
        return deal_acc_addr

    # Erachain tokens?
    token_system = None
    token_key = xcurr.as_token
    if token_key:
        token = db.tokens[token_key]
        token_system = db.systems[token.system_id]

        addr = token_system.account
    else:
        try:
            conn = crypto_client.connect(curr, xcurr)
        except:
            conn = None

        if not conn:
            return

        if xcurr.protocol == 'zen':
            ## in Horizen Account is removed
            addr = conn.getnewaddress()

        else:
            # http://docs.python.org/2/library/codecs.html?highlight=decoding
            x_acc_label = x_acc_label.decode('utf8')
            # x_acc_label = x_acc_label.encode('koi8_r') # 'iso8859_5') # 'cp866') # 'cp1251') #'cp855')
            # x_acc_label = x_acc_label.decode('cp855')
            ##print 'GET new addr for x_acc_label:', x_acc_label
            try:
                addr = crypto_client.get_xaddress_by_label(conn, x_acc_label)
            except:
                return

        if not addr:
            return

    id = db.deal_acc_addrs.insert(
        deal_acc_id=deal_acc_id,
        xcurr_id=xcurr.id,
        addr=addr)
    deal_acc_addr = db.deal_acc_addrs[id]
    ##print 'GETed new addr :', addr
    return deal_acc_addr


######################################################
######################################################
'''
d_e - направление перевода - dealer to exchange
'''


def get_price_with_fee(db, price, s_b, exchg_id, dealer_id, d_e=None):
    r = db((db.fees.exchg_id == exchg_id) & (db.fees.dealer_id == dealer_id)).select().first()
    '''
   Field('exchg_id', db.exchgs),
   Field('dealer_id', db.dealers),
   Field('fee_ed', 'decimal(4,2)', comment='fee in % from exhange to e-dealer'),
   Field('fee_de', 'decimal(4,2)', comment='fee in % from e-dealer to exhange'),
    '''
    if not r:
        # print "NOT FEE for exchg_id:",exchg_id, "dealer_id:", dealer_id
        return price, 0.0

    fee = float(d_e and r.fee_de or r.fee_ed) / 100.0
    # print 'fee:',fee
    fee_1 = 1.0 + (s_b and -fee or fee)
    # print 'fee:',fee, 'income price:',price, 'price:',price * fee
    return price * fee_1, fee


""" выдать лучшую цену от количества:
volume_in
s_b =
- True - покупки
- None - продажи

если есть ecurr_id то требуется найти с учетом вывода на дилера е-валюты
"""


def get_best_price_for_volume_1(db, in_id, out_id, volume, expired, s_b=None, dealer_id=None, d_e=None):
    fields = ""
    for i in range(5):
        # так как мы смотрим цену для нашей операции
        # то берем тут имя поля обратное от s_b
        fields += "%sp%s AS p%s, " % (s_b and 'b' or 's', i + 1, i + 1)
        fields += "%sv%s AS v%s, " % (s_b and 'b' or 's', i + 1, i + 1)

    qry = "SELECT " + fields + \
          "exchg_id, curr2_id \
 FROM exchg_pairs \
 WHERE (curr1_id=%s AND curr2_id=%s AND on_update > '%s');" % (in_id, out_id, expired)
    # print qry
    pairs = db.executesql(qry, as_dict=True)
    # print pairs
    best_price = best_pair = best_tax = best_fee_ed = None
    vol = 0
    for pair in pairs:
        # print pair['exchg_id'], "prices:",pair['p1'], " ... ", pair['p5'], 'vol:',pair['v5']
        vol = pair['v1'] or 0
        price = pair['p1']
        exchg = None
        fee_ed = None
        # тут в полях объема уже суммированный объем
        # поэтому без накопления тут идем - просто сравниваем
        if vol < volume:
            vol = pair['v2'] or 0
            price = pair['p2']
            if vol < volume:
                vol = pair['v3'] or 0
                price = pair['p3']
                if vol < volume:
                    vol = pair['v4'] or 0
                    price = pair['p4']
                    if vol < volume:
                        vol = pair['v5'] or 0
                        price = pair['p5']
                        if vol < volume:
                            # значит нету такого объема - пропустим
                            # price = None
                            # но укажем что пара торгуется
                            # print 'out of volume:', volume
                            best_pair = pair
                            continue
        # print "price get:", price
        if price:
            # use exchange tax
            exchg = db.exchgs[pair['exchg_id']]
            tax = float(exchg.tax or 0.2) * 0.01  # in %
            # print price, ' +  exchange tax(', tax, ') -> new price',
            if tax: price = price * Decimal(1 + (s_b and -tax or tax))
            # print price
        if dealer_id and price: price, fee_ed = get_price_with_fee(db, price, s_b, pair['exchg_id'], dealer_id, d_e)
        if best_price and price:
            if s_b and best_price < price \
                    or not s_b and best_price > price:
                best_price = price
                best_pair = pair
                best_tax = {exchg.url: tax}
                best_fee_ed = fee_ed
        else:
            best_price = price
            best_pair = pair
            best_tax = {exchg.url: tax}
            best_fee_ed = fee_ed

        # print best_price, vol

    # if best_price: print "best exch:", best_pair['exchg_id'], 'best price:', best_price
    # else: print "best exch:",None

    return best_price, best_pair, best_tax, best_fee_ed


# возвращает лучшую цену и список пар которые надо конвертировать
def get_best_price_for_volume(db, id1, id2, vol, expired, s_b=None, dealer_id=None, d_e=None):
    # найдем лучшиую цену для данного напрявления обмена
    if id1 == id2: return 1.0, None, None, None

    # если объем большой то выдаст Ноне для цены и данные по паре
    best_price, best_pair, best_tax, best_fee_ed = get_best_price_for_volume_1(
        db, id1, id2, vol, expired, s_b, dealer_id, d_e)
    # print best_tax
    if not best_pair:
        # если не нашлось такой ПАРЫ то обратный обмен ищем
        # но обратную операцию
        # print "rate not exist, try back rate...", id1, id2
        rateB, rateS, rateAVG = rates_lib.get_average_rate_bsa(db, id2, id1, expired)
        # print rateB, rateS, rateAVG
        # изменим количество
        vol2 = None
        if s_b and rateB:  # если нужна была продажа изначально то берем Покупку
            vol2 = float(vol) / rateB
        if not s_b and rateS:  # берем продажу
            vol2 = float(vol) / rateS
        # print vol2
        if vol2 != None:
            best_price, best_pair, best_tax, best_fee_ed = get_best_price_for_volume_1(
                db, id2, id1, vol2, expired, not s_b, dealer_id, d_e)
            # и курс надо перевернуть
            if best_price:
                best_price = 1 / best_price
    if best_pair: return best_price, [best_pair], [best_tax], best_fee_ed
    # сюда прийдет если нет такой пары и нет обратной пары
    #  попробуем взять через Биткоин кросскурс
    btc, x, e = get_currs_by_abbrev(db, 'BTC')
    # тут без учета комиссии биржа-дилер так как крипта в крипту
    best_price1, best_pair1, best_tax1, fee = get_best_price_for_volume_1(db, id1, btc.id, vol, expired, s_b)
    if not best_price1: return None, None, None, None
    # нашли кросскурс
    vol1 = vol * best_price1
    # print 'best_price1:',best_price1, 'vol1:', vol1
    best_price2, best_pair2, best_tax2, best_fee_ed = get_best_price_for_volume_1(
        db, btc.id, id2, vol1, expired, s_b, dealer_id, d_e)
    if not best_price2: return None, None, None, None

    return round(best_price1 * best_price2, 8), [best_pair1, best_pair2], [best_tax1, best_tax2], best_fee_ed


def test2():
    from gluon.dal import DAL
    db = DAL("sqlite://storage.sqlite",
             # pool_size=1,
             # check_reserved=['all'],
             # this keyword buil model on fly on load
             auto_import=True,
             folder="../databases")
    # задаим дату-время при котором будут считатья записи устаревшими
    expired = datetime.datetime.now() - datetime.timedelta(0, 600)
    # 2-BTC, 5-RUB
    c1, x, e = get_currs_by_abbrev(db, 'BTC').id
    c2, x, e = get_currs_by_abbrev(db, 'RUB').id
    pair = db((db.exchg_pairs.curr1_id == c1.id) & (db.exchg_pairs.curr2_id == c2.id)).select().first()
    for vol in (1, 10, 100, 1000, 10000, 33000):
        # print "\n", vol
        # print "--->"
        best_price, best_pair, best_tax, best_fee_ed = get_best_price_for_volume(db, x1_id, x2_id, vol, expired)
        # и проверим обратную
        # print "<<<<"
        rateB, rateS, rateA = rates_lib.get_average_rate_bsa(db, x2_id, x1_id, expired)
        # print "rateB, rateS, rateA", rateB, rateS, rateA
        if rateS: best_price, best_pair, best_tax, best_fee_ed = get_best_price_for_volume(db, x2_id, x1_id,
                                                                                           vol / rateS, expired)


####################################################################
# для выбора крипты в формах оплаты для данного дела
####################################################################
def curr_free_bal(curr):
    bal_out = curr.balance - curr.deposit - curr.clients_deposit - curr.fee_out
    if bal_out < 0: bal_out = 0
    return bal_out


# not_used - список запрещенных валют для клиентов или магазинов
# здесь на входе может быть количество - для магазинов где цена задана
def get_xcurrs_for_deal(db, amo_out, curr_out, deal, dealer=None, s_b_in=None, not_used=None):
    curr_out_id = curr_out.id
    dealer_id = dealer and dealer.id or None

    # берем в расчет только недавние цены
    expired = datetime.now() - timedelta(0, 360)
    pairs = []

    is_order = False
    dealer_deal = None
    deal = db.deals[current.TO_COIN_ID]

    s_b = s_b_in == None and True or s_b_in  ############################
    d_e = None
    # теперь по всем криптам пройдемся и если нет в парах то
    # значит запрет в форме сделаем
    for rec_in in db((db.currs.used == True)
                     & (db.xcurrs.curr_id == db.currs.id)).select(orderby='currs.name'):
        curr_in = rec_in.currs
        if not_used and curr_in.abbrev in not_used: continue
        disabled = None

        if curr_in.id == curr_out.id:
            continue

        if not amo_out:
            rates = rates_lib.get_best_rates(db, curr_in, curr_out)
            if rates:
                amo_in = rates[curr_out.id][0]
            else:
                amo_in = 0
        else:
            # количество уже жестко задано от магазина
            pr_b, pr_s, pr_avg = rates_lib.get_average_rate_bsa(db, curr_in.id, curr_out.id, expired)
            # print pr_b, pr_s, pr_avg
            if pr_b:
                amo_in = amo_out / pr_b

        rate = None
        if False:
            # OLD style - without taxes

            if not amo_out or pr_b:
                # print 'amo_in:', amo_in
                amo_out, rate_order, rate = rates_lib.get_rate(db, curr_in, curr_out, amo_in)
        else:
            # new STYLE - full price

            # amo_in = 1
            _, _, best_rate = rates_lib.get_rate(db, curr_in, curr_out, amo_in)
            if best_rate:
                amo_out, mess_out = calc_fees(db, deal, dealer_deal, curr_in, curr_out, amo_in,
                                              best_rate, is_order=0, note=0, only_tax=1)
                ## vol_out - is Decimal
                amo_out = common.rnd_8(amo_out)
                if amo_in:
                    rate = amo_out / amo_in

        if not rate:
            rate = -1
            disabled = True

        currs_stats = db((db.currs_stats.curr_id == curr_in.id)
                         & (db.currs_stats.deal_id == deal.id)).select().first()

        pairs.append({'id': curr_in.id, 'price': rate,
                      'name': curr_in.name, 'abbrev': curr_in.abbrev, 'icon': curr_in.icon,
                      'expired': disabled,
                      'name_out': curr_out.abbrev,
                      'used': currs_stats and currs_stats.count_ or 0,
                      'curr_id': curr_in.id,  # для того чтобы по 2му разу не брало
                      'bal': curr_in.balance,
                      'bal_out': curr_free_bal(curr_in)  # сколько можно продать
                      })

    return pairs


def get_xcurrs_for_buy(db, curr_in, deal):
    curr_in_id = curr_in.id

    # берем в расчет только недавние цены
    expired = datetime.now() - timedelta(0, 360)
    pairs = []

    # теперь по всем криптам пройдемся и если нет в парах то
    # значит запрет в форме сделаем
    for curr_out in db(db.currs.used == True).select(orderby='name'):
        xcurr = db(db.xcurrs.curr_id == curr_out.id).select().first()
        if not xcurr: continue
        disabled = None

        if curr_out.id == curr_in_id:
            rate = 1.0
        else:
            # берем в расчет только недавние цены
            ao_, ro_, rate = rates_lib.get_rate(db, curr_in, curr_out)
            # print  ao_, ro_, rate
            if rate:
                rate = 1 / rate
            else:
                rate = -1
                disabled = True

        currs_stats = db((db.currs_stats.curr_id == curr_out.id)
                         & (db.currs_stats.deal_id == deal.id)).select().first()

        if curr_out.tax_out < 0:
            # мы даем бонус за покуцпку этой крипты - отразим сразу в курсе
            rate = rate * (1 + 0.01 * float(curr_out.tax_out))

        pairs.append({'id': curr_out.id, 'price': rate,
                      'name': curr_out.name, 'abbrev': curr_out.abbrev, 'icon': curr_out.icon,
                      'expired': disabled,
                      # 'name_out': curr_out.abbrev,
                      'used': currs_stats and currs_stats.count_ or 0,
                      'curr_id': curr_out.id,  # для того чтобы по 2му разу не брало
                      'bal': curr_out.balance,
                      'bal_out': 9 * curr_free_bal(curr_out) / 10  # сколько можно продать
                      })

    return pairs


#######################################################
## тут только такса быиржи и вывода с биржи
def get_best_price_for_volume_buy(db, curr_in, curr_out, volume_in):
    rate = mess = pair = txs = efee = None
    if curr_in.id == curr_out.id:
        return 1.0, mess, pair, txs, efee
    # время жизни для курсов
    expired = datetime.now() - timedelta(0, 300)
    s_b = True
    # d_e = None # перевод с биржи на диллера
    # dealer_id = ed_common.get_acc(db).dealer_id
    # так как у нас тут неизвестно количестыво на выходе а есть
    # количество на входе, то надо обратную операцию:
    # поменяем in out s_b
    best_rate, pair, txs, efee = get_best_price_for_volume(
        db, curr_in.id, curr_out.id, volume_in, expired, s_b)  # , dealer.id, d_e)
    # print best_rate, '1/r=', round(1/best_rate,8), pair, '\n', txs, efee
    if not best_rate:
        if pair:
            best_rate, pair, txs, efee = get_best_price_for_volume(
                db, curr_in.id, curr_out.id, 0.001, expired, s_b)  # , dealer_id, d_e)
            best_rate = s_b and best_rate * 0.85 or best_rate * 1.25
            mess = 'out off VOLUME= %s for [%s]->[%s].' % (volume_in, curr_in.abbrev, curr_out.abbrev)
            mess = mess + ' I use RATE for 0.001 coins -15% = '
            mess = mess + '%s' % best_rate
            print mess
        else:
            mess = '[%s]->[%s] best rate NOT found!' % (curr_in.abbrev, curr_out.abbrev)
            print mess
            return rate, mess, pair, txs, efee
    volume_out = volume_in * best_rate
    rate = round(volume_in / volume_out, 8)  # тут обратный курс сразу берем
    return rate, mess, pair, txs, efee
    #################################################


#######################################################
def get_best_price_by_volume_out(db, curr_in_id, curr_out_id, volume_out, dealer_id, s_b_in=None):
    best_rate = pairs = taxs = fee_ed = None
    if curr_in_id == curr_out_id:
        best_rate = 1.0
        return best_rate, pairs, taxs, fee_ed
    # берем в расчет только недавние цены
    expired = datetime.now() - timedelta(0, 360)
    pr_b, pr_s, pr_avg = rates_lib.get_average_rate_bsa(db, curr_in_id, curr_out_id, expired)
    # print pr_b, pr_s, pr_avg
    if not pr_b:
        return best_rate, pairs, taxs, fee_ed
    volume_in = volume_out / Decimal(pr_b)
    # print volume_in, volume_out, pr_b
    s_b = s_b_in == None and True or s_b_in
    d_e = None
    # тут уже с учетом комиссии вывода с биржи на фиат
    # и с учетом комисии конвертаций через кросс-курсы
    best_rate, pairs, taxs, fee_ed = get_best_price_for_volume(
        db, curr_in_id, curr_out_id, volume_in, expired, s_b, dealer_id, d_e)
    # print best_rate, pairs, taxs
    return best_rate, pairs, taxs, fee_ed


# тут надо все таксы учесть
def get_fees_for_out(db, deal, dealer_deal, curr_in, curr_out, volume_out, rate, pairs, taxs, fee_ed):
    rate = float(rate)
    info = []
    if curr_in.id == curr_out.id:
        return volume_out, rate, info
    # здесь уже в курсе учтены такса биржи и такса вывода с биржи на диллера
    # теперь добавим таксу диллера для этого дела и наши таксы все
    vol = float(volume_out)
    # добавим наш оброк на дело
    fee = float(deal and deal.fee or 0)
    if fee:
        vol = vol + fee
        if fee > 0:
            mess = T('+ плата сервису %s[%s] по делу "%s". ')
        else:
            mess = T('+ бонус сервиса Вам %s[%s] по делу "%s". ')
        info.append(mess % (abs(fee), curr_out.abbrev, deal.name))

    # добавим наш оброк на вывод
    fee = float(curr_out.fee_out or 0)
    if fee:
        vol = vol + fee
        if fee > 0:
            mess = T('+ плата сервису %s[%s]. ')
        else:
            mess = T('+ бонус сервиса %s[%s]. ')
        info.append(mess % (abs(fee), curr_out.abbrev))

    # добавим таксу диллера за это дело
    tax = float(dealer_deal and dealer_deal.tax or 0)
    if tax:
        info.append(('+ %s' % tax) + '% ' + T('мзда диллера электронных денег за перевод на "%s". ') % (deal.name))
        tax_fee = vol * tax * 0.01
        fee_max = dealer_deal.fee_max
        fee_min = dealer_deal.fee_min
        fee_mess = ''
        if fee_max and tax_fee > fee_max:
            tax_fee = fee_max
            fee_mess = 'fee_max %s' % fee_max
        elif fee_min and tax_fee < fee_min:
            tax_fee = fee_min
            fee_mess = 'fee_min %s' % fee_min
        if fee_mess:
            info.append('Tax limited to %s' % fee_mess)
        vol += tax_fee
    fee = dealer_deal.fee
    if fee:
        vol += fee
        info.append('Edealer fee %s' % fee)

    # добавим таксу нашу на вывод валюты
    tax = float(curr_out.tax_out or 0)
    if tax:
        vol *= 1.0 + tax * 0.01
        if tax > 0:
            mess = T('такса сервиса за вывод валюты [%s]. ')
        else:
            mess = T('бонус от сервиса за вывод валюты [%s]. ')
        info.append(('+ %s' % tax) + '% ' + mess % curr_out.abbrev)

    # теперь посмотрим сколько надо входа:
    vol_in = vol / rate
    info.append(T('Расчетный курс: %s с учетом комиссии бирж') % rate)
    # print pairs, taxs
    if taxs and len(taxs) > 0:
        info.append(T(': {'))
        i = 0
        for tax in taxs:
            pair = pairs[i]
            curr_out = db.currs[pair['curr2_id']]
            i = i + 1
            for exchg_name, vol in tax.iteritems():
                ss = '%s ->[%s]: %s' % (exchg_name, curr_out.abbrev, vol * 100)
                info.append(ss + '%; ')
        info.append(' ')
        info.append('} и')

    if fee_ed:
        # тут значение не в процентах, поэтому умножим на 100
        info.append(T(' вывода с биржи %s: %s') % (exchg_name, fee_ed * 100) + '%. ')

    # тепеь добавим таксы на вход - в обратном порядке от выхода накрутки
    tax = float(curr_in.tax_in or 0)
    if tax:
        vol_in = vol_in * (1.0 + tax * 0.01)
        if tax > 0:
            mess = T('+ такса сервиса %s')
        else:
            mess = T('- бонус от сервиса %s')
        info.append((mess % tax) + '% ' + T('от входа [%s]. ') % (curr_in.abbrev))
    # это такса за создание заказа и столбление курса в заказе
    fee = float(curr_in.fee_in or 0)
    if fee:
        vol_in += fee
        if fee > 0:
            mess = T('+ плата за выход %s[%s]. ')
        else:
            mess = T('+ бонус за вход %s[%s]. ')
        info.append(mess % (fee, curr_in.abbrev))

    # пересчитаем курс тогда
    rate_out = float(volume_out) / vol_in
    vol_in = round(vol_in, 8)
    return vol_in, round(rate_out, 8), info


# взять все оброки и таксы при расчете от входящего количества монет
# тут уже учтено комиссия биржы и комиссия вывода
def use_fees_for_in(db, deal, dealer_deal, curr_in, curr_out, vol_in, rate, mess_in=None):
    mess = mess_in or ''
    if curr_in.id == curr_out.id:
        return vol_in, mess
    vol_in = float(vol_in)
    ''' для свободных входов - без закзаз - они идут по входам - НЕ БЕРЕМ эту таксу
    # это такса за создание заказа и столбление курса в заказе
    fee = float(curr_in.fee_in or 0)
    if fee >0:
        vol_in = vol_in + fee
    print deal
    print dealer_deal
    print curr_in
    print curr_out
    '''
    # тепеь добавим таксы на вход - в обратном порядке от выхода накрутки
    tax = float(curr_in.tax_in or 0)
    if tax > 0:
        vol_in = vol_in * (1.0 - tax * 0.01)
        mess = mess + T('Комиссия на вход: %s') % tax + '% . '
    elif tax < 0:
        vol_in = vol_in * (1.0 - tax * 0.01)
        mess = mess + T('+Бонус на вход: %s') % -tax + '% . '

    # теперь посмотрим сколько получили выхода:
    vol = vol_in * float(rate)
    mess = mess + T('(прямой курс: x%s, обратный курс: /%s ). ') % (rate, 1 / rate)

    # добавим таксу нашу на вывод валюты
    tax = float(curr_out.tax_out or 0)
    if tax > 0:
        vol = vol * (1.0 - tax * 0.01)
        mess = mess + T('Комиссия на выход: %s') % tax + '% . '
    elif tax < 0:
        vol = vol * (1.0 - tax * 0.01)
        mess = mess + T('+Бонус на выход: %s') % -tax + '% . '

    ''' не учитываем диллера так как рубли к нам уже пришли за вычетом их комисии
    # добавим таксу диллера за это дело
    tax = float(dealer_deal and dealer_deal.tax or 0)
    if tax >0:
        vol = vol * (1.0 - tax*0.01)
        mess = mess + T('Комиссия диллера: %s') % tax + '% . '
    '''

    # добавим наш оброк на вывод
    fee = float(curr_out.fee_out or 0)
    if fee > 0:
        vol = vol - fee
        mess = mess + T('Плата за вывод: %s [%s]. ') % (fee, curr_out.abbrev)

    # добавим наш оброк на дело
    fee = float(deal and deal.fee or 0)
    if fee > 0:
        vol = vol - fee
        mess = mess + T('Плата по делу: %s. ') % fee

    vol_out = vol

    return vol_out, mess


###################################
##
# уменьшим выходной платеж на таксу диллера для этого дела
def dealer_deal_tax_add(db, T, fee_rate, dealer_deal, abbrev_out, vol, mess, note=None, only_tax=None):
    if not dealer_deal:
        return vol, mess

    use_fee = not only_tax
    tax = dealer_deal.tax or 0
    if tax:
        ## у него только накрутка может быть - поэтому только больше 0
        if note:
            mess += '-' + T('Мзда диллера') + ': %s' % tax + '% '
        ## тут берем функуию MU
        tax_fee = vol - vol / (1 + tax * Decimal(0.01))

        # тут валюта мзды может быть другой
        fee_min = use_fee and dealer_deal.fee_min or 0
        fee_max = use_fee and dealer_deal.fee_max or 0
        if fee_min:
            # приведем к валюте выхода
            fee_min *= fee_rate
        if fee_max:
            # приведем к валюте выхода
            fee_max *= fee_rate
        if fee_min and abs(tax_fee) < abs(fee_min):
            tax_fee = fee_min
            if note:
                mess += '(' + T('ограничено снизу') + ' %s[%s])' % (abs(round(float(tax_fee), 2)), abbrev_out)
        elif fee_max and abs(tax_fee) > abs(fee_max):
            tax_fee = fee_max
            if note:
                mess += '(' + T('ограничено сверху') + ' %s[%s])' % (abs(round(float(tax_fee), 2)), abbrev_out)
        else:
            if note:
                mess += ' (=%s[%s])' % (abs(round(float(tax_fee), 2)), abbrev_out)
        vol -= tax_fee
        if note:
            mess += '. '
            # mess += ' %s ' % vol
    fee = use_fee and dealer_deal.fee or 0
    if fee:
        fee *= fee_rate  # для отображения тоже пересчет тут
        vol -= fee
        if note:
            mess += '-' + T('Взято диллером') + ': %s[%s]. ' % (float(fee), abbrev_out)  # + ' %s ' % vol
    return vol, mess


# увеличим платеж на таксу диллера для этого дела - тоесть то что с нас возьмет диллер
def dealer_deal_tax_neg(db, T, fee_rate, dealer_deal, abbrev_out, vol_out, mess, note=None, only_tax=None):
    if not dealer_deal:
        return vol_out, mess

    use_fee = not only_tax
    fee = use_fee and dealer_deal.fee or 0
    if fee:
        fee *= fee_rate
        vol_out += fee
        if note:
            mess += '-' + T('Взято диллером') + ': %s[%s]. ' % (float(fee), abbrev_out)  # + ' %s ' % vol_out
    tax = dealer_deal.tax or 0
    if tax:
        ## у него только накрутка может быть - поэтому только больше 0
        if note:
            mess += '-' + T('Мзда диллера') + ': %s' % tax + '% '
        fee_min = use_fee and dealer_deal.fee_min or 0
        fee_max = use_fee and dealer_deal.fee_max or 0
        tax_fee = vol_out * tax * Decimal(0.01)
        # приведем к валюте мзды дела
        if fee_min: fee_min *= fee_rate
        if fee_max: fee_max *= fee_rate
        if fee_min and abs(tax_fee) < abs(fee_min):
            tax_fee = fee_min
            if note:
                mess += '(' + T('ограничено снизу') + ' %s[%s])' % (abs(round(float(tax_fee), 2)), abbrev_out)
        elif fee_max and abs(tax_fee) > abs(fee_max):
            tax_fee = fee_max
            if note:
                mess += '(' + T('ограничено сверху') + ' %s[%s])' % (abs(round(float(tax_fee), 2)), abbrev_out)
        else:
            if note:
                mess += ' (=%s[%s])' % (abs(round(float(tax_fee), 2)), abbrev_out)
        vol_out += tax_fee
        if note:
            mess += '. '
            # mess += ' %s ' % vol_out
    return vol_out, mess


# взять все оброки и таксы при расчете от входящего количества монет
# тут уже учтено комиссия биржы и комиссия вывода
# is_order - если есть заказ на курс - не пашет
# note = None - не делать сообщение для человека
# порядок взятия мзды
# curr_in -fee_in /fax_in
# далее обмен - rate
# curr_out - /fax_in -fee_in  # в обратном порядке - тоесть сначала таксу %% а потом абсолютное значение минусуем
# +deal
# +dealer_deal OR NONE - если НОНЕ то такую сумму снимет с нам диллер даже ксли у него такса
# но мы должны дать диллеру на вход сумму с учтенными его таксми - задаем dealer_deal
def calc_fees(db, deal, dealer_deal, curr_in, curr_out, vol_in, rate, is_order=None, note=None, only_tax=None):
    vol_in = Decimal(vol_in)
    use_fee = not only_tax
    rate = Decimal(rate)

    mess = ''
    ## нет! таксы считаем все рравно if curr_in.id == curr_out.id:
    ##    return vol_in, mess
    fee_curr = db.currs[deal.fee_curr_id]
    fee_rate = Decimal(rates_lib.get_avr_rate_or_null(db, fee_curr.id, curr_out.id))
    ##print 'fee_rate', fee_rate
    abbrev_in = curr_in.abbrev
    # это такса за создание заказа и столбление курса в заказе
    fee = use_fee and curr_in.fee_in or 0
    if fee:
        vol_in -= fee
        if note:
            if fee > 0:
                m = '-' + T('Взято с входа')
            else:
                m = '+' + T('Скидка с входа')
            mess += m + ' %s[%s]. ' % (abs(float(fee)), abbrev_in)  # + ' %s ' % vol_in

    # тепеь добавим таксы на вход - в обратном порядке от выхода накрутки
    tax = curr_in.tax_in or 0
    if tax:
        vol_in -= vol_in * tax * Decimal(0.01)
        if note:
            if tax > 0:
                m = '-' + T('Взято за вход')
            else:
                m = '+' + T('Дар за вход')
            mess += m + ' [' + abbrev_in + ']: %s' % abs(float(tax)) + '%. '  # + ' %s ' % vol_in

    # теперь посмотрим сколько получили выхода:
    vol = vol_in * rate
    if note:
        mess += T('Прямой курс') + ': x%s' % float(rate) + ', ' + T('Обратный курс') + ': /%s. ' % float(1 / rate)

    # добавим наш оброк на вывод
    abbrev_out = curr_out.abbrev

    # теперь доход нам за это дело
    # добавим таксу нашу на вывод валюты
    tax = curr_out.tax_out or 0
    if tax:
        vol -= vol * tax * Decimal(0.01)
        if note:
            if tax > 0:
                m = ' -' + T('Взято за выход')
            else:
                m = ' +' + T('Дар за выход')
            mess += m + ' [' + abbrev_out + ']: %s' % abs(float(tax)) + '%. '  # + ' %s ' % vol

    fee = use_fee and curr_out.fee_out or 0
    if fee:
        vol -= fee
        if note:
            if fee > 0:
                m = '-' + T('Взято с выхода')
            else:
                m = '+' + T('Скидка с выхода')
            mess += m + ' %s[%s]. ' % (abs(float(fee)), abbrev_out)  # + ' %s ' % vol

    # добавим наш заработок с этого дела
    tax = deal.tax or 0
    if tax:
        if note:
            if tax > 0:
                m = '-' + T('Взято за это дело')
            else:
                m = '+' + T('Дар на это дело')
            mess += m + ': %s' % abs(float(tax)) + '% '
        # хдесь относительное поэтому без приведения к курсу fee_rate
        tax_fee = vol * tax * Decimal(0.01)
        # тут валюта мзды может быть другой
        fee_min = use_fee and deal.fee_min or 0
        fee_max = use_fee and deal.fee_max or 0
        if fee_min:
            # приведем к валюте выхода
            fee_min *= fee_rate
        if fee_max:
            # приведем к валюте выхода
            fee_max *= fee_rate
        # теперь проверим на превышения
        if fee_min and abs(tax_fee) < abs(fee_min):
            tax_fee = fee_min
            if note:
                mess += ' (' + T('ограничено снизу') + ': %s[%s])' % (abs(round(float(tax_fee), 8)), abbrev_out)
        elif fee_max and abs(tax_fee) > abs(fee_max):
            tax_fee = fee_max
            if note:
                mess += '(' + T('ограничено сверху') + ': %s[%s])' % (abs(round(float(tax_fee), 8)), abbrev_out)
        else:
            if note:
                mess += ' (=%s[%s])' % (abs(round(float(tax_fee), 8)), abbrev_out)
        vol -= tax_fee
        if note:
            mess += '. '
            # mess += ' %s ' % vol
    fee = use_fee and deal.fee or 0
    if fee:
        # приведем к валюте выхода
        fee *= fee_rate  # для отображения тоже пересчет тут
        vol -= fee
        if note:
            if fee > 0:
                m = '-' + T('Взято за эту услугу')
            else:
                m = '+' + T('Дар на эту услугу')
            mess += m + ': %s[%s]. ' % (abs(float(fee)), abbrev_out)  # + ' %s ' % vol

    # мзда диллера - то что он снимает с нас свыше суммы платежа
    if dealer_deal:
        vol, mess = dealer_deal_tax_add(db, T, fee_rate, dealer_deal, abbrev_out, vol, mess, note, only_tax)

    return vol, mess


#############################################
# взять все оброки и таксы при расчете от ВЫходящего количества монет
# тоесть обратный отсчет
# тут уже учтено комиссия биржы и комиссия вывода
# is_order - если есть заказ на курс
# note = None - не делать сообщение для человека
# порядок взятия мзды
# curr_in -fee_in /fax_in
# далее обмен - rate
# curr_out - /fax_in -fee_in  # в обратном порядке - тоесть сначала таксу %% а потом абсолютное значение минусуем
# +deal
# +dealer_deal
def calc_fees_back(db, deal, dealer_deal, curr_in, curr_out, vol_out, rate, is_order=None, note=None, only_tax=None):
    vol_out = Decimal(vol_out)
    rate = Decimal(rate)
    use_fee = not only_tax

    mess = ''
    ## НЕТ таксы все равно считаем if curr_in.id == curr_out.id:
    ##    return vol_out, mess

    abbrev_out = curr_out.abbrev
    fee_curr = db.currs[deal.fee_curr_id]
    fee_rate = Decimal(rates_lib.get_avr_rate_or_null(db, fee_curr.id, curr_out.id))

    ##print 'back - fee_rate', fee_rate, fee_curr.abbrev, abbrev_out
    ################ BACK ##################################
    ## сделано перестановкой от оригинала и - на + поменял
    # мзда диллера - то что он снимает с нас свыше суммы платежа
    if dealer_deal:
        vol_out, mess = dealer_deal_tax_neg(db, T, fee_rate, dealer_deal, abbrev_out, vol_out, mess, note, only_tax)

    fee = use_fee and deal.fee or 0
    if fee:
        fee *= fee_rate
        vol_out += fee
        if note:
            if fee > 0:
                m = '-' + T('Взято за эту услугу')
            else:
                m = '+' + T('Дар на эту услугу')
            mess += m + ': %s[%s]. ' % (abs(float(fee)), abbrev_out)  # + ' %s ' % vol_out

    # добавим наш заработок с этого дела
    tax = deal.tax or 0
    if tax:
        if note:
            if tax > 0:
                m = '-' + T('Взято за это дело')
            else:
                m = '+' + T('Дар на это дело')
            mess += m + ': %s' % abs(float(tax)) + '% '
        fee_min = use_fee and deal.fee_min or 0
        fee_max = use_fee and deal.fee_max or 0
        # Приведем к валюте Мзды Дела
        if fee_min: fee_min *= fee_rate
        if fee_max: fee_max *= fee_rate
        ## тут берем функуию MU
        tax_fee = vol_out / (1 - tax * Decimal(0.01)) - vol_out
        if fee_min and abs(tax_fee) < abs(fee_min):
            tax_fee = fee_min
            if note:
                mess += ' (' + T('ограничено снизу') + ': %s[%s])' % (abs(float(tax_fee)), abbrev_out)
        elif fee_max and abs(tax_fee) > abs(fee_max):
            tax_fee = fee_max
            if note:
                mess += '(' + T('ограничено сверху') + ': %s[%s])' % (abs(float(tax_fee)), abbrev_out)
        else:
            if note:
                mess += ' (=%s[%s])' % (abs(float(tax_fee)), abbrev_out)
        vol_out += tax_fee
        if note:
            mess += '. '
            # mess += ' %s ' % vol_out

    # добавим наш оброк на вывод
    fee = use_fee and curr_out.fee_out or 0
    if fee:
        vol_out += fee
        if note:
            if fee > 0:
                m = '-' + T('Взято с выхода')
            else:
                m = '+' + T('Скидка с выхода')
            mess += m + ' %s[%s]. ' % (abs(float(fee)), abbrev_out)  # + ' %s ' % vol_out

    # теперь доход нам за это дело
    # добавим таксу нашу на вывод валюты
    tax = curr_out.tax_out or 0
    if tax:
        ## тут берем функуию MU
        vol_out = vol_out / (1 - tax * Decimal(0.01))  ## vol_out*tax*Decimal(0.01)
        if note:
            if tax > 0:
                m = ' -' + T('Взято за выход')
            else:
                m = ' +' + T('Дар за выход')
            mess += m + ' [' + abbrev_out + ']: %s' % abs(float(tax)) + '%. '  # + ' %s ' % vol_out

    # теперь посмотрим сколько получили выхода:
    vol = vol_out / rate
    if note:
        mess += T('Прямой курс') + ': x%s' % float(rate) + ', ' + T('Обратный курс') + ': /%s. ' % float(1 / rate)

    abbrev_in = curr_in.abbrev
    # тепеь добавим таксы на вход - в обратном порядке от выхода накрутки
    tax = curr_in.tax_in or 0
    if tax:
        ## тут берем функуию MU
        vol = vol / (1 - tax * Decimal(0.01))  ## vol*tax*Decimal(0.01)
        if note:
            if tax > 0:
                m = '-' + T('Взято за вход')
            else:
                m = '+' + T('Дар за вход')
            mess += m + ' [' + abbrev_in + ']: %s' % abs(float(tax)) + '%. '  # + ' %s ' % vol

    # это такса за создание заказа и столбление курса в заказе
    fee = use_fee and curr_in.fee_in or 0
    if fee:
        vol += fee
        if note:
            if fee > 0:
                m = '-' + T('Взято с входа')
            else:
                m = '+' + T('Скидка с входа')
            mess += m + ' %s[%s]. ' % (abs(float(fee)), abbrev_in)

    return vol, mess

#

# test2()

# print db(db.exchg_pairs.id==1).select().first().s1
# db(db.exchg_pairs.id==1).update(s1='999')
# db.commit()
