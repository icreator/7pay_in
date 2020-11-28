#!/usr/bin/env python
# coding: utf8

#import common
#common.not_is_local(None, True)

#from gluon import *
from gluon.dal import DAL, Field, Table

reserveds = ['MIN', 'MAX', 'ref', 'template', 'count', 'sum', 'counter', 'average', 'connect', 'desc', 'page', 'level' ]
#print db.tables
def to_mysql(db, db_old=None):
    return 'nne none'
    if not db_old:
        db_old = DAL("sqlite://storage.sqlite",
            # this keyword buil model on fly on load
            auto_import=True,
            #folder="../../ipay_db/databases",
            #folder="/databases",
            #folder="../../ipay8/databases",
            folder="applications/ipay8/databases",
            )

    # те таблицы что не надо копировать
    exept = ['orders_stack', 'orders', 'pay_ins', 'pay_ins_stack', 'buys_stack', 'deal_acc_addrs', 'logs']
    for table in db:
        db[table].truncate()
        tn = table._tablename
        if tn in exept:
            print 'EXEPTED:', table
            continue
        print 'CONVERTing:', table
        for r in db_old(db_old[table]).select():
            #if tn == 'deals': print r
            # заменим зарезервированные слова
            r_ = dict()
            for f in r:
                #print f
                if f in reserveds:
                    r_[f] = r[f]
            for f in r_:
                r[f + '_'] = r_[f]
            try:
                db[table][0] = r
            except Exception as e:
                print e

        
        
        
# тут запуск из тулсов, поэтому коммит автоматом
def to7(db):
    return
    '''
    db_old = DAL("sqlite://storage.sqlite",
        #pool_size=1,
        #check_reserved=['all'],
# this keyword buil model on fly on load
        auto_import=True,
        folder="../../ipay_db/databases")
    '''
    db_old = db
    #import json
    print '\nconvert 6 to 7'
    
    for r in db(db.deals).select():
        r.used = True
        r.update_record()
    
    dealer = db.dealers[1]
    print dealer.name
    for deal in db(db.deals).select():
        db.dealer_deals.insert(
            dealer_id = dealer.id,
            deal_id = deal.id,
            used = True,
            scid = deal.scid,
            template = deal.template,
            grab_form = deal.grab_form,
            p2p = deal.p2p,
            tax = deal.dealer_tax,
            )

    db.commit()
    print 'end'


def from5(db):
    return
    db_old = DAL("sqlite://storage.sqlite",
        #pool_size=1,
        #check_reserved=['all'],
# this keyword buil model on fly on load
        auto_import=True,
        folder="../../ipay5-m/databases")
    
    db_new = DAL("sqlite://storage.sqlite",
        #pool_size=1,
        #check_reserved=['all'],
# this keyword buil model on fly on load
        auto_import=True,
        folder="../../ipay6-a/databases")
    import json
    print '\nimport 5 to 6'

    for xcurr in db(db.xcurrs).select():
        pass
    
    deal = db(db.deals.name=='to phone +7 RUBs').select().first()
    if not deal: return 'not deal "to phone +7 RUBs"'
    print "for deal:", deal
    for rec in db_old(db_old.to_phone).select():
        # найдем неимпортированные записи
        #
        acc = db((db.deal_accs.deal_id==deal.id)
                 & ( db.deal_accs.deal_acc==rec.phone)).select().first()
        #print deal_acc
        #continue
        if acc:
            acc_id = acc.id
        else:
            print 'insert deal_acc', rec.phone
            acc_id = db.deal_accs.insert( deal_id = deal.id, acc = rec.phone )

        acc_addr = db((db.deal_acc_addrs.deal_acc_id==acc_id)
                 & (db.deal_acc_addrs.addr==rec.wallet)
                 & (db.deal_acc_addrs.xcurr_id==rec.xcurr_id)).select().first()

        if acc_addr:  continue
        print 'insert acc_addr ',rec.xcurr_id, rec.wallet
        db.deal_acc_addrs.insert(deal_acc_id=acc_id,
                 addr=rec.wallet, xcurr_id=rec.xcurr_id,
                 incomed=rec.unspent, converted=rec.unspent)

    ####### теперь платежи
    #for p_in in db_old(db_old.payments).select():


    db_old.close()

if __name__ == "__main__":
    #to7(db)
    db.commit()
    db.close()
