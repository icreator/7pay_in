# coding: utf8
import db_client

## нельзя иначе не сохраняет начтсленные бонусы (( session.forget(response)

response.title=T("Получайте подарки за биткоин платежи!")
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


def add():
    response.js = "$('.go-btn').removeClass('disabled');$('#go').children('i').removeClass('fa-refresh fa-spin').addClass('fa-search');"
    addr = request.vars.wallet
    cod = request.vars.cod
    deal_acc_addrs = db(db.deal_acc_addrs.addr == addr).select().first()
    if not deal_acc_addrs:
        return mess('Адрес не найден')
        
    deal_acc = db.deal_accs[deal_acc_addrs.deal_acc_id]
    if not deal_acc:
        return mess('Аккаунт не найден')
        
    if deal_acc.gift_try >5:
        return mess('Попытки для аккаунта кончились')
    deal = db.deals[deal_acc.deal_id]
    if not deal:
        return mess('Дело не найдено')

    ##db_client.deal_acc_gift_update(db, T, deal, deal_acc, cod, True)
    import gifts_lib
    gift_mess = gifts_lib.add_cod(db, T, deal, deal_acc, cod, True)

    return mess(gift_mess)

def list():
    ## нельзя иначе не сохраняет начтсленные бонусы (( session.forget(response)
    try:
        tt = SQLFORM.grid(db.gifts,
            deletable=False,
            editable=False,
            details=False,
            selectable=None,
            create=False,
            csv=False,
            )
    except:
        tt = SQLFORM.grid(db.gifts,
            deletable=False,
            editable=False,
            details=False,
            selectable=None,
            create=False,
            csv=False,
            )
    h = CAT(tt,
        BR(),
        DIV(
            ua(CAT(TAG.i(_class='fa fa-gift'),' ',T('Как получить подарок от '+ DOMEN)), URL('gifts', 'index'),'col-sm-6'),
            ua(CAT(TAG.i(_class='fa fa-gift'),' ',T('Ввести подарочный код и получить подарок')), URL('gifts', 'get'),'col-sm-6'),
            _class='row')
    )
    return dict(h=h)

def get():
    return dict()

##@cache.action(time_expire=exp_time, cache_model=cache.ram, public=True, lang=True)
def index():
    title = response.title=T("Получайте подарки и бонусы за биткоин платежи!")
    subtitle = response.subtitle=T("Здесь можно найти бонусы за оплату некоторых услуг и дел через нашу службу платежей")
    #response.big_logo2=True
    #subtitle = response.logo2 = IMG(_src=URL('static','images/bitcoin-100039995-gallery.jpg'), _width=212)
    ph = session.toPhone
    bonus = ph and db(db.bonus.ph == ph).select().first()

    return dict(title = title, subtitle=subtitle,
                btns = CAT(DIV(
                        ua(CAT(TAG.i(_class='fa fa-gift'),' ',T('Список подарков')), URL('gifts', 'list'),'col-sm-6'),
                        ua(CAT(TAG.i(_class='fa fa-gift'),' ',T('Получить подарок')), URL('gifts', 'get'),'col-sm-6'),
                        _class='row'),
                    DIV(
                        ua(CAT(TAG.i(_class='fa fa-user-plus '),' ',T('Стать партнером и зарабатывать с платежей приглашенных пользователей')), URL('partners', 'index'),'col-sm-12'),
                        _class='row')),
                bonus=bonus,
                )

def clear_gift_code():
    if session.gc: session.pop('gc')
    if session.toPhone: session.pop('toPhone')
    if session.bonus_to_pay: session.pop('bonus_to_pay')
    if session.show_bonus_late: session.pop('show_bonus_late')
    ##print session
    from gifts_lib import store_in_cookies
    store_in_cookies('')
    redirect(URL('to_phone','index'))
