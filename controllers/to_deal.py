# coding: utf8

### !!!! {"img_url":"https://money.yandex.ru/i/shop/", "shops_url":"https://money.yandex.ru/phone.xml?"}
### в описании дилера нужно в INFO

import json
import re
import datetime

import common

import db_client
import ed_common
import rates_lib
import ed_YD # надо для сборки аккаунта платежа

import db_common
# берем только рубль
curr_out, x, ecurr_out = db_common.get_currs_by_abbrev(db,"RUB")#ecurr_out = db.ecurrs[ecurr_out_id]
ecurr_out_id = ecurr_out.id

exp_time = request.is_local and 3 or 360

def test_vol(vol, _min=None, _max=None):
    try:
        vol = float(vol)
    except:
        return None
    if _max and vol > _max: return _max
    if _min and vol < _min: return _min
    return vol

def u(h, url, cls='col-sm-4'):
    return DIV(DIV(P(h, _class='btn_mc2'), _class='btn_mc1', _onclick="location.href='%s'" % url), _class='btn_mc ' + cls)

def download():
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


#?scid=4556&from=isrch
scid_ = re.compile("[?&](\w+)=(\w+)")

def get_e_bal(deal, dealer, dealer_acc):
    e_balance = db_common.get_balance_dealer_acc( dealer_acc )
    MAX = deal.MAX_pay or 2777
    if e_balance:
        #dealer_acc.balance = e_balance
        #dealer_acc.update_record()
        if e_balance < MAX*2:
             MAX = round(e_balance/3,0)
    return e_balance, MAX * Decimal(0.8)


def make_img(r, dealer_info, shop_url=None):
    img = None
    _style = 'width: 3em;'
    if r.icon: img = IMG(_src=URL('default','download', args=['db', r.icon]),
                     _style=_style,
                     _alt=r.name)
    elif r.img:
        # это работает только если картинка загружена в экмлорер
        # когда открываешь сайт Яндекс-деньги
        img = XML(u'<img src="%s" style="%s" alt="%s">' %
                  (dealer_info['img_url'] + r.img,
                   _style,
                   #r.name, # - тут не хочет перекодировать символы имени
                   ''
                   ) )
        #img = IMG(_src=URL('more','download', args=[dealer_info['img_url'] + r.img] ))
        #img = IMG(_src="http://flylark.net/public/images/flylark_emblem.png")

    return img and A(img or r.name, _href=shop_url or URL('to_deal', 'index', args=[r.id]), _target=shop_url and '_blank') or ''

# заменить все не цифры и проверить длинну
regular_digs = re.compile("\D")
def valid_digs(acc,l):
    str = regular_digs.sub("","%s" % acc)
    if len(str) == l: return str
    return
def validate(v):
    acc = valid_digs(v['acc'],acc_len)
    if acc:
        f.vars.acc = acc
    else:
        f.errors.acc = T('Лицевой счёт должен содержать %s цифр!') % acc_len
    #if len(f.vars.codPP) != 2:
    #    f.errors.codPP = T('Длина "код РР" должна быть равна %s') % 2

#################################################

