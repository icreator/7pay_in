# -*- coding: utf-8 -*-

@cache.action(time_expire=IS_LOCAL and 5 or 300, cache_model=cache.ram, vars=None, public=True, lang=None)
def index():
    response.title=T("Купить биткоины криптовалюту за электронные деньги, обменять биткоины")
    response.subtitle=T("Быстро, надежно и удобно")
    
    curr_base = db(db.currs.abbrev=='USD').select().first()
    vol_out = float(request.vars.vol_out or 1000)

    title = T('Курсы обмена, комиссии и таксы на вход и выход валют на нашем сервисе')
    subtitle = T('Значения могут меняться в зависимости от запасов и потребностей валют, вида оплачиваемой услуги (здесь они не приведены) и объема платежа. Курсы ниже приведены для объема в') + ' %s [%s]' % (vol_out, curr_base.abbrev) + '.'

    #currs=db(db.currs.used==True).select(orderby=db.currs.name)

    return dict(title=title, subtitle=subtitle,
                currs=db((db.currs.used==True) & ~(db.currs.id==curr_base.id)).select(orderby=db.currs.name),
                curr_base = curr_base, vol_out = vol_out)
