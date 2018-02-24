# coding: utf8

#import copy
import datetime
import re

import common
#import db_common
#import ed_common
import db_client
#import crypto_client
import ed_common

import db_common
import rates_lib

response.logo2 = IMG(_src=URL('static','images/7P-30.png'), _width=200)

# берем только рубль
##curr_out, x, ecurr_out = db_common.get_currs_by_abbrev(db,"RUB") #ecurr_out = db.ecurrs[ecurr_out_id]
curr_out = db.currs[CURR_RUB_ID]
ecurr_out = db(db.ecurrs.curr_id == curr_out.id).select().first()
ecurr_out_id = ecurr_out.id

if TO_PHONE7_ID:
    deal = db.deals[ TO_PHONE7_ID ]
    deal_name = deal.name
else:
    deal_name = 'phone +7' # 'to phone +7 RUBs'
    # найдем дело
    deal = db(db.deals.name==deal_name).select().first()

if not deal: raise HTTP(200, T('ERROR: Not found deal "%s"') % deal_name)
# найдем счет у диллера электронных денег для этого дела
vol = (deal.MIN_pay or 100) * 2
dealer, dealer_acc, dealer_deal = ed_common.select_ed_acc(db, deal, ecurr_out, vol)
print dealer,'\n', dealer_acc,'\n', dealer_deal
dealer_acc = ed_common.sel_acc_max_for_balance(db, dealer, ecurr_out, vol, unlim=False)

if False and not dealer: raise HTTP(200, 
      #T('ERROR: Not found dealer for "%s". Please try in next month') % deal_name
      'Просьба подождать до следующего дня или месяца - превышен лимит по данному виду операций'
      )
if False and not dealer_acc: raise HTTP(200,
      #T('ERROR: Not found dealer acc "%s"') % deal_name
      'Просьба подождать до следующего дня или месяца - превышен лимит по данному виду операций'
      )


#from decimal import *
#getcontext().prec = 6

MIN = db_common.gMIN(deal, dealer)
e_balance = dealer_acc and db_common.get_balance_dealer_acc( dealer_acc )
MAX = int(deal.MAX_pay)
if e_balance:
    dealer_acc.balance = e_balance
    dealer_acc.update_record()
    e_balance = e_balance * 1
    if e_balance < MAX*2:
         MAX = int(e_balance/3)
free_bal = e_balance

def test_vol(vol, _min=MIN, _max=MAX):
    try:
        vol = float(vol)
    except:
        return None
    if _max and vol > _max: return _max
    if _min and vol < _min: return _min
    return vol

# переходник для показа ссылкок и картинок в листингах
def download():
    return response.download(request,db)

# заменить все не цифры и проверить длинну
regular_phone = re.compile("\D")
def valid_phone(ph):
    str = regular_phone.sub("","%s" % ph)
    if len(str) == 11 or len(str) == 10: return str
    return

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

