# -*- coding: utf-8 -*-
if False:
    from gluon import *
    request = current.request
    response = current.response
    session = current.session
    cache = current.cache
    T = current.T
    db = None

if not IS_LOCAL: raise HTTP(200, 'error')
session.forget(response)

from decimal import Decimal
import db_common, crypto_client, rpc_ethereum_geth

def index(): return dict(message="hello from tool_xcurr.py")

# get Address of wallet
def addrs():

    curr, xcurr, e = db_common.get_currs_by_abbrev(db, 'ETH')
    if not xcurr:
        return 'xcurr not found'

    json = rpc_ethereum_geth.rpc_request(xcurr.connect_url, 'eth_accounts')
    return BEAUTIFY(json)

# Test balance for Address
def bal_for_addrs():

    curr, xcurr, e = db_common.get_currs_by_abbrev(db, 'ETH')
    if not xcurr:
        return 'xcurr not found'

    if request.args(0):
        address = request.args(0)
    else:
        json = rpc_ethereum_geth.rpc_request(xcurr.connect_url, 'eth_accounts')
        address = json.result[0]

    res = rpc_ethereum_geth.get_balances(xcurr.connect_url, address)

    return BEAUTIFY(res)
