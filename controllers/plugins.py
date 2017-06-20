# coding: utf8
import socket


import common

def qr():
    session.forget(response)
    mess = request.vars['mess']
    file_name = 'QR%s.png' % response.session_id # session.id
    session.forget(response)
    path = 'static/temp--'
    common.QRcode(mess, request.folder + path + '/' + file_name)
    img = IMG(_src=URL(path, file_name)) # а то тормозит и качество ухудшает), _width=124)
    return img

def index():
    # запустим сразу защиту от внешних вызов
    # тут только то что на локалке
    if not IS_LOCAL: raise HTTP(200,'error1')

    #bt = BUTTON(T('Нажми меня'), _onclick=
    bt = DIV(A(T('Нажми меня'),  _class='btn',
               callback=URL('plugins','qr', vars={'mess':'eewerwer sdff df sdf wer'}),
               target='tag0',
               #delete='div#tag0'
               ), _id='tag0')
    div = DIV(_id='tag1')
    return locals()
