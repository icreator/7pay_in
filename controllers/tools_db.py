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

    if (remote_addr not in hosts) and (remote_addr not in TRUST_IP):
        #and request.function != 'manage':
        if vvv: raise HTTP(200, T('ERROR: not admin in local'))
        return True

# запустим сразу защиту от внешних вызов
if False:
    not_is_local(True)
# тут только то что на локалке


# попробовать что-либо вида
def index():
    #err(1)
    return dict(message="repopulate_db")


def repopulate_db():

    #########################################
    if db(db.exchgs).isempty():
        db.exchgs.truncate('RESTART IDENTITY CASCADE')

    if db(db.exchg_taxs).isempty():
        db.exchg_taxs.truncate('RESTART IDENTITY CASCADE')

    if db(db.exchg_pair_bases).isempty():
        db.exchg_pair_bases.truncate('RESTART IDENTITY CASCADE')

    if db(db.dealers).isempty():
        db.dealers.truncate('RESTART IDENTITY CASCADE')
        #db.dealers_accs.truncate('RESTART IDENTITY CASCADE)
        #db.clients_ewallets.truncate('RESTART IDENTITY CASCADE)
        #db.dealers_accs_trans.truncate('RESTART IDENTITY CASCADE)
        #db.dealer_deals.truncate('RESTART IDENTITY CASCADE)
        #db.pay_outs.truncate('RESTART IDENTITY CASCADE)

    if db(db.systems).isempty():
        db.systems.truncate('RESTART IDENTITY CASCADE')

    if db(db.deals_cat).isempty():
        db.deals_cat.truncate('RESTART IDENTITY CASCADE')

    if db(db.deals).isempty():
        db.deals.truncate('RESTART IDENTITY CASCADE')

    if db(db.currs).isempty():
        db.currs.truncate('RESTART IDENTITY CASCADE')

        xpass = 'login:password'
        for r in [
            ['USD', 'US dollar', 'usd', True], #1
            ['RUB', 'Ruble', 'ruble', True], #2
            ['BTC', 'Bitcoin', 'bitcoin', True, #3
             ['13', 'http://%s@127.0.0.1:8332' % xpass, 600, 0.0007000, 1, 101, 0],
             None,
             ],
            ['LTC', 'Litecoin', 'litecoin', True, #4
             ['L', 'http://%s@127.0.0.1:9332' % xpass, 150, 0.005, 3, 120, 0],
             None,
             ],
            ['DOGE', 'DOGE', 'doge', True, #5
             ['D9A', 'http://%s@127.0.0.1:9432' % xpass, 30, 0.1, 5, 101, 0],
             None,
             ],
            ['DASH', 'DASH', 'dash', True, #6
             ['', 'http://%s@127.0.0.1:13332' % xpass, 333, 0.005, 3, 101, 0],
             None,
             ],
            ['C01', 'Coin01', 'coin01', True, #7
             ['01', 'http://%s@127.0.0.1:11111' % xpass, 60, 0.1, 3, 101, 0],
             None,
             ],
            ['NVC', 'Novacoin', 'novacoin', True, #8
             ['4', 'http://%s@127.0.0.1:11332' % xpass, 450, 0.1, 3, 120, 0],
             None,
             ],
            ['ERA', 'ERA', 'ERA', True, # Erachain ERA
             ['', 'erachain ERA' % xpass, 0, 0, 2, 0, 1],
             None,
             ],
            ['COMPU', 'COMPU', 'COMPU', True, # Erachain COMPU
             ['', 'erachain COMPU' % xpass, 0, 0, 2, 0, 2],
             None,
             ],
            ['@BTC', 'ERA.BTC', 'era.btc', True, # Erachain BTC id 12
             ['', 'era-12' % xpass, 0, 0, 2, 0, 3],
             [1,1,1], # rates
             ],
            ['@1069', 'ERA.Coin1069', 'era.coin-1069', True, # Erachain coin on id=1001 for example http://erachain.org:9047/index/blockexplorer.html?asset=1069&lang=en
             ['', 'era-69' % xpass, 0, 0, 2, 0, 4],
             None,
             ],
        ]:

            print r[0], r[1], r[2], r[3]

            curr_id = db.currs.insert( abbrev = r[0], name = r[1], name2 = r[2], used=r[3])

            if len(r)>4:
                db.xcurrs.insert(curr_id = curr_id, first_char = r[4][0], connect_url = r[4][1],
                                 block_time=r[4][2], txfee = r[4][3], conf = r[4][4], conf_gen = r[4][5],
                                 as_token=r[4][6])
            else:
                db.ecurrs.insert(curr_id = curr_id)

            ##DAL.distributed_transaction_commit(db)
            db.commit()


    #### TOKENS ####
    if db(db.systems).isempty():

        system_id = db.systems.insert(name = 'Erachain', name2 = 'erachain', first_char = '7',
                                      connect_url = 'http://127.0.0.1:9068', account = '7F9cZPE1hbzMT21g96U8E1EfMimovJyyJ7',
                                      block_time = 288, conf = 2, conf_gen = 0, from_block = 30000)
        for asset in [
            [1, 'ERA'], [2, 'COMPU'],
        ]:
            token_id = db.tokens.insert(system_id = system_id, token_key = asset[0], name = asset[1])
            curr_id = db.currs.insert( abbrev = asset[1], name = asset[1], name2 = asset[1], used=True)
            db.xcurrs.insert(curr_id = curr_id, connect_url = 'erachain ' + asset[1],
                             as_token = token_id,
                             block_time=0, txfee = 0, conf = 0, conf_gen = 0)



    if db(db.exchg_taxs).isempty():
        db.exchg_taxs.insert( curr1_id = 3, curr2_id = 2, tax = 0)
        db.exchg_taxs.insert( curr1_id = 3, curr2_id = 1, tax = 0.5)
        db.exchg_taxs.insert( curr1_id = 4, curr2_id = 3, tax = 1)
        db.exchg_taxs.insert( curr1_id = 8, curr2_id = 3, tax = 1)


    if db(db.exchg_pair_bases).isempty():
        for r in [
            [1, 2, 0, 100, 0.1],
            [1, 3, 0, 100, 0.1],
            [1, 4, 0, 100, 0.1],
            [1, 5, 0, 100, 0.1],
            [1, 6, 0, 100, 0.1],
            [1, 7, 0, 100, 0.1],
            [1, 8, 0, 100, 0.1],
            [2, 1, 0, 10000, 0.1],
            [2, 3, 0, 10000, 0.1],
            [2, 4, 0, 10000, 0.1],
            [2, 5, 0, 10000, 0.1],
            [2, 6, 0, 10000, 0.1],
            [2, 7, 0, 10000, 0.1],
            [2, 8, 0, 10000, 0.1],
            [3, 1, 0, 1, 0.1],
            [3, 2, 0, 1, 0.1],
            [3, 4, 0, 1, 0.1],
            [3, 5, 0, 1, 0.1],
            [3, 6, 0, 1, 0.1],
            [3, 7, 0, 1, 0.1],
            [3, 8, 0, 1, 0.1],
            [4, 3, 0, 333, 0.1],
            [5, 3, 0, 3333, 0.1],
            [6, 3, 0, 3333, 0.1],
            [7, 3, 0, 33, 0.1],
            [8, 3, 0, 333, 0.1],
            [9, 10, 0.001, 1, 0.1],
        ]:
            db.exchg_pair_bases.insert(curr1_id = r[0], curr2_id = r[1], hard_price = r[2], base_vol = r[3], base_perc = r[4])


    #current.CURR_RUB = CURR_RUB = db.currs[ 2 ]
    ##current.CURR_RUB = CURR_RUB = db(db.currs.abbrev == 'RUB').select().first()

    if not CURR_RUB_ID:
        raise HTTP(500, 'currency RUB not found in db1.py')

    if db(db.deals_cat).isempty():
        db.deals_cat.insert(name='Other')
        db.deals_cat.insert(name='Internet')
        db.deals_cat.insert(name='Games')
        db.deals_cat.insert(name='Social')
        db.deals_cat.insert(name='Municipal services')

    if db(db.deals).isempty():
        db.deals.insert(
            fee_curr_id= CURR_RUB_ID, name = 'BUY', name2 = 'to BUY',
            used=False,  not_gifted=True,
            MIN_pay=10,  MAX_pay=2777,
            fee=3,  tax=0.2,  fee_min=0,  fee_max=0)
        db.deals.insert(
            fee_curr_id= CURR_RUB_ID, name = 'to COIN', name2 = 'to COIN',
            used=False,  not_gifted=True,
            MIN_pay=10,  MAX_pay=2777,
            fee=3,  tax=0.2,  fee_min=0,  fee_max=0)
        db.deals.insert(
            fee_curr_id= CURR_RUB_ID, name = 'WALLET', name2 = 'to WALLET',
            used=False,  not_gifted=True,
            MIN_pay=10,  MAX_pay=2777,
            fee=3,  tax=0.2,  fee_min=0,  fee_max=0)
        db.deals.insert( cat_id = 2,
                         fee_curr_id= CURR_RUB_ID, name = 'phone +7', name2 = 'to PHONE +7',
                         used=False,  not_gifted=True,
                         MIN_pay=10,  MAX_pay=2777,
                         fee=3,  tax=0.2,  fee_min=0,  fee_max=0)

    if db(db.dealers).isempty():
        dealer_id = db.dealers.insert(
            name = 'Yandex',
            used=True,
            API = '{ "URI_YM_API": "https://money.yandex.ru/api", "URI_YM_AUTH": "https://sp-money.yandex.ru/oauth/authorize", "URI_YM_TOKEN": "https://sp-money.yandex.ru/oauth/token", "acc_names": ["user", "PROPERTY1", "rapida_param1", "customerNumber", "CustomerNumber"] }',
            info = '{ "shops_url": "https://money.yandex.ru/shop.xml?scid=", "search_url": "https://money.yandex.ru/", "img_url": "https://money.yandex.ru" }',
            pay_out_MIN = 10)
        db.dealers_accs.insert(dealer_id = dealer_id, ecurr_id = 2, acc = '4100134701234567', balance = 9999999,
                               pkey = '{"YM_REDIRECT_URI": "https://7pay.in/ed_YD/yandex_response", "secret_response": "**secret response**", "CLIENT_ID": "**TOKEN**", "SCOPE": "account-info operation-history operation-details payment-shop.limit(1,37777) payment-p2p.limit(1,37777)"}',
                               used = True, expired = '2216-02-10')

        db.dealer_deals.insert(dealer_id = dealer_id, deal_id = TO_PHONE7_ID, used = False, scid = 'phone-topup', tax = 0.0)
        db.dealer_deals.insert(dealer_id = dealer_id, deal_id = TO_WALLET_ID, used = False, scid = 'p2p',
                               p2p = True, tax = 0.5,
                               template_ = '["not_mod", { "n": "p2p"}]')


    if db(db.exchgs).isempty():
        xpass = 'login:password'
        for r in [
            ['WEX', 'wex.nz', 'btc-e_3', '', True, 0.5, 0.0, [[1,""], [2, "rur"], [3,""], [4,""], [5,""], [6,"dsh"]],
             [[1, 2, True,''], [3, 1, True,''], [3, 2, True,''], [4, 1, True,''], [4, 2, True,''], [4, 3, True,''],
              [5, 3, True,''], [6, 3, True,''], [7, 3, True,''], [8, 3, True,'']]
             ],
            ['Livecoin', 'api.livecoin.net', 'livecoin', 'exchange/ticker', True, 0.2, 0.0, [[1,""], [2, ""], [3,""], [4,""], [5,""], [6,""]]],
            ['Cryptsy', 'cryptsy.com', 'cryptsy', '', False, 1, 0.0, [[5,"DOGE"]]],
            ['Poloniex.com', 'poloniex.com', 'poloniex', '', True, 0.2, 0, [],
             [[3, 5, True,'BTC_DOGE'], [3, 6, True,'BTC_DASH']]
             ]
        ]:

            exchg_id = db.exchgs.insert(name = r[0], url = r[1],
                                        API_type = r[2], API = r[3], used = r[4], tax = r[5],
                                        fee = r[6]
                                        )
            if len(r)>7:
                for ticker in r[7]:
                    db.exchg_limits.insert(exchg_id = exchg_id, curr_id = ticker[0], ticker = ticker[1])
            if len(r)>8:
                for pair in r[8]:
                    db.exchg_pairs.insert(exchg_id = exchg_id, curr1_id = pair[0], curr2_id = pair[1], used = pair[2], ticker = pair[3])

        db.fees.insert(exchg_id = 1, dealer_id = dealer_id, fee_ed = 1, fee_de = 0)
        db.fees.insert(exchg_id = 2, dealer_id = dealer_id, fee_ed = 1, fee_de = 0)
        db.fees.insert(exchg_id = 3, dealer_id = dealer_id, fee_ed = 1, fee_de = 0)
        db.fees.insert(exchg_id = 4, dealer_id = dealer_id, fee_ed = 1, fee_de = 0)

    return "Repopulated"
