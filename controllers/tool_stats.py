# -*- coding: utf-8 -*-

if False:
    from gluon import *
    import db

    request = current.request
    response = current.response
    session = current.session
    cache = current.cache
    T = current.T

import datetime
import ed_bal

import common
# запустим сразу защиту от внешних вызов
# тут только то что на локалке TRUST_IP in private/appconfig.ini
common.not_is_local(request)


def oborots():
    h = CAT()
    timedelta = datetime.timedelta(30)
    date0 = datetime.datetime.now()
    date1 = date0 - timedelta
    date2 = date1 - timedelta
    date3 = date2 - timedelta
    date4 = date3 - timedelta
    date_year = date0 - datetime.timedelta(356)
    curr_rub = db(db.currs.abbrev=='RUB').select().first()
    curr_rub_id = curr_rub.id
    sum_outs = db.pay_outs.amount.sum()
    sum_buys = db.buys.amount.sum()
    h += H3('Обороты сервиса по всем услугам в рублях')
    h += H4('Оплачено + куплено = оборот, - платящие аккаунты')
    sum1 = db((db.pay_outs.created_on>date1)
              & (db.pay_outs.created_on<date0)
              & (db.pay_outs.ref_==db.deal_accs.id)
              & (curr_rub_id==db.deal_accs.curr_id)
             ).select(sum_outs).first()[sum_outs]
    sum2 = db((db.buys.created_on>date1)
              & (db.buys.created_on<date0)
             ).select(sum_buys).first()[sum_buys]
    sum_accs = db((db.deal_accs.payed > 0)
              & (db.deal_accs.created_on>date1)
              & (db.deal_accs.created_on<date0)).count()
    h += H4('За последние 30 дней', ': ', sum1, ' + ', sum2, ' = ', float(sum1 + sum2), ' : ', sum_accs)
    sum1 = db((db.pay_outs.created_on>date2)
              & (db.pay_outs.created_on<date1)
              & (db.pay_outs.ref_==db.deal_accs.id)
              & (curr_rub_id==db.deal_accs.curr_id)
             ).select(sum_outs).first()[sum_outs]
    sum2 = db((db.buys.created_on>date2)
              & (db.buys.created_on<date1)
             ).select(sum_buys).first()[sum_buys]
    sum_accs = db((db.deal_accs.payed > 0)
              & (db.deal_accs.created_on>date2)
              & (db.deal_accs.created_on<date1)).count()
    h += H4('1 месяц назад', ': ', sum1, ' + ', sum2, ' = ', float(sum1 + sum2), ' : ', sum_accs)
    sum1 = db((db.pay_outs.created_on>date3)
              & (db.pay_outs.created_on<date2)
              & (db.pay_outs.ref_==db.deal_accs.id)
              & (curr_rub_id==db.deal_accs.curr_id)
             ).select(sum_outs).first()[sum_outs]
    sum2 = db((db.buys.created_on>date3)
              & (db.buys.created_on<date2)
             ).select(sum_buys).first()[sum_buys]
    sum_accs = db((db.deal_accs.payed > 0)
              & (db.deal_accs.created_on>date3)
              & (db.deal_accs.created_on<date2)).count()
    h += H4('2 месяца назад', ': ', sum1, ' + ', sum2, ' = ', float(sum1 + sum2), ' : ', sum_accs)
    sum1 = db((db.pay_outs.created_on>date4)
              & (db.pay_outs.created_on<date3)
              & (db.pay_outs.ref_==db.deal_accs.id)
              & (curr_rub_id==db.deal_accs.curr_id)
             ).select(sum_outs).first()[sum_outs]
    sum2 = db((db.buys.created_on>date4)
              & (db.buys.created_on<date3)
             ).select(sum_buys).first()[sum_buys]
    sum_accs = db((db.deal_accs.payed > 0)
              & (db.deal_accs.created_on>date4)
              & (db.deal_accs.created_on<date3)).count()
    h += H4('3 месяца назад', ': ', sum1, ' + ', sum2, ' = ', float(sum1 + sum2), ' : ', sum_accs)
    sum1 = db((db.pay_outs.created_on>date_year)
              & (db.pay_outs.ref_==db.deal_accs.id)
              & (curr_rub_id==db.deal_accs.curr_id)
             ).select(sum_outs).first()[sum_outs]
    sum2 = db((db.buys.created_on>date_year)
             ).select(sum_buys).first()[sum_buys]
    sum_accs = db((db.deal_accs.payed > 0)).count()
    h += H4('за год', ': ', sum1, ' + ', sum2, ' = ', float(sum1 + sum2), ' : ', sum_accs)

    h += H3('Обороты за разным делам всего')
    d = []
    for deal in db(db.deals.count_ >0).select():
        sum0 = db.deal_accs.payed.sum()
        sum1 = db(db.deal_accs.deal_id==deal.id).select(sum0).first()[sum0]
        #res.append({'name':deal.name, 'sum': sum1})
        d.append([deal.name, int(float('%s' % (sum1 or 0)))])
    d = sorted(d, key = lambda a: -a[1])
    for dd in d:
        h += DIV(DIV(dd[0], _class='col-sm-3'), DIV('%s' % dd[1], _class='col-sm-3'), _class='row')
    
    return dict(h=h)
