# coding: utf8

if False:
    from gluon import *
    import db
    request = current.request
    response = current.response
    session = current.session
    cache = current.cache
    T = current.T

#import copy
import datetime, time
import re

import common
#import db_common
#import ed_common
import db_client
#import crypto_client
import ed_common
import recl

import db_common
import rates_lib

# берем только рубль
curr_out, x, ecurr_out = db_common.get_currs_by_abbrev(db,"RUB")#ecurr_out = db.ecurrs[ecurr_out_id]
ecurr_out_id = ecurr_out.id

deal_name = 'WALLET'
# найдем дело
deal = db(db.deals.name==deal_name).select().first()
if not deal: raise HTTP(200, T('ERROR: not found deal "%s"') % deal_name)

deal_id = deal.id

# заменить все не цифры и проверить длинну
regular_phone = re.compile("\D")
def valid_phone(ph):
    str = regular_phone.sub("","%s" % ph)
    if len(str) == 11: return str
    return

def test_vol(vol, _min=None, _max=None):
    try:
        vol = float(vol)
    except:
        return None
    if _max and vol > _max: return _max
    if _min and vol < _min: return _min
    return vol

def get_e_bal(deal, dealer, dealer_acc):
    e_balance = db_common.get_balance_dealer_acc( dealer_acc )
    MAX = int(deal.MAX_pay or 1777)
    if e_balance:
        #dealer_acc.balance = e_balance
        #dealer_acc.update_record()
        if e_balance < MAX*3:
             MAX = int(e_balance/3)
    return e_balance, MAX


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
def get():

    args = request.args
    #print args, '\n', request.vars
    if len(args) != 1: return mess('err...')
    curr_id = args(0)
    if not curr_id.isdigit(): return mess('dig...')
    # теперь можно задать открытие кнопки
    scr = "$('#cvr%s').css('display','none');$('#tag%s').show('slow');" % (curr_id, curr_id)
    response.js = scr

    vol = request.vars.vol
    if not vol or len(vol) > 20: return mess(T('ОШИБКА') + ': ' + T('Задайте количество'))
    try:
        vol = float(vol)
        curr_id = int(curr_id)
        dealer_id = int(request.vars['dealer'])
        dealer = db.dealers[dealer_id]
    except:
        return mess('digs...')

    acc = request.vars.acc
    #print request.vars
    if not acc:
        return mess(T('ОШИБКА: Задайте кошелек'))

    try:
        if len(acc) < 6 or len(acc) > 40 or not IS_EMAIL(acc) and not valid_phone(acc) and not acc.isdidit():
            ##проверка на счет - если это не емайл и не ттелефон то надо длинну и на циифры
            return mess(T('ОШИБКА: неверный кошелек'))
    except:
        return mess(T('ОШИБКА: неверный кошелек 2'))

    curr_in = db.currs[ curr_id ]
    if not curr_in: return mess(T('curr...'))
    xcurr_in = db(db.xcurrs.curr_id == curr_id).select().first()
    if not xcurr_in: return mess(T('xcurr...'))

    try:
        session.toDlrAcc = acc
    except:
        print 'to_wallet session error .toDlrAcc:', type(acc), acc

    dealer_acc = ed_common.sel_acc_max(db, dealer, ecurr_out, vol)
    if not dealer_acc:
        return mess('''Извините, возможно достигнуто ограничение переводов на сотовые телефоны и электронные кошельки,
        просьба воспользоваться прямой оплатой нужных Вам услуг, например из меню "Всё". 
        Или можно уменьшить сумму платежа или подождать до следующего дня или месяца для снятия лимитов.
        ''', 'warning')
    
    dealer_deal = db((db.dealer_deals.dealer_id == dealer.id)
        & (db.dealer_deals.deal_id == deal.id )
        ).select().first()
    if not dealer_deal:
        return mess(T('Не найден дилер для дела [%s]... Зайдите позже') % deal.name, 'warning')

    MIN = db_common.gMIN(deal, dealer)
    if vol < MIN:
        try:
            session.vol = MIN
        except:
            print 'to_wallet session error .vol:', type(MIN), MIN
        return mess( T('ОШИБКА: Слишком маленькая сумма платежа %s < %s') % (vol, MIN))
    else:
        try:
            session.vol = vol
        except:
            print 'to_wallet session error .vol:', type(vol), vol

    # теперь проверку на правильность кошелька для дилера электронных платежей
    #res = ed_common.pay_test(db, deal, dealer, dealer_acc, dealer_deal, acc, deal.MIN_pay or dealer.pay_out_MIN or 20, False)
    #res = {'error': ' TEST'}
    if False and res.get('status')!='success':
        m = 'error_description' in res and res.ger('error_description', res.get('error', 'dealer error'))
        m = T('Платежная система %s отвергла платеж, потому что: %s') % (dealer.name, m)
        return mess(m, 'warning')

    token_system_in = None
    token_key_in = xcurr_in.as_token
    if token_key_in:
        token_in = db.tokens[token_key_in]
        token_system_in = db.systems[token_in.system_id]

    if token_system_in:
        addr_in = token_system_in.account
        deal_acc_id, deal_acc_addr = db_client.get_deal_acc_addr(db, deal_id, curr_out, acc, addr_in, xcurr_in)
    elif xcurr_in.protocol == 'geth':
        addr_in = xcurr_in.main_addr
        deal_acc_id, deal_acc_addr = db_client.get_deal_acc_addr(db, deal_id, curr_out, acc, addr_in, xcurr_in)
    else:
        curr_out_abbrev = curr_out.abbrev
        x_acc_label = db_client.make_x_acc(deal, acc, curr_out_abbrev)
        # найдем ранее созданный адресс для этого телефона, этой крипты и этого фиата
        # сначала найтем аккаунт у дела
        deal_acc_id = db_client.get_deal_acc_id(db, deal, acc, curr_out)
        # теперь найдем кошелек для данной крипты
        deal_acc_addr = db_client.get_deal_acc_addr_for_xcurr(db, deal_acc_id, curr_in, xcurr_in, x_acc_label)
        if not deal_acc_addr:
            return mess((T('Связь с сервером %s прервана') % curr_in.name) + '. ' + T('Невозможно получить адрес для платежа') + '. ' + T('Пожалуйста попробуйте позже'), 'warning')

        #request.vars['deal_acc_addr']=deal_acc_addr
        addr_in = deal_acc_addr.addr
        
    curr_in_abbrev = curr_in.abbrev

    h = CAT()
    e_bal, MAX = get_e_bal(deal, dealer, dealer_acc)
    if vol > MAX:
        vol = MAX
        h += mess(T('Сумма платежа снижена до возможного наибольшего значения, желательно не превышать его'), 'warning')

    okIN = session.okWt
    h += sect(DIV(
        okIN and DIV(H3(A('Правила оплаты', _onclick='$(".okIN").show("fast");', _class='button warn right'),
                      _class='pull-right-'), _class='col-sm-12') or '',
        DIV(okIN and ' ' or H3('ПРАВИЛА ОПЛАТЫ', _class='center'),
           P(T('При оплате необходимо соблюдать следующие правила:')),
           UL(
                T('У оплат дела [%s] существуют ограничения по суммам, поэтому если Вы хотите оплатить бОльшую сумму, то Вам нужно делать платежи небольшими суммами в эквиваленте до %s рублей на тот же адрес кошелька криптовалюты, который Вы получили от нашей службы для этой услуги') % (deal.name, MAX * 1.0),
                T('Желательно задать обратный адрес для возврата монет на случай если наша служба по каким-либо причинам не сможет совершить оплату по делу [%s]') % deal.name,
                T('Если Вы не задали обратный адрес для возврата монет, то необходимо платить биткоины и другую криптовалюту только со своего кошелька, задав адреса входов, которыми Вы действительно обладаете, а не с кошельков бирж, пулов или разных онлайн-кошельков. Так как монеты, в случае если платеж будет отвергнут нашим партнёром, могут автоматически вернуться только на адрес отправителя.'),
                T('Если Вы оплатите другую сумму, то курс обмена может немножко измениться'),
                T('Если Вы платите регулярно, то можете платить на тот же адрес кошелька криптовалюты, что получили ранее. Хотя желательно заходить на нашу службу для получения новостей хотябы раз в пол года или подписаться на важные новости и сообщения оставив свой емайл.'),
                ),
            H4(A('Понятно', _onclick='$(".okIN").hide("fast");ajax("%s")'
              % URL('aj','ok_to',args=['Wt']), _class='button warn'), _class='center'),
            _class='col-sm-12 okIN',
            _style='color:chocolate;display:%s;' % (okIN and 'none' or 'block')),
            _class='row'),
        'bg-warning pb-10')


    # если есть скрытый партнерский код то его забьем пользователю
    deal_acc = db.deal_accs[deal_acc_id]
    import gifts_lib
    adds_mess = XML(gifts_lib.adds_mess(deal_acc, PARTNER_MIN, T))
    if adds_mess:
        h += sect(XML(adds_mess), 'gift-bgc pb-10 pb-10')
    
    volume_out = vol
    hh = CAT(H2(T('3. Оплатите по данным реквизитам')))

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
        # сначала открутим обратную таксу
        volume_in, mess_in = db_client.calc_fees_back(db, deal, dealer_deal, curr_in, curr_out, volume_out,
                                           best_rate, is_order, note=0)
        ## теперь таксы для человека получим и должна та же цифра выйти
        vol_out_new, tax_rep = db_client.calc_fees(db, deal, dealer_deal, curr_in, curr_out, volume_in,
                                           best_rate, is_order, note=1)
        vol_out_new = common.rnd_8(vol_out_new)
        if volume_out != vol_out_new:
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
            T('Создан заказ №'), ' ', order_id,' ',
            T('на заморозку обменного курса по'), ' ', rate_out,
            #T('обратный курс'), ' ', round(1.0/rate_out,8),
            H5(T('*Данный курс будет заморожен для Вас на 20 минут для объёма криптовалюты не больше указанного. Проверить можно по номеру заказа в списке платежей.')),
            _class='row')
    else:
        volume_in = rate_out = None
        tax_rep = '-'
        hh += mess('[' + curr_in.name + '] -> [' + curr_out.name + ']' + T(' - лучшая цена не доступна.') + T('Но Вы можете оплатить вперед'), 'warning pb-10')


    _, url_uri = common.uri_make( curr_in.name2, addr_in, {'amount':volume_in, 'label': db_client.make_x_acc_label(deal, acc, curr_out_abbrev)})

    lim_bal, may_pay = db_client.is_limited_ball(curr_in)
    if lim_bal:
        if may_pay> 0:
            lim_bal_mess = P(
                'Внимание! Для криптовалюты %s существует предел запаса и поэтому наша служба может принять только %s [%s], Просьба не превышать это ограничение' % (curr_in.name, may_pay, curr_in_abbrev), '.',
                _style='color:black;'
                )
        else:
            lim_bal_mess = P(
                'ВНИМАНИЕ! Наша служба НЕ может сейчас принимать %s, так как уже достугнут предел запаса её у нас. Просьба попробовать позже, после того как запасы [%s] снизятся благодаря покупке её другими пользователями' % (curr_in.name, curr_in_abbrev),
                '. ', 'Иначе Ваш платеж будет ожидать момента когда запасы снизятся ниже %s' % lim_bal,'.',
                _style='color:brown;')
    else:
        lim_bal_mess = ''

    free_bal, MAX = get_e_bal(deal, dealer, dealer_acc)
    hh += DIV(
        P(
        T('Оплата %s') % dealer.name,': ',
        acc, ' ', T('на сумму'), ' ', volume_out, ' ', curr_out_abbrev,
        ' ', T('из доступных в службе'), ' ', free_bal, '. ', T('Наибольший возможный платеж'), ' ', MAX,
        ),
        volume_out > free_bal and P(
                        H3(T('Сейчас средств на балансе меньше чем Вам надо'), _style='color:crimson;'),
                        SPAN(T('Поэтому Ваш заказ будет исполнен позже'), BR(),
                        T('когда на балансе службы появится достаточно средств'), _style='color:black;'), BR(),
                        ) or '',
        lim_bal_mess,
        DIV(CENTER(
            A(SPAN(T('Оплатить'),' ', volume_in or '', ' ',
            IMG(_src=URL('static','images/currs/' + curr_in.abbrev + '.png'), _width=50)),
            _class='block button blue-bgc', _style='font-size:x-large; max-width:500px; margin:0px 7px;',
            _href=url_uri),
                    ),
            _class='row'
            ),
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
        T('или'), BR(),
        T('Оплатите вручную'), ': ',
        FORM( ## ВНИМАНИЕ !!! тут имена полей надр друние указывать или
            # FORM в основной делать тоже иначе они складываются
            INPUT(_name='v', value=volume_in, _class="pay_val", _readonly=''), curr_in.abbrev, BR(),
            T("Для этого скопируйте сумму и адрес (двойной клик по полю для выделения) и вставьте их в платеж на вашем кошельке"), ': ',
            INPUT(_name='addr_in', _value=addr_in, _class='wallet', _readonly=''), BR(),
            #T('Резервы службы'), ' ', B(free_bal), ' ', T('рублей'), BR(),
            #LOAD('where', 'for_addr', vars={'addr_in': addr_in}, ajax=True, times=100, timeout=20000,
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
        T('При этом Вы получаете следующие преимущества при оплате биткоинами услуг и дел у нас'),
        UL(
            [
                T('не нужно нигде регистрироваться'),
                T('не нужно делать подтверждения по СМС или по емайл'),
                T('не нужно копить много денег - платежи возможны от %s [%s]') % (MIN, curr_out_abbrev),
                T('не нужно ждать сутки вывода')
            ]
        ),
        T(' Время - деньги!'),
        _class='col-sm-12'), _class='row'))

    h += SCRIPT('''
        $('html, body').animate( { scrollTop: $('#cvr%s').offset().top - $('#aside1').height() }, 500 );
      ''' % (curr_id))
    return h

