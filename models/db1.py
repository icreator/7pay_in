# coding: utf8

TXID_LEN = 100

if False:
    ## for off errors in IDEA
    pass

# если ошибка то задаем migrate=False,
# fake_migrate = True
# либо если надо можифицировать какую таблицу, то остальным
# таблицам индивидуально migrate=False,
# после изменения полей и вызова таблицы
# опять закрываем - тогда ДБ быстрее в_орочится
# migrate=False,
'''
db = DAL("sqlite://storage.sqlite",
    pool_size=5,
    migrate=True,
    migrate_enabled=True,
    check_reserved=['all'],
    auto_import=True,
    folder="../databases"    )
'''

from decimal import Decimal

db.define_table('currs',
                Field('abbrev', length=5, unique=True),
                Field('used', 'boolean', default=False, comment='used by site'),
                Field('name', length=25, unique=True),
                Field('name2', length=25, unique=True,
                      comment='lower case for made a links (bitcoin, copperlark)'),
                Field('icon', 'upload'),
                Field('balance', 'decimal(16,8)', default = Decimal(0)),
                Field('deposit', 'decimal(16,8)', default = Decimal(0)), # то что нельзя выводить или продавать - запас для меня
                Field('clients_deposit', 'decimal(16,8)', default = Decimal('0.0')), # то что нельзя выводить или продавать так как это баланс клиеннтов-магазинов
                Field('max_bal', 'decimal(16,8)', default = Decimal(0), comment='if reached - stop payouts'), #если больше уже о не делать выплаты
                Field('fee_in', 'decimal(10,8)', default = Decimal(0.001), comment='into me'),
                Field('fee_out', 'decimal(10,8)', default = Decimal(0.001), comment='out me'),
                Field('tax_in', 'decimal(4,2)', default = Decimal(0), comment='% tax for sell coins to me'),
                Field('tax_out', 'decimal(4,2)', default = Decimal(0.01), comment='% tax for buy my coins'),
                Field('uses', 'integer', default = 0, comment='number of uses'),
                #migrate=False,
                #fake_migrate = True,
                format='%(abbrev)s',
                )

# CRYPTO
db.define_table('systems',
                Field('name', length=25, unique=True, readable=False, comment='name of tokenized system'),
                Field('name2', length=25, readable=False, comment='name for URI'),
                Field('first_char', length=5, readable=False, comment='insert in db.common.get_currs_by_addr !!!'), # для быстрого поиска крипты по адресу
                Field('connect_url', length=99, default='http://user:pass@localhost:3333', unique=True),
                Field('account', length=99, default='7F9cZPE1hbzMT21g96U8E1EfMimovJyyJ7', comment='address for incoming payments'),
                Field('password', length=99),
                Field('block_time', 'integer', comment='in sec. BTC = 600sec'),
                Field('txfee', 'decimal(10,8)', default = Decimal('0.0001'), comment='For one pay_out transaction. Payed to web'),
                Field('conf', 'integer', default = 3, comment='confirmations for accept'),
                Field('conf_gen', 'integer', default = 6, comment='confirmations for accept generated coins'),
                Field('from_block', 'integer', comment='block was tested'),
                format='%(name)s',
                )
db.define_table('tokens',
                Field('system_id', db.systems, ondelete='CASCADE'),
                Field('token_key', 'integer', default=1, comment='ID of token (coin or asset) in that system'),
                Field('name', length=125, readable=False, comment='name of token'),
                format='%(system_id)s:%(token_key)s %(name)s',
                )

# CRYPTO
db.define_table('xcurrs',
                Field('curr_id', db.currs, ondelete='CASCADE'),
                Field('first_char', length=5, readable=False, comment='insert in db.common.get_currs_by_addr !!!'), # для быстрого поиска крипты по адресу
                Field('as_token', 'integer', default=0, comment='ID in db.tokens (if its token, coin or asset)'),
                #Field('balance', 'decimal(16,8)', default = Decimal('0.0')),
                #Field('deposit', 'decimal(16,8)', default = Decimal('0.0')), # то что нельзя выводить или продавать - запас для меня
                #Field('clients_deposit', 'decimal(16,8)', default = Decimal('0.0')), # то что нельзя выводить или продавать так как это баланс клиеннтов-магазинов
                #Field('reserve', 'decimal(4,2)', default = Decimal('0.0')), # 1=100% reserve from RUBles
                Field('connect_url', length=99, default='http://user:pass@localhost:3333', unique=True),
                Field('block_time', 'integer', comment='in sec. BTC = 600sec'),
                Field('txfee', 'decimal(10,8)', default = Decimal('0.0001'), comment='For one pay_out transaction. Payed to web'),
                Field('conf', 'integer', default = 3, comment='confirmations for accept'),
                Field('conf_gen', 'integer', default = 6, comment='confirmations for accept generated coins'),
                Field('from_block', 'integer', comment='block was tested'),
                format='%(curr_id)s %(first_char)s',
                )

# eFIAT
db.define_table('ecurrs',
                Field('curr_id', db.currs, ondelete='CASCADE'),
                format='%(curr_id)s',
                )



