# coding: utf8

#if not IS_LOCAL:
#    raise HTTP(200, 'under construct')

import datetime, time

import common
import db_client
import db_common
import ed_common
import recl
import rates_lib

DEVELOP_USE = False

def test_vol(vol):
    try:
        vol = float(vol)
    except:
        return None
    return vol

# переходник для показа ссылкок и картинок в листингах
def download():
    ## нельзя иначе не сохраняет начтсленные бонусы (( session.forget(response)
    return response.download(request,db)

# готовый сектор - только ДИВ в него вставим
def sect(h, cls_bgc=' '):
    return DIV(DIV(h, _class='container'),  _class=cls_bgc)
## обрамим ее в контайнер
def mess(h, cls_c='error'):
    return DIV(DIV(DIV(h, SCRIPT("$('#tag1').scroll();"), _class='col-sm-12 ' + cls_c), _class='row'),
                   _class='container')
def err_dict(m, not_add_err=False):
    response.view = 'views/generic.html'
    return dict(h = mess(m + ( not_add_err and ' ' or ', ' + 'просьба сообщить об ошибке в службу поддержки!')))

def get_uri_in():
    response.js = "$('.go2-btn').removeClass('disabled');$('#go2').children('i').removeClass('fa-refresh fa-spin').addClass('fa-search');"

    h, result = get_rate_result(request, get_currs = True)
    print result
    
    addr_out = request.vars.addr
    #print request.vars
    if not addr_out:
        return mess(T('ОШИБКА: Задайте кошелек'))

    try:
        if len(addr_out) < 25 or len(addr_out) > 40:
            ##проверка на счет - если это не емайл и не ттелефон то надо длинну и на циифры
            return mess(T('ОШИБКА: неверный кошелек'))
    except:
        return mess(T('ОШИБКА: неверный кошелек 2'))
    
    curr_in = result['curr_in_rec']
    curr_id = curr_in.id
    xcurr_in = db(db.xcurrs.curr_id == curr_id).select().first()
    if not xcurr_in: return mess(T('xcurr in...'))

    curr_out = result['curr_out_rec']
    curr_out_id = curr_out.id
    xcurr_out = db(db.xcurrs.curr_id == curr_out_id).select().first()
    if not xcurr_out: return mess(T('xcurr out...'))

    deal_id = TO_COIN_ID
    deal = db.deals[deal_id]
    
    curr_in_abbrev = curr_in.abbrev
    curr_in_name = curr_in.name
    curr_out_abbrev = curr_out.abbrev
    curr_out_name = curr_out.name

    token_system_in = None
    token_key_in = xcurr_in.as_token
    if token_key_in:
        token_in = db.tokens[token_key_in]
        token_system_in = db.systems[token_in.system_id]
        import rpc_erachain

    token_system_out = None
    token_key_out = xcurr_out.as_token
    if token_key_out:
        token_out = db.tokens[token_key_out]
        token_system_out = db.systems[token_out.system_id]
        import rpc_erachain
        
    #print request.application[-5:]
    if request.application[:-3] != '_dvlp' and not DEVELOP_USE:
        # чето конфликт если из ipay3_dvlp вызывать то кошелек на ipay3 не коннектится
        if token_system_out:
            curr_block = rpc_erachain.get_info(token_system_out.connect_url)
            if type(curr_block) != type(1):
                return mess(T('Connection to [%s] is lost, try later ') % curr_out_name)
            if rpc_erachain.is_not_valid_addr(token_system_out.connect_url, addr_out):
                return mess(T('address not valid for ') + curr_out_name + ' - ' + addr_out)
            
            pass
        else:
            import crypto_client
            try:
                cc = crypto_client.conn(curr_out, xcurr_out)
            except:
                cc = None
            if not cc:
                return mess(T('Connection to [%s] is lost, try later ') % curr_out_name)
            if crypto_client.is_not_valid_addr(cc, addr_out):
                return mess(T('address not valid for - ') + curr_out_name + ' - ' + addr_out)

    try:
        session.toCoin = curr_out_abbrev
        session.toCoinA = addr_out
    except:
        print 'to_coin session error .toCoinA:', type(addr_out), addr_out

    volume_in = result['volume_in']
    try:
        session.vol = volume_in
    except:
        print 'to_coin session error .volume_in:', type(volume_in), volume_in
    
    if token_system_in:
        deal_acc_id, deal_acc_addr = rpc_erachain.get_deal_acc_addr(db, deal_id, curr_out, addr_out, token_system_in.account, xcurr_in)
        addr_in = token_system_in.account
        pass
    else:
        x_acc_label = db_client.make_x_acc(deal, addr_out, curr_out_abbrev)
        # найдем ранее созданный адресс для этого телефона, этой крипты и этого фиата
        # сначала найтем аккаунт у дела
        deal_acc_id = db_client.get_deal_acc_id(db, deal, addr_out, curr_out)
        # теперь найдем кошелек для данной крипты
        deal_acc_addr = db_client.get_deal_acc_addr_for_xcurr(db, deal_acc_id, curr_in, xcurr_in, x_acc_label)
        if DEVELOP_USE:
            deal_acc_addr = dict(addr='probe1DEVELOP_USE', id=1234)
        if not deal_acc_addr:
            return mess((T('Связь с сервером %s прервана') % curr_in_name) + '. ' + T('Невозможно получить адрес для платежа') + '. ' + T('Пожалуйста попробуйте позже'), 'warning')

        addr_in = deal_acc_addr['addr']
        

    okIN = session.okWt
    h += sect(DIV(
        okIN and DIV(H3(A(T('Правила оплаты'), _onclick='$(".okIN").show("fast");', _class='button warn right'),
                      _class='pull-right-'), _class='col-sm-12') or '',
        DIV(okIN and ' ' or H3(T('ПРАВИЛА ОПЛАТЫ'), _class='center'),
           P(T('При оплате необходимо соблюдать следующие правила:')),
           UL(
                #T('Желательно задать обратный адрес для возврата монет на случай если наша служба по каким-либо причинам не сможет совершить оплату по делу [%s]') % deal.name,
                T('Желательно производить плату только со своего кошелька, задав адреса входов, которыми Вы действительно обладаете, а не с кошельков бирж, пулов или онлайн-кошельков. Так как при отправке со своего личного кошелька Вы всегда сможете доказать что это Ваш платеж.'),
                T('Комиссия сети добавляется к сумме для обмена, о чем указывается ниже.'),
                T('Если Вы оплатите другую сумму, то курс обмена может немножко измениться'),
                T('Если Вы платите регулярно, то можете далее платить на тот же адрес кошелька криптовалюты, что получили ранее с указанием тех же деталей платежа. Хотя желательно заходить на нашу службу для получения новостей хотябы раз в пол года или подписаться на важные новости и сообщения оставив свой емайл.'),
                ),
            H4(A(T('Понятно'), _onclick='$(".okIN").hide("fast");ajax("%s")'
              % URL('aj','ok_to',args=['Wt']), _class='button warn'), _class='center'),
            _class='col-sm-12 okIN',
            _style='color:chocolate;display:%s;' % (okIN and 'none' or 'block')),
            _class='row'),
        'bg-warning pb-10')


    # если есть скрытый партнерский код то его забьем пользователю
    deal_acc = db.deal_accs[deal_acc_id]
    if not deal_acc.partner:
        try:
            _ = GIFT_CODE
        except:
            GIFT_CODE = session.gc

    #from gifts_lib import gift_proc
    #GIFT_CODE, gift_mess = gift_proc(db, T, deal, deal_acc, request, session, GIFT_CODE)
    #if GIFT_CODE:
    #    h += sect(XML(gift_mess), 'gift-bgc pb-10 pb-10')
    import gifts_lib
    adds_mess = XML(gifts_lib.add_mess_curr(deal_acc, curr_out, T))
    if adds_mess:
        h += sect(XML(adds_mess), 'gift-bgc pb-10 pb-10')

    hh = CAT(H2(T('Реквизиты оплаты'), _class='center'))

    if 'base_rate' in result:
        base_rate = result['base_rate']
        is_order = True
        dealer_deal = None
        volume_out, tax_rep = db_client.calc_fees(db, deal, dealer_deal, curr_in, curr_out, volume_in,
                                           base_rate, is_order, note=1)

        volume_out = common.rnd_8(volume_out)
        rate_out = volume_out / volume_in
        #print 'rate_out', rate_out, 'volume_in', volume_in, 'volume_out', volume_out

        # new make order
        order_id = db.orders.insert(
            ref_ = deal_acc_addr['id'],
            volume_in = volume_in,
            volume_out = volume_out,
            )
        # теперь стек добавим, который будем удалять потом
        db.orders_stack.insert( ref_ = order_id )
        txfee = float(xcurr_out.txfee or 0.0001)
        hh += DIV(P(
            T('Создан заказ №%s') % order_id,' ', T('на заморозку обменного курса по'), ' ', rate_out,
            ' (', T('обратный курс'), ' ', round(1.0/float(rate_out),8),') ',
            T('для объема'),' ',volume_out, ' ', curr_out_abbrev, ' (', T('с учётом комиссии сети'),' ',txfee,').',
            H5('*',T('Данный курс будет заморожен для Вас на 20 минут для объёма криптовалюты не больше указанного. Проверить можно по номеру заказа в списке платежей.'))),
            _class='row')
    else:
        base_rate = volume_out = rate_out = tax_rep = None

    _, url_uri = common.uri_make( curr_in.name2, addr_in, {'amount':volume_in, 'label': db_client.make_x_acc_label(deal, addr_out, curr_out_abbrev)})

    if token_system_in:
        addr_out_full = (token_system_out and ('%d' % token_out.token_key) or curr_out_abbrev) + ':' + addr_out
    else:
        addr_out_full = addr_out

    free_bal = result['free_bal']
    hh += DIV(
        P(
        T('Оплата обмена на'), ' ',curr_out_abbrev, ' ', T('с выплатой монет на адрес'),  ': ', addr_out, '. ',
        CAT(T('Текущая сумма обмена'), ' ', volume_out, ' ', curr_out_abbrev,' (', T('с учётом комиссии сети'),') ',
        ' ', T('из доступных в службе')) if volume_out else CAT(T('Доступно в службе')),
        ' ', free_bal, '. '),
        P(T('Вы можете делать ещё платежи на созданый %s адрес для совершения автоматического обмена %s на %s по текущему курсу.') % (curr_in_name, curr_in_name, curr_out_name),
        ),
        DIV(CENTER(
            A(SPAN(T('Оплатить'),' ', volume_in or '', ' ',
            IMG(_src=URL('static','images/currs/' + curr_in_abbrev + '.png'), _width=50)),
            _class='block button blue-bgc', _style='font-size:x-large; max-width:500px; margin:0px 7px;',
            _href=url_uri),
            H5(T('Если кошелек не запускается автоматически, произведите оплату вручную по указанным ниже реквизитам, см. ниже')),
                    ),
            _class='row'
            ) if True or not token_system_in else '',
        BR(),
        DIV(H3(A(T('Показать QR-код'),
               _onclick="jQuery(this).parent().html('<i class=\"fa fa-spin fa-refresh\" />')",
               callback=URL('plugins','qr', vars={'mess': url_uri}),
               target='tagQR',
               _class='button blue-bgc right'), _class='pull-right-'), _class='col-sm-12', _id='tagQR'),
        T('Для оплаты вручную скопируйте детали платежа в свой кошелек'), ': ',
        H5(T("Двойной клик по полю или нажмите Ctrl-A внутри поля для выделения в поле всех данных. Далее нажмите Ctrl-C для копирования выделенного в буфер обмена")),
        FORM( ## ВНИМАНИЕ !!! тут имена полей надо другие указывать или
            # FORM в основной делать тоже иначе они складываются
            LABEL(T("Volume"),":"), " ", INPUT(_name='v', value=volume_in, _class="pay_val", _readonly=''), curr_in_abbrev, BR(),
            LABEL(T("Получатель"),":"), " ", INPUT(_name='addr_in', _value=addr_in, _class='wallet', _readonly=''), BR(),
            CAT(LABEL(T("Назначение (вставьте в заголовок платежа или в тело сообщения, которое так же можно зашифровать)"),":"), " ", INPUT(_name='addr_out', _value=addr_out_full, _class='wallet', _readonly=''), BR()) if token_system_in else '',
            #T('Резервы службы'), ' ', B(free_bal), ' ', T('рублей'), BR(),
            #LOAD('where', 'for_addr', vars={'addr': addr_in}, ajax=True, times=100, timeout=20000,
            #    content=IMG(_src=URL('static','images/loading.gif'), _width=48)),
            INPUT( _type='submit',
                _class='button blue-bgc',
                _value=T('Подробный просмотр платежей'),
                _size=6,
                  ),
            _action=URL('where', 'index'), _method='post',
            )
        )
    
    
    h += sect(hh, 'bg-info pb-10')

    if base_rate:
        h += sect(DIV(DIV(
            H3(T('Почему получился такой курс?')),
            tax_rep, BR(),
            T('При этом Вы получаете следующие преимущества при обмене криптовалют у нас'),':',
            UL(
                [
                    T('Вы можете теперь постоянно делать обмен со своего кошелька на полученный адрес даже не заходя на наш сайт'),
                    T('не нужно нигде регистрироваться'),
                    T('не нужно делать подтверждения по СМС или по емайл'),
                    T('обмен производится быстро и автоматически'),
                    T('Вам не нужно хранить свои деньги у нас'),
                ]
            ),
            T('Время - деньги!'),
            _class='col-sm-12'), _class='row'))

    h += SCRIPT('''
        $('html, body').animate( { scrollTop: $('#tag2').offset().top - $('#aside1').height() }, 500 );
      ''')
    
    #response.js = "$('.go2-btn').removeClass('disabled');$('#go2').children('i').removeClass('fa-refresh fa-spin').addClass('fa-search');"

    return h