def get():

    #common.page_stats(db, response['view'])
    #print request.vars
    args = request.args
    if len(args) < 2: return mess('args<2 err...')
    curr_id = args(0)
    if len(curr_id)>5 or not curr_id.isdigit(): return mess('curr_id dig...')
    # теперь можно задать открытие кнопки
    scr = "$('#cvr%s').css('display','none');$('#tag%s').show('slow');" % (curr_id, curr_id)
    response.js = scr


    deal_id = args(1)

    if not deal_id or len(deal_id)>10 or not deal_id.isdigit():
        return mess('deal_id vars..')

    curr_in = db.currs[ curr_id ]
    if not curr_in: return mess(T('curr...'))
    xcurr_in = db(db.xcurrs.curr_id == curr_id).select().first()
    if not xcurr_in: return mess(T('xcurr...'))

    #print request.vars
    try:
        # если русский язык то выдаст ошибку в if v.find(c) >-1:
        for k, v in request.vars.items():
            #print k, v
            for c in u'\\/<>\'"':
                if v.find(c) >-1:
                    return mess('error in pars <script>')
    except:
        pass

    client = db(db.clients.deal_id == deal_id).select().first()
    if client:
        redirect(URL('to_shop','index',args=[client.id], vars={}))

    volume_out = test_vol(request.vars.vol)
    if not volume_out: return mess('volume_out error...')

    deal = db.deals[deal_id]
    vol = (deal.MIN_pay or 100) * 2
    dealer, dealer_acc, dealer_deal = ed_common.select_ed_acc(db, deal, ecurr_out, vol, True)
    if not dealer:
        return mess('ERROR: not found dealer for "%s"' % deal.name)
    dealer_acc = ed_common.sel_acc_max_for_balance(db, dealer, ecurr_out, vol, unlim=True)

    MIN = db_common.gMIN(deal, dealer)
    #MAX = deal.MAX_ or 777

    if MIN > volume_out:
        return mess('ОШИБКА: Слишком маленькая сумма платежа, меньше чем: %s' % MIN)

    ################################################
    # соберем аккаунт для оплаты из введенных данных
    ################################################
    if dealer_deal.grab_form:
        deal_pars = {}
        #print request.post_vars
        # удалим наши параметры
        for key in ['xcurr', 'volume', 'deal_id']:
            deal_pars[key] = request.post_vars.pop(key)
        # парамтеры что ввел пользователь обрежем чтобы скрипты не писали
        for (k,v) in request.post_vars.iteritems():
            if len(v) > 20:
                request.post_vars[k] = v[:20]
        acc = request.post_vars #.list.sort()
        if len(acc)>10:
            m = 'ОШИБКА: параметров слишком много: %s, свяжитесь с администратором' % acc
            print m
            return mess(m)
        acc = json.dumps( acc )
        #print 'ACC:', acc
    else:
        # проверку параметров
        # и собрем из параметров счет клиента
        acc_pars = []
        if dealer_deal.p2p:
            if deal.template_ == '--':
                pay_pars_deal=[]
                pay_pars_dealer=[]
                acc_pars.append('main')
            else:
                pay_pars_deal = ed_common.PAY_PARS_P2P
                pay_pars_dealer = ed_YD.PAY_PARS_P2P
        else:
            pay_pars_deal = deal.template_ and json.loads(deal.template_) or ed_common.PAY_PARS
            pay_pars_dealer = dealer_deal.template_ and json.loads(dealer_deal.template_) or ed_YD.PAY_PARS
        #print request.vars
        for par in pay_pars_deal:
            ## par - параметры от ДЕЛА
            if 'calc' in par:
                continue
            p_n_name = par.get('n')
            if not p_n_name:continue

            val = request.vars[p_n_name] or ''
            p = pay_pars_dealer[p_n_name]
            #print p, val

            if 'f' in par:
                # фильтр регулярный
                #regular = re.compile(p['f'])
                #val = regular.sub("","%s" % val)
                val = re.sub(p['f'], "","%s" % val)
            if 'ln' in p:
                # проверка длинны
                ln = (p['ln'] + 0)
                if len(val) != ln:
                    l = p['l']
                    db.deal_errs.insert( deal_id= deal.id, err = 'len!=%s - %s = %s' % (ln, l, val) )
                    l = l.encode('utf8')
                    return mess('ОШИБКА: Проверьте введенные данные!')
            acc_pars.append(val)

        #все прошло

        # теперь проверку на правильность лицевого счета и прочего для дилера электронных платежей
        #dealer_acc
        #print pars
        if len(acc_pars)>10:
            m = 'ОШИБКА: параметров слишком много: %s, свяжитесь с администратором' % acc_pars
            print m
            return mess(m)
        acc =' '.join(acc_pars).rstrip() # и удалим пробелы справа от калькуляторов
        #print 'ACCOUNT:',acc

    if not acc or len(acc)<3:
        return mess('ОШИБКА: Аккаунт слишком короткий: %s' % acc)

    # запомним что это дело кто-то захотел оплатить
    dealer_deal.update_record( wanted = dealer_deal.wanted + 1 )

    pattern_id = dealer_deal.scid
    res = ed_common.pay_test(db, deal, dealer, dealer_acc,
         dealer_deal, acc,
         #(deal.MIN_pay or dealer.pay_out_MIN or 10)*2,
         volume_out,
         False )

    err_mess = '%s' % res
    if res['status']!='success':
        ed_common.dealer_deal_errs_add(db, dealer_deal, acc, err_mess)

        response.title=T("ОШИБКА")
        #print res
        mm = 'error_description' in res and res['error_description'] or res['error'] or 'dealer error'
        mm = T('Платежная система %s отвергла платеж, потому что: %s') % (dealer.name, mm)
        return mess(mm)

    dealer_info = json.loads(dealer.info)
    if deal.url and len(deal.url)>0:
        shops_url = deal.url
    else:
        shops_url = dealer_info['shops_url'] + "%s" % dealer_deal.scid
    deal_img = make_img(deal, dealer_info, shops_url)


    # get new or old adress for payment
    x_acc_label = db_client.make_x_acc(deal, acc, curr_out.abbrev)
    #print x_acc_label
    # найдем ранее созданный адресс для этого телефона, этой крипты и этого фиата
    # сначала найтем аккаунт у дела
    deal_acc_id = db_client.get_deal_acc_id(db, deal, acc, curr_out)
    #print 'deal_acc_id',deal_acc_id
    #return
    # теперь найдем кошелек для данной крипты
    #print x_acc_label
    deal_acc_addr = db_client.get_deal_acc_addr_for_xcurr(db, deal_acc_id, curr_in, xcurr_in, x_acc_label)
    if not deal_acc_addr:
        return mess( T(' связь с кошельком ') + curr_in.name + T(' прервана.'))

    addr = deal_acc_addr.addr

    deal_name = deal.name
    # если есть скрытый партнерский код то его забьем пользователю
    deal_acc = db.deal_accs[deal_acc_id]
    import gifts_lib
    adds_mess = XML(gifts_lib.adds_mess(deal_acc, PARTNER_MIN, T))

    deal_url = A(deal.name, _href=shops_url, _target="_blank")
    e_bal, MAX = get_e_bal(deal, dealer, dealer_acc)

    if MAX and volume_out > MAX: volume_out = MAX
    # используем быстрый поиск курса по формуле со степенью на количество входа
    # только надо найти кол-во входа от выхода
    pr_b, pr_s, pr_avg = rates_lib.get_average_rate_bsa(db, curr_in.id, curr_out.id, None)
    if pr_avg:
        vol_in = volume_out / pr_b
        amo_out, _, best_rate = rates_lib.get_rate(db, curr_in, curr_out, vol_in)
    else:
        best_rate = None
    if not best_rate:
        return mess('[' + curr_in.name + '] -> [' + curr_out.name + ']' + T(' - лучшая цена не доступна.'))

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

    # теперь для заказ на курс уберем комиссию диллера - просто пересчитаем вход с наченкой диллера
    fee_curr = db.currs[ deal.fee_curr_id ]
    fee_rate = Decimal(rates_lib.get_avr_rate_or_null(db, fee_curr.id, curr_out.id))
    vol_out_dd_neg, _ = db_client.dealer_deal_tax_neg(db, T, fee_rate, dealer_deal, '', Decimal(volume_out), '')
    #print vol_out_dd_neg

    # причем тут учитываем уже накрутку диллера за дело - в заказе курс будет с учетом накрутки автоматом
    volume_in = common.rnd_8(volume_in)
    rate_out = volume_out / volume_in

    # new make order
    order_rate_id = db.orders.insert(
        ref_ = deal_acc_addr.id,
        volume_in = volume_in,
        volume_out = vol_out_dd_neg,
        )
    # теперь стек добавим, который будем удалять потом
    db.orders_stack.insert( ref_ = order_rate_id )

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

    _uri, uri_url = common.uri_make( curr_in.name2, addr, {'amount':volume_in, 'label': db_client.make_x_acc_label(deal, acc, curr_out.abbrev)})

    qr = DIV(DIV(DIV(P(T('Показать QR-код'), _class='btn_mc2'), _class='btn_mc1'),
        _onclick='''
            jQuery(this).html('%s');
            ajax("%s", [], 'tag_qr');
        ''' % ( IMG(_src=URL('static','images/loading.gif'), _width=64), URL('plugins','qr', vars={'mess': uri_url})),
        _id = 'tag_qr',
        _class='btn_mc col-sm-6'),
        _class='row')

    curr_in_abbrev = curr_in.abbrev
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

    return dict(deal_name = deal_name, adds_mess = adds_mess, MIN = MIN, MAX = MAX, acc = acc,
                order_rate_id = order_rate_id, rate_out = rate_out, curr_in_name = curr_in_abbrev,
                curr_out_name = curr_out.abbrev, e_bal = e_bal,
                deal_url=deal_url, volume_in=volume_in, volume_out=volume_out,
                tax_rep=tax_rep, deal_img=deal_img,
                uri_url=uri_url, addr=addr, addr_ret=addr_ret, qr=qr, curr_id=curr_id,
               lim_bal_mess=lim_bal_mess)