#
db.define_table('exchgs',
                Field('name', length=25, unique=True, ondelete='CASCADE'),
                Field('used', 'boolean', default=False, comment='used by site'),
                Field('url', length=55, unique=True),
                Field('tax', 'decimal(4,3)', required=True, default=0.2, comment='tax % for one order'),
                Field('fee', 'decimal(5,3)', required=True, default=0, comment='absolut fee for one order'),
                Field('API_type', length=15, comment='API type = upbit, btce'),
                Field('API', 'text', comment='API commands and urls in JSON format'),
                Field('pkey', 'text', comment='public key'),
                Field('skey', 'text', comment='secret key'),
                format='%(name)s',
                )

# the need set ticker name on this ecchange an limits of reserves and sells
db.define_table('exchg_limits',
                Field('exchg_id', db.exchgs, ondelete='CASCADE'),
                Field('curr_id', db.currs, ondelete='CASCADE'),
                # btc, rur ...
                Field('ticker', length=7, required=True, comment='set TICKET name for this exchange (default = lower(xcurr). ...btc, rur'),
                Field('reserve', 'decimal(16,6)', default = Decimal('0.0'), comment='reserve balance, not sale'),
                Field('sell', 'decimal(16,6)', comment='limit for one sale'),
                Field('buy', 'decimal(16,6)', comment='limit for one buy'),
                format='%(curr_id)s %(ticker)s',
                )


# тут сделаем уникальный сложную проверку
db.exchg_limits.exchg_id.requires=IS_IN_DB(db, 'exchgs.id', '%(name)s',
                                           _and = IS_NOT_IN_DB(db(db.exchg_limits.curr_id==request.vars.curr_id),'exchg_limits.exchg_id'))

db.exchg_limits.curr_id.requires=IS_IN_DB(db, 'currs.id', db.currs._format,
                                          _and = IS_NOT_IN_DB(db(db.exchg_limits.exchg_id==request.vars.exchg_id),'exchg_limits.curr_id'))

# мои таксы обменов
db.define_table('exchg_taxs',
                Field('curr1_id', db.currs, ondelete='CASCADE'),
                Field('curr2_id', db.currs, ondelete='CASCADE'),
                Field('tax', 'decimal(5,2)', comment='tax %'),
                )
# тут сделаем уникальный сложную проверку
db.exchg_taxs.curr1_id.requires=IS_IN_DB(db, 'currs.id', '%(name)s',
                                         _and = IS_NOT_IN_DB(db(db.exchg_taxs.curr2_id==request.vars.curr2_id),'exchg_taxs.curr1_id'))
db.exchg_taxs.curr2_id.requires=IS_IN_DB(db, 'currs.id', '%(name)s',
                                         _and = IS_NOT_IN_DB(db(db.exchg_taxs.curr1_id==request.vars.curr1_id),'exchg_taxs.curr2_id'))

db.define_table('exchg_pair_bases',
                Field('curr1_id', db.currs, ondelete='CASCADE'),
                Field('curr2_id', db.currs, ondelete='CASCADE'),
                Field('hard_price', 'decimal(16,8)'), # hard price - if >0 - not  use sp-sv values
                Field('base_vol', 'decimal(16,8)', default=10),
                Field('base_perc', 'decimal(5,3)', default=0.3, comment='%'),
                )


db.define_table('exchg_pairs',
                Field('exchg_id', db.exchgs, ondelete='CASCADE'),
                Field('used', 'boolean', default=False, comment='used by site'),
                Field('curr1_id', db.currs, ondelete='CASCADE'),
                Field('curr2_id', db.currs, ondelete='CASCADE'),
                Field('ticker', length=12, comment='pair id - 132 on cryptsy DOGE-BTC'),
                Field('on_update', 'datetime', writable=False,
                      default=request.now,
                      update=request.now, # contains the default value for this field when the record is updated
                      ),
                # depth
                Field('sp1', 'decimal(16,8)'), # price up 1% from curr sell price
                Field('sv1', 'decimal(16,8)'), # selled volume up 1% from curr sell price
                Field('sp2', 'decimal(16,8)'),
                Field('sv2', 'decimal(16,8)'),
                Field('sp3', 'decimal(16,8)'),
                Field('sv3', 'decimal(16,8)'),
                Field('sp4', 'decimal(16,8)'),
                Field('sv4', 'decimal(16,8)'),
                Field('sp5', 'decimal(16,8)'),
                Field('sv5', 'decimal(16,8)'),
                Field('bp1', 'decimal(16,8)'), # buyed volume up 1% from curr buy price
                Field('bv1', 'decimal(16,8)'),
                Field('bp2', 'decimal(16,8)'),
                Field('bv2', 'decimal(16,8)'),
                Field('bp3', 'decimal(16,8)'),
                Field('bv3', 'decimal(16,8)'),
                Field('bp4', 'decimal(16,8)'),
                Field('bv4', 'decimal(16,8)'),
                Field('bp5', 'decimal(16,8)'),
                Field('bv5', 'decimal(16,8)'),
                #migrate=False,
                format='%(exchg_id)s %(curr1_id)s %(curr2_id)s',
                )
db.exchg_pairs.exchg_id.requires=IS_IN_DB(db, 'exchgs.id', '%(name)s',
                                          _and = IS_NOT_IN_DB(db((db.exchg_pairs.curr1_id==request.vars.curr1_id) & (db.exchg_pairs.curr2_id==request.vars.curr2_id)),'exchg_pairs.exchg_id'))
