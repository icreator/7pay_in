# -*- coding: utf-8 -*-

if DEVELOP: print ('menu1.py - app.DEVELOP')

if request.ajax:
    pass
else:

    ALERT = None
    #ALERT='ВНИМАНИЕ!!! На сервисе идёт пересинхронизация кошелька Биткоин, операции с этой валютой приостановлены. Приносим извинения за задержку.'
    MNU_ICONS = True
    #MNU_ICONS = False


    if not IS_MOBILE:
        LOGO=''
        '''
        from os import listdir
        images = listdir(request.folder + '/static/images/logos')
        import random
        random.shuffle(images)
        LOGO = A(IMG(_src=URL('static','images/logos/' + images[0]), _style='height: 90px;',
                          _title=T('Домой'),
                          _class='pull-left'), _href=URL('default','index'))
        LOGO = B(A(SPAN(7), 'Pay',
                        IMG(_src=URL('static','images/currs_BTC.png'), _width=40, _style='margin-top:10px;'),
                        'in',
                _href=URL('default','index'), _class='logo pull-left',
                _style='margin-left:15px;'))
        '''
        pass
    else:
        LOGO = A(XML('<i class="fa fa-home"></i>'), _href=URL('default','index'))


    LANG_CURR = session.lang or T.accepted_language
    def lang_sel():
        langs = []
        for (n,l) in LANGS.items():
            if LANG_CURR == n: continue
            vars = request.vars.copy()
            vars['lang'] = n
            langs.append((
                    CAT(IMG(_src=URL('static', 'images/flags/' + l[1]), _width=30, _alt=''),
                        ' ', not IS_MOBILE and l[0] or ''), False, URL(args=request.args, vars=vars))
                  )
        return langs


    # если текущий язык не ннайден в нашем списке то покажем Англ как текущий
    lang = LANGS.get(LANG_CURR, LANGS.get('en', LANGS.get('ru', list(LANGS.values())[0])))
    MENU_RIGHT = [
        (CAT(IMG(_src=URL('static', 'images/flags/' + lang[1]), _width=30, _alt=''), not IS_MOBILE and CAT( ' ', lang[0]) or ''),
            False, None, lang_sel())
        ]
    #MENU_RIGHT = [
    #    (TAG.i(MNU_ICONS and TAG.i(_class='fa fa-rocket bbig', _style='font-size:40px;') or T('Вверх'), _title=T('Инвесторам')),
    #     False, URL('default','up')),
    #    ]


    MENU_1 = [
        #(response.logo or '',None, None),
        LI(
            #A(IMG(_src=URL('static','images/7P-30-2.png'), _style="height:70px"),_style="padding:0", _href=URL('default','index'))
            response.logo
        )
    ]
    MENU_1.append(
        (SPAN(MNU_ICONS and TAG.i(_class='fa fa-retweet bbig') or '', ' ', T('Обменять'), _title=T('Обменять Монеты')),
         False, URL('to_coin','index'))
        )
    if USE_BUY_SELL:
        MENU_1 += [
        # money
        (SPAN(MNU_ICONS and TAG.i(_class='fa fa-btc bbig') or '', ' ', T('Купить'), _title=T('Купить Биткоины')),
         False, URL('to_buy','index')) if USE_BUY_SELL else None,
        (SPAN(MNU_ICONS and TAG.i(_class='fa fa-usd bbig') or '', ' ', T('Продать'), _title=T('Продать Биткоины')),
         False, URL('to_wallet','index')) if USE_BUY_SELL else None,
            ]
    if USE_TO_PHONE:
        ## тут id= задаем для мигания
        MENU_1.append(
        (SPAN(MNU_ICONS and TAG.i(_class='fa fa-mobile bbig') or '',  ' ', T('на Сотовый'),
             CAT(BR(),TAG.sup('+', session.bonus_to_pay, _class='sub', _style='color:chartreuse;')) if session.bonus_to_pay else '',
             _title=T('Оплатить Сотовый'), _id='li_phone'),
         False, URL('to_phone','index'))
            )

    MENU_1.append(
        (SPAN(MNU_ICONS and TAG.i(_class='fa fa-eye bbig') or '',  ' ', T('Платежи'), _title=T('Проверить платежи')),
         False, URL('where','index'))
            )

            
    ## тут id= задаем для мигания
    #(SPAN(MNU_ICONS and TAG.i(_class='fa fa-gift bbig') or '',  ' ', T('Подарки '),
    #     CAT(BR(),TAG.sup(GIFT_CODE, _class='sub', _style='color:chartreuse;')) if GIFT_CODE else '',
    #     _title=T('Подарки для Вас'),
    #     _id='li_gift'),
    # False, URL('gifts','index')),


    MENU_2 = None
    if USE_TO_DEALS and request.controller=='gifts' or request.controller=='bonuses':
        MENU_2 = [
            (SPAN(T('Награды')), False, URL('bonuses','index')),
            (SPAN(T('Подарки')), False, URL('gifts', 'list')),
            ]
    elif USE_TO_DEALS:
        MENU_2 = [
            LI('Оплатить', BR(), 'биткоинами:', _style='font-size:smaller;'),
            (SPAN(TAG.i(_class='fa fa-home'),' ', T('ЖКУ'), _title=T('Оплата ЖКУ')), False, URL('deal', 'index', args=[6])),
            (SPAN(TAG.i(_class='fa fa-play'),' ', T('Игры'), _title=T('Оплата игр')), False, URL('deal', 'index', args=[2])),
            (SPAN(TAG.i(_class='fa fa-phone'),' ', T('Связь'), _title=T('Оплата интернет')), False, URL('deal', 'index', args=[3])),
            (SPAN(TAG.i(_class='fa fa-file'),' ', T('Софт'), _title=T('Оплата софта')), False, URL('deal', 'index', args=[10])),
            (SPAN(TAG.i(_class='fa fa-users'),' ', T('Общение'), _title=T('Оплата Соц.Сетей')), False, URL('deal', 'index', args=[4])),
            (SPAN(TAG.i(_class='fa fa-bus'),' ', T('Проезд'), _title=T('Оплата Проезда')), False, URL('deal', 'index', args=[11])),
            (SPAN(TAG.i(_class='fa fa-credit-card'),' ', T('Банк'), _title=T('Вывод в банк или на карту')), False, URL('deal', 'index', args=[9])),
            (SPAN(TAG.i(_class='fa fa-search'),' ', T('Найти'), _title=T('Найти услугу')), False, URL('deal', 'index')),
            #(SPAN(XML(
            #        IS_MOBILE and '<i class="fa fa-ellipsis-h" onclick="$(\'.mob_hide\').toggle();"></i>' or
            #    '<i class="fa fa-picture-o" onclick="$(\'#main_cont, #logo\').toggle();"></i>')),None,None),
        ]

    reclama = [
        DIV(H4(T('Partners')),
        DIV(
            DIV(A(IMG(_src=URL('static','images/logos/erachain.png'), _style='width: 100%;'),
                  _href="https://www.erachain.org", _target="_blank"),
                _class='col-sm-4', _style='padding-right: 5px; padding-left: 0px;'),
            DIV(T('Blockchain platform 3.0 generation Erachain'), _class='col-sm-8'),
            _class='row'
            ),
        P(),
        DIV(
            DIV(A(IMG(_src=URL('static','images/logos/e-coin.png'), _style='width: 100%;'),
                  _href="https://www.e-coin.io/?ref=4b3a38cb437f4317a1e9ee5782fea22d", _target="_blank"),
                _class='col-sm-4', _style='padding-right: 5px; padding-left: 0px;'),
            DIV(T('Банковская карта в биткоинах - храни биткоины, пополняй биткоинами, а плати долларами и рублями!'), _class='col-sm-8'),
            _class='row'
            ) if False else '',
        )
        ]
    import random
    random.shuffle(reclama)

    ############################
    #############################
    ### лояльность - за заходы копейки кидаем

    ##VISIT_DATE = session.date_log
    #session.bonus_day = None
    BONUS_DATE = session.bonus_day
    #session.toPhone = None
    #session.bonus_new = None
    #session.bonus_day = None
    #session.show_bonus_late = None

    def show_bonus():

        ## тут массив взятых бонусов уже
        ph = session.toPhone
        if ph and len(ph) == 10:
            # для наших добавим 7-ку
            ph = '7' + ph
            session.toPhone = ph
        # первоначальная проверка по сессии - без заходя в базу данных
        import datetime
        today = datetime.date.today() # обязательно тут берем так как ниже его в сессию закатываем
        recalc = None
        if session.bonus_recalc:
            # что-то произошло - надо пересчитать бонус
            session.pop('bonus_recalc')
            recalc = True
        elif not ph or not BONUS_DATE:
            # нет телефона - это новичек
            recalc = True
        elif BONUS_DATE:
            #print (today, BONUS_DATE #, session)
            try:
                days_left = (today - BONUS_DATE).days
            except:
                days_left = 0
                session.pop('bonus_day')

            if days_left > BONUSES['wait']:
                recalc = True

        bonus_new = None
        bonus_to_pay = session.bonus_to_pay
        if recalc:
            from gifts_lib import calc
            gres, bonus_new, bonus_to_pay, wait_days = calc(db, BONUSES, ph, today, GIFT_CODE)
            #print ('session.bonus_day', today)
            #print (gres)
            #print (bonus_new, bonus_to_pay, wait)
            # если что-то взяли сегодня ои дату взятия поменяем
            session.bonus_day = bonus_new and today
            session.bonus_to_pay = bonus_to_pay
        elif bonus_to_pay:
            pass
        else:
            from gifts_lib import exist
            session.bonus_to_pay = bonus_to_pay = exist(db, ph)
            

        if not bonus_new or session.show_bonus_late or request.controller=='default':
            # возможно что начислено что-то но не показываем
            # show_bonus_late - надо учитывать, так как если телефорн не задан то bonus_new = None
            return None, None, bonus_to_pay

        bres = CAT()
        for (k, b) in gres.items():
            if k=='new':
                bres += H2('За первое посещение нашей службы',' ',B(b), ' ', 'Satoshi')
            elif k =='gc':
                bres += H2('За использование подарочного кода',' ',B(b), ' ', 'Satoshi')
            elif k =='visit':
                bres += H2('За повторное посещение сайта',' ',B(b), ' ', 'Satoshi')
        bonus = CENTER(DIV(
                    DIV(H1(T('Вы получили подарок!')),
                        bres,
                        H2('Всего Вы уже имеете бонусов', ' ', B(bonus_to_pay), ' ', 'Satoshi') if bonus_to_pay >bonus_new else '',
                        P(SPAN(T('Этот подарок Вы сможете положить потом на свой сотовый телефон.'), ' ',
                            T('Просто задайте его тут и когда Вы пополните его через наш сервис этот бонус добавится к Вашему платежу')),
                        #LABEL('Только цифры и пробелы'),
                        BR(),
                        ),
                        P(A(T('Хорошо'), _onclick="ajax('%s');" % URL('bonuses','show_late/1'),
                                _style='margin-right: 10px;',
                                _class='button ll-blue-bgc'),' ',
                            A(T('Потом'), _onclick="ajax('%s');" % URL('bonuses','show_late'),
                                _style='margin-left: 10px;',
                                _class='button ll-blue-bgc'),
                            _style='padding: 10px;',
                            _id='show_bonus_buttons',
                         ),
                        _style='background-color:pink; margin-top:5em; max-width: 800px;',
                        #_class='col-lg-offset-2 col-lg-8 col-sm-12',
                        ),
                _class='row'),
            _id='show_bonus',
            _style=IS_MOBILE and 'position:relative; width:100%;' or 
                       'z-index:10000; background-color:rgba(0, 0, 0, 0.33); position:fixed;height:100%; width:100%;top: 0px;' )
        return bonus, bonus_new, bonus_to_pay
