# -*- coding: utf-8 -*-

def index():
    response.title=T("Купить биткоины криптовалюту за электронные деньги, обменять биткоины")
    response.subtitle=T("Быстро, надежно и удобно")
    
    curr_rub = db(db.currs.abbrev=='RUB').select().first()
    vol_out = float(request.vars.vol_out or 1000)

    title = T('Курсы обмена, комиссии и таксы на вход и выход валют на нашем сервисе')
    subtitle = T('Значения могут меняться в зависимости от запасов и потребностей валют, вида оплачиваемой услуги (здесь они не приведены) и объема платежа. Курсы ниже приведены для объема в') + ' %s [%s]' % (vol_out, curr_rub.abbrev) + '.'


    return dict(title=title, subtitle=subtitle, currs=db(db.currs.used==True).select(orderby=db.currs.name),
                curr_rub = curr_rub, vol_out = vol_out)
