# coding: utf8
import db_client

b1_VOL = 20 # rubles
b1_BNS_need = 12000 # bonuses need

## нельзя иначе не сохраняет начтсленные бонусы (( session.forget(response)
    
response.title=T("Получайте награды и бонусы за биткоин платежи!")
#response.big_logo2=True
#response.logo2 = IMG(_src=URL('static','images/bitcoin-100039995-gallery.jpg'), _width=212)

exp_time = request.is_local and 1 or 33

def ua(h, url, cls='col-sm-4', clsA='blue-bgc'):
    return DIV(A(h, _class='block col-center button btn10 ' + clsA,
                #_style='background-color:%s;' % SKIN['bg-clr-ftr-mnu']
                 _href=url,
                )
               , _class=cls)

# готовый сектор - только ДИВ в него вставим
def sect(h, cls_bgc=' '):
    return DIV(DIV(h, _class='container'),  _class=cls_bgc)
## обрамим ее в контайнер
def mess(h, cls_c='error'):
    return DIV(DIV(DIV(h, SCRIPT("$('#tag').scroll();"), _class='col-sm-12 ' + cls_c), _class='row'),
                   _class='container')
def err_dict(m):
    response.view = 'views/generic.html'
    return dict(h = mess(m + ', ' + 'просьба сообщить об ошибке в службу поддержки!'))

def validate_phone(ph):
    if not ph: return 'Пустой номер', None
    if len(ph)>17: return 'Слишком длинный номер', None
    import re
    regular_phone = re.compile("\D")
    ph = regular_phone.sub("","%s" % ph)
    #print ph
    if len(ph) < 11:
        return 'Слишком короткий номер', None
    return None, ph

def show_late():
    # отложим на потом
    response.js = "$('#show_bonus').hide('slow');"
    session.show_bonus_late = True
    if len(request.args):
        redirect(URL('bonuses','index'), client_side=True)

def phone_add():
    response.js = "$('.go-btn').removeClass('disabled');$('#go').children('i').removeClass('fa-refresh fa-spin').addClass('fa-search');"

    ph = request.vars.phone
    err, ph = validate_phone(ph)
    if err: return mess(err)

    session.toPhone = ph
    bonus = db(db.bonus.ph == ph).select().first()
    if bonus:
        ##return mess('Такой телефонн уже задан')
        response.flash = 'Такой телефон уже задан'
        redirect( #request.env.http_web2py_component_location,
            URL('index'), client_side=True)

    else:
        # чтобы не было спама
        import time
        time.sleep(3)
        # заново расчитаем
        from gifts_lib import calc
        gift_cod = request.vars.gift_cod
        gres, bonus_taken, bonus_to_pay, wait = calc(db, BONUSES, ph, None, gift_cod)
        # сбосим "не показывать бонусы"
        session.show_bonus_late = None
        
        if False:
            deal_acc = db((db.deal_accs.deal_acc == ph)
                & (db.deal_accs.deal_id == TO_PHONE7_ID)).select().first()
            if not deal_acc:
                return

        redirect( #request.env.http_web2py_component_location,
            URL('index'), client_side=True)

