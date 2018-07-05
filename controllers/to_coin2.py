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
    h, result = get_rate_result(request)
    addr = request.vars.get('addr')
    
    return h


def get_rate_result(request):
    import rates_lib
    result = rates_lib.get_rate_for_api(db, request.vars.get('curr_in'), request.vars.get('curr_out'), request.vars.get('vol_in'), get_limits = True)

    response.js = "$('.go-btn').removeClass('disabled');$('#go').children('i').removeClass('fa-refresh fa-spin').addClass('fa-search');"

    if 'wrong' in result:
        h = CAT(
            H2(XML(T('Обменный курс %s/%s не найден') % (B(result['curr_in']), B(result['curr_out']))), '', _class='alert_value'),
            P(T('Возможно это носит временный характер. Вы можете совершить платеж по предоставленным платежным реквизитом и ваша заявка автоматически сработает при появлении курса обмена на сервисе и при условии что нужные Вам средства есть на сервисе в достаточном объеме'), '.')
            )
        return h

    print result

    #import gluon.contrib.simplejson
    #return CAT(gluon.contrib.simplejson.dumps(result))
    h = CAT()
    if result['rate_out'] <= 0:
        h += CAT(
            H2(
               XML(T('Введена слишком маленькая величина для обмена: %s. Введите значение больше') % (B(result['volume_in'], '[', result['curr_in'], ']'))), '', _class='alert_value'))
        return h
        
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

    return h, result

def get_rate():
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
        abberv = abbrev or request.vars.get('curr')
        addr = addr or request.vars.get('addr')
        vol = vol or request.vars.get('vol')

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
