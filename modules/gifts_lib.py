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

# from gluon import *
G_MIN_LEN = 7
PICK_GIFT_VERO_MIN = 0.3


# Bonuses in satoshi

# есть ли невыплаченныее бонус?
def exist(db, ph, bonus=None):
    bonus = bonus or ph and db(db.bonus.ph == ph).select().first()
    if not bonus: return 0
    return bonus.taken - bonus.payed


# погашение бонуса подарком
def bonus_payout(db, bonus, vol, today, memo=None):
    if not today:
        import datetime
        today = datetime.date.today()
    # тут дату начисления у бонуса не меняем
    bonus.update_record(payed=(bonus.payed or 0) + vol)
    db.bonus_trans.insert(ref_id=bonus.id, vol=-vol, on_day=today, memo=memo)


# рамчитывается пи загрузке странице на предмет нового бонуса - menu1 + layout
# выдает сколько начислено и сколько всего к получению
def calc(db, bonuses, ph, today=None, gift_code=None):
    if not ph:
        # это точно новый пользователь - нет его телефона у нас
        vol = (gift_code and bonuses['gc'] or 0) + bonuses['new']

        return gift_code and {'gc': bonuses['gc'], 'new': bonuses['new']} or \
               {'new': bonuses['new']}, vol, vol, 0

    res = {}
    if not today:
        import datetime
        today = datetime.date.today()

    if len(ph) == 10:
        # для наших добавим 7-ку
        ph = '7' + ph
    wait = 0
    bonus = ph and db(db.bonus.ph == ph).select().first()
    if bonus:
        bonus_id = bonus.id
        d_diff = today - bonus.on_day
        days_left = bonuses['wait'] - d_diff.days
        if days_left < 1:
            memo = 'visit'
            vol = bonuses[memo]
            bonus.update_record(taken=bonus.taken + vol, on_day=today)
            db.bonus_trans.insert(ref_id=bonus_id, vol=vol, on_day=today, memo=memo)
            taken = res[memo] = vol
        else:
            # надо подождать
            wait = days_left
            taken = 0
        # тетепрь все что к выплате с учетом нового начисления
        to_pay = bonus.taken - bonus.payed
    else:
        memo = 'new'
        vol = bonuses[memo]
        bonus_id = db.bonus.insert(ph=ph, taken=vol, on_day=today)
        db.bonus_trans.insert(ref_id=bonus_id, vol=vol, on_day=today, memo=memo)
        bonus = db.bonus[bonus_id]
        res[memo] = taken = to_pay = vol

    if gift_code and not bonus.gift_code:
        # бонус за ввод подарочного кода
        memo = 'gc'
        vol = bonuses[memo]
        res[memo] = vol
        taken += vol
        to_pay += vol
        bonus.update_record(gift_code=True, taken=bonus.taken + vol)
        db.bonus_trans.insert(ref_id=bonus_id, vol=vol, on_day=today, memo=memo)

    return res, taken, to_pay, wait


def store_in_cookies(gift_code, erase=None):
    from gluon import current
    response = current.response
    response.cookies[response.session_id_name] = response.session_id
    response.cookies[response.session_id_name]['path'] = '/'
    response.cookies['gift_code'] = gift_code
    response.cookies['gift_code']['expires'] = 200 * 24 * 3600
    # внимание - если мы проверяем кукие на локалке - то они для всех приложений == будут
    # так как тут путь от домена задан пустой - тоесть будет домен один для всех
    response.cookies['gift_code']['path'] = '/'
    # print ('response.cookies', response.cookies)


