# -*- coding: utf-8 -*-

if not IS_LOCAL: raise HTTP(200, 'error...')

def add_pay_in_tx():
    curr = request.vars.curr
    if not curr:
        return 'error - need curr'
    txid = request.vars.txid
    if not txid:
        return 'error - need txid'
    vout = request.vars.vout
    if not vout:
        return 'error - need vout'
    import db_common
    curr,xcurr,e = db_common.get_currs_by_abbrev(db, curr)
    if not xcurr:
        return 'error - invalid curr'
    
    from time import sleep
    sleep(1)
    
    pay_in = db((db.pay_ins.txid==txid)
                & (db.pay_ins.vout==vout)).select().first()
    if pay_in:
        return CAT(H2('already in PAY_INS'),BEAUTIFY(pay_in))
    
    import crypto_client
    conn = crypto_client.conn(curr, xcurr)
    if not conn:
        return 'error - not connected to wallet'
    res = None
    try:
        res = conn.getrawtransaction(txid,1) # все выдает
    except Exception as e:
        return 'error %s'  % e
    
    if 'hex' in res: res.pop('hex')
    txid = res.get('txid')
    if not txid:
        return BEAUTIFY(res)
    
    res.pop('vin')
    vout = int(vout)
    vouts = res['vout']
    if len(vouts) <= vout:
        return CAT(H3('vout so BIG'), BEAUTIFY(vouts))
    vout = vouts[vout]
    res.pop('vout')
    
    scriptPubKey = vout['scriptPubKey']
    addr = scriptPubKey['addresses'][0]
    acc_addr = db(db.deal_acc_addrs.addr==addr).select().first()
    if not acc_addr:
        return H3('not found order for address: ' + addr)
    
    value = vout['value']
    confs = res['confirmations']

    return CAT(LABEL('confs'), INPUT(_name='confs', _value=confs),' ', LABEL('address:'), INPUT(_name='addr', _value=addr),
              ' ', LABEL('value:'), INPUT(_name='amount', _value=value),BR(),
              INPUT(_type='submit'))

def add_pay_in():
    form = FORM(
            LABEL('curr'), INPUT(_name='curr'), ' ',
            LABEL('txid'), INPUT(_name='txid'), ' ',
            LABEL('vout'), INPUT(_name='vout'), BR(),
            A('Search', _onclick='ajax("add_pay_in_tx", ["curr", "txid", "vout"], "tag");', _class='btn button'),
            DIV(_id="tag"),
            )
    # непередается кнопка в эту форму - просто по рекваесту ловим
    if form.process().accepted or request.vars.confs:
        import datetime
        #print form.vars
        form.vars = request.vars
        acc_addr = db(db.deal_acc_addrs.addr==form.vars.addr).select().first()
        if not acc_addr:
            response.flash = 'not acc_addr founded'
            return dict(form=form)
        pay_in = db((db.pay_ins.txid==form.vars.txid)
                & (db.pay_ins.vout==form.vars.vout)).select().first()
        if pay_in:
            response.flash = 'txid + vout already exist'
            return dict(h=CAT(H3('txid + vout already exist'), form))
        pay_in_id = db.pay_ins.insert(
                      ref_ = acc_addr.id,
                      txid = form.vars.txid,
                      vout = form.vars.vout,
                      amount = form.vars.amount,
                      confs = form.vars.confs,
                      created_on = datetime.datetime.now(),
                      )
        db.pay_ins_stack.insert( ref_ = pay_in_id)
        response.flash = 'added'
    else:
        print 'not accepted (('
        print 'request.vars:', request.vars
        print 'form.vars:', form.vars
        
    return dict(h=DIV(H2('Try add lost transaction to pay_ins + pay_in_stack'), form, _class='container'))

def add_pay_in_stack():
    h = CAT()
    form = FORM(
            LABEL('ref_id in pay_ins'), INPUT(_name='ref_id'),
            INPUT(_type='submit'),
                )
    h += P(form)
    ref_id = request.vars.ref_id
    if ref_id:
        pay_in = db.pay_ins[ ref_id ]
        print pay_in
        if not pay_in:
            response.flash = 'not exist'
            return dict(h=DIV(h, _class='container'))

        db.pay_ins_stack.insert( ref_ = pay_in.id)
        
        response.flash = ' pay_ins_stack added'
        deal_acc_addrs = db.deal_acc_addrs[pay_in.ref_]
        deal_acc = db.deal_accs[deal_acc_addrs.deal_acc_id]
        deal = db.deals[deal_acc.deal_id]
        deal_name = deal.name
        h += DIV(deal.name, '[', deal_acc.acc,'] ', pay_in.amount, ' ', pay_in.created_on )
    
    return dict(h=DIV(h, _class='container'))

def index(): return dict(message="hello from tools_pay_ins.py")
