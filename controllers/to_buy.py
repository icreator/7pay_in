# coding: utf8

if False:
    from gluon import *
    import db
    request = current.request
    response = current.response
    session = current.session
    cache = current.cache
    T = current.T

import datetime

try:
    import common
except Exception as e:
    raise HTTP(200, T('ERROR: copy ALL files from _web2py_site-packages to web2py/site-packages') + ('. %s' % e))

import db_common
import db_client
import rates_lib
import crypto_client
import ed_common
import recl
import serv_to_buy

response.title=T("Купить биткоины, криптовалюту")

def log(mess):
    print mess
    db.logs.insert(mess='BUY: %s' % mess)
def log_commit(mess):
    log(mess)
    db.commit()
    
# берем только рубль
curr_in, x, ecurr = db_common.get_currs_by_abbrev(db,"RUB")

deal_name = 'BUY'
# найдем дело
deal = db(db.deals.name==deal_name).select().first()
if not deal: raise HTTP(200, T('ERROR: not found deal "%s"') % deal_name)
MAX = deal.MAX_pay

# переходник для показа ссылкок и картинок в листингах
def download():
    session.forget(response)
    return response.download(request,db)

def u(h, url, cls='col-sm-4'):
    return DIV(DIV(P(h, _class='btn_mc2'), _class='btn_mc1', _onclick="location.href='%s'" % url), _class='btn_mc ' + cls)

# готовый сектор - только ДИВ в него вставим
def sect(h, cls_bgc='', style=''):
    return DIV(DIV(h, _class='container pb-10'),  _class=cls_bgc, _style=style)
## обрамим ее в контайнер
def mess(h, cls_c='error'):
    return DIV(DIV(DIV(h, SCRIPT("$('#tag1').scroll();"), _class='col-sm-12 ' + cls_c), _class='row'),
                   _class='container')

def err_dict(m):
    response.view = 'views/generic.html'
    return dict(h = mess(m + ', ' + 'просьба сообщить об ошибке в службу поддержки!'))

############## BANK ###############

def bank_check():
    import time
    addr = request.vars.get('addr')
    ref = request.vars.get('ref')
    amo = request.vars.get('amo')
    if not addr: return mess('Адрес кошелька пуст') # Wallet address is empty
    if not ref: return mess('Номер платежа пуст') # Reference address is empty
    if not amo: return mess('Сумма не задана') # Amount is empty
    if not amo.replace('.','').isdigit(): return mess('Amount Error')
    
    time.sleep(2)
    rec = db((db.buys_stack.ref_ == db.buys.id)
             & (db.buys.amount == amo)
             & (db.buys.buyer.startswith(ref + ' '))).select().first()
    # если вводился не номер платежа а номер платежа [op_id]
    rec = rec or db((db.buys_stack.ref_ == db.buys.id)
             & (db.buys.amount == amo)
             & (db.buys.operation_id == ref)).select().first()
    if not rec:
        return mess('Платеж не найден') # Records not founded
    if rec.buys.addr:
        return mess('Адрес уже задан') # This payment already assigned!!!

    from db_common import get_currs_by_addr
    curr, xcurr, _ = get_currs_by_addr(db, addr)
    if not xcurr:
        return mess("Неверный адрес") # Invalid wallet address
    conn = crypto_client.conn(curr, xcurr)
    if not conn:
        return mess("Нет связи с [%s]" % curr.abbrev) # Not connected to wallet [%s]
    valid = conn.validateaddress(addr)
    if not valid.get('isvalid'):
        return mess("Неверный адрес для [%s]" % curr.abbrev) # Invalid wallet address for [%s]
    
    rec.buys.update_record( xcurr_id = xcurr.id, addr = addr)
    return mess('Задан для %s' % curr.name, 'info-bg')

def bank():
    response.title=T("Купить биткоины, криптовалюту за безналичные по платежу из любого банка, который может пополнить Яндекс.Кошелек (Альфа-банк, ...). Однако пока Сбербанк не дает эту возможность")
    response.big_logo2=True
    response.logo2 = IMG(_src=URL('static','images/7P-302.png'), _width=200)
    response.not_show_func = True
    
    h = CAT(
        T('После того, как Вы пополнили безналичным платежом из Вашего банка Яндекс.Кошелек, предоставленный для покупки биткоинов (лайткоинов и другой криптовалюты) нашим сервисом, введите реквизиты своего платежа для того чтобы присвоить ему адрес для выплаты криптовалюты'),'.',BR(),
        T('Так же Вы можете задать адрес кошелька для платежей, у которых его забыли указать'),'.',BR(),
        INPUT(_name='addr', _placeholder=T('Адрес кошелька...')),BR(), # Wallet address
        INPUT(_name='ref', _placeholder=T('Номер платежа')), # payment referrence
        INPUT(_name='amo', _placeholder=T('Сумма платежа')), #payment amount
        BUTTON(T('Check'), _onclick='ajax("bank_check", ["addr", "ref", "amo"], "res");\
               $("#res").html(\'<i class="fa fa-spinner fa-spin"></i>\');'),
        DIV(_id='res'),
        #u(T('Назад на покупку биткоинов и другой криптовалюты'),
        #    URL('TO_buy', 'index'),'col-sm-12'),
    )
    return dict(h = sect(h))

