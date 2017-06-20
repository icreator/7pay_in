# coding: utf8
import socket
import urllib2
import trans


if not IS_LOCAL:
    raise HTTP(200, 'error')

import sys
import time

from decimal import Decimal
import datetime
import json

dealer = db(db.dealers.name=='Yandex').select().first()
HIDDENS = ['hidden', 'hidden-fields']

def log(mess):
    print mess
    db.logs.insert(mess='CNT: %s' % mess)
def log_commit(mess):
    log(mess)
    db.commit()

# попробовать что-либо вида
def index():
    return dict(message="hello from tools.py")

def parse_item(ii, tab_sums, comp, deal_templ, tab):
    if comp.attributes.get('_place') in HIDDENS: return
    print 'item', comp.attributes
    bind = comp.attributes.get('_bind')
    name = comp.attributes.get('_name')
    role = comp.attributes.get('_role')
    #par_name = role or bind or name
    par_name = bind or role or name
    if role in ['sum']:
        tab_sums.append(par_name)
        return
    if par_name in ['FormComment', 'sum', 'inrow']: return

    deal_par_name = 'acc%s' % (ii[0])
    print comp.tag
    print comp.element()
    label = comp.element('xf:label')
    print 'label:', label, label and len(label)
    label = label and label[0] or ''
    if type(label) != type(''):
        # тут вложенный <para><ptext>Реквизиты перевода</ptext></para>
        label = label.element('ptext')[0]

    hint = comp.element('xf:hint')
    print hint
    if hint:
        if type(hint) == type(comp):
            if len(hint)>0:
                hint = hint[0]
            else:
                hint = '*'
    print label, hint
    if hint:
        if type(hint) != type('') and len(hint)>0:
            # тут вложенный <para><ptext>Реквизиты перевода</ptext></para>
            hint = hint.element('ptext')[0]
        label = '%s (%s)' % (label, hint)

    attr = par_name and { 'n': par_name } or None

    if comp.tag == 'xf:select1':
        #print 'select'
        opts = comp.element('xf:choices')
        if not opts:
            opts = comp.elements('xf:item')
        if opts and len(opts)>0:
            # если список задан
            sel = []
            for item in opts:
                if type(item)==type(''):
                    # тут иногда текст а не элемент встречается
                    #print '"%s"' % comp
                    continue
                l = item.element('xf:label')
                #print type(l), type([])
                v = item.element('xf:value')
                #print v
                if l and v:
                    sel.append({ 'label':l[0], 'value': v[0] })
            #print sel
            if sel and len(sel)>0: attr['sel'] = sel
        else:
            # иначе просто как поле делаем
            #l = item.element('xf:label')[0]
            pass

    #print attr

    #label = label.decode('utf8')
    #label = label.decode('ascii')
    #print label
    tt = {}
    if label: tt['l'] = label
    if attr:
        tt['n'] = deal_par_name
        ii[0] = ii[0]+1
        tab[deal_par_name] = attr
    if len(tt)>0: deal_templ.append( tt )

def parse_group(ii, tab_sums, gr, deal_templ, tab):
    print 'group', gr.attributes
    for comp in gr: # .components:
        if type(comp)==type(''):
            # тут иногда текст а не элемент встречается
            #print '"%s"' % comp
            continue
        if comp.attributes.get('_type') in HIDDENS: continue
        if comp.attributes.get('_place') in HIDDENS: continue
        if comp.tag in ['xf:group']:
            # https://money.yandex.ru/internal/mobile-api/get-showcase.xml?scid=773
            # <xf:group role="inrow">
            # тут похоже старые компоненты
            parse_group(ii, tab_sums, comp, deal_templ, tab)
        else:
            parse_item(ii, tab_sums, comp, deal_templ, tab)

