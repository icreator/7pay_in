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
    print request.vars
    import rates_lib
    result = rates_lib.get_rate_for_api(db, request.vars.get('curr_in'), request.vars.get('curr_out'), request.vars.get('vol_in'), get_limits = True)
    print result

    response.js = "$('.go2-btn').removeClass('disabled');$('#go2').children('i').removeClass('fa-refresh fa-spin').addClass('fa-search');"

    import gluon.contrib.simplejson
    return CAT(gluon.contrib.simplejson.dumps(result))


def get_rate():
    print request.vars
    import rates_lib
    result = rates_lib.get_rate_for_api(db, request.vars.get('curr_in'), request.vars.get('curr_out'), request.vars.get('vol_in'), get_limits = True)
    print result

    response.js = "$('.go-btn').removeClass('disabled');$('#go').children('i').removeClass('fa-refresh fa-spin').addClass('fa-search');"

    import gluon.contrib.simplejson
    return CAT(gluon.contrib.simplejson.dumps(result))
    

################# used INCOME AMOUNT ###########################################
###  pars:
### curr = xcurr ABBREV
### sum + addr + mess
### /BTC/addr/sum_in
def index():

    #common.page_stats(db, response['view'])
    #print request.args

    response.title=T("Обмен цифровых активов")
    response.subtitle = T('Bitcoin Erachaim')

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
            SPAN(IMG(_src=URL('static', 'images/currs/' + r.currs.abbrev + '.png'), _width=30, _alt=''),
                        ' ', r.currs.name, ' ', free_bal,
                _onclick='$("#curr_in").val("' + r.currs.abbrev + '");'), False, ''
                  )
            )
        output_currs.append(
            (
            SPAN(IMG(_src=URL('static', 'images/currs/' + r.currs.abbrev + '.png'), _width=30, _alt=''),
                        ' ', r.currs.name, ' ', free_bal,
                _onclick='$("#curr_out").val("' + r.currs.abbrev + '");'), False, ''
                  )
            )

    if len(inp_currs)==0:
        return err_dict(
            T('ОШИБКА: Нет доступных криптовалют для обмена')
            + (abbrev and (' ' + T('или неправильно задано имя [%s] нужной криптовалюты!') % abbrev) or ''))

    
    input_currs = [
        (
            TAG.i(_class='fa fa-search go-btn- button- ll-blue-bgc- center', _style='width:100px;',
                    ),
            False, None, input_currs)
        ]
    output_currs = [
        (
            TAG.i(_class='fa fa-search go-btn- button- ll-blue-bgc- center', _style='width:100px;',
                  ),
            False, None, output_currs)
        ]

    amo_in = INPUT(_name='amo_in')

    return dict(title=title, subtitle=subtitle, inp_currs=inp_currs,
               abbrev=abbrev, addr=addr, vol=vol, input_currs = input_currs, output_currs=output_currs)
