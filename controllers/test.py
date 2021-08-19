# -*- coding: utf-8 -*-

if not IS_LOCAL: raise HTTP(200, 'error')


# попробовать что-либо вида
def index(): return dict(message="hello from test.py")

def a():
    mess = '7pb4'
    print (mess[0:3])
    if mess.startswith('7pb'):
        # просто код заказа тут
        order_id = mess[3:]
        order_id = mess.split('7pb')[1]
        print (order_id)
        if order_id.isdigit():
            order = db.addr_orders[ order_id ]
            if order:
                xcurr = db.xcurrs[ order.xcurr_id ]
                addr = order.addr
                if xcurr: return addr
    return 'ddd'