####################################################################

def get():

    args = request.args
    if len(args) != 1: return mess('err...')
    curr_id = args(0)
    ##scr = "$('#cvr%s').css('z-index',-1);$('#tag%s').show('slow');" % (curr_id, curr_id)
    scr = "$('#cvr%s').css('display','none');$('#tag%s').show('slow');" % (curr_id, curr_id)
    response.js = scr
    if not curr_id.isdigit(): return mess('dig...')
    vol = request.vars['vol']
    if not vol or len(vol) > 20: return mess(T('ОШИБКА') + ': ' + T('Задайте количество'))
    try:
        vol = float(vol)
        curr_id = int(curr_id)
    except:
        return mess('digs...')
    addr = request.vars['wallet']
    if not addr or len(addr) < 30 or len(addr)> 35:
        return mess(T('ОШИБКА') + ': ' + T('Введите адрес кошелька криптовалют'))

    curr_out = db.currs[ curr_id ]
    if not curr_out: return mess(T('curr...'))
    xcurr_out = db(db.xcurrs.curr_id == curr_id).select().first()
    if not xcurr_out: return mess(T('xcurr...'))
    curr_out_name = curr_out.name
    
    amo_in = vol
    _amo_out, rate_order, best_rate = rates_lib.get_rate(db, curr_in, curr_out, amo_in)
    
    try:
        dealer_id = request.vars['dealer']
        dealer = db.dealers[dealer_id]
    except:
        return mess('digs...')

    MIN = db_common.gMIN(deal, dealer)
    if vol < MIN:
        try:
            vol = MIN
            session.vol = vol
        except:
            print 'to_buy session error .vol:', type(addr), addr

        return mess( T('ОШИБКА: Слишком маленькая сумма платежа %s < %s') % (vol, MIN))


    dealer_acc = ed_common.sel_acc_min(db, dealer, ecurr, amo_in)
    if not dealer_acc:
        return mess((T('Электронные деньги [%s] не доступны сейчас.' % dealer.name)
             + ' ' + T('Попробуйте позже')), 'warning')


    if not best_rate:
        response.title=T("ОШИБКА")
        return mess(T('Курс не найден'), 'warning')

    try:
        session.buyAddr = addr
        session.buyVol = vol
    except:
        print 'list session error .buyAddr:', type(addr), vol
        print 'list session error .buyVol:', type(vol), vol

    #print best_rate
    if request.application[:-3] != '_dvlp':
        # чето конфликт если из ipay3_dvlp вызывать то кошелек на ipay3 не коннектится
        cc = crypto_client.conn(curr_out, xcurr_out)
        if cc:
            if crypto_client.is_not_valid_addr(cc, addr):
                #return mess(T('address not valid for ') + curr_out_name)
                return mess(T('ОШИБКА') + ': ' + T('Адрес кошелька не подходит для выбранной криптовалюты %s') % curr_out_name)
        else:
            # ЕСЛИ НЕТ СВЯЗИ - пусть пллатит - потом связь появится
            #return mess(T('Connection to [%s] is lost, try later ') % curr_out_name)
            ##return mess(T('Связь с кошельком ') + curr_out_name + T(' прервана.') + ' ' + T('Пожалуйста попробуйте позже'), 'warning')
            pass


    volume_in = vol
    is_order = True
    dealer_deal = db((db.dealer_deals.deal_id == deal.id)
                     & (db.dealer_deals.dealer_id == dealer_id)).select().first()
    ## теперь таксы для человека получим и должна та же цифра выйти
    vol_out, tax_rep = db_client.calc_fees(db, deal, dealer_deal, curr_in, curr_out, volume_in,
                                       best_rate, is_order, note=1)
    volume_out = common.rnd_8(vol_out)
    volume_in = common.rnd_8(volume_in)
    rate_end = volume_in / volume_out
    ##print 'buy:', volume_in, vol_out, rate_end

    h = CAT()

    okIN = session.okBu
    h += sect(DIV(
        okIN and DIV(H3(A('Правила оплаты', _onclick='$(".okIN").show("fast");', _class='button warn right'),
                      _class='pull-right-'), _class='col-sm-12') or '',
        DIV(okIN and ' ' or H3('ПРАВИЛА ОПЛАТЫ', _class='center'),
           P(T('При оплате необходимо соблюдать следующие правила:')),
           UL(
                T('Если Вы хотите оплатить большую сумму, то нужно делать платежи небольшими суммами по 2000-3000 рублей и получать разные счета - просто еще раз нажмите на кнопку выбора необходимой валюты'),
                T('Если Вы оплатите другую сумму, то курс обмена может немножко измениться'),
                T('Если Вы платите регулярно, то просьба каждый раз получать счет нажатием на кнопку выбора валюты - возможно счет будет выбран другой, а ранее полученный счет может быть перегружен и заморожен на сутки и более'),
                ),
            H4(A('Понятно', _onclick='$(".okIN").hide("fast");ajax("%s")'
              % URL('aj','ok_to',args=['Bu']), _class='button warn'), _class='center'),
            _class='col-sm-12 okIN',
            _style='color:chocolate;display:%s;' % (okIN and 'none' or 'block')),
            _class='row'),
        'bg-warning pb-10')

    # создадим номер заказа чтобы не показывать что мы на крипту принимаем платеж
    order = db((db.addr_orders.xcurr_id == xcurr_out.id)
               & (db.addr_orders.addr == addr)).select().first()
    if not order:
        order_id = db.addr_orders.insert( xcurr_id = xcurr_out.id, addr = addr )
    else:
        order_id = order.id

    amo_in = round(amo_in*1.005, 2) # добавим таксу яндекса 0.5%
    destination = '7pb%s' % order_id # + ' ' + T('или') +' ' + curr_out.abbrev + ' ' + addr
    free_bal = db_client.curr_free_bal(curr_out)
    h += sect(DIV(DIV(
        H2(T('3. Оплатите по данным реквизитам покупку %s') % curr_out_name, _class='center'),
        P(
        T('курс обмена: %s (обратный курс: %s)') % (round(rate_end,8), round(1/rate_end,8)),BR(),
        T('Вы получите'),' ', B(round(volume_out, 8)), IMG(_src=URL('static','images/currs/' + curr_out.abbrev + '.png'), _width=36), ' ',
        T('из доступных'),' ', free_bal,
        ),
        P(
        volume_out > free_bal and CAT(
                        H3(T('Сейчас средств на балансе меньше чем Вам надо'), _style='color:crimson;'),
                        SPAN(T('Поэтому Ваш заказ будет исполнен позже'), BR(),
                        T('когда на балансе службы появится достаточно средств'), _style='color:black;'), BR(),
                        ) or '',
        ),
        DIV(CENTER(
            A(SPAN(T('Оплатить'),' ', amo_in, ' ',
            IMG(_src=URL('static','images/currs/' + curr_in.abbrev + '.png'), _width=50)),
            _class='block button blue-bgc', _style='font-size:x-large; max-width:500px; margin:0px 7px;',
            _href='https://money.yandex.ru/direct-payment.xml?scid=767&receiver=%s&sum=%s&destination=%s&FormComment=buy %s on ' + DOMEN
                  % (dealer_acc.acc, amo_in, destination, curr_out.abbrev)),
                    ),
            _class='row'
            ),
        BR(),

        P(
            T('Или сделайте платеж вручную на %s кошелек %s') % (dealer.name, dealer_acc.acc), BR(),
            T('указав в назначении платежа код оплаты'),':', BR(),
            B(destination),
          ),
        tax_rep,
        FORM(
            INPUT(_name='addr', _value=addr, _type='hidden'),
            INPUT( _type='submit',
                _class='button blue-bgc',
                _value=T('Подробный просмотр платежей'),
                _size=6,
                  ),
            _action=URL('where', 'index'), _method='post'),
        _class='center', _style='color:blue;'),
        _class='row'), 'bg-info pb-10')

    h += sect(CAT(
        DIV(H3(T('Так же Вы можете пополнить этот %s кошелек') % dealer.name,':', _class='center'),
            _class='row'),
        DIV(
            DIV(
                IMG(_src=URL('static', 'images/m-cards.png'), _style='float:left;margin:10px;'),
                T('С любой банковской карточки, указав в сообщении получателю код оплаты (как показано выше)'),
               _class='col-lg-8 col-lg-offset-2 col-sm-12', _style='black;padding: 5px;'),
        _class='row'),
        DIV(
            DIV(
               IMG(_src=URL('static', 'images/m-banks.png'), _style='float:left;margin:10px;'),
               T('Из любого банка, например Альфа-Банк (пока Сбербанк не даёт такие данные)'),'. ',
               T('После чего'), ' ',
               A(B(T('ПОДТВЕРДИТЬ')),
                    _href=URL('to_buy', 'bank')), ' ',
               T('покупку биткоинов по банковским реквизитам платежа (сумме и референсу платёжки)'),
           _class='col-lg-8 col-lg-offset-2 col-sm-12', _style='black;padding: 5px;'),
        _class='row'),
        ),
        #_style='background-color:#FFF47D;color:black;'
        'gold-bgc pb-10'
        )
    h += SCRIPT('''
        $('html, body').animate( { scrollTop: $('#cvr%s').offset().top - $('#aside1').height() }, 500 );
      ''' % (curr_id))

    return h
