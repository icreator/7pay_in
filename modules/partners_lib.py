#!/usr/bin/env python
# -*- coding: utf-8 -*-

if False:
    from gluon import *
    import db

    request = current.request
    response = current.response
    session = current.session
    cache = current.cache
    T = current.T

### партнерсие начисляются только с выходных curr.fee + deal.fee
# и конвертируются в валюту дела у партнера
# причем минимального значения нет так как выходы на прямом обмене могут быть мизер
PARTNER_MAX_EARN = 3 # в рублях
##PARTNER_MIN_EARN = 1

from decimal import Decimal


#from gluon import current
import rates_lib

# считаем партнерские тут
def calc(db, deal, curr_out, deal_acc, vol_out, probe=None):
    # найдем партнера по подарочному коду
    deal_acc_partner = deal_acc.gift and db(db.deal_accs.partner==deal_acc.gift).select().first()
    if not deal_acc_partner: return
    ##vol_out = Decimal(vol_out)
    if probe:
        partner_deal_curr = db.currs[ deal_acc_partner.curr_id ]

    fee_d = deal.fee or 0
    if fee_d:
        if probe:
            print 'for partner  deal_fee', fee_d
        # преобразуем выходную мзду Дела в валюту аккаунта партнера
        fee_rate = Decimal(rates_lib.get_avr_rate_or_null(db, deal.fee_curr_id, deal_acc_partner.curr_id))
        fee_d *= fee_rate / 2
        if probe:
            partner_deal_curr = db.currs[ deal_acc_partner.curr_id ]
            print 'for partner curr - rate -> deal_fee', fee_rate, fee_d, curr_out.abbrev, partner_deal_curr.abbrev
        deal_acc_partner.partner_sum = (deal_acc_partner.partner_sum or 0) + fee_d
    fee_c = curr_out.fee_out or 0
    if fee_c:
        if probe:
            print 'for partner curr_fee_out', fee_c
        # преобразуем выходную мзду валюты выхода в валюту аккаунта партнера
        fee_rate = Decimal(rates_lib.get_avr_rate_or_null(db, curr_out.id, deal_acc_partner.curr_id))
        fee_c *= fee_rate / 2
        if probe:
            print 'for partner curr - rate -> curr_fee_out', fee_rate, fee_c, curr_out.abbrev, partner_deal_curr.abbrev
        deal_acc_partner.partner_sum = (deal_acc_partner.partner_sum or 0) + fee_c

    if probe:
        return dict(fee_d=fee_d , fee_c=fee_c, curr=partner_deal_curr.abbrev)
    
    if fee_d or fee_c:
        deal_acc_partner.update_record()
    
def calc_new(db, deal, curr_out, deal_acc, vol_out, probe=None):
    # найдем партнера по подарочному коду
    deal_acc_partner = deal_acc.gift and db(db.deal_accs.partner==deal_acc.gift).select().first()
    if not deal_acc_partner: return
    vol_out = Decimal(vol_out)
    
    fee_curr = db.currs[ deal.fee_curr_id ]
    # возьмем курс для валюты в котрой такса дела записана
    fee_curr_rate = Decimal(rates_lib.get_avr_rate_or_null(db, fee_curr.id, curr_out.id))
    if fee_curr_rate:
        tax = deal.tax or 0
        if tax:
            # приведем к валюте дела
            tax = vol_out * tax * fee_curr_rate
            fee_max = deal.fee_max
            fee_min = deal.fee_min
            if fee_max and tax > fee_max: tax = fee_max
            elif fee_min and tax < fee_min: tax = fee_min

        fee = fee_rub = 3 * (fee_curr_rate(curr_out.fee_out or 0) + (deal.fee or 0) + tax) /10
        if fee > PARTNER_MAX_EARN: fee_rub = PARTNER_MAX_EARN
        ## тут могут на обмене мизер накидать а партнерские начислятся по 1рублю
        ## elif fee_rub < PARTNER_MIN_EARN: fee_rub = PARTNER_MIN_EARN
        # приведем таксу в валюте выхода
        fee = fee / fee_curr_rate

    # теперь к валюте дела пратнера приведем
    # возьмем курс для валюты в котрой такса дела записана
    fee_curr_rate = Decimal(rates_lib.get_avr_rate_or_null(db, fee_curr, curr_out))
    if current.CURR_RUB.id != deal_acc_partner.curr_id:
        pr_b, pr_s, pr_avg = rates_lib.get_average_rate_bsa(db, current.CURR_RUB.id, deal_acc_partner.curr_id)
        if pr_avg:
            fee = fee_rub * Decimal(pr_avg)
        else:
            fee = 0
    if probe: return dict(fee=fee, curr=partner_deal_curr.abbrev)

    deal_acc_partner.partner_sum = (deal_acc_partner.partner_sum or 0) + fee
    deal_acc_partner.update_record()
