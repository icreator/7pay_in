# -*- coding: utf-8 -*-

if DEVELOP: print ('db_session.py - app.DEVELOP')
#print ('db_session.py',request.controller, request.function)
#print ('db_session.py - session.gc', session.gc)

if request.ajax:
    # для вызовов аякса многое не нужно
    ##   GIFT_CODE = session.gc - оже для всех аяксов отключим!!! там где надо берем из сессии только
    #if session.gc:
    #    GIFT_CODE = session.gc
    pass
else:
    # code - тут будет всегда определен
    GIFT_CODE = None
    ## старый вариант использования кодов - по первому параметру
    cntrl = request.controller
    if True and cntrl in ['to_phone', 'default', 'bonuses', 'gifts', 'to_buy','to_wallet','to_coin','to_deal']:
        args_len = len(request.args)
        if args_len:
            # возьмем последний параметр
            gc=request.args(args_len - 1)
            if gc and len(gc) == 10:
                partner = db(db.deal_accs.partner == gc).select().first()
                if partner:
                    GIFT_CODE = partner.partner
                    #print (partner)

    if not GIFT_CODE and 'gift_code' in request.cookies:
        GIFT_CODE = request.cookies['gift_code'].value
        #print ("request.cookies['gift_code'].value:", GIFT_CODE)
    if GIFT_CODE and len(GIFT_CODE) < 5: GIFT_CODE = None

    GIFT_CODE = GIFT_CODE or session.gc
    if GIFT_CODE and len(GIFT_CODE) < 5: session.gc = GIFT_CODE = None
    #print ('db_session GIFT_CODE1 [%s]' % GIFT_CODE, type(GIFT_CODE), len(GIFT_CODE), not GIFT_CODE)

    var_gc = request.vars.gc # из запроса возьмем пригласительный код - перенаправим потом
    #print ('var_gc', var_gc)

    # если в кукиях нет кода то возможно он есть в запросе
    if not GIFT_CODE and var_gc:
        from gifts_lib import store_in_cookies
        store_in_cookies(var_gc)
        # а теперь когда запомнили куки переадресуемся чтобыс бросить код в строке запроса
        GIFT_CODE = var_gc
        # значит взято из запроса! - пересчитать и перенаправить
        # пересчитать бонус при следующем запросе
        session.bonus_recalc = True
    #print ('db_session GIFT_CODE', GIFT_CODE)

    if var_gc:
        request.vars.pop('gc')
        redirect(URL(args=request.args, vars=request.vars))

    # первонаперво редиректы сделаем если надо
    # если в вызове смена языка назначенна
    # то его запомним в сесси и вызов обратный без параметра по РЕДИРЕКТУ
    _ = request.vars.lang
    if _ and _ != session.lang:
        session.lang = _
        vars = request.vars
        vars.pop('lang')
        redirect(URL( args = request.args, vars = vars))

# теперь язык зададим
#print ('session.lang and T.accepted_language', session.lang, T.accepted_language, T.accepted_language[0:3])
if T.accepted_language[0:3] == 'en-':
    T.accepted_language = 'en'
    T.force('en')
if session.lang and T.accepted_language != session.lang:
    #print ('0.py - forsed T.[%s]' % session.lang)
    T.force(session.lang)