db.exchg_pairs.curr1_id.requires=IS_IN_DB(db, 'currs.id', db.currs._format,
                                          _and = IS_NOT_IN_DB(db((db.exchg_pairs.exchg_id==request.vars.exchg_id) & (db.exchg_pairs.curr2_id==request.vars.curr2_id)),'exchg_pairs.curr1_id'),
                                          )
db.exchg_pairs.curr2_id.requires=IS_IN_DB(db, 'currs.id', db.currs._format,
                                          _and = IS_NOT_IN_DB(db((db.exchg_pairs.exchg_id==request.vars.exchg_id) & (db.exchg_pairs.curr1_id==request.vars.curr1_id)),'exchg_pairs.curr2_id'))



# держатели валюты - qiwi, YD, mail.ru, PayPal,...
db.define_table('dealers',
                Field('name', label='Name', length='50', unique=True),
                Field('used', 'boolean', default=False, comment='used by site'),
                Field('balance', 'decimal(12,2)', default = Decimal('0.0'), comment='current balance'),
                Field('deposit', 'decimal(16,3)', default = Decimal('0.0')), # то что нельзя выводить или продавать - запас для меня
                Field('clients_deposit', 'decimal(16,3)', default = Decimal('0.0')), # то что нельзя выводить или продавать так как это баланс клиеннтов-магазинов
                Field('API', 'text', comment='API commands and urls in JSON format'),
                Field('info', 'text', label='Info', comment='Description'),
                Field('pay_out_MIN', 'decimal(6,2)', default = Decimal('10.0'), comment='MIN paymennt for this ecurr and edialer'),
                format='%(name)s',
                )
# one ACC = one CURR (+reserve)
db.define_table('dealers_accs',
                Field('dealer_id', db.dealers, ondelete='CASCADE', label='to dealer'),
                Field('ecurr_id', db.ecurrs, ondelete='CASCADE', label='in currency'),
                Field('used', 'boolean', default=False, comment='used by site'),
                Field('acc', length=50, label='ACCOUNT', required=True), #notnull=True),
                Field('pkey', 'text', comment='public key'),
                Field('skey', 'text', comment='secret key'),
                Field('expired', 'date', comment='expired date for secret key'),
                Field('info', 'text', label='Text', comment='Description'),
                Field('reserve_MIN', 'decimal(12,2)', comment='reserve balance, not sale'),
                Field('reserve_MAX', 'decimal(12,2)', comment='over balance, sale!'),
                Field('balance', 'decimal(12,2)', default = Decimal('0.0'), comment='current balance'),
                Field('deposit', 'decimal(12,2)', default = Decimal('0.0')), # депозит который нельзя снять -его минусуем из баланса - see ecurrs
                Field('limited', 'boolean', default=True, comment='limited sums?'), # если не персонализированный то ограничение по выплатам
                Field('day_limit', 'integer'), # номер дня месяца если наступило дневное ограничение выплат
                Field('day_limit_sum', 'integer'), # сколько в день уже выплотили - меньше 10 000 р
                Field('mon_limit', 'integer'), # номер месяца если наступило месячное ограничение выплат
                Field('mon_limit_sum', 'integer'), # сколько в месяц уже выплотили - меньше 40 000 р
                Field('from_dt', 'string', default = '0', comment='proc transactions from this DT'),
                format='%(acc)s %(ecurr_id)s',
                )

db.define_table('dealers_accs_trans',
                Field('dealer_acc_id', db.dealers_accs, ondelete='CASCADE'),
                Field('info', 'text', label='Text', comment='Description'),
                Field('vars', 'json'),
                Field('amo', 'decimal(12,2)', default = Decimal('0.00')),
                Field('balance', 'decimal(16,2)', default = Decimal('0.0')),
                Field('diff', 'decimal(16,2)', default = Decimal('0.0'), comment='разница с предыдущим баллансом'),
                Field('created_on', 'datetime', writable=False, default=request.now),
                Field('op_id', length=60),
                #migrate=True,
                #redefine=True,
                format='%(id)s %(amo)s %(created_on)s',
                )

# fee between exchande and dealer
db.define_table('fees',
                Field('exchg_id', db.exchgs, ondelete='CASCADE'),
                Field('dealer_id', db.dealers, ondelete='CASCADE'),
                Field('fee_ed', 'decimal(4,2)', comment='fee in % from exhange to e-dealer'),
                Field('fee_de', 'decimal(4,2)', comment='fee in % from e-dealer to exhange'),
                #Field('tax_ed', 'decimal(4,2)', comment='abs tax from exhange to e-dealer in RUB'),
                #Field('tax_de', 'decimal(4,2)', comment='abs tax from e-dealer to exhange in RUB'),
                format='%(exchg_id)s %(dealer_id)s',
                )
db.fees.exchg_id.requires=IS_IN_DB(db, 'exchgs.id', '%(name)s',
                                   _and = IS_NOT_IN_DB(db((db.fees.dealer_id==request.vars.dealer_id)),'fees.exchg_id'))
