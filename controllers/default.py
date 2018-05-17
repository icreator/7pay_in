# -*- coding: utf-8 -*-
#
session.forget(response)

if IS_MOBILE:
    response.top_line = None
else:
    response.top_line = DIV(
        TAG.center(T('Здесь Вы можете купить биткоины и оплатить биткоинами разные услуги')),
        _id="top_line")

def ua(h, url, cls='col-sm-4',
       clsA='ll-blue-bgc'):
       #clsA='gray-bgc'):
    return DIV(A(h, _class='block col-center button btn10 ' + clsA,
                #_style='background-color:%s;' % SKIN['bg-clr-ftr-mnu']
                 _href=url,
                )
               , _class=cls)

class Jammer():
    def read(self,n): return 'x'*n
def jam():
    return 'be-'*400
    # return response.stream(Jammer(),4) - that suspend response!

def consult():
    h = CAT(
        DIV(
        H1('Консультируем бизнес и инвесторов по bitcoin и blockchain'),
        H2('Как использовать биткоин в международных платежах и бизнесе'),
        P('Осуществляем консультации для бизнеса по использованию биткоин платежей и по использованию блокчейн-технологий. Правовое регулирование и применение бухгалтерского учёта для биткоинов. Например:'),
        H3('Как купить биткоин по безналу'),
        H3('Как продать биткоины за безнал'),
        H2('Биткоин-стартапы и блокчейн-стартапы для инвесторов'),
        P('Для инвесторов проведём предварительную экспертизу по биткоин-стартапу или блокчейн-стартапу.',),
        P('Свяжитесь', ' ', A(B('с нами'), _href=URL('default','contacts'))),
            _style='padding:10px 10%;',
            _class='container'),
        )
    return dict(h=h)

def up():
    h = CAT(
        DIV(
            H1('Глобальный инновационный проект',':'),
            P(
               A('Блокчейн для бизнеса, государства и жизни',
              _href='http://datachains.world', _target='_blank'),
              ' - ', 'приглашаем инвесторов и сторонников'),
            BR(),
            H1('Биткоин-бизнес, стартапы в биткоин экономике:'),
            P('Ищем инвестиции или предпринимателей для развития биткоин стартапов в международный бизнес'),
            UL(
                LI(B(DOMEN), ' - оплата услуг биткоинами, обмен и продажа криптовалют'),
                LI(B('LITE.cash'), ' - платежный шлюз для приёма криптовалют на сайтах'),
                LI(B('WAGERS.win'), ' - служба по созданию своих споров и пари со ставками в биткоинах'),
                ),
            P('Описание смотрите в ',A('бизнес-концепции',
              _href='https://docs.google.com/document/d/1OyDbOruXBc7rpJAhWVf3Jv5-sEVWX5gGR0f1byT1faI/edit?usp=sharing', _target='_blank')),
            _style='padding:10px 10%;',
            _class='container'),
        )
    return dict(h=h)

def subscribe():
    form = SQLFORM(db.news_descrs, fields = ['email'],
        submit_button = T('Подписаться'),
        labels = {'email': T('Ваш емэйл')  },
        formstyle='divs',
        )
    if form.accepts(request.vars, session):
        response.flash = T('Вы подписаны')
    elif form.errors:
        response.flash = T('ОШИБКА!')

    return locals()

def to_many():
    response.title = T("Автоматические выплаты на запрлатные счета биткоинов, догикоинов и других криптовалют")
    response.subtitle = ' '
    h = CAT(DIV(
        H2(T('Зарплатные счета и автовыплаты на них')),
        P(T('Если Вам надо делать выплаты на много различных счетов по заранее заданным множителям или долям, то лучше всего это сделать с помощью “разделяющего счёта” - все поступившие на него платежи будут автоматически разделены на заданные доли и выплачены на соответствующие счета. Такой разделяющий или зарплатный счёт создаётся один раз на сервисе LITE.cash и потом все поступления на него автоматически распределяются между получателям на ихние кошельки криптовалют')),
        P(
            A('LITE.cash divided payouts', _href='http://lite.cash/bs3b/more/divided_payments', _target='_blabk')
         ),
        _class='container'),
        )
    return dict(h=h)

