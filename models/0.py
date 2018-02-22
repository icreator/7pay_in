# -*- coding: utf-8 -*-

### тут еще сессия не задана!!! что конектимся к кукиясам - она в ДВ открывается
### поэтому все операции с сессией в файле ниже ДБ

##if request.is_https:
##    redirect(URL(args=request.args, vars=request.vars, scheme='http', host=True))

from gluon import current
current.PARTNER_MIN = PARTNER_MIN = 10
PARTNER_GO = 77
CACHE_EXP_TIME = request.is_local and 5 or 360

## app configuration made easy. Look inside private/appconfig.ini
from gluon.contrib.appconfig import AppConfig
## once in production, remove reload=True to gain full speed
myconf = AppConfig(reload=True)

DEVELOP = myconf.take('app.develop', cast=bool)
TO_BUY_ID = myconf.take('deals.buy')
TO_WALLET_ID = myconf.take('deals.wallet')
TO_COIN_ID = myconf.take('deals.coin')
TO_PHONE7_ID = myconf.take('deals.phone_7')

CURR_USD_ID = myconf.take('currs.usd_id')
CURR_RUB_ID = myconf.take('currs.rub_id')
CURR_BTC_ID = myconf.take('currs.btc_id')

TRUST_IP = myconf.take('app.trust_ip')


if DEVELOP: print '0.py - app.DEVELOP'

current.IS_LOCAL = IS_LOCAL = request.is_local
current.IS_MOBILE = IS_MOBILE = request.user_agent().is_mobile
current.IS_TABLET = IS_TABLET = request.user_agent().is_tablet


ADMIN = request.controller == 'appadmin'
##print ADMIN
SKIN = myconf['skin']

if request.ajax:
    pass
else:
    LANGS = {
        'ru': ['Русский', 'ru.png'],
        'en': ['English', 'gb.png'],
        'de': ['Deutsche ', 'de.png'],
        'tr': ['Türkçe', 'tr.png'],
    }