def get_rate_result(request, get_currs = False):
    import rates_lib
    result = rates_lib.get_rate_for_api(db, request.vars.get('curr_in'), request.vars.get('curr_out'), request.vars.get('vol_in'), get_limits = True, get_currs = get_currs)

    print result
    
    if 'error' in result:
        return mess(result['error']), result

    if 'wrong' in result:
        h = CAT(
            H2(XML(T('Обменный курс %s/%s не найден') % (B(result['curr_in']), B(result['curr_out']))), '', _class='alert_value'),
            P(T('Возможно это носит временный характер. Вы можете совершить платеж по предоставленным платежным реквизитом и ваша заявка автоматически сработает при появлении курса обмена на сервисе и при условии что нужные Вам средства есть на сервисе в достаточном объеме'), '.')
            )
        return DIV(h, _class='container'), result

    #import gluon.contrib.simplejson
    #return CAT(gluon.contrib.simplejson.dumps(result))
    h = CAT()
    if result['rate_out'] <= 0:
        h += CAT(
            H2(
               XML(T('Введена слишком маленькая величина для обмена: %s. Введите значение больше') % (B(result['volume_in'], '[', result['curr_in'], ']'))), '', _class='alert_value'))
        return DIV(h, _class='container'), result
        
    h += H2(T('Найден курс обмена для'), ' ', B(result['volume_in'], '[', result['curr_in'], ']'), ': x ', SPAN(B(result['rate_out']), _class='rate_succes'))

    if result['free_bal'] - result['volume_out'] < 0:
        h += CAT(H2(T('Сейчас на сервисе недостаточно средств'), ' ', B(result['curr_out']), _class='alert_value'),
            P(XML(T('Скорее всего это носит временный характер. Вы можете совершить платеж по предоставленным платежным реквизитом и ваша заявка автоматически сработает при появлении на сервисе нужных Вам средств %s в достаточном объеме и при условии что курс обмена будет доступен') % ('<b>'+result['curr_out']+'</b>')), '. ',
             T('Для исполнения вашей заявки необходимо чтобы на сервисе появилось еще'), ' ', B(result['volume_out'] - result['free_bal'],
              '[', result['curr_out'], ']', _class='alert_value'))
            )

    if result['lim_bal'] > 0 and result['may_pay'] < result['volume_in']:
        h += CAT(H2(T('Сейчас сервис не готов принять всю вашу сумму'), ' ', B(result['curr_in']), _class='alert_value'),
            P(XML(T('Скорее всего это носит временный характер. Вы можете совершить платеж по предоставленным платежным реквизитом и ваша заявка автоматически сработает когда остатки %s на сервисе уменьшатся до %s и при условии что на сервисе досточно нужных Вам средств %s и что курс обмена доступен') % ('<b>'+result['curr_in']+'</b>', B(result['volume_in'], '[', result['curr_in'], ']'), '<b>'+result['curr_out']+'</b>')), '. ', T('Либо уменьшите количество обмена до'), ' ', B(result['may_pay'], '[',result['curr_in'],']', _class='alert_value'))
            )

    return DIV(h, _class='container'), result

