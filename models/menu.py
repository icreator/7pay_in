# -*- coding: utf-8 -*-

if request.ajax:
    # для вызовов аякса многое не нужно
    pass
else:

    response.title = 'bitcoin payments купить биткоин оплаты'
    ## read more at http://dev.w3.org/html5/markup/meta.name.html
    response.meta = dict(
        author = 'iCreator <icreator@mail.ru>',
        description = 'Оплата биткоинами догикоинами мобильного интернет ЖКХ онлайн-игр и прочее. Покупка биткоинов и криптовалют (Догикоины, Лайткоины). Оплатить проездной биткоинами и догикоинами',
        keywords = 'биткоин сайты, криптовалюта, криптовалюты, купить биткоины, потратить биткоины, продать биткоины, оплатить биткоинам сотовый, потратить Dogecoin, купить догикоин, оплатить догикоинами сотовый',
        generator = 'Web2py iCreator',
        )

    ## your http://google.com/analytics id
    response.google_analytics_id = None

    #########################################################################
    ## this is the main application menu add/remove items as required
    #########################################################################

    if request.controller != 'appadmin':
        response.logo = A(
            #IMG(_src=URL('static','images/7P-30-2.png'), _height=50, _style='margin-left:-15px;height:70px;pading-right:20px'),
            IMG(_src=URL('static','images/currs/BTC.png'), _height=40, _style='margin-left:-1px;height:60px'),
            IMG(_src=URL('static','images/currs/ERA.png'), _height=40, _style='margin-left:-15px;height:60px'),
            IMG(_src=URL('static','images/currs/COMPU.png'), _height=40, _style='margin-left:-15px;height:60px'),
            IMG(_src=URL('static','images/currs/LTC.png'), _height=40, _style='margin-left:-15px;height:60px'),
                      _href=URL('default','index'))
        #response.top_line = DIV(_id="top_line")