db.fees.dealer_id.requires=IS_IN_DB(db, 'dealers.id', '%(name)s',
                                    _and = IS_NOT_IN_DB(db((db.fees.exchg_id==request.vars.exchg_id)),'fees.dealer_id'))


######################################################################
db.define_table('deals_cat',
                Field('name', length=50,  unique=True),
                format='%(name)s',
                )

# тут все настройки платежей для данного дела - мин и макс платеж, вылюта выхода и пр
# валюты входа отдельно, сначала пользователи на дело, потомвалта входа на пользователя
db.define_table('deals',
                Field('cat_id', db.deals_cat, ondelete='CASCADE', default = 1),
                #Field('curr_id', 'integer', comment='NOT USED now! GEt curr in DEAL_ACC'), # db.currs
                Field('fee_curr_id', db.currs, comment='curr for calc FEE'),
                Field('name', length=100,  unique=True), # for URL and LABELs
                Field('name2', length=100, comment='english-name for URL and label'),
                #Field('name_like', length=200, comment='name for .like() - eng + rus + ..'),
                Field('show_text', 'text'),
                # дело по телефонам отключим - оно отдельно - хотя можно потом и тут же делать тоже
                Field('wants', 'integer', default=1),
                Field('used', 'boolean', default=False, comment='used by site'),
                Field('is_shop', 'boolean', default=False, comment='as shop'),
                Field('not_gifted', 'boolean', default=False, comment='not gifts for this deal'), # нельзя использовать подарки для этого дела
                Field('url', length=60, unique=False, comment='url to shop'), #
                # если задана ссылка ответ - значит это наш клиент
                Field('my_client', 'boolean', default=False, comment='=True if not made autopayouts - its my client!'), # нельзя использовать подарки для этого дела
                Field('icon', 'upload'),
                Field('img', length=50), # src="/i/shop/ufanet.gif" - ссылка на картинку у диллера
                # тут шаблон по которму собираем имя аккаунта
                # для мосэнерго [12345 123 12 199 6]
                Field('template_', 'text'),
                Field('calcs_', 'json'),
                ## MIN_pay + MAX_pay - Только для фиата выставляются потому точно малая
                Field('MIN_pay', 'decimal(6,2)', default = 13, comment='для фиата только действует'), # минимум который можно платить
                # если превышает то берем пропорциональный оброк при оплате
                Field('MAX_pay', 'decimal(13,2)', default = 1777, comment='для фиата только действует'), # максимум который можно платить за раз
                Field('fee', 'decimal(14,8)', default = 0, comment='Оброк мне за это дело'),
                Field('tax', 'decimal(4,2)', default = 1, comment='% подать мне за это дело'),
                Field('fee_min', 'decimal(14,8)', default = 1, comment='limit tax down'),
                Field('fee_max', 'decimal(14,8)', default = 100, comment='limit tax up'),
                Field('average_', 'decimal(16,8)', default = 0, comment='average OUTcome'),
                Field('count_', 'integer', default = 0), # used
                format='%(name)s',
                )


# ошибки при вводе данных пользователя - может данные поменялись?
db.define_table('deal_errs',
                Field('deal_id', db.deals, ondelete='CASCADE'),
                Field('dealer_id', db.dealers, ondelete='CASCADE'),
                Field('dealer_acc', length=50),
                Field('acc', length=50),
                Field('count_', 'integer'),
                Field('err', 'text'),
                Field('updated_on', 'datetime', writable=False, default=request.now, update=request.now ),
                format='%(deal_id)s %(err)s',
                )
'''
# что еще подключить
db.define_table('deals_wants',
    Field('dealer_id', db.dealers),
    Field('scid', 'integer'),
    Field('name', length=20),
    Field('count_', 'integer'),
    Field('err', 'text'),
    Field('updated_on', 'datetime', writable=False, default=request.now, update=request.now ),
    format='%(dealer_id)s  %(name)s  %(count)s %(err)s',
    )
'''
# тут только персональные данные пользователя для данного дела
# - его ИД или телефон и т.д - то что надо указать в платежке для диллера
## for TO COUN - acc = out addres + curr_id = oute CURR
db.define_table('deal_accs',
                Field('deal_id', db.deals, ondelete='CASCADE'),
                Field('curr_id', db.currs, ondelete='CASCADE'),
                # phone, name, id etc
                Field('acc', length=100, required=True), # тут все коды через пробел
                Field('price', 'decimal(16,8)'), # если задано то это стоимость заказа - ее нужно всю собрать
                Field('expire', 'integer', comment='in minits, =0 not expired'), # минут до протухания
                #Field('ecurr_id', db.ecurrs),
                Field('to_pay', 'decimal(16,8)', default=Decimal(0)), # сколько мы еще должны заплатить
                Field('payed', 'decimal(16,8)', default=Decimal(0)), # сколько мы уже выплатили
                Field('payed_month', 'decimal(16,8)', default=Decimal(0)), # сколько мы уже выплатили за этот месяц
                Field('payed_month_num', 'integer', default=0), # номер месяца в котором был последний платеж - если не равно тек то сброс делаем
                Field('payed3', 'decimal(16,8)', default=Decimal(0)), # сколько мы уже выплатили раньше
                Field('partner', length=20), # код партнера
                # дадим им сразу по 1р, все равно они их сразу не полдучат
                ### НЕЛЬЗЯ - так там может быть валюта БИТКОИН!
                Field('partner_sum', 'decimal(16,8)', default=Decimal(0)), # сколько уже накапало и пора бы вывести
                Field('partner_payed', 'decimal(16,8)', default=Decimal(0)), # сколько уже выплатили
                Field('gift', length=20), # Подарочный код = коду пратнера
                Field('gift_try', 'integer', default=0), # сколько попыток на ввод кода было
                # а если несколько подарков на 1 счет?
                Field('gift_amount', 'decimal(16,8)', default=Decimal(0)), # сколько денег дарим
                Field('gift_pick', 'decimal(14,8)', default=Decimal(0), comment='if >0 - not add a new gist_amo'),
                Field('gift_payed', 'decimal(16,8)', default=Decimal(0)), # сколько денег уже подарили
                Field('created_on', 'datetime', writable=False, default=request.now),
                format='%(id)s %(acc)s %(curr_id)s',
                )