############################################################
###  pars:
### ed = edealer_name
### sum + acc + mess
def index():

    #common.page_stats(db, response['view'])
    #print request.args

    response.title=T("Обмен биткоинов криптовалют на электронные деньги Яндекс")
    response.subtitle = T('Dogecoin Litecoin NEXT')

    if False and session.date_log:
        d_diff = datetime.datetime.today() - session.date_log
        if d_diff.seconds > 1200:
            session.date_log = None
            session.YD_acc = '-'

    acc = session.toDlrAcc
    title = acc and T('Ваш кошелек') + ':' + acc[:3] + '***' + acc[-3:] or response.title
    subtitle = session.date_log and (T('Дата посещения %s') % session.date_log) or response.subtitle

    try:
        session.date_log = request.now
    except:
        print 'to_wallet session error .date_log:', type(request.now), request.now

    # берем только тех кто за рубли и для этого дела
    # причем по 1 аккаунту на диллера тут нужно - для писка
    # какой диллер вообще на кошельки принимает
    ed_name = None
    if request.vars:
        vn = 'ed'
        if vn in request.vars:
            ed_name = request.vars[vn]

    limit_bal, inp_dealers_tab = ed_common.get_edealers_for_to_wallet(db, deal, curr_out, ecurr_out_id, ed_name)

    if len(inp_dealers_tab)==0:
        return err_dict(
            T('ОШИБКА: Нет доступных диллеров')
            + (ed_name and (' ' + T('или неправильно задано имя [%s] системы электронных денег!') % ed_name) or ''))
    
    inp_dealers = []
    for r in inp_dealers_tab:
        inp_dealers.append([r[0], ('%s [%s], ' + T('доступно') + ' %s, %s...%s') % r[1]])

    from gluon.storage import Storage
    vars = Storage()
    if request.vars:
        vn = 'sum'
        if vn in request.vars:
            vars[vn] = test_vol(request.vars[vn])
        vn = 'acc'
        if vn in request.vars:
            acc = request.vars[vn]
            vars[vn] = acc
            if not ed_name:
                return err_dict(T("ОШИБКА: Не задано имя системы электронных денег для данного кошелька %s! Пример ссылки: %s?ed=yandex&sum=1500&acc=423456780345") % (acc, URL()), True)
        vn = 'mess'
        if 'mess' in request.vars:
            vars[vn] = request.vars[vn]
    
    h = CAT()
    dealer = None
    for rr in db_client.get_xcurrs_for_deal(db, 0, curr_out, deal, dealer):
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
                      ajax('%s',['vol','acc','dealer'], 'tag%s');
                      ''' % (id, id, URL('get', args=[id]), id)
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
    xcurrs_h = h

    _, reclams = recl.get(db,2)

    #response.top_line = None

    return dict(title=title, subtitle=subtitle, acc=acc, inp_dealers=inp_dealers, limit_bal=limit_bal,
                # это для ограничения в поле ввода и пересчета в нем
                MIN = db_common.gMIN(deal, None),
                MAX = int(deal.MAX_pay or 2555),
                vars=vars,
                xcurrs_h=xcurrs_h, reclams=reclams)
