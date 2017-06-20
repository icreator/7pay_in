# coding: utf8

## перенаправления с версии 2
def to_pay():
    redirect(URL('to_deal', 'index', args=request.args, vars=request.vars))

def index():
    redirect(URL('deal', 'index', args=request.args, vars=request.vars))