# для входов разных приптовалют
# - адреса в разных кошельках
db.define_table('deal_acc_addrs',
                Field('deal_acc_id', db.deal_accs, ondelete='CASCADE'),
                Field('unused', 'boolean', default=False, comment='if stolen or unused by site'),
                Field('xcurr_id', db.xcurrs), # тут валюта ВЫходящая
                # имя аккаунта в кошельке должно создаваться по deals.name + deal_acc_id
                # так даже не надо имени дела - deal_acc_id уже уникальный будет
                # Field('account', length=30, required=True),
                Field('addr', length=40, required=True), # его адрес в кошельке крипты
                Field('addr_return', length=40, required=False), # если задан - авто перевод на него будет
                Field('incomed', 'decimal(16,8)'), # сколько крипты пришло
                Field('converted', 'decimal(16,8)'), # сколько мы уже конвертировали
                format='%(id)s %(xcurr_id)s %(addr)s',
                )

# тут у какого дилера данное дело
# какие имеет параметры и ИД
# поидее ИД клиента одна и таже, только у разных дилеров разные имена параметров
db.define_table('dealer_deals',
                # для какого дилера это дело - например в кошелек какого дилера переводить
                # для телефонов тут должно быть ПУСТО, так как:
                # диллер и счет диллера должны выбираться автоматически по остаткам и %-м диллера за перевод
                Field('dealer_id', db.dealers, ondelete='CASCADE'),
                Field('deal_id', db.deals, ondelete='CASCADE'),
                Field('used', 'boolean', default=False, comment='used by my service'),
                # тут ID для этого дела у данного дилера - { "pattern_id": "phone-topup", "p2p", scid и тд }
                # тоесть если тут "phone-topup" или "p2p" то в ACC пишем аккаунт-телефон кому шлем
                # НЕ уникально так как онлайн игры на 1го поставщика и юзера один акк
                Field('scid', length=50, unique=False),
                Field('taken', 'integer', default=0, comment='if > 3 - no change tax by calculate'),
                Field('wanted', 'integer', default=0),
                # тут шаблон по которму делать платеж у дилера
                # тоесть тут перврод имен параметров для данного дилера
                Field('template_', 'text'),
                Field('calcs_', 'json'),
                Field('grab_form', 'boolean', default=False, comment='use form from dealer site'),
                Field('p2p', 'boolean', default=False, comment='it p2p or partner shop'),
                Field('fee', 'decimal(6,2)', default = 0, comment='FEE_CURR in DEAL - edealer abs fee '),
                Field('tax', 'decimal(4,2)', default = 1, comment='% комиссия дилера за это дело, добавка сверху'),
                Field('fee_min', 'decimal(8,2)', default = 0, comment='limit tax down'),
                Field('fee_max', 'decimal(8,2)', default = 0, comment='limit tax up'),
                )
db.define_table('dealer_deal_errs',
                Field('dealer_deal_id', db.dealer_deals),
                Field('acc', length=50),
                Field('mess', 'text'),
                )

##################################################################################
# в ЗАКАЗАХ стопорится курс обмена для данной крипты данного дела пользователя
#
db.define_table('orders',
                Field('ref_', db.deal_acc_addrs, ondelete='CASCADE'),
                Field('created_on', 'datetime', # if time expired
                      writable=False, default=request.now),
                Field('volume_in', 'decimal(18,10)'),
                Field('volume_out', 'decimal(18,10)'),
                Field('status', length=3),
                )
# вновь созданные ордера создают тут записи тоже
# оплата по ордерам идет сюда, если время ордера вышло или он оплачен
# запись из стека удаляется так чтобы не мешаться
# а основная таблица ордеров - это как архив
db.define_table('orders_stack',
                Field('ref_', db.orders, ondelete='CASCADE')
                )

