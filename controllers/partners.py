# coding: utf8

#if not IS_LOCAL:
#    raise HTTP(200, 'under construct')

response.title=T("Заработаем Вместе!")

def make_p_url(id, deal_name, cod):
    if deal_name == 'phone +7':
        return '<a href=%s>%s</a>' % (URL('to_phone','index', vars={ 'gc': cod }, scheme=True, host=True),
                                  T('Получи подарок пополнив сотовый телефон!'))
    elif deal_name == 'to COIN':
        return '<a href=%s>%s</a>' % (URL('to_coin','index', vars={ 'gc': cod }, scheme=True, host=True),
                                  T('Получи подарок пополнив сотовый телефон!'))

    return '<a href=%s>%s</a>' % (URL('to_deal','index',args=[id], vars={ 'gc': cod }, scheme=True, host=True),
                                  T('Получи подарок в %s') % deal_name)

def index():
    #print request.post_vars
    addr = request.post_vars.wallet
    if not addr or len(addr)<2:
        parts = db((db.deal_accs.partner_payed + db.deal_accs.partner_sum >0)
                  & (db.deal_accs.deal_id == db.deals.id)
                  & (db.deal_accs.curr_id == db.currs.id)
                 #).select(orderby=~db.deal_accs.partner_payed, limitby=(0,33), orderby_on_limitby=False)
                 ).select(orderby=~(db.deal_accs.partner_payed + db.deal_accs.partner_sum), limitby=(0,33), orderby_on_limitby=False)
        return dict(mess = None, cod=None, parts=parts)
    if addr:
        # чтобы народ не перебирал быстро
        from time import sleep
        sleep(2)
        if len(addr)<30:
            deal_acc = db(db.deal_accs.partner == addr).select().first()
        else:
            #print addr
            deal_acc_addr = db(db.deal_acc_addrs.addr == addr).select().first()
            if not deal_acc_addr: return dict(mess=T("такой адрес не найден"), cod=None)
    
            deal_acc = db.deal_accs[deal_acc_addr.deal_acc_id]
        if not deal_acc: return dict(mess=T("такой аккаунт или счет не найден"), cod=None)
    
    deal = db.deals[deal_acc.deal_id]
    if not deal: return dict(mess=T("такое дело не найдено"), cod=None)
    if deal.not_gifted:
        mess = T('Это дело [%s] не может быть использовано для сотрудничества. Лучше используйте дело по оплате сотового телефона.') % deal.name
        return dict(mess = mess, cod=None)

    curr=db.currs[ deal_acc.curr_id ]
    deal_name = deal.name
    if deal_name == 'to COIN':
        deal_name_url = A(T('Обмен на'),' ', curr.name, _href=URL('to_coin','index', args=[curr.abbrev]))
    elif deal_name == 'phone +7':
        deal_name_url = A(T('на сотовый +7'), _href=URL('to_phone','index'))
    else:
        deal_name_url = A(T('на дело'), _href=URL('to_deal','index', args=[deal_acc.id]))

    mess = XML(T('дела <b>%s</b> и аккаунта <b>[%s]</b>') % (deal_name_url, deal_acc.acc))
    cod = deal_acc.partner
    if cod and len(cod) >4:
        return dict(mess = mess, cod=cod,
                    deal_name = deal.name,
                    acc = deal_acc.acc,
                    partner_sum = deal_acc.partner_sum,
                    curr=curr.abbrev,
                    partner_url = make_p_url(deal.id, deal.name, cod),
                    partner_count = db(db.deal_accs.gift==cod).count() or '0'
                    )
    
    if False:
        rub_curr = db(db.currs.abbrev=='RUB').select().first()
        need_pay_fiat = deal_acc.curr_id == rub_curr.id and deal_acc.payed < PARTNER_MIN
        if not deal_acc.payed or deal_acc.curr_id == rub_curr.id and deal_acc.payed < PARTNER_MIN:
            u = A(deal.name, _href=URL('more','to_pay', args=[deal.id]))
            return dict(mess = XML(T('Вы не можете начать сотрудничество пока сами не совершите платеж') +
                       (need_pay_fiat and (' ' + T('хотя бы на %s рублей') % PARTNER_MIN) or ' ') +
                       T('через наш сервис по этому делу [%s]. Ваш сумарный платеж еще всего %s <i class="fa fa-rub"></i>.') % (u, deal_acc.payed or 0)), cod=None)

    for i in range(1, len(addr) - 11):
        cod = addr[i:i+10]
        #print cod
        deal_acc_is = db(db.deal_accs.partner==cod).select().first()
        if not deal_acc_is:
            deal_acc.partner = cod
            # партнеры не получают подарков, поэтому сбросим подарок
            deal_acc.gift_amount = 0 # None
            deal_acc.gift_pick = 0 # None
            deal_acc.gift = None
            deal_acc.partner_sum = 0
            deal_acc.update_record()
            return dict(mess = mess, cod = cod,
                    deal_name = deal.name,
                    acc = deal_acc.acc,
                    partner_sum = 0,
                    curr=db.currs[ deal_acc.curr_id ].abbrev,
                    partner_url = make_p_url(deal.id, deal.name, cod),
                    partner_count = '0'
                    )

    return dict(mess=T('Что-то не так'), cod=None)