######################################################

def index():

    #raise HTTP(200, T('на переработке'))
    #common.page_stats(db, response['view'])

    response.title=T("Купить биткоины криптовалюту за электронные деньги")
    response.subtitle=T("Быстро, надежно и удобно")

    if False and session.date_log:
        d_diff = datetime.datetime.today() - session.date_log
        if d_diff.seconds > 1200:
            session.date_log = None
            session.addr_buy = None

    addr = session.buyAddr
    title = addr and T('Ваш кошелек') + ':' + addr[:3] + '****' + addr[-3:] or response.title or ''
    subtitle = addr and T('Дата посещения %s') % session.date_log or response.subtitle or ''

    try:
        session.date_log = request.now
    except:
        print 'to_buy session error .date_log:', type(request.now), request.now
    
    # берем только тех кто за рубли и для этого дела
    # причем по 1 аккаунту на диллера тут нужно - для писка
    # какой диллер вообще на кошельки принимает
    ecurr_in_id = ecurr.id
    #print ecurr_in_id
    inp_dealers = []
    for r in db(
            (db.dealers.id == db.dealers_accs.dealer_id)
            & (db.dealers_accs.ecurr_id==ecurr_in_id)
            & (db.dealers_accs.used == True)
            & (db.dealers.used == True)
    ).select(db.dealers.ALL, groupby=db.dealers.id):
        MIN = db_common.gMIN(deal, r.dealers)
        ##MAX = db_common.gMAX(deal, r.dealers)
        inp_dealers.append([r.dealers.id, '%s [%s] %s...%s' % (r.dealers.name, curr_in.abbrev, MIN, MAX)])

    #print dd
    if len(inp_dealers)==0:
        # ошибка какаято что нет диллера
        return err_dict(T('Не найден диллер для выплаты, просьба сообщить об ошибке в службу поддержки!'))
    
    xcurrs = db_client.get_xcurrs_for_buy(db, curr_in, deal)
    h = CAT()
    for rr in xcurrs:
        #print rr
        id = '%s' % rr['id']
        disabled = rr['expired']
        if disabled:
            memo = CAT(T('Курс не найден'),', ', T('Когда курс будет получен платеж пройдёт автоматически'), '. ', T('Или попробуйте зайти позже'))
            _class = 'col sel_xcurrNRT'
        else:
            memo = CAT(' ', T('по курсу'),  B(' %8g' % rr['price']), ', ',#' =', rr['price'] * rr['bal_out'],
                    T('это около'),' ', int(rr['price'] * float(rr['bal_out'])),
                    #curr_in.abbrev,
                    TAG.i(_class='fa fa-rub blue-c'),
                    ', ',
                    ' а Вы хотите купить около ', B(SPAN(_class='pay_vol')), ' ', rr['name'])
            _class = 'col sel_xcurrRTE'

        # пусть клики все равно будут
        onclick='''
                      //$(this).css('z-index','0');
                      $('#tag%s').hide('fast');
                      $('#cvr%s').css('display','block'); // .css('z-index','10');
                      ajax('%s',['vol', 'wallet','dealer'], 'tag%s');
                      ''' % (id, id, URL('get', args=[id]), id)
        #print r
        h += DIV(
            DIV(
                DIV(
                    IMG(_src=URL('static','images/currs/' + rr['abbrev'] + '.png'),
                       _width=60, __height=36, _class='lst_icon', _id='lst_icon' + id),
                    ' ', T('есть'), ' ', B(rr['bal_out']),' ',
                    SPAN(rr['price'], _class='price hidden'),
                    SPAN(rr['abbrev'], _class='abbrev hidden'),
                    memo,
                    #' ', SPAN(T('Всего покупок:'), rr['used']),
                    #if rr['expired'] else ''
                    _onclick=onclick if onclick else '',
                    #_style=style,
                    _id='btn%s' % id,
                    _class=_class,
                    ),
                DIV(TAG.i(_class='fa fa-spin fa-spinner right wait1'),
                    _id='cvr%s' % id,
                    _class='col sel_xcurrCVR',
                    ),
                _class='row sel_xcurr',
            ),
            _class='container')
        h += DIV(_id='tag%s' % id, _class='blue-c')
    xcurrs_h = h

    _, reclams = recl.get(db,2)
    #response.top_line = None

    return dict(title=title, subtitle=subtitle, inp_dealers=inp_dealers, MIN=MIN, MAX=MAX, xcurrs_h=xcurrs_h, reclams=reclams)
