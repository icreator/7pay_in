#!/usr/bin/env python
# -*- coding: utf-8 -*-
from gluon import current as C

def get1():
    if C.IS_LOCAL: return ''
    
    if C.IS_MOBILE:
        r = '''
<iframe data-aa='76221' src='https://ad.a-ads.com/76221?size=320x50' scrolling='no' style='width:320px; height:50px; border:0px; padding:0;overflow:hidden' allowtransparency='true' frameborder='0'></iframe>
'''
    elif False:
        r = '''
<iframe data-aa='76220' src='https://ad.a-ads.com/76220?size=336x280' scrolling='no' style='width:336px; height:280px; border:0px; padding:0;overflow:hidden' allowtransparency='true' frameborder='0'></iframe>
'''
    else:
        r = '''
<iframe data-aa='76174' src='https://ad.a-ads.com/76174?size=728x90' scrolling='no' style='width:728px; height:90px; border:0px; padding:0;overflow:hidden' allowtransparency='true' frameborder='0'></iframe>
'''
    return '''
            <div class="container">
                <div class='col-sm-12'>
                    <div class='center'>''' + r + '''</div>
                </div>
            </div>
'''
