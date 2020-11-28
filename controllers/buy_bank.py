# coding: utf8

import time

response.title=T("Купить биткоины, криптовалюту за безналичные по платежу из любого банка, который может пополнить Яндекс.Кошелек (Альфа-банк, ...). Однако пока Сбербанк не дает эту возможность")
response.big_logo2=True
response.logo2 = IMG(_src=URL('static','images/7P-302.png'), _width=200)
response.not_show_func = True

def log(mess):
    print mess
    db.logs.insert(mess='BUY: %s' % mess)
def log_commit(mess):
    log(mess)
    db.commit()

# переходник для показа ссылкок и картинок в листингах
def download():
    return response.download(request,db)

def u(h, url, cls='col-sm-4'):
    return DIV(DIV(P(h, _class='btn_mc2'), _class='btn_mc1', _onclick="location.href='%s'" % url), _class='btn_mc ' + cls)

def check():
    addr = request.vars.get('address')
    ref = request.vars.get('ref')
    amo = request.vars.get('amo')
    if not addr: return T('Адрес кошелька пуст') # Wallet address is empty
    if not ref: return T('Номер платежа пуст') # Reference address is empty
    if not amo: return T('Сумма не задана') # Amount is empty
    if not amo.replace('.','').isdigit(): return 'Amount Error'
    
    time.sleep(3)
    rec = db((db.buys_stack.ref_ == db.buys.id)
             & (db.buys.amount == amo)
             & (db.buys.buyer.startswith(ref + ' '))).select().first()
    # если вводился не номер платежа а номер платежа [op_id]
    rec = rec or db((db.buys_stack.ref_ == db.buys.id)
             & (db.buys.amount == amo)
             & (db.buys.operation_id == ref)).select().first()
    if not rec:
        return T('Платеж не найден') # Records not founded
    if rec.buys.addr:
        return T('Адрес уже задан') # This payment already assigned!!!

    from db_common import get_currs_by_addr
    curr, xcurr, _ = get_currs_by_addr(db, addr)
    if not xcurr:
        return T("Неверный адрес") # Invalid wallet address
    from crypto_client import connect
    conn = connect(curr, xcurr)
    if not conn:
        return T("Нет связи с [%s]") % curr.abbrev # Not connected to wallet [%s]
    valid = conn.validateaddress(addr)
    if not valid.get('isvalid'):
        return T("Неверный адрес для [%s]") % curr.abbrev # Invalid wallet address for [%s]
    
    rec.buys.update_record( xcurr_id = xcurr.id, addr = addr)
    return T('Задан для %s') % curr.name # accepted to %s

def index():
    h = CAT(
        T('После того, как Вы пополнили безналичным платежом из Вашего банка Яндекс.Кошелек, предоставленный для покупки биткоинов (лайткоинов и другой криптовалюты) нашим сервисом, введите реквизиты своего платежа для того чтобы присвоить ему адрес для выплаты криптовалюты'),'.',BR(),
        T('Так же Вы можете задать адрес кошелька для платежей, у которых его забыли указать'),'.',BR(),
        INPUT(_name='address', _placeholder=T('Адрес кошелька...')),BR(), # Wallet address
        INPUT(_name='ref', _placeholder=T('Номер платежа')), # payment referrence
        INPUT(_name='amo', _placeholder=T('Сумма платежа')), #payment amount
        BUTTON(T('Check'), _onclick='ajax("buy_bank/check", ["address", "ref", "amo"], "res");\
               $("#res").html(\'<i class="fa fa-spinner fa-spin"></i>\');'),
        DIV(_id='res'),
        u(T('Назад на покупку биткоинов и другой криптовалюты'),
            URL('buy', 'index'),'col-sm-12'),
    )
    return dict(h=h)