#@cache.action(time_expire=CACHE_EXP_TIME, cache_model=cache.ram, public=True, lang=True)
def crypto_trans():
    session.forget(response)
    #ss = common.page_stats(db,response['view'])
    #print response['view'], ss, common.ip()

    #response.logo2 = IMG(_src=URL('static','images/slide3.png'), _width=256)
    response.title = T("Бесплатные переводы СНГ без посредников")
    response.subtitle = ' '
    response.top_line = DIV(
        TAG.center(T("Как перевести деньги в СНГ и другие страны без посредников?")),
        _id="top_line")
    h = CAT()
    h += DIV(H1(T('ПРИВЕТ')),
            ua(T('Купить'),URL('to_buy', 'index')),
            ua(T('Оплатить'),URL('deal', 'index')),
            ua(T('Обменять'),URL('to_wallet', 'index')),
            ua(T('Начало'),URL('default', 'index'),'col-sm-12'),
            _class='row')
    return dict(h = h)

#@cache.action(time_expire=CACHE_EXP_TIME, cache_model=cache.ram, public=True, lang=True)
def crypto():
    session.forget(response)
    #ss = common.page_stats(db,response['view'])
    #print response['view'], ss, common.ip()

    response.logo2 = IMG(_src=URL('static','images/slide3.png'), _width=256)
    response.title = T("Что такое криптовалюта и биткоин?")
    response.subtitle = ' '
    h = CAT()
    h += DIV(
            ua(T('Купить'),URL('to_buy', 'index')),
            ua(T('Оплатить'),URL('deal', 'index')),
            ua(T('Обменять'),URL('to_wallet', 'index')),
            ua(T('Начало'),URL('default', 'index'),'col-sm-12'),
            _class='row')
    return dict(h = h, ua = ua(T('Да, мне интересно попробовать криптовалюту'), URL('crypto_go'), 'col-sm-10'))

#@cache.action(time_expire=CACHE_EXP_TIME, cache_model=cache.ram, public=True, lang=True)
def crypto_go():
    session.forget(response)
    #ss = common.page_stats(db,response['view'])
    #print response['view'], ss, common.ip()

    response.title = T("Как начать добывать биткоин и догикоин?")
    response.subtitle = ' '

    h = CAT()
    h += DIV(
            ua(T('Купить'),URL('to_buy', 'index')),
            ua(T('Оплатить'),URL('deal', 'index')),
            ua(T('Обменять'),URL('to_wallet', 'index')),
            ua(T('Начало'),URL('default', 'index'),'col-sm-12'),
            _class='row')
    return dict(h = h)

#@cache.action(time_expire=CACHE_EXP_TIME, cache_model=cache.disk, vars=False, public=False, lang=True)
def contacts():
    session.forget(response)
    response.title=T('Контакты')
    response.not_show_func = True
    h = CAT(
        H3(T('Отзывы, Обсуждение, Жалобы, Благодарности')),
        T('Можно найти в ветке на'),' ',
        A(T('международном форуме о криптовалютах'),
          _href='https://bitcointalk.org/index.php?topic=307648.0', _target='_blank'),'. ',
        T('Там же можно сообщить об ошибке'),'.',
        H3('Обратная связь'),
        T('телефон'),': ', '+7 916 917 2019', BR(),
        T('Почтовый ящик'),': ', 'support@'+DOMEN, BR(),
        T('Skype'),': ', 'i-creator'
    )
    return dict(h =h)