# добавим код подарочны к этому аккаунту
# T = None - без сообщений по тихому добавить код
def add_cod(db, T, deal, deal_acc, cod, use_try=None):
    silent = not T
    if False and deal_acc.not_gifted:
        if not T: return
        # добавим код все равно - вдруг потом к этому делуподключим подарки
        mess = T('')
        return mess

    acc = deal_acc.acc
    deal_name = deal.name

    if deal_acc.gift and len(deal_acc.gift) > G_MIN_LEN:
        if silent: return
        mess = T('Для этих платежей по делу [%s] для аккаунта [%s] уже задан подарочный код.') % (deal_name, acc)
        mess = '%s %s' % (mess, T('Остаток подарка: %s c разовой выплатой в %s руб.') % (
        float(deal_acc.gift_amount or 0), float(deal_acc.gift_pick or 0)))
        return mess
    if not cod or len(cod) < G_MIN_LEN:
        if silent: return
        mess = T('Подарочный код не введён')
        return mess
    # это дальше как попытку запоминает else:
    #    mess = T('Неверный подарочный код')
    #    return mess

    # - пусть кто получал подарки может стать партнерорм но не наоборот?
    if deal_acc.partner and len(deal_acc.partner) > G_MIN_LEN:
        if silent: return
        mess = T('Вы являетесь партнёром для этого дела, поэтому не можете получать подарки')
        return mess

    partner_acc = db(db.deal_accs.partner == cod).select().first()
    # если вводили код вручную а не по ссылке и такого партнера нету
    if not partner_acc:
        if silent: return
        if use_try:
            deal_acc.gift_try = deal_acc.gift_try and deal_acc.gift_try + 1 or 1
            deal_acc.update_record()
            # print (deal_acc.gift_try)
            mess = T('Такого подарочного кода [%s] не существует. У Вас осталлось %s попыток.') % (
            cod, 6 - deal_acc.gift_try)
        else:
            mess = T('Такого подарочного кода [%s] не существует.') % cod
        return mess

    deal_acc.update_record(gift=cod)


def add_amo(db, T, deal, deal_acc, cod):
    silent = not T
    if deal_acc.gift_pick and deal_acc.gift_pick > 0:
        return silent or T('Уже подарок получен. Ожидайте следующей компании!')

    deal_name = deal.name
    gift_rec = db(db.gifts.deal_id == deal.id).select().first()
    if not gift_rec:
        return silent or T(
            'Сейчас подарков для этого дела [%s] нет, но они могут появиться позже и будут автоматичеески начислены на этот подарочный код.') % deal_name

    gift_rec.count_ = (gift_rec.count_ or 0) + 1
    if gift_rec.sum_ <= 0:
        return silent or T('Подарки закончились...')

    # тут нажо положить подарок на счет
    amo_gift = gift_rec.amount < gift_rec.sum_ and gift_rec.amount or gift_rec.sum_
    deal_acc.gift_amount = amo_gift
    deal_acc.gift_pick = gift_rec.pick
    # спишем сумму с фонда подарка
    gift_rec.sum_ = gift_rec.sum_ - amo_gift
    mess = silent or '%s %s' % (
    "", T('Сумма подарка: %s c разовой выплатой в %s руб.') % (float(amo_gift), float(gift_rec.pick)))
    mess = silent or '%s %s' % (mess, T(
        'Эта разовая выплата будет добавляться как подарок к каждому вашему платежу по аккаунту [%s] для дела [%s] пока вся сумма подарка не израсходуется.') % (
                                deal_acc.acc, deal_name))

    gift_rec.update_record()
    deal_acc.update_record()
    return silent or mess


## вероятность выпадения подарка - сначала часто потом редко
def pick_ver(gift_amount, gift_pick):
    # if not gift_amount or not gift_pick: return 0
    vvv = round(gift_amount / gift_pick / 5, 2)
    if vvv > 1:
        vvv = 1
    elif vvv < PICK_GIFT_VERO_MIN:
        vvv = PICK_GIFT_VERO_MIN
    return vvv


def deal_acc_gift_mess(deal_acc):
    gift_amount = deal_acc.gift_amount
    gift_pick = deal_acc.gift_pick
    gift_pick = gift_pick < gift_amount and gift_pick or gift_amount
    vvv = pick_ver(gift_amount, gift_pick)
    '''
    gift_mess = CAT(H3(T('Поздравляем!'), ' ', T('Вы получили подарок'), ' ', B(float(gift_amount)), ' руб'),
                    ' за подарочный код ', deal_acc.gift, BR(),
               XML(T('Вероятность получить <b>%s</b> из них в следующем платеже составляет: %s') % (float(gift_pick), vvv))
               )
    '''
    return [float(gift_amount), deal_acc.gift, float(gift_pick), vvv, float(deal_acc.gift_payed or 0)]


