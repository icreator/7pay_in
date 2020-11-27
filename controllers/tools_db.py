# coding: utf8

##from __future__ import print_function

if False:
    from gluon import *
    import db

    request = current.request
    response = current.response
    session = current.session
    cache = current.cache
    T = current.T

import socket

session.forget(response)


# vvv=True - включает секртную сессию и выдает страницу ошибки
def not_is_local(vvv=None):
    http_host = request.env.http_host.split(':')[0]
    remote_addr = request.env.remote_addr
    # http_host[7pay.in] remote_addr[91.77.112.36]
    # raise HTTP(200, T('appadmin is disabled because insecure channel http_host[%s] remote_addr[%s]') % (http_host, remote_addr))
    try:
        hosts = (http_host, socket.gethostname(),
                 socket.gethostbyname(http_host),
                 '::1', '127.0.0.1', '::ffff:127.0.0.1')
    except:
        hosts = (http_host,)

    if vvv and (request.env.http_x_forwarded_for or request.is_https):
        session.secure()

    if (remote_addr not in hosts) and (remote_addr not in TRUST_IP):
        # and request.function != 'manage':
        if vvv: raise HTTP(200, T('ERROR: not admin in local'))
        return True


# запустим сразу защиту от внешних вызов
if False:
    not_is_local(True)


# тут только то что на локалке


# попробовать что-либо вида
def index():
    # err(1)
    return dict(message="repopulate_db")


def deals_to_tmp():
    if True:
        return 'stoppper - open me'

    db.deals_tmp.truncate('RESTART IDENTITY CASCADE')  # restart autoincrement ID

    # First deals
    db.deals_tmp.insert(
        fee_curr_id=CURR_RUB_ID, name='BUY', name2='to BUY',
        used=False, not_gifted=True,
        MIN_pay=10, MAX_pay=2777,
        fee=3, tax=0.2, fee_min=0, fee_max=0)
    db.deals_tmp.insert(
        fee_curr_id=CURR_RUB_ID, name='to COIN', name2='to COIN',
        used=False, not_gifted=True,
        MIN_pay=10, MAX_pay=2777,
        fee=3, tax=0.2, fee_min=0, fee_max=0)
    db.deals_tmp.insert(
        fee_curr_id=CURR_RUB_ID, name='WALLET', name2='to WALLET',
        used=False, not_gifted=True,
        MIN_pay=10, MAX_pay=2777,
        fee=3, tax=0.2, fee_min=0, fee_max=0)
    db.deals_tmp.insert(cat_id=1,
                        fee_curr_id=CURR_RUB_ID, name='phone +7', name2='to PHONE +7',
                        used=False, not_gifted=True,
                        MIN_pay=10, MAX_pay=2777,
                        fee=3, tax=0.2, fee_min=0, fee_max=0)
    db.deals_tmp.insert(cat_id=1,
                        fee_curr_id=CURR_USD_ID, name='phone', name2='to PHONE',
                        used=False, not_gifted=True,
                        MIN_pay=1, MAX_pay=2777,
                        fee=3, tax=0.2, fee_min=0, fee_max=0)

    for rec in db(db.deals).select():
        if rec.name == 'BUY' or rec.name == 'to COIN' or rec.name == 'WALLET' or rec.name == 'phone +7' or rec.name == 'phone':
            continue

        rec.fee_curr_id = CURR_RUB_ID
        db.deals_tmp.insert(**rec)

    return 'ok'


def deals_from_tmp():
    if True:
        return 'stoppper - open me'

    db.deals.truncate('RESTART IDENTITY CASCADE')  # restart autoincrement ID

    # if True: return 'stoppper - open me'

    for rec in db(db.deals_tmp).select():
        db.deals.insert(**rec)

    return 'ok from TMP'


