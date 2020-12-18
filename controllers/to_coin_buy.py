# coding: utf8

#if not IS_LOCAL:
#    raise HTTP(200, 'under construct')

if False:
    from gluon import *
    import db
    request = current.request
    response = current.response
    session = current.session
    cache = current.cache
    T = current.T

import datetime, time

import common
import db_client
import db_common
import ed_common
import recl
import rates_lib

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


###############################################################
# /deal_id/curr_id
def get():

    args = request.args
    ##print args, '\n', request.vars
    if len(args) < 2: return mess('err...')
    deal_id = args(0)
    curr_id = args(1)
    if not deal_id.isdigit() or not curr_id.isdigit(): return mess('dig...')
    # теперь можно задать открытие кнопки
    scr = "$('#cvr%s').css('display','none');$('#tag%s').show('slow');" % (curr_id, curr_id)
    response.js = scr

    vol = request.vars.vol
    if not vol or len(vol) > 20: return mess(T('ОШИБКА') + ': ' + T('Задайте количество'))
    try:
        vol = float(vol)
        curr_id = int(curr_id)
    except:
        return mess('digs...')

    addr_out = request.vars.addr
    #print request.vars
    if not addr_out:
        return mess(T('ОШИБКА: Задайте кошелек'))

    try:
        if len(addr_out) < 25 or len(addr_out) > 44:
            ##проверка на счет - если это не емайл и не ттелефон то надо длинну и на циифры
            return mess(T('ОШИБКА: неверный кошелек'))
    except:
        return mess(T('ОШИБКА: неверный кошелек 2'))

    deal = db.deals[ deal_id ]
    if not deal: return mess(T('deal...'))
    
    curr_in = db.currs[ curr_id ]
    if not curr_in: return mess(T('curr...'))
    xcurr_in = db(db.xcurrs.curr_id == curr_id).select().first()
    if not xcurr_in: return mess(T('xcurr...'))

    import crypto_client

    #print request.vars
    curr_out = db.currs[ request.vars.curr_out ]
    xcurr_out = db(db.xcurrs.curr_id == curr_out.id).select().first()
    curr_out_abbrev = curr_out.abbrev
    curr_out_name = curr_out.name

    token_system_in = None
    token_key_in = xcurr_in.as_token
    if token_key_in:
        token_in = db.tokens[token_key_in]
        token_system_in = db.systems[token_in.system_id]

    token_system_out = None
    token_key_out = xcurr_out.as_token
    if token_key_out:
        token_out = db.tokens[token_key_out]
        token_system_out = db.systems[token_out.system_id]

    #print request.application[-5:]
    if request.application[:-3] != '_dvlp':
        # чето конфликт если из ipay3_dvlp вызывать то кошелек на ipay3 не коннектится
        if token_system_out:
            curr_block = crypto_client.get_height(xcurr_out, token_system_out)
            if type(1) != type(curr_block):
                return mess(T('Connection to [%s] is lost, try later ') % curr_out_name)

            pass
        else:
            try:
                conn = crypto_client.connect(curr_out, xcurr_out)
            except:
                conn = None

            if not conn:
                return mess(T('Connection to [%s] is lost, try later ') % curr_out_name)

        if crypto_client.is_not_valid_addr_xcurr(token_system_out, addr_out, conn):
            return mess(T('address not valid for - ') + curr_out_name + ' - ' + addr_out)

    try:
        session.toCoin = curr_out_abbrev
        session.toCoinA = addr_out
    except:
        print 'to_coin session error .toCoinA:', type(addr_out), addr_out

    try:
        session.vol = vol
    except:
        print 'to_coin session error .vol:', type(vol), vol

    curr_in_name = curr_in.name

    if token_system_in:
        addr_in = token_system_in.account
        deal_acc_id, deal_acc_addr = db_client.get_deal_acc_addr(db, deal_id, curr_out, addr_out, addr_in, xcurr_in)
    elif xcurr_in.protocol == 'geth':
        addr_in = xcurr_in.main_addr
        deal_acc_id, deal_acc_addr = db_client.get_deal_acc_addr(db, deal_id, curr_out, addr_out, addr_in, xcurr_in)
    else:
        x_acc_label = db_client.make_x_acc(deal, addr_out, curr_out_abbrev)
        # найдем ранее созданный адресс для этого телефона, этой крипты и этого фиата
        # сначала найтем аккаунт у дела
        deal_acc_id = db_client.get_deal_acc_id(db, deal, addr_out, curr_out)
        # теперь найдем кошелек для данной крипты
        deal_acc_addr = db_client.get_deal_acc_addr_for_xcurr(db, deal_acc_id, curr_in, xcurr_in, x_acc_label)
        if not deal_acc_addr:
            return mess((T('Связь с сервером %s прервана') % curr_in_name) + '. ' + T('Невозможно получить адрес для платежа') + '. ' + T('Пожалуйста попробуйте позже'), 'warning')

        addr_in = deal_acc_addr.addr
        
    h = CAT()

    okIN = session.okWt
    h += sect(DIV(
        okIN and DIV(H3(A(T('Правила оплаты'), _onclick='$(".okIN").show("fast");', _class='button warn right'),
                      _class='pull-right-'), _class='col-sm-12') or '',
        DIV(okIN and ' ' or H3(T('ПРАВИЛА ОПЛАТЫ'), _class='center'),
           P(T('При оплате необходимо соблюдать следующие правила:')),
           UL(
                T('Желательно задать обратный адрес для возврата монет на случай если наша служба по каким-либо причинам не сможет совершить оплату по делу [%s]') % deal.name,
                T('Если Вы не задали обратный адрес для возврата монет, то необходимо платить биткоины и другую криптовалюту только со своего кошелька, задав адреса входов, которыми Вы действительно обладаете, а не с кошельков бирж, пулов или разных онлайн-кошельков. Так как монеты, в случае если платеж будет отвергнут нашим партнёром, могут автоматически вернуться только на адрес отправителя.'),
                T('Комиссия сети добавляется к сумме для обмена, о чем указывается ниже.'),
                T('Если Вы оплатите другую сумму, то курс обмена может немножко измениться'),
                T('Если Вы платите регулярно, то можете платить на тот же адрес кошелька криптовалюты, что получили ранее. Хотя желательно заходить на нашу службу для получения новостей хотябы раз в пол года или подписаться на важные новости и сообщения оставив свой емайл.'),
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
    
    volume_out = vol
    hh = CAT(H2('4. ' + T('Оплатите по данным реквизитам'), _class='center'))

    # используем быстрый поиск курса по формуле со степенью на количество входа
    # только надо найти кол-во входа от выхода
    pr_b, pr_s, pr_avg = rates_lib.get_average_rate_bsa(db, curr_in.id, curr_out.id, None)
    if pr_avg:
        vol_in = volume_out / pr_b
        amo_out, _, best_rate = rates_lib.get_rate(db, curr_in, curr_out, vol_in)
    else:
        best_rate = None

    if best_rate:
        is_order = True
        dealer_deal = None
        # сначала открутим обратную таксу
        txfee = float(xcurr_out.txfee or 0.0001)
        volume_out += txfee
        volume_in, mess_in = db_client.calc_fees_back(db, deal, dealer_deal, curr_in, curr_out, volume_out,
                                           best_rate, is_order, note=0)
        ## теперь таксы для человека получим и должна та же цифра выйти
        vol_out_new, tax_rep = db_client.calc_fees(db, deal, dealer_deal, curr_in, curr_out, volume_in,
                                           best_rate, is_order, note=1)
        vol_out_new = common.rnd_8(vol_out_new)
        if common.rnd_8(volume_out) != vol_out_new:
            print 'to_phone error_in_fees: volume_out != vol_out_new', volume_out,  vol_out_new

        volume_in = common.rnd_8(volume_in)
        rate_out = volume_out / volume_in

        # new make order
        order_id = db.orders.insert(
            ref_ = deal_acc_addr.id,
            volume_in = volume_in,
            volume_out = volume_out,
            )
        # теперь стек добавим, который будем удалять потом
        db.orders_stack.insert( ref_ = order_id )
        hh += DIV(
            T('Создан заказ №%s') % order_id,' ',
            T('на заморозку обменного курса по'), ' ', rate_out,
            ' (',T('обратный курс'), ' ', round(1.0/float(rate_out),8),') ',
            T('для объема'),' ',volume_out, ' ', curr_out_abbrev, ' (', T('с учётом комиссии сети'),' ',txfee,').',
            H5('*',T('Данный курс будет заморожен для Вас на 20 минут для объёма криптовалюты не больше указанного. Проверить можно по номеру заказа в списке платежей.')),
            _class='row')
    else:
        volume_in = rate_out = tax_rep = None
        hh += mess('[' + curr_in_name + '] -> [' + curr_out_name + ']' + T(' - лучшая цена не доступна.') + T('Но Вы можете оплатить вперед'), 'warning pb-10')

    _, url_uri = common.uri_make( curr_in.name2, addr_in, {'amount':volume_in, 'label': db_client.make_x_acc_label(deal, addr_out, curr_out_abbrev)})

    curr_in_abbrev = curr_in.abbrev
    lim_bal, may_pay = db_client.is_limited_ball(curr_in)
    if lim_bal:
        if may_pay> 0:
            lim_bal_mess = P(
                T('Внимание! Для криптовалюты %s существует предел запаса и поэтому наша служба может принять только %s [%s], Просьба не превышать это ограничение') % (curr_in.name, may_pay, curr_in_abbrev), '.',
                _style='color:black;'
                )
        else:
            lim_bal_mess = P(
                T('ВНИМАНИЕ! Наша служба НЕ может сейчас принимать %s, так как уже достугнут предел запаса её у нас. Просьба попробовать позже, после того как запасы [%s] снизятся благодаря покупке её другими пользователями') % (curr_in.name, curr_in_abbrev),
                '. ', T('Иначе Ваш платеж будет ожидать момента когда запасы снизятся ниже %s') % lim_bal,'.',
                _style='color:brown;')
    else:
        lim_bal_mess = ''

    free_bal = db_client.curr_free_bal(curr_out)
    if token_system_in:
        addr_out_full = (token_system_out and ('%d' % token_out.token_key) or curr_out.abbrev) + ':' + addr_out
    else:
        addr_out_full = addr_out

    hh += DIV(
        P(
        T('Оплата обмена на'), ' ',curr_out_abbrev, ' ', T('с выплатой монет на адрес'),  ': ',
        addr_out, '. ', T('Текущая сумма обмена'), ' ', volume_out, ' ', curr_out_abbrev,' (',
            T('с учётом комиссии сети'),') ',
        ' ', T('из доступных в службе'), ' ', free_bal, '. ',
        T('Так же Вы можете делать ещё платежи на созданый %s адрес для совершения автоматического обмена %s на %s по текущему курсу.') % (curr_in_name, curr_in_name, curr_out_name),
        ),
        volume_out > free_bal and P(
                        H3(T('Сейчас средств на балансе меньше чем Вам надо'), _style='color:crimson;'),
                        SPAN(T('Поэтому Ваш заказ будет исполнен позже'), BR(),
                        T('когда на балансе службы появится достаточно средств'), _style='color:black;'), BR(),
                        ) or '',
        lim_bal_mess,
        DIV(CENTER(
            A(SPAN(T('Оплатить'),' ', volume_in or '', ' ',
            IMG(_src=URL('static','images/currs/' + curr_in_abbrev + '.png'), _width=50)),
            _class='block button blue-bgc', _style='font-size:x-large; max-width:500px; margin:0px 7px;',
            _href=url_uri),
                    ),
            _class='row'
            ) if not token_system_in else '',
        BR(),
        DIV(
            A(T('Показать QR-код'),  _class='btn btn-info',
               ##_onclick="jQuery(this).parent().html('%s')" % IMG(_src=URL('static','images/loading.gif'), _width=64),
               _onclick="jQuery(this).parent().html('<i class=\"fa fa-spin fa-refresh\" />')",
               callback=URL('plugins','qr', vars={'mess': url_uri}),
               target='tag0',
               #delete='div#tag0'
               ),
            _id='tag0'),
        H3(T('или')),
        T('Оплатите вручную'), '. ',# 'URI:', url_uri,'. ',
        T("Для этого скопируйте значения полей (двойной клик по полю для выделения) и вставьте их в платеж на вашем кошельке"), ': ',
        FORM( ## ВНИМАНИЕ !!! тут имена полей надо другие указывать или
            # FORM в основной делать тоже иначе они складываются
            LABEL(T("Volume")), " ", INPUT(_name='v', value=volume_in, _class="pay_val", _readonly=''), curr_in_abbrev, BR(),
            LABEL(T("Получатель")), " ", INPUT(_name='addr_in', _value=addr_in, _class='wallet', _readonly=''), BR(),
            CAT(LABEL(T("Назначение (вставьте в заголовок платежа)")), " ", INPUT(_name='addr_out', _value=addr_out_full, _class='wallet', _readonly=''), BR()) if token_system_in else '',
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
        $('html, body').animate( { scrollTop: $('#cvr%s').offset().top - $('#aside1').height() }, 500 );
      ''' % (curr_id))
    return h

############################################################
###  pars:
### address + vol + mess
def sel():

    addr_out = None

    h = CAT(SCRIPT('''
        $('.btn_sel').removeClass('disabled');
        $('html, body').animate( { scrollTop: $('#sel').offset().top - $('#aside1').height() }, 500 );
      '''))
    try:
        curr_out_id = request.args(0)
        curr_out_id = curr_out_id and int(curr_out_id)
        curr_out = db.currs[ curr_out_id ]
        curr_out_name = curr_out.name
    except:
        return h+'error curr_id'

    deal_name = 'to COIN'
    deal = db.deals[TO_COIN_ID]
    if deal:
        deal_id = deal.id
    else:
        curr_rub = db(db.currs.abbrev=='RUB').select().first()
        deal_id = db.deals.insert(name = deal_name, name2 = deal_name, fee_curr_id = curr_rub.id,
                used = False, fee = 1, MIN_pay = 0, MAX_pay = 0)
        deal = db.deals[ deal_id ]

    from gluon.storage import Storage
    vars = Storage()
    if request.vars:
        vn = 'vol'
        if vn in request.vars:
            vars[vn] = test_vol(request.vars[vn])
        vn = 'addr'
        if vn in request.vars:
            addr_out = request.vars[vn]
            vars[vn] = addr_out
    
    dealer = None
    for rr in db_client.get_xcurrs_for_deal(db, 0, curr_out, deal, dealer):
        if rr['id'] == curr_out.id: continue
        #print rr
        id = '%s' % rr['id']
        disabled = rr['expired']
        if disabled:
            memo = CAT(T('Курс не найден'),', ', T('Когда курс будет получен платеж пройдёт автоматически'), '. ', T('Или попробуйте зайти позже'))
            _class = 'col sel_xcurrNRT'
        else:
            memo = CAT(SPAN(' ', T('по курсу'),  (' %8g' % rr['price']), ' ', T(' нужно оплатить около')),' ',
                    B(SPAN(_class='pay_vol')), ' ', rr['name'])
            _class = 'col sel_xcurrRTE'

        # пусть клики все равно будут
        onclick='''
                      //$(this).css('z-index','0');
                      $('#tag%s').hide('fast');
                      $('#cvr%s').css('display','block'); // .css('z-index','10');
                      ajax('%s',['vol','addr','curr_out'], 'tag%s');
                      ''' % (id, id, URL('get', args=[deal_id, id]), id)
        #print rr
        h += DIV(
            DIV(
                DIV(
                    #T('Есть'), ': ', rr['bal_out'],' ',
                    IMG(_src=URL('static','images/currs/' + rr['abbrev'] + '.png'),
                      _width=60, __height=36, _class='lst_icon', _id='lst_icon' + id),
                    SPAN(rr['price'], _class='price hidden'),
                    SPAN(rr['abbrev'], _class='abbrev hidden'),
                    memo,
                    '. ', SPAN(T('Всего было продаж:'), rr['used'], _class='small'),
                    _onclick=onclick if onclick else '',
                    _id='btn%s' % id,
                    _class=_class,
                ),
              DIV(TAG.i(_class='fa fa-spin fa-spinner right wait1'),
                  _id='cvr%s' % id,
                  _class='col sel_xcurrCVR'),
              _class='row sel_xcurr'),
            _class='container')
        h += DIV(_id='tag%s' % id, _class='blue-c')

    _, reclams = recl.get(db,2)

    #response.top_line = None
    return dict(curr_out_id = curr_out_id, addr=addr_out,
                img_url = URL('static','images/currs/' +  curr_out.abbrev + '.png'),
                curr_out_name = curr_out_name,
                vars=vars,
                xcurrs_h=h, reclams=reclams)

############################################################
###  pars:
### curr = xcurr ABBREV
### sum + address + mess
### /BTC/address/sum
def index():

    #common.page_stats(db, response['view'])
    #print request.args

    response.title=T("Обмен биткоинов и других цифровых активов между собой включая токены Erachain")
    response.subtitle = T('Bitcoin Dogecoin Litecoin NEXT')

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
        abberv = abbrev or request.vars.get('curr')
        addr = addr or request.vars.get('addr')
        vol = vol or request.vars.get('vol')

    inp_currs = []
    for r in db(
             (db.currs.used == True)
             & (db.currs.id == db.xcurrs.curr_id)
             & (not abbrev or db.currs.abbrev == abbrev)
             ).select(orderby=~db.currs.uses):
        free_bal = db_client.curr_free_bal(r.currs)
        inp_currs.append([r.currs.id, r.currs.abbrev, r.currs.name, free_bal])

    if len(inp_currs)==0:
        return err_dict(
            T('ОШИБКА: Нет доступных криптовалют для обмена')
            + (abbrev and (' ' + T('или неправильно задано имя [%s] нужной криптовалюты!') % abbrev) or ''))

    return dict(title=title, subtitle=subtitle, inp_currs=inp_currs,
               abbrev=abbrev, addr=addr, vol=vol)