def get():

    # CHECK ARGS AND VARS
    args = request.args
    if len(args) != 1: return mess('err...')
    curr_id = args(0)
    if not curr_id.isdigit(): return mess('dig...')
    # теперь можно задать открытие кнопки
    scr = "$('#cvr%s').css('display','none');$('#tag%s').show('slow');" % (curr_id, curr_id)
    response.js = scr

    vol = request.vars['vol']
    if not vol or len(vol) > 20: return mess(T('ОШИБКА') + ': ' + T('Задайте количество'))
    try:
        vol = float(vol)
        curr_id = int(curr_id)
    except:
        return mess('digs...')

    if vol < MIN:
        try:
            session.vol = MIN
        except:
            print 'to_phone session error .vol:', type(MIN), MIN

        return mess( T('ОШИБКА: Слишком маленькая сумма платежа %s < %s') % (vol, MIN))

    kod = request.vars.kod or '7'
    ph = request.vars.phone
    #print request.vars
    if not ph:
        return mess(T('ОШИБКА: Задайте номер телефона'))
    ph = valid_phone(kod+ph)
    if not ph:
        return mess(T('ОШИБКА: Проверьте номер телефона, он должен содержать 10 цифр с досупными разделитялями: пробел, скобки, тире.'))

    curr_in = db.currs[ curr_id ]
    if not curr_in: return mess(T('curr...'))
    xcurr_in = db(db.xcurrs.curr_id == curr_id).select().first()
    if not xcurr_in: return mess(T('xcurr...'))

    # ALL CHECKED GOOD - store vars
    try:
        ph_sess = ph
        if len(ph) == 10:
            # для наших добавим 7-ку
            ph_sess = '7' + ph_sess
        session.toPhone = ph_sess
        session.vol = vol
    except:
        print 'to_phone session error .toPhone:', type(ph), ph
        print 'to_phone session error .vol:', type(vol), vol

    ##print 'ph, session.phone:', ph, session.toPhone

    # теперь проверку на правильность телефона для дилера электронных платежей
    # dealer и dealer_acc - выбирается в начале файла
    # pay_test(deal, dealer, dealer_acc, dealer_deal, acc, volume_out)
    res = dealer_acc and ed_common.pay_test(db, deal, dealer, dealer_acc, dealer_deal, ph, vol, False)
    ##print 'PAY:',res
    if True:
        pass
    elif not res:
        return mess('dealer error - Возможно достигнуто ограничение переводов на сотовые телефоны и электронные кошельки, просьба воспользоваться прямой оплатой нужных Вам услуг, например из меню "Всё"')
    elif res['status']!='success':
        mm = 'error_description' in res and res['error_description'] or res['error'] or 'dealer error'
        return mess(T('Платежная система %s отвергла платеж, потому что: %s (... %s)') % (dealer.name, mm, dealer_acc.acc[-4:]))

    gift_cod = request.vars.gift_cod
    curr_out_abbrev = curr_out.abbrev
    x_acc_label = db_client.make_x_acc(deal, ph, curr_out_abbrev)
    # найдем ранее созданный адресс для этого телефона, этой крипты и этого фиата
    # сначала найтем аккаунт у дела
    deal_acc_id = db_client.get_deal_acc_id(db, deal, ph, curr_out)
    # теперь найдем кошелек для данной крипты
    deal_acc_addr = db_client.get_deal_acc_addr_for_xcurr(db, deal_acc_id, curr_in, xcurr_in, x_acc_label)
    #deal_acc_addr = '123qwewfddgdfgfg'
    if not deal_acc_addr:
        return mess(T('Связь с кошельком ') + curr_in.name + T(' прервана.') + ' ' + T('Пожалуйста попробуйте позже'), 'warning')

    #request.vars['deal_acc_addr']=deal_acc_addr
    addr = deal_acc_addr.addr

    curr_in_abbrev = curr_in.abbrev
    
    h = CAT()
    addr_return = deal_acc_addr.addr_return
    if addr_return:
        addr_ret = DIV(
            DIV(
                T('Адрес для возвратов'),': ',
                B(addr_return[:5] + '...' + addr_return[-5:]),
                _class='col-sm-12'),
            _class='row success',
            )
    else:
        addr_ret= LOAD('aj', 'addr_ret',
           #args=[deal_acc_addr.addr_return or 0, deal_acc_addr.id, ],
           # лучше передавать через переменные - чтобы там по кругу они гонялись
           # в request
           args=[deal_acc_addr.id],
           ajax=False, # тут без асинхронной подгрузки модуля - вместе со страницей сразу грузим модуль
           )

    okIN = session.okPh
    h += sect(
        DIV(
            addr_ret,
            okIN and DIV(SPAN(A('Правила оплаты', _onclick='$(".okIN").show("fast");', _class='button warn right'),
                          _class='pull-right-'), _class='col-sm-12') or '',
            DIV(okIN and ' ' or H3('ПРАВИЛА ОПЛАТЫ', _class='center'),
               P(T('При оплате необходимо соблюдать следующие правила:')),
               UL(
                    T('У оплат дела [%s] существуют ограничения по суммам, поэтому если Вы хотите оплатить бОльшую сумму, то Вам нужно делать платежи небольшими суммами в эквиваленте до %s рублей на тот же адрес кошелька, который Вы получили от нашей службы для этой услуги') % (deal.name, MAX),
                    T('Желательно задать обратный адрес для возврата монет на случай если наша служба по каким-либо причинам не сможет совершить оплату по делу [%s]') % deal.name,
                    T('Если Вы не задали обратный адрес для возврата монет, то необходимо платить биткоины и другую криптовалюту только со своего кошелька, задав адреса входов, которыми Вы действительно обладаете, а не с кошельков бирж, пулов или разных онлайн-кошельков. Так как монеты, в случае если платеж будет отвергнут нашим партнёром, могут автоматически вернуться только на адрес отправителя.'),
                    T('Если Вы оплатите другую сумму, то курс обмена может немножко измениться'),
                    T('Если Вы платите регулярно, то можете платить на тот же адрес кошелька криптовалюты, что получили ранее. Хотя желательно заходить на нашу службу для получения новостей хотябы раз в пол года или подписаться на важные новости и сообщения оставив свой емайл.'),
                    ),
                H4(A('Понятно', _onclick='$(".okIN").hide("fast");ajax("%s")'
                  % URL('aj','ok_to',args=['Ph']), _class='button warn'), _class='center'),
                _class='col-sm-12 okIN',
                _style='display:%s;' % (okIN and 'none' or 'block')),
            _style='color:chocolate',
            _class='row'),
        'bg-warning pb-10')


    # если есть скрытый партнерский код то его забьем пользователю
    deal_acc = db.deal_accs[deal_acc_id]
    #print gift_cod, deal_acc
    if gift_cod:
        if not deal_acc.gift and not deal_acc.partner:
            #print 'added', gift_cod
            deal_acc.update_record(gift = gift_cod)
            h += P('Подарочный код', ': ', gift_cod)

    import gifts_lib
    adds_mess = XML(gifts_lib.adds_mess(deal_acc, PARTNER_MIN, T))
    if adds_mess:
        h += sect(XML(adds_mess), 'gift-bgc pb-10 pb-10')
    
    volume_out = vol
    hh = CAT(H2(T('3. Оплатите по данным реквизитам'), _class='center'))

    ###if volume_out > MAX: volume_out = MAX
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
        volume_in, _mess_in = db_client.calc_fees_back(db, deal, dealer_deal, curr_in, curr_out, volume_out,
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
            T('на заморозку курса'), ' ', rate_out,
            #T('обратный курс'), ' ', round(1.0/rate_out,8),
            H5(T('*Данный курс будет заморожен для Вас на 20 минут для объёма криптовалюты не больше указанного. Проверить можно по номеру заказа в списке платежей.')),
            _class='row')
    else:
        volume_in = rate_out = None
        tax_rep = ''
        hh += mess('[' + curr_in.name + '] -> [' + curr_out.name + ']' + T(' - лучшая цена не доступна.') + T('Но Вы можете оплатить вперед'), 'warning')

    _, url_uri   = common.uri_make( curr_in.name2, addr, {'amount':volume_in, 'label': db_client.make_x_acc_label(deal, ph, curr_out_abbrev)})

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

    hh += DIV(
        P(
        T('Оплата телефона'),': ', #kod, ' ',
        ph, ' ', T('на сумму'), ' ', volume_out, ' ', curr_out_abbrev,
        ' ', T('из доступных в службе'), ' ', free_bal
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
            ),
        BR(),
        DIV(
            A(T('Показать QR-код'),  _class='btn btn-info',
               #_onclick="jQuery(this).parent().html('%s')" % IMG(_src=URL('static','images/loading.gif'), _width=64),
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
            INPUT(_name='v', value=volume_in, _class="pay_val", _readonly=''), curr_in_abbrev, BR(),
            T("Для этого скопируйте сумму и адрес (двойной клик по полю для выделения) и вставьте их в платеж на вашем кошельке"), ': ',
            INPUT(_name='addr', _value=addr, _class='wallet', _readonly=''), BR(),
            T('Резервы службы'), ' ', B(free_bal), ' ', T('рублей'), BR(),
            ##LOAD('where', 'for_addr', vars={'addr': addr}, ajax=True, times=100, timeout=20000,
            ##    content=IMG(_src=URL('static','images/loading.gif'), _width=48)),
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
def index():

    #common.page_stats(db, response['view'])

    response.title = T("Пополнить биткоинами телефон")
    response.subtitle = T('Оплатить телефон биткоинами')

    if False and session.date_log:
        d_diff = datetime.datetime.today() - session.date_log
        if d_diff.seconds > 1200:
            session.date_log = None
            session.toPhone = None

    #print request.vars
    if request.vars:
        #print 'reset'
        vol = test_vol(request.vars.sum)
        session.vol = vol if vol else None
        phone = request.vars.phone
        phone = phone and valid_phone(phone)
        print phone
        if phone: session.toPhone = phone
    else:
        phone = session.toPhone

    ##print 'phone, session.phone:', phone, session.toPhone
    if phone and len(phone) == 10:
        phone = session.toPhone = '7' + phone
    title = phone and CAT(T('Ваш телефон') + ':' + phone[:3] + '***' + phone[-3:] + ' ', SPAN(response.title, _class='small')) or response.title
    subtitle = session.date_log and (T('Дата посещения %s') % session.date_log) or response.subtitle

    try:
        session.date_log = request.now
    except:
        print 'to_phone session error .date_log:', type(request.now), request.now

    h = CAT()
    hh = CAT(H1(response.title), response.subtitle and H3(response.subtitle) or '')
    h += DIV(hh, _class='container')

    phone_deal7 = phone
    if phone and len(phone) == 11 and phone[0] == '7':
        phone_deal7 = phone[1:]
        
    h = CAT()
    for rr in db_client.get_xcurrs_for_deal(db, 0, curr_out, deal, dealer):
        #print row
        id = '%s' % rr['id']
        disabled = rr['expired']
        #bgc = 'gold'
        if disabled:
            memo = CAT(T('Курс не найден'),', ', T('Когда курс будет получен платеж пройдёт автоматически'), '. ', T('Или попробуйте зайти позже'))
            _class = 'col sel_xcurrNRT'
        else:
            memo = CAT(SPAN(' ', T('по курсу'),  (' %8g' % rr['price']), ' ', T('нужно оплатить примерно')),' ',
                    B(SPAN(_class='pay_vol')), ' ', rr['name'])
            _class = 'col sel_xcurrRTE'

        # пусть клики все равно будут
        onclick='''
                      //$(this).css('z-index','0');
                      $('#tag%s').hide('fast');
                      $('#cvr%s').css('display','block'); // .css('z-index','10');
                      ajax('%s',['vol', 'phone', 'gift_cod'], 'tag%s');
                      ''' % (id, id, URL('get', args=[id]), id)
        #print row
        h += DIV(
            DIV(
                DIV(
                    #T('Есть'), ': ', rr['bal_out'],' ',
                    IMG(_src=URL('static','images/currs/' + rr['abbrev'] + '.png'),
                      _width=60, __height=36, _class='lst_icon', _id='lst_icon' + id),
                    SPAN(rr['price'], _class='price hidden'),
                    SPAN(rr['abbrev'], _class='abbrev hidden'),
                    memo,
                    '. ', SPAN(T('Всего было оплат:'), rr['used'], _class='small'),
                    _onclick=onclick if onclick else '',
                    #_style=style,
                    _id='btn%s' % id,
                    _class=_class,
                ),
              DIV(TAG.i(_class='fa fa-spin fa-spinner right wait1'),
                  _id='cvr%s' % id, _class='col sel_xcurrCVR'),
              _class='row sel_xcurr'),
            _class='container')
        h += DIV(_id='tag%s' % id, _class='blue-c')
    xcurrs_h = h

    import recl
    _, reclams = recl.get(db,2)

    '''
    response.top_line = DIV(
        TAG.center(tl),
        _id="top_line")
    '''
    response.top_line = None

    return dict(title=title, subtitle=subtitle, MIN=MIN, MAX=MAX, phone_deal7=phone_deal7,
                free_bal = free_bal, xcurrs_h=xcurrs_h, reclams=reclams)
