#!/usr/bin/env python
# coding: utf8
import datetime
import logging
import urllib

#log =logging.Logger()
#log.debug

from gluon import *
def ip(): return current.request.client

import socket
# vvv=True - включает секртную сессию и выдает страницу ошибки
def not_is_local(request, vvv=True):
    request = request or current.request
    http_host = request.env.http_host.split(':')[0]
    remote_addr = request.env.remote_addr
    #http_host[7pay.in] remote_addr[91.77.112.36]
    #raise HTTP(200, T('appadmin is disabled because insecure channel http_host[%s] remote_addr[%s]') % (http_host, remote_addr))
    try:
        hosts = (http_host, socket.gethostname(),
                 socket.gethostbyname(http_host),
                 '::1', '127.0.0.1', '::ffff:127.0.0.1')
    except:
        hosts = (http_host, )

    if (remote_addr not in hosts) and (remote_addr not in current.TRUST_IP):
        #and request.function != 'manage':
        if vvv:
            raise HTTP(200, current.T('ERROR: not admin in local'))
        return True
    
def uri_make(name, addr, pars_in, label_in=None):
    if name=='copperlark':
        pars = ''
    else:
        pars = '?' + urllib.urlencode(pars_in)
    href = name + ":" + addr + pars
    #qr = MARKMIN('qr:%s' % href)

    return A(XML('<button class="uri">%s</button>' % (label_in or current.T('ОПЛАТИТЬ'))), _class='btn_uri', _href=href), href


def page_stats(db,view):
    v = view[:19]
    ss = db(db.site_stats.page_==v).select().first()
    if not ss:
        id = db.site_stats.insert(page_=v, loads=1)
        return 1
    ss.loads = ss.loads + 1
    ss.update_record()
    # вызов там на страницах автоматом этот db.commit()
    print view, ss.loads, ip()
    return ss.loads

def last_year():
    td = datetime.date.today()
    m = td.month
    y = td.year
    if m == 1: return y-1
    return '%s' % y
def last_year2():
    y = "%s" % last_year()
    return y[-2:]
def last_month():
    td = datetime.date.today()
    m = td.month
    y = td.year
    if m == 1: return 12
    return m-1
def last_month2():
    mm = '%02d' % last_month()
    return mm

#import PIL
#import Image
#import _imaging
# для Апаче нужно установить отсюда пакет:
# http://www.lfd.uci.edu/~gohlke/pythonlibs/ -- Pillow‑2.4.0.win32‑py2.7.exe
import pyqrnative
def QRcode(data_string,file_name=None):
    #import os
    quality={1: pyqrnative.QRErrorCorrectLevel.L,
             2: pyqrnative.QRErrorCorrectLevel.M,
             3: pyqrnative.QRErrorCorrectLevel.Q,
             4: pyqrnative.QRErrorCorrectLevel.H}
    size = 4
    level = 1
    file_name = file_name or "1111.png"
    while 1:
        #print size
        try:
            q = pyqrnative.QRCode(size, quality[level])
            q.addData(data_string)
            q.make()
            break
        except TypeError:
            size+=1
    x=q.makeImage()
    #qr_file = os.path.join('C:/web2py/applications/ipay10/static', file_name)
    qr_file = file_name
    img_file = open(qr_file, 'wb')
    x.save(img_file, 'PNG')
    img_file.close()
    #img = IMG(_src=URL('static', file_name)) # а то тормозит и качество ухудшает), _width=124)
    #return dict(im = img)

def rnd_8(v, rnd=8):
    return round( float( v ), rnd )