################################################################
def index():
    #if not IS_LOCAL:
    #    redirect(URL('ipay','more','to_pay',args=request.args))

    #common.page_stats(db, response['view'])

    if len(request.args) == 0: redirect(URL('deal','index'))
    deal_id = request.args(0)
    if len(deal_id) >10 or not deal_id.isdigit():
        redirect(URL('deal','index'))

    deal = db.deals[deal_id]
    if not deal:
        redirect(URL('deal','index'))

    deal.update_record( wants = deal.wants + 1 )

    if not deal.used:
        redirect(URL('deal','index'))


    response.title='Платежи оплата биткоинами криптовалютой услуги %s' % deal.name

    client = db(db.clients.deal_id == deal.id).select().first()
    if client:
        # to_shop/index/2?order=12&user=eytu
        #redirect(URL('to_shop','index',args=[client.id], vars=request.vars))
        raise HTTP(200, T('ERROR: it is client "%s"') % client.email)

    vol = (deal.MIN_pay or 100) * 2
    dealer, dealer_acc, dealer_deal = ed_common.select_ed_acc(db, deal, ecurr_out, vol, True)
    if not dealer:
        raise HTTP(200, T('ERROR: not found dealer for "%s"') % deal.name)
    dealer_acc = ed_common.sel_acc_max_for_balance(db, dealer, ecurr_out, vol, unlim=True)

    #print dealer.info
    dealer_info = dealer.info and json.loads(dealer.info)
    shops_url = dealer_info['shops_url']
    #MAX = deal.MAX_pay or 777
    MIN = db_common.gMIN(deal, dealer)

    if not response.vars: response.vars = {}

    if deal.url and len(deal.url)>0:
        shops_url = deal.url
    else:
        shops_url = dealer_info['shops_url'] + "%s" % dealer_deal.scid
    deal_img = make_img(deal, dealer_info, shops_url)

    title=XML(XML(T("Задайте параметры платежа для ") + '<BR>') + XML( deal_img or '' ) + ' ' +\
            XML( A(deal.name, _href=shops_url, _target="_blank")))
    title = XML(XML(deal_img or '') + ' <b>' + deal.name + '</b> ' + 'оплата биткоинами и криптовалютой')
    deal_cat = db.deals_cat[deal.cat_id]
    subtitle = XML('Другие услуги вида %s' % A(deal_cat.name, _href=URL('deal','index', args=[deal_cat.id])))

    response.vars['s_url'] = XML( A(T('тут'), _href=shops_url, _target="_blank"))
    response.vars['shops_url'] = shops_url

    acc_pars = None
    if dealer_deal.grab_form:
        # тут тырим форму с сайта яндекса напрямую
        #scid, name, img, form = ed_form.load_YD(...)
        response.vars['grab_form'] = ed_form.load_YD(shops_url,  URL('more', 'pay'))
        #print response.vars['grab_form']

    else:
        acc_pars = []
        ajax_vars = []
        if dealer_deal.p2p:
            if deal.template_ == '--':
                pay_pars_deal=[]
                pay_pars_dealer=[]
            else:
                pay_pars_deal = ed_common.PAY_PARS_P2P
                pay_pars_dealer = ed_YD.PAY_PARS_P2P
        else:
            pay_pars_deal = deal.template_ and json.loads(deal.template_) or ed_common.PAY_PARS
            pay_pars_dealer = dealer_deal.template_ and json.loads(dealer_deal.template_) or ed_YD.PAY_PARS
            #print dealer_deal.template_, json.loads(dealer_deal.template_)
        #print dealer_deal
        #print pay_pars_deal
        #print pay_pars_dealer
        calcs = dealer_deal.calcs_ or {}
        for p in pay_pars_deal:
            read_only = None
            if 'calc' in p: continue
            if type(p) == type([]): continue

            #print p
            p_n_name = p.get('n')
            p_t = p_n_name and pay_pars_dealer.get(p_n_name)
            def_val = subsel_parent = None
            add_pars = {}
            calc2 = calcs.get(p_n_name)
            #print 'calc2', calc2
            if calc2 != None and type(calc2) not in [type(dict()), type([]), type({})]:
                # тут простое вычисление - прпустим
                continue
            if calc2:
                # это поле вычисляется автоматически
                # или есть зависимые от него поля
                subsel_name = calc2.get('subsel')
                subsel_parent = calc2.get('parent')
                if subsel_name:
                    # это поле главное и у него есть подчиненное поле
                    add_pars['_onChange'] = 'ajax("../subsel_callback", ["%s", "deal_id", "dealer_deal_id"], "%s");' % (p_n_name, 'div_'+subsel_name)
                    #_onChange="ajax('selsub2_callback', ['%s'], '%s');" % (sel1_name, sel2_div_name),
                if subsel_parent:
                    add_pars['_disabled'] = 'disabled'
                if not subsel_name and not subsel_parent:
                    # это поле обычное вычисляемое -- пропустим
                    continue

            # если параметры передаются как параметры после ?
            def_val = request.vars.get(p_n_name)
            if def_val:
                read_only = True

            sel = p_t and p_t.get('sel')
            lab_ = p.get('l')
            tip_ = p.get('m')
            if sel:
                lab_ = LABEL(lab_ and T(lab_) or p_n_name)
                opt=[]
                for item in sel:
                    #for (v, l) in item.iteritems():
                    opt.append(OPTION(item['label'], _value=item['value']))
                #print opt
                inp = SELECT(opt, _name=p_n_name, _id=p_n_name, _type="text", _class='field blue-c', **add_pars)
            elif p_n_name:
                lab_ = LABEL(lab_ and T(lab_) or p_n_name)
                # если имя поля задано то поле покажем
                inp = INPUT(_name=p_n_name, _id=p_n_name, # тут имя поля указываем для диллера
                         _placeholder = p.get('ph', ''),
                         _value=def_val or session.vars and session.vars.get(p.get('n')) or p.get('v'),
                         _readonly = read_only,
                         #_size=('ln' in p and p['ln'] or 5)+1,
                         _onblur='ln' in p and 'get_acc(this, %s, "%s");' % (p['ln'] or 0, 'символов %s'),
                         requires=IS_NOT_EMPTY(),
                         _class='field blue-c',
                         **add_pars
                         )
            elif lab_:
                acc_pars.append({ 'l': HR(_align="center", _width="auto", _size="3", _color="#ffffff"),
                                 'i':''})
                ##lab_ = LABEL(lab_ and T(lab_) or '')
                lab_ = LABEL(H5(T(lab_)))
                inp = ''
            elif tip_:
                lab_ = LABEL(H4(TAG.i(_class='fa fa-exclamation-triangle', _style='color:yellow; font-size:1.5em;'), ' ', tip_))
                inp = ''

            if subsel_parent:
                # это подчиненное поле - результат аякса
                # то вложем его внутрь
                inp = DIV(inp, _id='div_' + p_n_name)

            item = {
                    'l': lab_,
                    'i': inp,
                    }
            info = p.get('i')
            if info:
                item['l'] += '*'
                item['m'] = XML(info)
            acc_pars.append(item)

            if p_n_name:
                ## для полей АЯКСа
                ## причем надо от УНИКОДЕ строки избавиться - поэтому %
                _sss = p_n_name.encode('ascii')
                ##print _sss, type(_sss)
                ajax_vars.append(_sss)


        #print i_d, request.args
        #if False and len(request.args)>i_d+1:
        #    # цена тоже задана
        #    volume_out = float(request.args[i_d+1])
        #    response.vars['vol_readonly'] = True

    response.vars['e_bal'], MAX = get_e_bal(deal, dealer, dealer_acc)
    volume_out = 377
    if request.vars:
        #print request.vars
        if 'mess' in request.vars: response.vars['shop_mess'] = request.vars['mess']
        if 'sum' in request.vars:
            volume_out = test_vol(request.vars['sum'], MIN, MAX)
            response.vars['vol_readonly'] = True
        session.vol = volume_out

    response.vars['deal_id'] = deal_id
    response.vars['dealer_deal_id'] = dealer_deal.id
    response.vars['MIN'] = MIN
    response.vars['MAX'] = MAX
    response.vars['volume_out'] = volume_out
    response.vars['not_gifted'] = deal.not_gifted


#  except Exception as e:
#    db.deal_errs.insert( deal_id = deal.id, dealer_id = dealer.id, err = '%s' % e)

    # поля для передачи по запросу АЯКСа
    ajax_vars.append('vol')
    ajax_vars = '%s' % ajax_vars
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
                      ajax('%s',%s,'tag%s');
                      ''' % (id, id, URL('get', args=[id, deal_id]), ajax_vars, id)
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

    #response.top_line = None

    return dict(title=title, subtitle=subtitle,
                deal_name = deal.name, deal_info=deal.show_text,
                deal_icon = make_img(deal, dealer_info),
                MIN=MIN, MAX=MAX, #reclams=reclams,
                pars=acc_pars, xcurrs_h=xcurrs_h)