#@cache.action(time_expire=CACHE_EXP_TIME, cache_model=cache.ram, public=True, lang=True)
def index():
    session.forget(response)

    users = db(db.deal_accs).count()

    stats = []
    sum_ = db.currs_stats.count_.sum()
    recs = db(
           db.currs.id == db.currs_stats.curr_id).select(sum_, db.currs.ALL, groupby=db.currs_stats.curr_id, orderby=~sum_)
    for r in recs:
        #print r._extra
        #print r._extra['SUM("currs_stats"."count_")']
        try:
            uses = r._extra['SUM(currs_stats.count_)']
        except:
            try:
                uses = r._extra['SUM("currs_stats"."count_")']
            except:
                uses = r._extra['SUM(`currs_stats`.`count_`)']
        r.currs.update_record(uses = uses)
        stats.append('%s: %s' % (r.currs.name, uses))

    h = CAT(
        CAT(DIV(H1('Отличия нашего сервиса', _class='center'), _style='color:steelblue;background-color:gainsboro;',
            _class='row m-0'
            ) if 'short' in request.vars else DIV(
            DIV(
                H1(T('Биткоины купить и потратить'), _class='wb-headline wb-white wb-mt-0 '),
                H1(T('Oплатить биткоинами услуги'), _class='wb-headline wb-white wb-mt-0 '),
                H1(T('Обменять битоины на рубли'), _class='wb-headline wb-white wb-mt-0 '),
                H1(T('Это сервис оплат криптовалютами'), _class='wb-headline- wb-white wb-mt-0 '),
                A(H1('- bitcoin, litecoin, dogecoin...',_class='wb-headline- wb-white wb-mt-0 '),
                  _href=URL('seo','index'), _class='lite'),
                _style='bottom:100px;right:10px;',
                _class=IS_MOBILE and 'right col-sm-12' or 'absolute right col-md-10 col-lg-8'), # wb-join- wb-grid-'),
            _style='min-height:350px;background-color:blue;',
            _class='row m-0 relative' +  (not IS_LOCAL and ' wb-img' or '')
        )), # if False else '',

        DIV(
        DIV(CENTER(H1(T('Наши преимущества'))),
        DIV(
            TAG.center(
                H2(T('Надежность')),
                P(T('Наш сервис работает с 2013 года и зарекомендовал себя с хорошей стороны. Отзывы можно посмотреть на независимом форуме о криптовалютах')),
                A(T('Посмотреть отзывы и обсуждения'), _href='https://bitcointalk.org/index.php?topic=307648.0', _target='_blank',
                   _class='button blue-bgc'), # lightblue-bgc
                _style='padding: 30px;',
                _class='col-sm-6'),
            TAG.center(
                H2(T('Открытость')),
                P(T('Вы можете посмотреть свои платежи по адресу криптовалюты, а так же недавние платежи других пользователей нашего сервиса в обезличенном виде')),
                  A(T('Посмотреть платежи'), _class='button blue-bgc', _href=URL('where','index'),
                   ),
                _style='padding: 30px;',
                _class='col-sm-6'),
            _class='row m-0'),
            DIV(
                P(T('Количество обработанных транзакций за время работы нашей службы') + ': ', ', '.join(stats)),
                H2(T('Нам доверяют уже %s+ человек со всего мира') % (users + 500), _class='center'),
            _class='row m-0'),
            _class='container'),
            _style='background-color:#00188F; color:#ddd;padding-bottom:30px;',
            _class='row m-0'),

        DIV(
            DIV(
                H2(T('Защита персональных данных'), _class='blue-c'),
                UL([T('Наш сервис не требует регистраций'), T('Мы не запрашиваем паролей'), T('Ваши средства не хранятся у нас'),
                   T('Ваши платежи обезличены и анонимны')]),
                _class='col-sm-6'),
            _style='color:#666;' + (not IS_LOCAL and 'background-image: url(' + URL('static','images/bg-p/lifestyle_girl_tablet_1x.jpg') + ');' or ''),
            _class='row m-0 wb-img-2bbg'),
        DIV(
        DIV(
                H1(
                    T('Пресса о нас'),
                    _class="center"),
                DIV(
                    DIV(
                        IMG(_src=URL('static','images/logos/coinTelegram.png'), _width=60),' ',SPAN('The Cointelegraph',
                             _style='font-size: 24px; margin: 0; text-transform: uppercase; letter-spacing: 0.12em; color: #ffcd04;font-weight: 700; padding-bottom: 3px;'),
                        H3(UL(A('Russians Can Pay Internet and Phone Bills with Bitcoin without Fees',
                          _href='http://cointelegraph.com/news/116026/russians-can-pay-internet-and-phone-bills-with-bitcoin-without-fees' ,
                          _target='_blank',
                          _class='lite'),
                          )),
                        H3(UL(A('EmerCoin Fever Quickly Making a Name Among Fintech Projects',
                          _href='http://cointelegraph.com/news/emercoin-fever-quickly-making-a-name-among-fintech-projects' ,
                          _target='_blank',
                          _class='lite'),
                          )),
                        _class='col-sm-6'),
                    DIV(
                        IMG(_src=URL('static','images/logos/forklog.png'), _width=200),' ',
                        H3(UL(A('Bitcoin Conquers Official Moscow',
                          _href='http://forklog.net/bitcoin-conquers-official-moscow/' ,
                          _target='_blank',
                          _class='lite'),
                          A('Как биткоин покоряет официальную Москву',
                              _href='http://forklog.com/kak-bitkoin-pokoryaet-ofitsialnuyu-moskvu/',
                              _target='_blank',
                              _class='lite'),
                          )),
                        _class='col-sm-6'),
                    _class='row', _style='margin-top:20px;'),
                DIV(
                    DIV(
                        IMG(_src=URL('static','images/logos/slon.svg'), _width=200),' ',
                        H3(A('Московский Bit: кто зарабатывает на биткоинах в России?',
                            _href='https://slon.ru/economics/moskovskiy_bit_kto_zarabatyvaet_na_bitkoinakh_v_rossii-1077043.xhtml' ,
                            _target='_blank',
                            _class='lite'),
                          ' ','Здесь сайт еще со старым интерфейсом, но его можно узнать по логотипу "7Pay.in"',
                          ),
                        _class='col-sm-6'),
                    DIV(
                        IMG(_src=URL('static','images/logos/tvrain.png'), _width=200),' ',
                        H3(A('Московский бит. Краткий путеводитель по криптовалютам в России',
                              _href='https://tvrain.ru/teleshow/reportazh/moskovskij_bit_kratkij_putevoditel_po_kriptovaljutam_v_rossii-366325/',
                              _target='_blank',
                              _class='lite'),
                          ),
                        _class='col-sm-6'),
                    _class='row', _style='margin-top:20px;'),
                DIV(
                    DIV(
                        _class='col-sm-6'),
                    DIV(
                        _class='col-sm-6'),
                    _class='row', _style='margin-top:20px;'),
            _class='container'),
            _style='background-color:#00188F; color:#ddd;padding-bottom:30px;',
            _class='row m-0 bg-info'),
        DIV(
            DIV(
                H2(T('Удобно платить повторно'), _class='blue-c'),
                P(T('Повторно оплатить услугу можно простым переводом биткоинов тот же адрес, который Вы уже получили на нашем сервисе для оплаты данной услуги. В Вашем кошельке просто присвойте метку для данного адреса чтобы потом по ней в Вашем кошельке найти адрес для оплаты данной услуги или дела. Теперь, не заходя на наш сервис, Вы можете делать повторные оплаты разных дел и услуг из Вашего кошелька криптовалюты.')),
                _class='col-sm-5 pull-right'),
            _style='color:#666;' + (not IS_LOCAL and 'background-image: url(' + URL('static','images/bg-p/lifestyle_guy_computer_1x-2.jpg') + ');' or ''),
            _class='row m-0 wb-img-2bbg'),
        DIV(
        DIV(
            #TAG.center(
            #    P('Так же Вы можете купить биткоины лайткоины догикоины на нашем сайте', _class='blue-c'),
            #    A(H1(T('Купить биткоины')), _href=URL('to_buy','index'),
            #     _class='block button blue-bgc'),
            #    _style='padding:10px;',
            #    _class='col-sm-6'),
            #TAG.center(
            #    P('Быстро оплатить биткоинами услуги ЖКХ, за свет, интернет, игры, телефон', _class='blue-c'),
            #    A(H1(T('Оплатить биткоинами')), _href=URL('deal','index'),
            #     _class='block button blue-bgc'),
            #    _style='padding:10px;',
            #    _class='col-sm-6'),
            _class='container'),
            _style='background-color:currentColor;color:#ddd;',
            _class='row m-0 bg-info'),
        DIV(
        DIV(
            #TAG.center(
            #    P('Или Вы можете оплатить сотовый телефон и мобильный интернет', _class='blue-c'),
            #    A(H1(T('Пополнить сотовый телефон биткоинами')), _href=URL('to_phone','index'),
            #     _class='block button blue-bgc'),
            #    P('Так же Вы можете получить от нас консультацию об использовании биткоинов в бизнесе', _class='blue-c'),
            #    A(H1(T('Консультация для бизнеса и инвесторов о биткоинах')), _href=URL('default','consult'),
            #     _class='block button blue-bgc'),
            #    _style='padding:10px;',
            #    _class='col-sm-12'),
            _class='container'),
            #_style='background-color:currentColor;color:#ddd;',
            _class='row m-0 bg-info'),
    )

    return dict(h = h)