####################################################################
####################################################################
# клиенты, отдельно от магазинов - приход на их счет не делает вывода немежденно
# а только изменяет баланс данной валюты у клиента внутри  нашего сервиса
db.define_table('clients',
                Field('deal_id', db.deals, ondelete='CASCADE',  unique=True),
                Field('email', length=60, unique=True,
                      requires = IS_EMAIL(error_message='invalid email!')),
                Field('auto_collect', 'boolean', comment=T('высылать юаланс автоматически?')),
                Field('note_url', 'text', unique=False, comment='url for notify incomes - =account-order, =amount, =curr_abbrev, =txid, =data_time, =mess'), # после оплаты куда идти
                Field('auto_convert', 'boolean', comment=T('конвертировать автоматически?')),
                Field('conv_curr_id', db.currs, ondelete='CASCADE', comment=T('в какую валюту конвертировать')),
                Field('created_on', 'datetime', # if time expired
                      writable=False, default=request.now),
                format='%(email)s',
                )
db.define_table('clients_balances',
                Field('client_id', db.clients, ondelete='CASCADE'),
                Field('curr_id', db.currs, ondelete='CASCADE'),
                Field('bal', 'decimal(16,8)'),
                Field('updated_on', 'datetime', writable=False, default=request.now, update=request.now ),
                format='%(client_id)s %(curr_id)s %(bal)s',
                )
db.define_table('clients_xwallets',
                Field('client_id', db.clients, ondelete='CASCADE'),
                Field('xcurr_id', db.xcurrs, ondelete='CASCADE'),
                Field('addr', length=40, required=True),
                Field('bal', 'decimal(16,8)'),
                format='%(client_id)s %(xcurr_id)s %(addr)s',
                )
db.define_table('clients_ewallets',
                Field('client_id', db.clients, ondelete='CASCADE'),
                Field('dealer_id', db.dealers, ondelete='CASCADE'),
                Field('ecurr_id', db.ecurrs),
                Field('addr', length=40, required=True),
                Field('bal', 'decimal(16,3)', default=Decimal(0.0)),
                format='%(client_id)s %(dealer_id)s %(ecurr_id)s %(addr)s',
                )

# тут есливход или выход = 0 или валюта неизвестна или = входу, значит
# это не обмен внутри в вход извне или вывод вовне на счета клиента
db.define_table('clients_trans',
                Field('client_id', db.clients, ondelete='CASCADE'),
                Field('order_id', length=100), # == deal_acc.acc или сюда номер транзакции при выводе клиенту вкатываем - чтобы повторно не вывести по ошибке
                Field('curr_out_id', db.currs, ondelete='CASCADE'),
                Field('amo_out', 'decimal(16,8)', default=Decimal(0.0)), # если это не обмен то вход или выход может быть с 0
                Field('curr_in_id', db.currs, ondelete='CASCADE'),
                Field('amo_in', 'decimal(16,8)', default=Decimal(0.0)),
                Field('desc_', 'text'), # сюда пишем
                Field('created_on', 'datetime', writable=False, default=request.now),
                format='%(id)s %(client_id)s %(amo_out)s %(curr_out_id)s -> %(curr_in_id)s %(amo_in)s %(created_on)s',
                )

# подписка для клиентов
db.define_table('news_descrs',
                Field('email', length=60, unique=True,
                      requires = [IS_EMAIL(error_message=T('Неправильный емайл!')),
                                  IS_NOT_IN_DB(db, 'news_descrs.email')]),
                format='%(email)s',
                )

# база по персонам
db.define_table('persons',
                Field('used', 'boolean', default=True),
                format='%(id)s %(used)s',
                )
db.define_table('person_addrs',
                Field('pers', db.persons, ondelete='CASCADE'),
                Field('addr', length=40),
                format='%(addr)s',
                )
# данные на персону - ключ - значение
db.define_table('person_recs',
                Field('pers', db.persons, ondelete='CASCADE'),
                Field('k0', length=10),
                Field('v0', length=60),
                format='%(pers)s %(k)s %(v)s',
                )

####################################################################
####################################################################
####################################################################
####################################################################
# с какого счета проплачено за какое дело
db.define_table('pay_outs',
                Field('ref_', db.deal_accs, ondelete='CASCADE'), # аккаунт для дела
                Field('txid', length=TXID_LEN), # ИД операции
                Field('dealer_acc_id', db.dealers_accs), # какой аккаунт у дилера с заданной фиатной валютой использовался
                Field('amount', 'decimal(16,8)', comment='netto value payouted'),
                Field('amo_taken', 'decimal(16,8)', comment='taken value by dealer'),
                Field('amo_to_pay', 'decimal(14,8)', comment='to_pay payouted'), # о что мы им должны были
                Field('amo_gift', 'decimal(14,8)', comment='gift payouted'),
                Field('amo_partner', 'decimal(16,8)', comment='partner payouted'),
                Field('amo_in', 'decimal(16,8)', comment='value payined'),
                Field('created_on', 'datetime', writable=False), # сами должны вставить default=request.now),
                # что с платежом - зачислен, конвертирован, оплачен диллеру/поставщику
                Field('status', length=15),
                Field('tax_mess', 'text'), # какие % и оброки взял сервис с транзакции
                Field('info', 'text'), # JSON - платежа в системе диллера и прочее что пришло в ответ
                Field('vars', 'json'), # JSON - платежа в системе диллера и прочее что пришло в ответ
                format='%(id)s %(amount)s %(created_on)s %(status)s',
                )
#db.clients_trans.pay_out_id.requires=IS_IN_DB(db, 'pay_outs.id')