def gift_proc(db, T, deal, deal_acc, request, session, GIFT_CODE):
    # если партнер то подарки не дарим!
    gift_amount_old = deal_acc.gift_amount
    if not GIFT_CODE and request.cookies.has_key('gift_code'):
        GIFT_CODE = request.cookies['gift_code'].value
        # print ("to phone - request.cookies['gift_code'].value:", GIFT_CODE)

    if GIFT_CODE and len(GIFT_CODE) < 5: GIFT_CODE = None
    GIFT_CODE = deal_acc.gift or GIFT_CODE
    # print ('to phone GIFT_CODE1:', GIFT_CODE)
    if not GIFT_CODE:
        # если в кукиях нет кода то может тут задали вручную?
        GIFT_CODE = request.vars.gift_cod
        if GIFT_CODE:
            # да - задали вручную
            store_in_cookies(GIFT_CODE)
    if GIFT_CODE:
        ## если нет gift_amount - то сообщим что получен подарок
        # not gift_amount and T
        add_cod(db, T, deal, deal_acc, GIFT_CODE)
        add_amo(db, T, deal, deal_acc, GIFT_CODE)

    # print ('deal_acc.gift != GIFT_CODE', deal_acc.gift, GIFT_CODE)
    if deal_acc.gift and deal_acc.gift != GIFT_CODE:
        # возможно что раньше уже для этого дела заданы были коды то из возьмем
        GIFT_CODE = session.gc = deal_acc.gift
        store_in_cookies(GIFT_CODE)
        # print (session.gc)

    if not GIFT_CODE:
        return None, None

    m_end = ' *' + T('Вы сняли уже') + ' <b>%s</b> <i class="fa fa-rub"></i>' % int(deal_acc.gift_payed or 0) + '</div>'

    gift_amount = deal_acc.gift_amount
    if not gift_amount:
        return GIFT_CODE, '<div class="row">' + (T(
            'Сейчас подарков для этого дела [%s] нет, но они могут появиться позже и будут автоматичеески начислены на этот подарочный код.') % deal.name) + m_end

    gift = deal_acc_gift_mess(deal_acc)
    if gift_amount_old:
        m1 = T('Вы имеете подарок')
    else:
        m1 = T('Поздравляем! Вы получили подарок')
    return GIFT_CODE, '<div class="row"><h3>' + m1 + (' <b>%s</b> ' % gift[0]) + T('за подарочный код') + ' ' + gift[
        1] + '</h3>' \
           + T('Вероятность снять <b>%s</b> из них в следующем платеже составляет: <b>%s</b>') % (
           gift[2], gift[3]) + '. ' + m_end


## тут все РУБЛИ только
def adds_mess(deal_acc, PARTNER_MIN, T, rnd=2):
    mess = to_pay_mess = gift_mess = partner_mess = ''
    to_pay = deal_acc.to_pay
    to_pay = to_pay and round(float(to_pay), rnd + 1)
    if to_pay:
        to_pay_mess = '<h4>' + (to_pay > 0 and T(
            'Ваша переплата') + ' <b>%s' % to_pay + ' <i class="fa fa-rub""></i></b> <small style="color:white">' \
                                + T('Она будет добавлена к следующему платежу') + '</small>' \
                                or '<i style="color:navajowhite;">' + T(
                    'Ваша задолженность') + ' <b>%s <i class="fa fa-rub"></i></b></i>' % -to_pay) + '</h4>'
    if deal_acc.partner:
        amo_partner = deal_acc.partner_sum
        if amo_partner:
            partner_mess = '<h3>' + T('Начислено партнерских') + ' <b>%s' % round(float(amo_partner), 2) \
                           + '<i class="fa fa-rub"></i></b></h3>' + T(
                'Они добавятся к Вашему следующему платежу, если Вы накопите больше чем') + ' %s' % PARTNER_MIN
        partner_payed = deal_acc.partner_payed
        if partner_payed:
            partner_mess = partner_mess \
                           + '<h3>' + T('Всего получено партнерских') + ' <b>%s <i class="fa fa-rub"></i></b>' \
                           % round(float(partner_payed), 2) + (
                                       not amo_partner and '. ' + T('К получению пока') + ' 0' or '') \
                           + '</h3>'  ##+ 'Вы являетесь партнером, поэтому обычные подарки Вам не достаются.'
    else:
        if deal_acc.gift_amount:
            gift = deal_acc_gift_mess(deal_acc)
            gift_mess = '<h3>' + T(
                'Поздравляем! У Вас есть подарок') + ' <b>%s</b> <i class="fa fa-rub" style="color:chartreuse;"></i></h3>' % \
                        gift[0]
            if gift[1]:
                gift_mess += T('за подарочный код') + ' %s<br />' % gift[1]
            else:
                gift_mess += T(
                    'Используйте подарочный код чтобы получать подарки еще. Подарочный код можно взять у наших партнёров') + '.<br />'
            gift_mess += T('Вероятность снять <b>%s</b> из них в следующем платеже составляет: <b>%s</b>') % (
            gift[2], gift[3]) \
                         + '. ' + T('Вы сняли уже') + ' %s' % gift[4]
        elif deal_acc.gift_payed:
            gift_mess = T('Вам выдавались подарки') + ': ' + T('всего Вы сняли %s') % deal_acc.gift_payed

    if gift_mess:
        mess += '<div class="row"><div class="col-sm-12" style="">' + gift_mess \
                + '</div></div>'
    if partner_mess:
        mess += '<div class="row"><div class="col-sm-12" style="">' + partner_mess \
                + '</div></div>'
    if to_pay_mess:
        mess += '<div class="row"><div class="col-sm-12" style="">' + to_pay_mess \
                + '</div></div>'

    return mess


