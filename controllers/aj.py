# coding: utf8


@cache.action(time_expire=IS_LOCAL and 5 or 300, cache_model=cache.ram, public=False, lang=False)
def rates():
    session.forget(response)
    curr_out = db(db.currs.abbrev == 'BTC').select().first()
    if not curr_out: return 'curr_out [BTC] not found'

    currs_list = ['BTC', 'LTC', 'ERA', 'COMPU']
    import rates_lib
    tl = CAT()
    for r in rates_lib.top_line(db, curr_out, currs_list):
        tl += SPAN(
                  #r[0],
                  IMG(_src=URL('static','images/currs/' +  r[1] + '.png'),
                           _width=24),#':',
                  r[0],
                  TAG.i(_class='fa fa-btc', _style='color:#ffb761;'), # chartreuse
                  ' ',
                  #_class='small'
            )
    #return DIV(TAG.center(tl))

    curr_out = db(db.currs.abbrev == 'USD').select().first()
    if not curr_out: return 'curr_out [USD] not found'

    for r in rates_lib.top_line(db, curr_out, currs_list):
        tl += SPAN(
                  #r[0],
                  IMG(_src=URL('static','images/currs/' +  r[1] + '.png'),
                           _width=24),#':',
                  r[0],
                  TAG.i(_class='fa fa-usd', _style='color:chartreuse;'), # chartreuse
                  ' ',
                  #_class='small'
            )

    curr_out = db(db.currs.abbrev == 'RUB').select().first()
    if not curr_out: return 'curr_out [RUB] not found'

    for r in rates_lib.top_line(db, curr_out, currs_list):
        tl += SPAN(
                  #r[0],
                  IMG(_src=URL('static','images/currs/' +  r[1] + '.png'),
                           _width=24),#':',
                  r[0],
                  TAG.i(_class='fa fa-rub', _style='color:#ffacac;'), # chartreuse
                  ' ',
                  #_class='small'
            )

    #return DIV(TAG.center(tl))
    
    return tl

@cache.action(time_expire=IS_LOCAL and 5 or 300, cache_model=cache.ram, public=False, lang=False)
def rates_aj():
    session.forget(response)
    curr_out = db(db.currs.abbrev == 'BTC').select().first()
    if not curr_out: return 'curr_out [BTC] not found'

    currs_list = ['BTC', 'LTC', 'ERA', 'COMPU']
    import rates_lib
    btc_rates = []
    for r in rates_lib.top_line(db, curr_out, currs_list):
        btc_rates.append(r)

    curr_out = db(db.currs.abbrev == 'USD').select().first()
    if not curr_out: return 'curr_out [USD] not found'

    usd_rates = []
    for r in rates_lib.top_line(db, curr_out, currs_list):
        usd_rates.append(r)

    curr_out = db(db.currs.abbrev == 'RUB').select().first()
    if not curr_out: return 'curr_out [RUB] not found'

    rub_rates = []
    for r in rates_lib.top_line(db, curr_out, currs_list):
        rub_rates.append(r)
    
    return dict( btc = btc_rates, usd = usd_rates, rub = rub_rates)