db.define_table('clients_notifies',
                Field('clients_tran_id', db.clients_trans, ondelete='CASCADE'),
                Field('created_on', 'datetime', writable=False, default=request.now),
                Field('resp', 'boolean'), # передан успешно?
                Field('tries', 'integer', default=0), # попыток былоо сообщить - чтобы время задержки увеличивать
                format='%(id)s %(created_on)s %(resp)s',
                )
db.define_table('deal_accs_notifies',
                Field('deal_acc_id', db.deal_accs, ondelete='CASCADE'),
                Field('client_id', db.clients, ondelete='CASCADE'),
                Field('created_on', 'datetime', writable=False, default=request.now),
                Field('tries', 'integer', default=0), # попыток былоо сообщить - чтобы время задержки увеличивать
                format='%(id)s %(created_on)s %(resp)s',
                )

# какие суммы пришли на какой адресс
# по этим данным найдем дело в deals_income
db.define_table('pay_ins',
                #requires = IS_EMPTY_OR(IS_IN_DB(db, 'dealers.id', '%(doc)s %(FIO)s')
                Field('ref_',  #  кому мы ее причислили
                      db.deal_acc_addrs, ondelete='CASCADE',
                      #requires = IS_EMPTY_OR(IS_IN_DB(db, 'deal_acc_addrs.id', '%(addr)s')),
                      ),
                Field('amount', 'decimal(14,8)', comment='value received'),
                Field('confs', 'integer', comment='confirmations when record maked'),
                Field('txid', length=TXID_LEN), # транзакция
                Field('vout', 'integer'), # выход в транзакции
                Field('created_on', 'datetime', writable=False), # сами должны вставить default=request.now),
                # что с платежом - зачислен, конвертирован, оплачен диллеру/поставщику
                Field('status', length=15), # если ошибка при выплате - сюда сообщение вкатываем
                Field('status_mess', length=150), # если ошибка при выплате - сюда сообщение вкатываем
                Field('order_id', db.orders), # какой заказ был использован
                Field('payout_id', db.pay_outs), # в какой выплате этот вход крипты содержится
                Field('clients_tran_id', db.clients_trans), # если это клиента платеж внутри сервиса
                format='%(id)s %(amount)s %(created_on)s %(status)s',
                )
# стек платежей которые на проплату
db.define_table('pay_ins_stack',
                Field('ref_', db.pay_ins, ondelete='CASCADE'),
                Field('in_proc', 'integer'), # уже в процессе обработки
                Field('tries', 'integer', default=0), # попыток было оплатить
                Field('to_refuse', 'boolean'), # ОТВЕРГНУТЬ - вернуть обратно
                )
# какие суммы пришли но не на наши адреса
# их в других сервисах могут разобрать
db.define_table('pay_ins_unused',
                Field('amount', 'decimal(16,8)', comment='value received'),
                Field('confs', 'integer', comment='confirmations when record maked'),
                Field('txid', length=TXID_LEN), # транзакция
                Field('vout', 'integer'), # выход в транзакции
                Field('created_on', 'datetime', writable=False), # сами должны вставить default=request.now),
                # что с платежом - зачислен, конвертирован, оплачен диллеру/поставщику
                format='%(id)s %(created_on)s %(amount)s',
                )

#######################################################

# это для связи адреса крипты с номером заказа
db.define_table('addr_orders',
                Field('xcurr_id', db.xcurrs, ondelete='CASCADE'),
                Field('addr', length=40), #
                format='%(id)s %(addr)s',
                )
db.define_table('buys',
                Field('dealer_acc_id', db.dealers_accs, ondelete='CASCADE'), # какой аккаунт у дилера с заданной фиатной валютой использовался
                Field('buyer', length=50), # с какого счета платили
                Field('operation_id', length=50), # номер транзакции у диллера
                Field('amount', 'decimal(10,2)', comment='value received'),
                Field('created_on', 'datetime', writable=False, default=request.now),
                ##Field('vars', 'string'), # если платеж не идентифицирован то сюда параметры закатаем
                ## нет лучше вручную сделаем запрос и посмотрим ответ
                Field('xcurr_id', db.xcurrs),
                Field('addr', length=60), #
                # что с платежом - зачислен, конвертирован, оплачен диллеру/поставщику
                Field('status', length=15), # если ошибка при выплате - сюда сообщение вкатываем
                Field('status_mess', length=150), # если ошибка при выплате - сюда сообщение вкатываем
                Field('txid', length=TXID_LEN), # транзакция
                Field('vout', 'integer'), # выход в транзакции
                Field('tax_mess', 'text'), # какие % и оброки взял сервис с транзакции
                Field('amo_out', 'decimal(16,8)', comment='value payouted'),
                format='%(id)s %(xcurr_id)s %(addr)s %(amount)s %(created_on)s %(status)s',
                )
# стек плаатежей которые на проплату
db.define_table('buys_stack',
                Field('ref_', db.buys, ondelete='CASCADE'),
                # при обрабтке их метим, если будет ошибка - значит уже обрабатывалась
                Field('in_proc', 'boolean', default = False, comment='True - may be error accured'),
                )
#####################################################################
# если наша созданная транзакция не включена в блок,
# то запустить ее в сеть поновой надо?
db.define_table('xcurrs_raw_trans',
                Field('xcurr_id', db.xcurrs, ondelete='CASCADE'),
                Field('txid', length=TXID_LEN), # дело в котром крипта использовалась
                Field('tx_hex', 'text'),
                Field('confs', 'integer'),
                )