# награду в деньги на сотовый а to_pay
def b1_sel():
    try:
        ii = int(request.args(0))
    except:
        return 'err arg0'
    bonus = db.bonus[ ii ]
    if not bonus: return 'err bonus_id'
    try:
        ii = int(request.vars.b1_sel)
    except:
        return 'err b1_sel'
    ### RUBLES ###
    vol = b1_VOL
    vol_pick = 5
    ## SATOSHIS ###
    dis_vol = b1_BNS_need
    if bonus.payed and bonus.payed>vol_pick: return 'already payed'
    deal_acc = db.deal_accs[ ii ]
    if not deal_acc: return 'err del_acc'
    if deal_acc.partner: return 'Вы являетесь партнером, а партнерам подарки не положены'
    curr = db.currs[ deal_acc.curr_id ]
    gift_curr_abbrev = 'RUB'
    if curr.abbrev != gift_curr_abbrev:
        rub_curr = db(db.currs.abbrev=='RUB').select().first()
        if not rub_curr:
            return 'deal RUB CURR wrong'
        import rates_lib
        rate = Decimal(rates_lib.get_avr_rate_or_null(db, rub_curr.id, deal_acc.curr_id))
        # преобразуем рубли в валюту делла
        vol_pick *= rate
        vol *= rate
        gift_curr_abbrev = curr.abbrev
    if not deal_acc.gift_pick or deal_acc.gift_pick < vol_pick: deal_acc.gift_pick = vol_pick
    deal_acc.gift_amount = (deal_acc.gift_amount or 0) + vol
    deal_acc.update_record()
    deal = db.deals[ deal_acc.deal_id ]
    import gifts_lib
    gifts_lib.bonus_payout(db, bonus, dis_vol, today=None, memo='[%s][%s] + %s[%s]' % (deal.name, '***'+deal_acc.deal_acc[-3:], vol, gift_curr_abbrev))
    #redirect( #request.env.http_web2py_component_location,
    #    URL('index'), client_side=True)
    return '+%s добавлено!' % vol

def b1():
    try:
        ii = int(request.args(0))
    except:
        return 'err'
    bonus = db.bonus[ ii ]
    if not bonus: return mess('err bonus_id')
    if bonus.payed: return mess('already payed')
    if bonus.taken < b1_BNS_need:
        return mess('Не хаватет бонусов, у Вас есть %s, а надо %s. Зайдите к нам позже чтобы получить еще бонусов или используйте подарочный код.' % (bonus.taken, b1_BNS_need))

    ## Теперь берем все дела - даже не с рублем - а там внутри пересчитаем
    recs = db((db.deal_accs.deal_acc == bonus.ph)
                  & (db.deal_accs.deal_id == db.deals.id)
                  ).select()
    if not recs: return 'deals for phone not found'
    sel = []
    for r in recs:
        #if r.deal_accs.partner: continue
        sel.append(OPTION(r.deals.name, _value=r.deal_accs.id))

    return DIV(H4('Выберите услугу, на которую будет передан подарок'),
               SELECT(sel, _name='b1_sel'), ' ', A(XML('<i class="fa fa-check-square-o"></i>'), _onclick="ajax('%s',['b1_sel'],'b1_tag');" % URL('bonuses', 'b1_sel', args=[bonus.id]), _class='button ll-blue-bgc center'),
              _id='b1_tag')

def use():
    #if not IS_LOCAL:
    #    return 'under construct'
    ph = session.toPhone
    bonus = ph and db(db.bonus.ph == ph).select().first()
    if not bonus: return mess('phone not found')
    
    h = CAT(
        H3('Сейчас Вы можете:')
        )
    if not bonus.payed:
        func='b1'
        h += DIV(
            P(
                A('Получить ПЕРВОЕ вознаграждение', callback=URL('bonuses', func, args=[bonus.id]), target=func),
                ' ', b1_VOL, ' рублей. ',' - цена', ': ', b1_BNS_need,' ','satochi',
            ),
            DIV(_id=func),
            _class="row")
        
    return h

def top():

    r =  db(db.bonus).select(orderby=~db.bonus.taken,
                                 limitby=(0,100), orderby_on_limitby=False)
    
    return dict(bonuses=r)

def index():
    ph = session.toPhone
    import gifts_lib
    gres, taken, topay, wait = gifts_lib.calc(db, BONUSES, ph, None, GIFT_CODE)
    if request.args(0) == 'calc':
        return BEAUTIFY({'gres':gres, 'taken':taken, 'topay':topay, 'wait': wait})
    bonus = ph and db(db.bonus.ph == ph ).select().first()
    trans = bonus and db(db.bonus_trans.ref_id == bonus.id ).select()
    if bonus:
        # обновим статистику по доступным бонусам
        session.bonus_to_pay = (bonus.taken or 0) - (bonus.payed or 0)
    # для вызова АЯКС нужно передать
    session.BONUSES = BONUSES
    return dict(bonus = bonus, trans = trans, wait=wait)