#@cache.action(time_expire=IS_LOCAL and 5 or 30, cache_model=cache.ram, public=False, lang=False)
def informer():
    session.forget(response)
    curr_out = db(db.currs.abbrev == 'RUB').select().first()
    if not curr_out: return 'curr_out [RUB] not found'
    
    args = request.args
    gc = args(0)
    if not gc:
        return 'use URL/[partner_cod]/CURR1/CURR2/...?m=[TEXT] or URL/[partner_cod]?m=[TEXT} or URL/[partner_cod]'

    import rates_lib
    tl = CAT()
    for r in rates_lib.top_line(db, curr_out, len(args)>1 and args[1:] or []):
        tl += SPAN(
                  IMG(_src=URL('static','images/currs/' +  r[1] + '.png'),
                      _style='margin-bottom: -10px;',
                      _width=30),
                  r[0],' ',

            )
    h = CAT(
        #INPUT(_name='deal_acc'),
        DIV(
            DIV(
                A(
                    tl,BR(),
                    request.vars.m or 'Призы на сотовый',
                    _href='https://' + DOMEN + '/to_phone?gc=%s' % gc, _target='_blank',
                    _style='color:#333;display:block;line-height: 30px; font-size:20px; text-decoration: none; padding:8; background-color:#ADD8FF',
                    _onMouseOver="this.style.color='#000'; this.style.backgroundColor='#CDE8FF'",
                    _onMouseOut="this.style.color='#333'; this.style.backgroundColor='ADD8FF'",
                ),
                _style='',
            ),
        _style='',
        ),
        )
    return h

def ok_to():
    to = request.args(0)
    if len(to)>10:return
    v = 'ok' + to
    #print (v)
    try:
        session[v] = 1
    except:
        print ('aj.to_ok session error [v]:', type(v), v)

# TODO тут надо блокировать внесение адреса возврата если дата разошлась с датой создания записи на пол дня
def addr_ret1():
    session.forget(response)
    addr = request.vars['addr_ret_addr']
    if not addr or len(addr)< 30:
        return T('ОШИБКА: адрес слишком короткий')
    addr_ret_id = request.vars.addr_ret_id
    daa = addr_ret_id and db.deal_acc_addrs[addr_ret_id]
    if not daa: return T('ОШИБКА: deal_acc_addr не найден')
    if daa.addr_return:
        #### ОБЯЗАТЕЛЬНО ПРОВЕРКУ иначе могут чужой адрес подстваить всем
        return CAT(T('Адрес для возвратов'),' ', T('уже задан!'))
    
    daa.update_record(addr_return = addr)
    response.js = '$("#ar%s").hide();$("#art%s").removeClass("error").addClass("success");' % (addr_ret_id, addr_ret_id)
    return CAT(T('Адрес для возвратов'),' ', XML('<i class="fa fa-check-square-o "></i>'))

#
#
#### Тут надо задавать _id= имена оригинальные для всей страници куда загружаем этот модуль!!!
# и передавать значения через request.vars - тогда оно на автомате крутятся внутри
# когда по рекурсии вызов надо делать ИД не цели :
#        _id=mess and '-' or 'targ_ar')
def addr_ret():
    session.forget(response)
    addr_ret_id = request.args(0)
    if not addr_ret_id: return 'empty addr_ret_id'
    d = CAT(
        DIV(
            H5(T('ВНИМАНИЕ!!! Настоятельно рекомендуем задать Ваш адрес для возврата монет, чтобы они могли вернуться в Ваш кошелек в случае если платеж будет отвергнут нашим партнёром.')),
            #### Тут надо задавать имена оригинальные для всей страници куда загружаем этот модуль!!!
            INPUT(_name='addr_ret_addr',
                  _class = 'wallet', # почемутотут он пустой Юзер_Агент request.user_agent().is_mobile
                  ),
            INPUT(_name='addr_ret_id',
                  #_value=request.args(1),
                  _value=addr_ret_id,
                  _style="display: none;", _class='--hidden'),
            ' ',
            #INPUT(XML('<i class="fa fa-download"></i>'), _type='submit',
            BUTTON(XML('<i class="fa fa-download bbig"></i>'), _type='submit',
                  #_value = '',
                  _onclick="ajax('%s', ['addr_ret_id', 'addr_ret_addr'], 'art%s')" % (URL('aj', 'addr_ret1'), addr_ret_id),
                  _class = 'button blue-bgc'),
        _class = 'row',
        _id = 'ar%s' % addr_ret_id),
        DIV(
        #_style="display: inline-block;",
        _class='row error',
        _id = 'art%s' % addr_ret_id),
        )
    return d