###################################################################
###################################################################
db.define_table('buy_partners',
                Field('cod', length=5), #
                Field('unused', 'boolean', default=False),
                Field('tax', 'decimal(4,3)', label=T('Накрутка коэф'), default = Decimal('0.25')),
                Field('fee', 'decimal(5,2)', label=T('Накрутка абс'), default = Decimal('1.0')),
                format='%(cod)s',
                )
db.define_table('buy_partners_xw',
                Field('buy_partner_id', db.buy_partners, ondelete='CASCADE'), #
                Field('curr_id', db.currs), #
                Field('addr', length=40), #
                Field('amo', 'decimal(12,8)', label=T('Накоплено'), default = Decimal('0.0')),
                )

#####################################################################
db.define_table('gifts',
                Field('name', length=30, label=T('Название подарочной программы')),
                Field('deal_id', db.deals, required=True, unique=True, label=T('Для дела')), # дело
                Field.Virtual('deal_url', lambda r: A(T('Перейти'), _href=URL('to_deal','index', args=[r.gifts.deal_id])), label=T('Ссылка')),
                #    Field.Virtual('deal_url', lambda r: A(T('Перейти'), _href=URL('more','to_pay', args=[r.deal_id])), label=T('Ссылка')),
                Field('sum_', 'decimal(8,2)', label=T('Выделено'), default = Decimal('1000.0')),
                Field('gifted', 'decimal(8,2)', label=T('Подарено'), default = Decimal('0.0')),
                Field('amount', 'decimal(7,2)', label=T('Сумма подарка'), default = Decimal('50.0')),
                Field('pick', 'decimal(6,2)', label=T('За раз'), default = Decimal('10.0')),
                Field('count_', 'integer', label=T('Польз'), default = 0),# readable=False, writable=False),
                Field('on_create', 'datetime', writable=False, default=request.now, label=T('Запущен') ),
                )
#def pppp(r):
#    print r
#db.gifts.deal_url = Field.Virtual(
#    lambda row: URL('more','to_pay', args=[row.gifts.deal_id]))

# это бонусы за посещение сайта
db.define_table('bonus',
                Field('ph', length=15),
                Field('gift_code', 'boolean', comment='gift_code used?'),
                Field('taken', 'integer', default=0, comment='in Satoshi'), # сколько начислили к оплате в САТОШИ
                Field('payed', 'integer', default=0, comment='payouted'), # сколько начислили к оплате
                Field('on_day', 'date', default=request.now),
                )
db.define_table('bonus_trans',
                Field('ref_id', db.bonus, ondelete='CASCADE'),
                Field('vol', 'integer', default=1000, comment='in Satoshi'), # сколько начислили к оплате в САТОШИ
                Field('on_day', 'date'),
                Field('memo', length=50, comment='зва что'),
                )

db.define_table('site_stats',
                Field('page_', length=20),
                Field('loads', 'integer'),
                )
db.define_table('currs_stats',
                Field('curr_id', db.currs, ondelete='CASCADE'), # тут валюта входящая
                Field('deal_id', db.deals, ondelete='CASCADE'), # дело в котром крипта использовалась
                Field('average_', 'decimal(16,8)', default = 0, comment='average income'),
                Field('count_', 'integer'),
                )

db.define_table('wallets_stats',
                Field('xcurr_id', db.xcurrs, ondelete='CASCADE'), # тут валюта входящая
                Field('wallet', length=100), # адрес в кошельке крипты или счет у дилера - по нему найдем дело если еще деньги придут сюда
                Field('value_in', 'decimal(16,8)', default = 0, comment='value received'),
                Field('value_out', 'decimal(16,8)', default = 0, comment='value sended'),
                Field('value_gen', 'decimal(16,8)', default = 0, comment='value generated'),
                Field('value_orh', 'integer', default = 0),
                )
db.define_table('news',
                Field('on_create', 'datetime', writable=False, default=request.now, update=request.now,  ),
                Field('head', length=100),
                Field('body', 'text'),
                format='%(head)s',
                )

db.define_table('recl',
                Field('on_create', 'datetime', writable=False, default=request.now, update=request.now,  ),
                Field('url', 'text'),
                Field('count_', 'integer', default = 0),    # сколько раз показали
                Field('level_', 'integer', default = 0),    # уровень стоимости рекламы - гдде ее показывать
                format='%(url)s',
                )

## http://127.0.0.1:8000/ipay/edealers/buys_twiced
## база создается по двойным выплатам
db.define_table('buyers_credit',
                Field('acc', length=50), # с какого счета платили
                Field('credit', 'decimal(10,2)', default = 0, comment='то что я им выплатил лишнее двойные разы'),
                Field('accepted', 'decimal(10,2)', default = 0, comment='то что я с них получил'),
                Field('un_rewrite', 'boolean', comment='True - not rewrite!'),
                Field('mess', 'text'),
                )
db.define_table('logs',
                Field('on_create', 'datetime', writable=False, default=request.now, update=request.now,  ),
                Field('mess', 'text'),
                format='%(mess)s',
                )