##@cache.action()
def download():
    session.forget(response)
    """
    allows downloading of uploaded files
    http://..../[app]/default/download/[filename]
    """
    return response.download(request, db)

#@cache.action(time_expire=CACHE_EXP_TIME, cache_model=cache.ram, public=True, lang=True)
def e_gold():
    import rates_lib, db_common
    session.forget(response)
    #ss = common.page_stats(db,response['view'])
    #print response['view'], ss, common.ip()

    title = response.title = T("Биткоин - Настоящее цифровое золото...")
    subtitle = response.subtitle = 'Здесь мы научим тебя как заработать на своё будущее.'
    a_in,x,e = db_common.get_currs_by_abbrev(db, 'BTC')
    a_out,x,e = db_common.get_currs_by_abbrev(db, 'RUB')
    b,s, avg = rates_lib.get_average_rate_bsa(db, a_in.id, a_out.id, None)
    rate2 = rate = avg and int(avg) or '****' #round(float(avg or 0),2)
    #a_in2,x,e = db_common.get_currs_by_abbrev(db, 'SIB')
    #b,s, avg2 = rates_lib.get_average_rate_bsa(db, a_in2.id, a_out.id, None)
    #rate2 = avg2 and round(float(avg2 or 0), 2) or -1

    return dict(title=title, subtitle=subtitle,
               rate = rate, rate2 = rate2 )

#@cache.action(time_expire=CACHE_EXP_TIME, cache_model=cache.ram, public=True, lang=True)
def halava():
    session.forget(response)
    #ss = common.page_stats(db,response['view'])
    #print response['view'], ss, common.ip()

    title=response.title = T("Как получить немного денег на халяву?")
    subtitle=response.subtitle = ' '
    return dict(title=title, subtitle=subtitle)

#@cache.action(time_expire=CACHE_EXP_TIME, cache_model=cache.ram, public=True, lang=True)
def halava2():
    session.forget(response)
    #ss = common.page_stats(db,response['view'])
    #print response['view'], ss, common.ip()

    title=response.title = T("Как получить деньги на халяву?")
    subtitle=response.subtitle = 'от 300 до 3000 рублей в месяц!'
    return dict(title=title, subtitle=subtitle)