def init_db_records():
    #########################################
    if db(db.exchgs).isempty():
        db.exchgs.truncate('RESTART IDENTITY CASCADE')  # restart autoincrement ID

    if db(db.exchg_taxs).isempty():
        db.exchg_taxs.truncate('RESTART IDENTITY CASCADE')

    if db(db.exchg_pair_bases).isempty():
        db.exchg_pair_bases.truncate('RESTART IDENTITY CASCADE')

    if db(db.dealers).isempty():
        db.dealers.truncate('RESTART IDENTITY CASCADE')

    if db(db.systems).isempty():
        db.systems.truncate('RESTART IDENTITY CASCADE')

    if db(db.deals_cat).isempty():
        db.deals_cat.truncate('RESTART IDENTITY CASCADE')

    if db(db.deals).isempty():
        db.deals.truncate('RESTART IDENTITY CASCADE')

    if db(db.currs).isempty():
        db.currs.truncate('RESTART IDENTITY CASCADE')
        db.deals_cat.truncate('RESTART IDENTITY CASCADE')
        db.systems.truncate('RESTART IDENTITY CASCADE')
        db.exchgs.truncate('RESTART IDENTITY CASCADE')

        xpass = 'login:password'
        for r in [
            ['USD', 'US dollar', 'usd', True],  # 1
            ['RUB', 'Ruble', 'ruble', True],  # 2
            ['BTC', 'Bitcoin', 'bitcoin', True,  # 3
             ['13', None, 'http://%s@127.0.0.1:8332' % xpass, 600, 0.0007000, 1, 101, 0],
             None,
             ],
            ['LTC', 'Litecoin', 'litecoin', True,  # 4
             ['L', None, 'http://%s@127.0.0.1:9332' % xpass, 150, 0.005, 3, 120, 0],
             None,
             ],
            ['DOGE', 'DOGE', 'doge', True,  # 5
             ['D9A', None, 'http://%s@127.0.0.1:9432' % xpass, 30, 0.1, 5, 101, 0],
             None,
             ],
            ['DASH', 'DASH', 'dash', True,  # 6
             ['', None, 'http://%s@127.0.0.1:13332' % xpass, 333, 0.005, 3, 101, 0],
             None,
             ],
            ['ZEN', 'Horizen', 'horizen', True,  # 7
             ['Z', 'zen', 'http://%s@127.0.0.1:11111' % xpass, 300, 0.1, 3, 101, 0],
             None,
             ],
            ['NVC', 'Novacoin', 'novacoin', False,  # 8 - False - if not used on service
             ['4', None, 'http://%s@127.0.0.1:11332' % xpass, 450, 0.1, 3, 120, 0],
             None,
             ],
            # The Erachain tiokens will set below
        ]:

            curr_id = db.currs.insert(abbrev=r[0], name=r[1], name2=r[2], used=r[3])

            if len(r) > 4:
                db.xcurrs.insert(curr_id=curr_id, first_char=r[4][0], protocol=r[4][1], connect_url=r[4][2],
                                 block_time=r[4][3], txfee=r[4][4], conf=r[4][5], conf_gen=r[4][6],
                                 as_token=r[4][7])
            else:
                db.ecurrs.insert(curr_id=curr_id)

    #### TOKENS ####
    if db(db.systems).isempty():

        #####  Ethereum
        name = 'ethereum'
        system_id = db.systems.insert(name='Ethereum', name2=name, first_char='0x',
                                      connect_url='http://localhost:8545',  # for Testnet use http://127.0.0.1:9068
                                      password='123456789',
                                      block_time=60, conf=2, conf_gen=64,
                                      from_block=1000000  # for Testnet use 0
                                      )

        for asset in [
            [1, 'ETH']
        ]:
            token_id = db.tokens.insert(system_id=system_id, token_key=asset[0], name=asset[1])
            curr_id = db.currs.insert(abbrev=asset[1], name=asset[1], name2=asset[1], used=True)
            db.xcurrs.insert(curr_id=curr_id, protocol='', connect_url=name + ' ' + asset[1],
                             as_token=token_id,
                             block_time=0, txfee=0, conf=0, conf_gen=0)

        ##### Set ERACHAIN tokens and stablecoins
        # see http://erachain.org:9047/index/blockexplorer.html?assets=&lang=en&start=25
        name = 'erachain'
        system_id = db.systems.insert(name='Erachain', name2=name, first_char='7',
                                      connect_url='http://127.0.0.1:9048',  # for Testnet use http://127.0.0.1:9068
                                      account='7F9cZPE1hbzMT21g96U8E1EfMimovJyyJ7',
                                      password='123456789',
                                      block_time=30, conf=1, conf_gen=0,
                                      from_block=1000000  # for Testnet use 0
                                      )
        for asset in [
            [1, 'ERA'], [2, 'COMPU'], [12, '@BTC'],  # @BTC etc is stablecoins
            [95, '@USD'], [92, '@RUB'], [14, '@ETH'], [16, '@ZEN'],
            [1064, 'WWP']  ## examole for asset http://erachain.org:9047/index/blockexplorer.html?asset=1064&lang=en
        ]:
            token_id = db.tokens.insert(system_id=system_id, token_key=asset[0], name=asset[1])
            curr_id = db.currs.insert(abbrev=asset[1], name=asset[1], name2=asset[1], used=True)
            db.xcurrs.insert(curr_id=curr_id, protocol='', connect_url=name + ' ' + asset[1],
                             as_token=token_id,
                             block_time=0, txfee=0, conf=0, conf_gen=0)

    if db(db.exchg_taxs).isempty():
        db.exchg_taxs.insert(curr1_id=3, curr2_id=2, tax=0)
        db.exchg_taxs.insert(curr1_id=3, curr2_id=1, tax=0.5)
        db.exchg_taxs.insert(curr1_id=4, curr2_id=3, tax=1)
        db.exchg_taxs.insert(curr1_id=8, curr2_id=3, tax=1)

    if db(db.exchg_pair_bases).isempty():
        # set directions of exchanges and HARD PRICE for direction
        for r in [
            ['USD', 'RUB', 0, 100, 0.1],
            ['USD', 'BTC', 0, 100, 0.1],
            ['USD', 'ETH', 0, 100, 0.1],
            ['USD', 'LTC', 0, 100, 0.1],
            ['USD', 'DOGE', 0, 100, 0.1],
            ['USD', 'DASH', 0, 100, 0.1],
            ['USD', 'ZEN', 0, 100, 0.1],
            ['USD', 'NVC', 0, 100, 0.1],
            ['RUB', 'USD', 0, 10000, 0.1],
            ['RUB', 'BTC', 0, 10000, 0.1],
            ['RUB', 'ETH', 0, 10000, 0.1],
            ['RUB', 'LTC', 0, 10000, 0.1],
            ['RUB', 'DOGE', 0, 10000, 0.1],
            ['RUB', 'DASH', 0, 10000, 0.1],
            ['RUB', 'ZEN', 0, 10000, 0.1],
            ['RUB', 'NVC', 0, 10000, 0.1],
            ['BTC', 'USD', 0, 1, 0.1],
            ['BTC', 'RUB', 0, 1, 0.1],
            ['BTC', 'ETH', 0, 1, 0.1],
            ['BTC', 'LTC', 0, 1, 0.1],
            ['BTC', 'DOGE', 0, 1, 0.1],
            ['BTC', 'DASH', 0, 1, 0.1],
            ['BTC', 'ZEN', 0, 1, 0.1],
            ['BTC', 'NVC', 0, 1, 0.1],
            ['LTC', 'BTC', 0, 333, 0.1],
            ['DOGE', 'BTC', 0, 3333, 0.1],
            ['DASH', 'BTC', 0, 3333, 0.1],
            ['ZEN', 'BTC', 0, 33, 0.1],
            ['NVC', 'BTC', 0, 333, 0.1],
            ['ERA', 'COMPU', 0.001, 100, 0.1],
            ['ERA', 'USD', 0.5, 100, 0.1],
            ['COMPU', 'USD', 100, 1, 0.1],
            ['BTC', '@BTC', 1, 10, 0.1],
            ['@BTC', 'BTC', 1, 10, 0.1],
            ['ZEN', '@ZEN', 1, 100, 0.1],
            ['@ZEN', 'ZEN', 1, 100, 0.1],
            ['USD', '@USD', 1, 1000, 0.1],
            ['@USD', 'USD', 1, 1000, 0.1],
            ['RUB', '@RUB', 1, 10000, 0.1],
            ['@RUB', 'RUB', 1, 10000, 0.1],
        ]:
            curr1 = db(db.currs.abbrev == r[0]).select().first()
            if not curr1:
                return 'exchg_pair_bases - not found', r[0]
            curr2 = db(db.currs.abbrev == r[1]).select().first()
            if not curr2:
                return 'exchg_pair_bases - not found', r[1]
            db.exchg_pair_bases.insert(curr1_id=curr1.id, curr2_id=curr2, hard_price=r[2], base_vol=r[3],
                                       base_perc=r[4])

    if not CURR_RUB_ID:
        raise HTTP(500, 'currency RUB not found in db1.py')

    if db(db.deals_cat).isempty():
        db.deals_cat.insert(name='Прочее')  # 1 Other
        db.deals_cat.insert(name='Игры, Онлайн игры')  # 2 Games
        db.deals_cat.insert(name='Интерент, Связь, Телефония')  # 3 Internet
        db.deals_cat.insert(name='Социальные Сети, Знакомства, Объявления')  # 4 Social Network
        db.deals_cat.insert(name='Магазины')  # 5 Shops
        db.deals_cat.insert(name='Коммунально-бытовые услуги')  # 6 Municipal services
        db.deals_cat.insert(name='Билеты в кино, театры, Развлечения')  # 7 Cinema
        db.deals_cat.insert(name='Благотворительнсть')  # 8 Charity
        db.deals_cat.insert(name='Банки, Финансы, Платежи, Штрафы')  # 9 Banks, Financial
        db.deals_cat.insert(name='Программное обеспечение')  # 10 Soft
        db.deals_cat.insert(name='Проездный билеты')  # 11 Bus pass

    if db(db.deals).isempty():
        db.deals.insert(
            fee_curr_id=CURR_RUB_ID, name='BUY', name2='to BUY',
            used=False, not_gifted=True,
            MIN_pay=10, MAX_pay=2777,
            fee=3, tax=0.2, fee_min=0, fee_max=0)
        db.deals.insert(
            fee_curr_id=CURR_RUB_ID, name='to COIN', name2='to COIN',
            used=False, not_gifted=True,
            MIN_pay=10, MAX_pay=2777,
            fee=3, tax=0.2, fee_min=0, fee_max=0)
        db.deals.insert(
            fee_curr_id=CURR_RUB_ID, name='WALLET', name2='to WALLET',
            used=False, not_gifted=True,
            MIN_pay=10, MAX_pay=2777,
            fee=3, tax=0.2, fee_min=0, fee_max=0)
        db.deals.insert(cat_id=2,
                        fee_curr_id=CURR_RUB_ID, name='phone +7', name2='to PHONE +7',
                        used=False, not_gifted=True,
                        MIN_pay=10, MAX_pay=2777,
                        fee=3, tax=0.2, fee_min=0, fee_max=0)

        ##
        db.currs_stats.insert(curr_id=3, deal_id=2)

    dealer_id = None
    if db(db.dealers).isempty():
        dealer_id = db.dealers.insert(
            name='Yandex',
            used=True,
            API='{ "URI_YM_API": "https://money.yandex.ru/api", "URI_YM_AUTH": "https://sp-money.yandex.ru/oauth/authorize", "URI_YM_TOKEN": "https://sp-money.yandex.ru/oauth/token", "acc_names": ["user", "PROPERTY1", "rapida_param1", "customerNumber", "CustomerNumber"] }',
            info='{ "shops_url": "https://money.yandex.ru/shop.xml?scid=", "search_url": "https://money.yandex.ru/", "img_url": "https://money.yandex.ru" }',
            pay_out_MIN=10)
        db.dealers_accs.insert(dealer_id=dealer_id, ecurr_id=2, acc='4100134701234567', balance=9999999,
                               pkey='{"YM_REDIRECT_URI": "https://7pay.in/ed_YD/yandex_response", "secret_response": "**secret response**", "CLIENT_ID": "**TOKEN**", "SCOPE": "account-info operation-history operation-details payment-shop.limit(1,37777) payment-p2p.limit(1,37777)"}',
                               used=True, expired='2216-02-10')

        db.dealer_deals.insert(dealer_id=dealer_id, deal_id=TO_PHONE7_ID, used=False, scid='phone-topup', tax=0.0)
        db.dealer_deals.insert(dealer_id=dealer_id, deal_id=TO_WALLET_ID, used=False, scid='p2p',
                               p2p=True, tax=0.5,
                               template_='["not_mod", { "n": "p2p"}]')
    else:
        dealer_id = db.dealers[1].id

    if db(db.exchgs).isempty():
        # SET Exhanges pairs roe API calls
        xpass = 'login:password'
        for r in [
            ['WEX', 'wex.nz', 'btc-e_3', '', False,  # not used now
             0.5, 0.0, [['USD', ""], ['RUB', "rur"], ['BTC', ""], ['LTC', ""], ['DOGE', ""], ['DASH', "dsh"]],
             [['USD', 'RUB', False, ''], ['BTC', 'USD', False, ''], ['BTC', 'RUB', False, ''],
              ['LTC', 'BTC', False, ''],
              ['LTC', 'RUB', True, ''], ['LTC', 'BTC', False, ''],
              ['DOGE', 'BTC', False, ''], ['DASH', 'BTC', False, ''], ['ZEN', 'BTC', False, ''],
              ['NVC', 'BTC', True, '']]
             ],
            ['Livecoin', 'api.livecoin.net', 'livecoin', 'exchange/ticker', True, 0.2, 0.0,
             [['USD', ""], ['RUB', ""], ['BTC', ""], ['LTC', ""], ['DOGE', ""], ['DASH', ""]],
             [['BTC', 'RUB', True, ''], ['USD', 'RUB', True, '']]
             ],
            ['Cryptsy', 'cryptsy.com', 'cryptsy', '', False, 1, 0.0, [['DOGE', "DOGE"]]],
            ['Poloniex.com', 'poloniex.com', 'poloniex', '', True, 0.2, 0, [],
             [['USD', 'BTC', True, 'USDT_BTC'], ['BTC', 'LTC', True, 'BTC_LTC'], ['BTC', 'DOGE', True, 'BTC_DOGE'],
              ['BTC', 'DASH', True, 'BTC_DASH']]
             ]
        ]:

            exchg_id = db.exchgs.insert(name=r[0], url=r[1],
                                        API_type=r[2], API=r[3], used=r[4], tax=r[5],
                                        fee=r[6]
                                        )
            if len(r) > 7:
                for ticker in r[7]:
                    curr = db(db.currs.abbrev == ticker[0]).select().first()
                    if not curr:
                        return 'exchg_limits - not found', ticker[0]
                    db.exchg_limits.insert(exchg_id=exchg_id, curr_id=curr.id, ticker=ticker[1])

                if len(r) > 8:
                    for pair in r[8]:
                        curr1 = db(db.currs.abbrev == pair[0]).select().first()
                        if not curr1:
                            return 'exchg_pairs - not found', pair[0]
                        curr2 = db(db.currs.abbrev == pair[1]).select().first()
                        if not curr2:
                            return 'exchg_pairs - not found', pair[1]
                        db.exchg_pairs.insert(exchg_id=exchg_id, curr1_id=curr1.id, curr2_id=curr2.id, used=pair[2],
                                              ticker=pair[3])

        for exhange in db(db.exchgs).select():
            db.fees.insert(exchg_id=exhange.id, dealer_id=dealer_id, fee_ed=1, fee_de=0)

    return "Initiated"
