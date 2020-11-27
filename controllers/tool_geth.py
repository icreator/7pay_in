# -*- coding: utf-8 -*-

if False:
    from gluon import *
    import db
    request = current.request
    response = current.response
    session = current.session
    cache = current.cache
    T = current.T

## if not IS_LOCAL: raise HTTP(200, 'error')
session.forget(response)

from decimal import Decimal
import db_common, rpc_ethereum_geth

def index(): return dict(message="hello from tool_xcurr.py")

# get Address of wallet
def addrs():

    curr, xcurr, e = db_common.get_currs_by_abbrev(db, 'ETH')
    if not xcurr:
        return 'xcurr not found'

    json = rpc_ethereum_geth.rpc_request(xcurr.connect_url, 'eth_accounts')
    #return xcurr.connect_url + (' %s' % json)
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
        address = json['result'][0]

    res = rpc_ethereum_geth.get_balance(xcurr.connect_url, address)

    return BEAUTIFY(res)

def send():
    curr, xcurr, e = db_common.get_currs_by_abbrev(db, 'ETH')
    if not xcurr:
        return 'xcurr not found'

    if request.args(0):
        toAddress = request.args(0)
    else:
        toAddress = '0xd46e8dd67c5d32be8058bb8eb970870f07244567'

    res, bal = rpc_ethereum_geth.send(db, curr, xcurr, toAddress, Decimal(0.01), mess=None)

    return BEAUTIFY(dict(res=res, bal=bal))

def block():
    curr, xcurr, e = db_common.get_currs_by_abbrev(db, 'ETH')
    if not xcurr:
        return 'xcurr not found'

    if request.args(0):
        block = request.args(0)
    else:
        block = '0x1'

    return BEAUTIFY(rpc_ethereum_geth.get_block(xcurr.connect_url, block))

def enhex():
    if request.args(0):
        return request.args(0).encode("hex")
    return '0x' + (u'ETH from erachain.org stablecoin'.encode("hex"))

def dehex():
    if request.args(0):
        return request.args(0)[2:].decode("hex")
    return u'ETH from erachain.org stablecoin'.encode("hex").decode("hex")

