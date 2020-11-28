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

    token_key = xcurr.as_token
    token = db.tokens[token_key]
    token_system = db.systems[token.system_id]

    res = rpc_ethereum_geth.get_balance(token_system, address)

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

def add_system():

    name = 'ethereum'
    system_id = db.systems.insert(name='Ethereum', name2=name, first_char='0x',
                                  connect_url='http://localhost:8545',  # for Testnet use http://127.0.0.1:9068
                                  password='123456789',
                                  block_time=60, conf=2, conf_gen=64,
                                  from_block=1000000  # for Testnet use 0
                                  )
    for asset in [
        [1, 'ETH']
    ]:
        token_id = db.tokens.insert(system_id=system_id, token_key=asset[0], name=asset[1])
        curr_id = db.currs.insert(abbrev=asset[1], name=asset[1], name2=asset[1], used=True)
        db.xcurrs.insert(curr_id=curr_id, protocol='', connect_url=name + ' ' + asset[1],
                         as_token=token_id,
                         block_time=0, txfee=0, conf=0, conf_gen=0)
