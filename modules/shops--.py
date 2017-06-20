# coding: utf8
import socket

# vvv=True - включает секртную сессию и выдает страницу ошибки
def not_is_local(vvv=None):
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

    if vvv and (request.env.http_x_forwarded_for or request.is_https):
        session.secure()

    if (remote_addr not in hosts) and (remote_addr != "127.0.0.1"):
        #and request.function != 'manage':
        if vvv: raise HTTP(404, T('ERROR 0432'))
        return True

import datetime
import json

import db_common
import db_client


def log(mess):
    print mess
    db.logs.insert(mess='CNT: %s' % mess)
def log_commit(mess):
    log(mess)
    db.commit()

# try something like
def index(): return dict(message="hello from clients.py")

def list():
    l = [[TD(B(T('Иконка')), _class='center'), TD(B(T('Польз'), _class='center')), TD(B(T('Описание')), _class='center')]]
    for r in db(db.shops.not_listed != True ).select( orderby=~db.shops.uses|db.shops.name ):
        img = None
        if r.icon: img = IMG(_src=URL('default','download', args=['db', r.icon], ))
        l.append([TD(A(img or r.name, _href=r.url, _target='_blank'), _width=124), TD(r.uses, _class='center' or ''), TD(r.descr or '')])
    
    
    return locals()

from gluon.tools import Mail
# шлем рассылку в скрытых копиях
def send_email_to_descr(to_addrs, subj, mess=None, rec=None, templ=None):
    if not_is_local(): raise HTTP(404, T('ERROR 0131'))
    mail = Mail()
    #mail.settings.server = 'smtp.yandex.ru' #:25'
    mail.settings.server = 'smtp.sendgrid.net'
    mail.settings.sender = 'support@cryptoPay.in'
    #mail.settings.login = 'support@7pay.in:huliuli'
    mail.settings.login = 'azure_90ebc94457b0e6a1c4c920993753f5a6@azure.com:7xirv1rc'
    mess = mess or ''
    if rec and templ:
        context = dict( rec = rec )
        #mess = response.render('add_shop_mail.html', context)
        mess = response.render(templ, context)
    #print mess
    #to_addrs = ['kentrt@yandex.ru','icreator@mail.ru']
    mail.send(to=to_addrs[0],
           cc=len(to_addrs)>1 and to_addrs[1:] or None,
#           bcc=len(to_addrs)>1 and to_addrs[1:] or None,
           subject=subj,
           message=mess)

def mail_to_clients1():
    if not_is_local(): raise HTTP(404, T('ERROR 0131'))
    subj = 'Новости от биллинга cryptoPay.in - 2'
    mess = '''
    Здравствуйте!
    
    Появился модуль (плагин) биллинга поатежей для магазинов, созданных на PrestaShop http://cryptopay.in/shop/default/plugins
    Подключение свободное и бесплатное. Просьба тех кто хочет установить на свой сайт этот плагин, откликнуться.
    
    С Уважением, Ермолаев Дмитрий
    '''
    mess = mess + '%s.' % A('cryptoPay.in', _href='http://cryptoPay.in')
    #send_email_to_descr('icreator@mail.ru',subj,mess)
    return mess
    to_addrs = []
    for r in db(db.startup).select():
        to_addrs.append(r.email)
        if len( to_addrs ) >15:
            send_email_to_descr(to_addrs, subj, mess)
            to_addrs = []
    if len(to_addrs)>0: send_email_to_descr(to_addrs, subj, mess)
    
def mail_to_polza1():
    if not_is_local(): raise HTTP(404, T('ERROR 0131'))
    subj = 'cryptoPay.in - СТАРТАП: сообщение 5'
    return 'stopped'
    mess = '''
    Здравствуйте!
    
    И так нас зарегистрировали. Название выбрано нейтральное что бы не привлекать внимание на начальных этапах и при регистрации:
    Инновационное Постребительское Общество "Польза"
    
    На неделе открываем расчетный счет в СберБанке, после чего можно будет вносить паи.
    
    Уже запущен сайт ipo-polza.ru (пока очень сырой, чисто как наметки для будущего)
    Хотя через него уже можно подавать данные  на регистрацию.
    
    Для получения новостей, подключайтесь в социальной сети google+ к пользователю ipo.polza@gmail.com

    
    С Уважением, Дмитрий Ермолаев
    http://ipo-polza.ru
'''
    #mess = mess + '%s.' % A('cryptoPay.in Стартап', _href='http://cryptopay.in/shop/default/startup')
    #send_email_to_descr('icreator@mail.ru',subj,mess)
    to_addrs = []
    if True:
        for r in db(db.startup).select():
            to_addrs.append(r.email)
            if len( to_addrs ) >10:
                send_email_to_descr(to_addrs, subj, mess)
                to_addrs = []
        if len (to_addrs) > 0: send_email_to_descr(to_addrs, subj, mess)
    else:
        send_email_to_descr(['icreator@mail.ru'], subj, mess)

    return 'sended'