def parse_scid(scid):
    dn = dn_e = deal_templ = tab = None
    uu = 'https://money.yandex.ru/internal/mobile-api/get-showcase.xml?scid=%s' % scid
    rq = urllib2.Request(uu) #, '')
    #rq.add_header('Authorization', 'Bearer ' + token)
    try:
        f = urllib2.urlopen(rq)
        html = f.read()
    except Exception as e:
        print 'xml ', rq, e
        dn_e = e
        return dn, dn_e, deal_templ, tab, None

    parsed_html = TAG(html)
    resp = parsed_html.element('response')
    deal_name = resp.element('name')
    xforms = resp.element('xforms')
    if not xforms:
        return dn, dn_e, deal_templ, tab, html
    deal_templ = []
    ii = [1]
    tab_sums = ['sum']
    tab = {'_sum_names': tab_sums}
    for comp in xforms:
        if type(comp) == type(''): continue
        if comp.attributes.get('_type') in HIDDENS: continue
        if comp.attributes.get('_place') in HIDDENS: continue
        if comp.tag in ['xf:group']:
            parse_group(ii, tab_sums, comp, deal_templ, tab)

    if len(deal_templ)<1:
        return None, None, None, None, html
    dn = deal_name[0]
    dn_e = dn.decode('utf8')
    dn_e = dn_e.encode('trans')
    return dn, dn_e, deal_templ, tab, html

def parse():
    if len(request.args) == 0:
        mess = 'parse/scid'
        print mess
        return mess
    dn, dn_e, deal_templ, dealer_deal_templ, html = parse_scid(request.args[0])
    return BEAUTIFY(XML(html)) + BEAUTIFY(dn) + BEAUTIFY(dn_e) + BEAUTIFY(deal_templ) +'\n' + BEAUTIFY(dealer_deal_templ)

def make_YD_deal_0(scid, upd=None):
    upd = upd and int(upd)
    dn, dn_e, deal_templ, dealer_deal_templ, _ = parse_scid(scid)
    if not dn:
        return dn, dn_e, deal_templ, dealer_deal_templ
    deal_templ = json.dumps(deal_templ)
    dealer_deal_templ = json.dumps(dealer_deal_templ)

    deal = db(db.deals.name == dn).select().first()
    if not deal:
        print '\n insert', dn_e
        id = db.deals.insert(name = dn, name2 = dn_e, used=True,
                             cat_id =1,
                             template_ = deal_templ)
        deal = db.deals[id]
    elif deal.used:
        print '\n update', dn_e
        deal.update_record( template_ = deal_templ, used=True )
    else:
        print '\n not Used!', dn_e
        return None, None, None, None

    dealer_deal = db(
        (db.dealer_deals.dealer_id==dealer.id)
        & (db.dealer_deals.deal_id==deal.id)
        ).select().first()
    if not dealer_deal:
        id = db.dealer_deals.insert(dealer_id=dealer.id, deal_id=deal.id,
                                    used=True, scid = scid, template_ = dealer_deal_templ,
                                    )
    else:
        if upd:
            dealer_deal.update_record( used=True, scid = scid, template_ = dealer_deal_templ, grab_form	= False)
        else:
            dn = '*** NOT UPDATED: ' + dn

    return dn, dn_e, deal_templ, dealer_deal_templ

# http://127.0.0.1:8000/YD_grab/make_YD_deal/929
# http://127.0.0.1:8000/YD_grab/make_YD_deal/4895/0
# 5171
# ВТОРОЙ параметр - принудительно апдейтить - иначе если есть такой и работает тоне апдейтить
def make_YD_deal():
    if len(request.args) == 0:
        mess = 'make_YD_deal/scid/[to update=1 or 0 or empty]'
        print mess
        return mess
    scid = request.args[0]
    ## принудительный апдейт - иначе не апдейтить если уже есть и работает
    upd = request.args(1)
    dn, dn_e, deal_templ, dealer_deal_templ = make_YD_deal_0(scid, upd)

    return BEAUTIFY(dn) + BEAUTIFY(dn_e) + BEAUTIFY(deal_templ) +'\n' + BEAUTIFY(dealer_deal_templ)

# http://127.0.0.1:8000/YD_grab/update_from_to/1/4895
# http://127.0.0.1:8000/YD_grab/update_from_to/6910/30000
# ТРЕТИЙ параметр - принудительно апдейтить - иначе если есть такой и работает тоне апдейтить
def update_from_to():
    if len(request.args) == 0:
        mess = 'len(request.args)==0'
        print mess
        return mess
    e = ''
    upd = request.args(2)
    for scid in range(int(request.args[0]), int(request.args(1))):
        print scid
        try:
        #if True:
            dn, dn_e, deal_templ, dealer_deal_templ = make_YD_deal_0(scid, upd)
            print dn, dn_e
        except Exception as e:
            log('%s - %s' % (scid, e))
        db.commit()