# тут выплаты показывает в валюте дела-аккунта
def add_mess_curr(deal_acc, curr_out, T):
    mess = to_pay_mess = gift_mess = partner_mess = ''
    curr_abbrev = curr_out.abbrev
    to_pay = deal_acc.to_pay
    if to_pay:
        to_pay_mess = '<h4>' + (to_pay > 0 and (T('Ваша переплата') + (' <b>%s [%s]</b>' % (to_pay, curr_abbrev)) + \
                                                + ' <small style="color:white">' + T(
                    'Она будет добавлена к следующему платежу') + '</small>') \
                                or '<i style="color:navajowhite;">' + T(
                    'Ваша задолженность') + ' <b>%s [%s]</b></i>' % (-to_pay, curr_abbrev)) + '</h4>'
    if deal_acc.partner:
        amo_partner = deal_acc.partner_sum
        if amo_partner:
            partner_mess = '<h3>' + T('Начислено партнерских') + (' <b>%s [%s]</b></h3>' % (amo_partner, curr_abbrev)) \
                           + T('Они добавятся к Вашему следующему платежу')
        partner_payed = deal_acc.partner_payed
        if partner_payed:
            partner_mess = partner_mess \
                           + '<h3>' + T('Всего получено партнерских') \
                           + (' <b>%s [%s]</b>' % (partner_payed, curr_abbrev)) \
                           + (not amo_partner and '. ' + T('К получению пока 0') or '') \
                           + '</h3>'  ##+ 'Вы являетесь партнером, поэтому обычные подарки Вам не достаются.'
    else:
        if deal_acc.gift_amount:
            gift = deal_acc_gift_mess(deal_acc)
            gift_mess = '<h3>' + T('Поздравляем! У Вас есть подарок') + (
                        ' <b>%s</b> [%s]</h3>' % (gift[0], curr_abbrev))
            if gift[1]:
                gift_mess += T('за подарочный код') + (' %s<br />' % gift[1])
            else:
                gift_mess += T(
                    'Используйте подарочный код чтобы получать подарки еще. Подарочный код можно взять у наших партнёров') + '.<br />'
            gift_mess += (T('Вероятность снять <b>%s</b> из них в следующем платеже составляет: <b>%s</b>') % (
            gift[2], gift[3])) \
                         + '. ' + T('Вы сняли уже') + (' %s [%s]' % (gift[4], curr_abbrev))
        elif deal_acc.gift_payed:
            gift_mess = T('Вам выдавались подарки') + ': ' + (
                        T('всего Вы сняли %s [%s]') % (deal_acc.gift_payed, curr_abbrev))

    if gift_mess:
        mess += '<div class="row"><div class="col-sm-12" style="">' + gift_mess \
                + '</div></div>'
    if partner_mess:
        mess += '<div class="row"><div class="col-sm-12" style="">' + partner_mess \
                + '</div></div>'
    if to_pay_mess:
        mess += '<div class="row"><div class="col-sm-12" style="">' + to_pay_mess \
                + '</div></div>'

    return mess
