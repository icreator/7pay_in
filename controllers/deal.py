# coding: utf8

import json

exp_time = IS_LOCAL and 3 or 360

def download():
    session.forget(response)
    return response.download(request,db)

# готовый сектор - только ДИВ в него вставим
def sect(h, cls_bgc=' '):
    return DIV(DIV(h, _class='container'),  _class=cls_bgc)
## обрамим ее в контайнер
def mess(h, cls_c='error'):
    return DIV(DIV(DIV(h, SCRIPT("$('#tag1').scroll();"), _class='col-sm-12 ' + cls_c), _class='row'),
                   _class='container')
def err_dict(m):
    response.view = 'views/generic.html'
    return dict(h = mess(m + ', ' + 'просьба сообщить об ошибке в службу поддержки!'))


# вызывается при изменении поля
# на входе имя параметра главного и имя выхода
#
def subsel_callback():
    try:
        session.forget(response)
        vars = request.vars
        #print (vars)
        dealer_deal_id = vars.pop('dealer_deal_id')
        deal_id = vars.pop('deal_id')
        dealer_deal = db.dealer_deals[dealer_deal_id]
        deal = db.deals[deal_id]
        (k, v) = vars.popitem()
        if dealer_deal.calcs_:
            calc = dealer_deal.calcs_.get(k)
            items = calc.get('items')
            subsel_name = calc.get('subsel')
            if items:
                opts = []
                for item in items:
                    #print (item)
                    if '%s' % item[0] == '%s' % v:
                        opts.append(OPTION(item[2], _value=item[1]))

                #print (opts)
                if len(opts)>0:
                    sel = SELECT(
                        opts,
                        _name=subsel_name, _id=subsel_name, _type="text", _class='field',
                        )
                else:
                    opts = [OPTION('Выбор отсутсвует...', _value=0)]
                    sel = SELECT(
                        opts,
                        _name=subsel_name, _id=subsel_name, _class='field',
                        _disabled='disabled',
                    )

            return sel
    except Exception as e:
        print (e)
        return e

def make_img(r, dealer_info, shop_url=None):
    img = None
    # _style: max-width: 88px;
    if r.icon: img = IMG(_src=URL('default','download', args=['db', r.icon]),
                     _style='max-width:88px;',
                     _alt=r.name)
    elif r.img:
        # это работает только если картинка загружена в экмлорер
        # когда открываешь сайт Яндекс-деньги
        img = XML(u'<img src="%s" style=max-width:88px; alt="%s">' %
                  (dealer_info['img_url'] + r.img,
                   #r.name - тут не хочет перекодировать символы имени
                   ''
                   ) )
        #img = IMG(_src=URL('more','download', args=[dealer_info['img_url'] + r.img] ))
        #img = IMG(_src="http://flylark.net/public/images/flylark_emblem.png")

    return img and A(img or r.name, _href=shop_url or URL('to_deal', 'index', args=[r.id]), _target=shop_url and '_blank') or ''

@cache.action(time_expire=IS_LOCAL and 5 or 10000, cache_model=cache.ram, vars=None, public=True, lang=None)
def most():
    session.forget(response)
    dealer = db(db.dealers.name=="Yandex").select().first()
    ##if not dealer or not dealer.info: return ''
    dealer_info = json.loads(dealer.info)
    h = CAT()
    for r in db(db.deals.used==True).select(orderby=~db.deals.count_, limitby=(0, 20)):
        img = make_img(r, dealer_info)
        h += img
        h += ' '
    return DIV(h, _class='row', _style='line-height:2;')

@cache.action(time_expire=exp_time, cache_model=cache.ram, vars=True, public=True, lang=True)
def list():
    response.js = "$('#go').removeClass('disabled').children('i').removeClass('fa-refresh fa-spin').addClass('fa-search');"
    cat_id = request.args(0) or request.vars.cat
    if cat_id:
        if len(cat_id) <10:
            if cat_id.isdigit():
                deal_cat = db.deals_cat[cat_id]
                if not deal_cat:
                    return mess('digs.')
            elif cat_id=='all':
                deal_cat = None # покажем все
            else:
                return mess('digs...')
        else:
            return mess('digs.....')
    else:
        deal_cat = None

    search = request.vars.get('search')
    if search and (len(search)<3 or len(search)>20):
        return sect('Введите больше 2-х и меньше 10-ти букв')

    dealer = db(db.dealers.name=='Yandex').select().first()
    if not dealer: return mess('Не найден диллер платежей Yandex')
    if not dealer.info:
        return edd_dict('Ошибка в описании диллера - img_url')
    dealer_info = json.loads(dealer.info)

    #if search:
    #    return dict(rs = get_search_list(search, dealer_info))

    rs = []
    # закешируем выборку - орна у нас почти не меняется
    #t1 = datetime.datetime.now()
    recs = db(
                (db.deals.used==True)
                & (not deal_cat or db.deals.cat_id==deal_cat.id)
                & (not search or db.deals.name.contains(search))
                ).select(orderby=~db.deals.count_|db.deals.name,
                         cache=(cache.ram, not IS_LOCAL and 3600 or 0), cacheable= not IS_LOCAL)
    #print (datetime.datetime.now() - t1)

    for r in recs:
        if r.name=='phone +7' or r.name=='WALLET': continue
        #if not r.used: continue
        # берем только с scid=NUM
        url = A(r.name, _href=URL('to_deal', 'index', args=[r.id]))
        pars = {'icon': make_img(r, dealer_info),
                     'url': url, 'id':  r.id,
                     'text': r.show_text or '',
                     'count': r.count_, 'average': r.average_,
                     'wants': r.wants }
        rs.append(pars)

    if deal_cat:
        rs.append({'icon': '',
                     'url': H4(A(T('Больше'), _href=URL('index',args=['all']))),
                     'text': '',
                     'count': '', 'average': '' })

    return dict(rs=rs)

# если дать 2й параметр то выдаст тулбар
# {{=response.toolbar()}}
##@cache.action(time_expire=exp_time, cache_model=cache.ram, vars=True, public=True, lang=True)
def index():
    #common.page_stats(db, response['view'])

    response.title='Платежи оплата биткоинами криптовалютой услуг'
    title = 'Оплата биткоинами и криптовалютой услуг'
    subtitle = 'Здесь Вы можете выбрать оплату биткоинами услуг по их виду или найти в общем списке'

    return dict(title=title, subtitle=subtitle)