def get_rate():
    response.js = "$('.go-btn').removeClass('disabled');$('#go').children('i').removeClass('fa-refresh fa-spin').addClass('fa-search');"

    h, _ = get_rate_result(request)

    return h

################# used INCOME AMOUNT ###########################################
###  pars:
### curr = xcurr ABBREV
### sum + addr + mess
### /BTC/addr/sum_in
def index():

    #common.page_stats(db, response['view'])
    #print request.args

    response.title=T("Exchange Bitcoin and ERA, COMPU")
    response.subtitle = T('Bitcoin Erachain Gate')

    abbrev = request.args(0)
    addr = request.args(1)
    vol = request.args(2)

    title = abbrev and addr and T('Ваш кошелек') + ': ' + abbrev + ' ' + addr[:5] + '***' + addr[-3:] or response.title
    subtitle = session.date_log and (T('Дата посещения %s') % session.date_log) or response.subtitle

    try:
        session.date_log = request.now
    except:
        print 'to_coin session error .date_log:', type(request.now), request.now

    if request.vars:
        abberv = abbrev or request.vars.get('curr') or session.toCoin
        addr = addr or request.vars.get('addr') or session.toCoinAddr
        vol = vol or request.vars.get('vol') or session.vol

    input_currs = []
    output_currs = []
    inp_currs = []
    otpions_currs = []
    for r in db(
             (db.currs.used == True)
             & (db.currs.id == db.xcurrs.curr_id)
             & (not abbrev or db.currs.abbrev == abbrev)
             ).select(orderby=~db.currs.uses):
        free_bal = db_client.curr_free_bal(r.currs)
        inp_currs.append([r.currs.id, r.currs.abbrev, r.currs.name, free_bal])
        
        input_currs.append(
            (
                ## need DIV insead SPAN
            DIV(IMG(_src=URL('static', 'images/currs/' + r.currs.abbrev + '.png'), _width=30, _alt=''),
                        ' ', SPAN(r.currs.name, _style='font-size:22px'),
                _onclick='$("#curr_in").val("' + r.currs.abbrev + '");', # _style='margin: 0px -20px; padding: 10px 40px 10px 30px;'
                 _style='margin: 0px -20px; padding: 5px 20px 5px 20px; font-size:22px'
                ), False, ''
              )
            )
        output_currs.append(
            (
            DIV(IMG(_src=URL('static', 'images/currs/' + r.currs.abbrev + '.png'), _width=30, _alt=''),
                        ' ', SPAN(r.currs.name, _style='font-size:22px'), ' ', free_bal,
                _onclick='$("#curr_out").val("' + r.currs.abbrev + '");', # _style='margin: 0px -20px; padding: 10px 40px 10px 30px;'
                 _style='margin: 0px -20px; padding: 5px 20px 5px 20px; font-size:24px'
                 ), False, ''
              )
            )

    if len(inp_currs)==0:
        return err_dict(
            T('ОШИБКА: Нет доступных криптовалют для обмена')
            + (abbrev and (' ' + T('или неправильно задано имя [%s] нужной криптовалюты!') % abbrev) or ''))

    
    input_currs = [
        (
            TAG.i(_class='fa fa-search go-btn- button- ll-blue-bgc- center', _style='width:50px;',
                    ),
            False, None, input_currs)
        ]
    output_currs = [
        (
            TAG.i(_class='fa fa-search go-btn- button- ll-blue-bgc- center', _style='width:50px;',
                  ),
            False, None, output_currs)
        ]

    amo_in = INPUT(_name='amo_in')

    return dict(title=title, subtitle=subtitle, inp_currs=inp_currs,
               abbrev=abbrev, addr=addr, vol=vol, input_currs = input_currs, output_currs=output_currs)
