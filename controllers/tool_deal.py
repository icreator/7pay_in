# -*- coding: utf-8 -*-

import common
# запустим сразу защиту от внешних вызов
# тут только то что на локалке TRUST_IP in private/appconfig.ini
common.not_is_local(request)

import json

def index():
    if len(request.args) == 0: return '/tool_deal/index/[deal_id]'
    
    deal = db.deals[request.args(0)]
    if not deal: return 'not deal'
    
    tt = json.loads(deal.template_)
    return BEAUTIFY(tt)

## fees/BTC/deal_acc_id/vol/dealer_id/only_tax
#deal_id - 3801 - to COIN
## если дилер не задан или нен айден dealer_deal - то без мзды диллера за это дело
def fees():
    if len(request.args) < 3: return 'tool_deal/fees/BTC/deal_acc_id/vol[/dealer_id]/[only_tax]<br>' +\
        '4097 - to BTC; 4106 - to LTC; 4123 - to DGE; 3031 - MosEnergoSbyt + 2, 4049 - BANK +4,5 dealer_id'
    abbrev = request.args(0)
    deal_acc_id = request.args(1)
    vol_in = float(request.args(2) or 0)
    if not vol_in: return 'error not vol'
    dealer_id = request.args(3)
    import db_common
    curr_in = db(db.currs.abbrev==abbrev.upper()).select().first()
    if not curr_in: return 'error not curr'
    deal_acc = deal_acc_id and db.deal_accs[ deal_acc_id ]
    if not deal_acc_id: return 'error not deal_acc'
    if dealer_id:
        dealer = db.dealers[ dealer_id ]
        if not dealer: return 'error not dealer'
    else:
        dealer = None
    
    from decimal import Decimal
    curr_out = db.currs[ deal_acc.curr_id ]
    deal = db.deals[ deal_acc.deal_id ]
    rate = 100
    is_order = True
    dealer_deal = dealer and db((db.dealer_deals.deal_id == deal.id)
                     & (db.dealer_deals.dealer_id == dealer_id)).select().first()
    import db_client
    vol_out, mess_out = db_client.calc_fees(db, deal, dealer_deal, curr_in, curr_out, vol_in, rate, is_order,
                                            note=1, only_tax = request.args(4))
    vol_in_new, mess_in = db_client.calc_fees_back(db, deal, dealer_deal, curr_in, curr_out, vol_out, rate,
                                           is_order, note=1, only_tax = request.args(4))
    dealer_deal_none = None
    vol_out_none, mess_out_none = db_client.calc_fees(db, deal, dealer_deal_none, curr_in, curr_out, vol_in, rate, is_order,
                                            note=1, only_tax = request.args(4))
    fee_curr = db.currs[ deal.fee_curr_id ]
    import rates_lib
    fee_rate = Decimal(rates_lib.get_avr_rate_or_null(db, fee_curr.id, curr_out.id))
    vol_out_dd_add, _ = db_client.dealer_deal_tax_add(db, T, fee_rate, dealer_deal, '', vol_out_none, '')
    vol_out_dd_neg, _ = db_client.dealer_deal_tax_neg(db, T, fee_rate, dealer_deal, '', vol_out_dd_add, '')
    rate_new = vol_out / Decimal(vol_in)
    tax_full = 100 - 100 * rate_new / rate
    h = CAT(H3(deal.name, ' [', curr_out.abbrev,']'),
        dealer and H3('через ', dealer.name) or '',
        dealer_deal and H3('dealer_deal tax:', dealer_deal.tax, '  fee:', dealer_deal.fee, '  fee_min:', dealer_deal.fee_min, '  fee_max:', dealer_deal.fee_max) or '',
        DIV(float(vol_in), ' [', curr_in.abbrev, '] x', rate, ' -> out: ', float(vol_out),' [', curr_out.abbrev,']',
            ' и обратная раскрутка с выходной суммы: ', float(vol_in_new),
           ),
        DIV('курс был и стал: ', rate, ' -> ', float(rate_new), ' это общий процент мзды: %', float(tax_full)),
        DIV(mess_out),
        DIV(mess_in),
        H3('Без учета диллерских накруток на это дело получим'),
        P(vol_out_none, ' - это должно с нас сниматься когда мы платим с учетом диллерских'),
        H3('Если учесть дилеские на это дело то получим на выходе'),
        P(vol_out_dd_add),
        H3('посмотрим сколько диллер возьмет с нас за это дело'),
        P(vol_out_dd_neg, ' совпало?  При этом курс для валюты таксы: ', fee_rate),
       )
    return dict(h=DIV(h, _class='container'))
    
# partner_calc/4130/100000
def partner_calc():
    import partners_lib
    if len(request.args)<2: return 'partner_calc/4130/100000'
    deal_acc_id = request.args(0)
    deal_acc = deal_acc_id and db.deal_accs[ deal_acc_id ]
    if not deal_acc: return 'partner_calc/deal_acc_id with gift code/vol'
    
    deal = db.deals[ deal_acc.deal_id ]
    curr_out = db.currs[ deal_acc.curr_id ]
    res = partners_lib.calc(db, deal, curr_out, deal_acc, request.args(1), probe=True)
    return BEAUTIFY(res)
