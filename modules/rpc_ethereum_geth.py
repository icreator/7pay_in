#!/usr/bin/env python
# coding: utf8

import urllib2

from gluon import current
from decimal import Decimal
import decimal

from gluon.contrib import simplejson as json
import time

import db_common

PRECISION = 18


def log(db, mess):
    print 'rpc_ethereum_geth - ', mess
    db.logs.insert(mess='GETH: %s' % mess)


def log_commit(db, mess):
    log(db, mess)
    db.commit()


##
def rpc_request(rpc_url, method, params=[], test=None):
    ## curl -X POST --data '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":83}'

    if test:
        params['test_result'] = test

    headers = {'Content-Type': 'application/json'}

    # json.dumps() - ' -> "
    data = '{"method":"' + method + '", "jsonrpc": "2.0", "params":' + ('%s' % json.dumps(params)) + ', "id":1}'
    # return data
    rq = urllib2.Request(rpc_url, data, headers=headers)

    try:
        f = urllib2.urlopen(rq)
        # r = f.read()
        r = json.load(f)

        # print 'GETH response - res:', r
    except Exception as e:
        # или любая ошибка - повтор запроса - там должно выдать ОК
        # print 'YmToConfirm while EXEPTION:', e
        log(current.db, 'rpc ' + method + (' %s' % params) + ' EXCEPTION: %s' % e)
        return '%s' % e

    return r


def get_xcurr_by_system_token(db, token_system, token_key):
    try:
        token_key = int(token_key)
        if token_key is 1:
            ## ETH
            token = db((db.tokens.system_id == token_system.id)
                       & (db.tokens.token_key == token_key)).select().first()
            if not token:
                return

            return db(db.xcurrs.as_token == token.id).select().first()
    except:
        curr_out, xcurr, _ = db_common.get_currs_by_abbrev(db, token_key)
        return xcurr


def get_addresses(rpc_url):
    result = rpc_request(rpc_url, "eth_accounts")
    try:
        return result['result']
    except:
        return result

# eth.blockNumber should return the latest synced block number at all times
# see: https://github.com/ethereum/go-ethereum/issues/14338
def get_height(rpc_url):
    result = rpc_request(rpc_url, "eth_blockNumber")
    try:
        return int(result['result'], 16)
    except:
        return result


def is_not_valid_addr(rpc_url, address):
    result = rpc_request(rpc_url, "eth_getBalance", [address, "latest"])
    try:
        return result['error'] != None
    except:
        return False


## balances by token ID = [[0, balance]]
def get_assets_balances(token_system, address=None):
    result = get_balance(token_system, 1, address)
    try:
        return {
            '1': [[0, result]]  # ETH
        }
    except:
        return result


def get_balance(token_system, token=1, address=None):
    if token == 1:
        result = rpc_request(token_system.connect_url, "eth_getBalance", [address or token_system.account, "latest"])
        try:
            balance = long(result['result'], 16)
        except:
            return result

        ##  x WEI
        ##return dict(long=long(str, 16), decimal=Decimal(long(str, 16)), decimal18=Decimal(long(str, 16))*Decimal(1E-18))
        decimal.getcontext().prec = 18  # WEI
        balance = Decimal(balance) * Decimal(1E-18)
        if balance > 1E7:  ## in test network
            balance = Decimal(1E7)
        return balance
    else:
        return 0


## get transactions/unconfirmedincomes/7F9cZPE1hbzMT21g96U8E1EfMimovJyyJ7
def get_unconf_incomes(rpc_url, address):
    incomes = []
    try:
        for rec in get_block(rpc_url, 'pending'):
            if 'to' not in rec or 'value' not in rec or 'input' not in rec or rec['input'] == '0x' \
                    or 'from' not in rec or rec['to'] != address:
                continue

            rec['message'] = rec['input'][2:].decode('hex')

            incomes.append(rec)

        return incomes
    except Exception as e:
        print e
        log(current.db, 'get_transactions %s EXCEPTION: %s' % (rpc_url, e))
        return "%s" % e


def get_tx_info(rpc_url, txid):
    res = rpc_request(rpc_url, "eth_getTransactionReceipt", [txid])
    return res


def get_block(rpc_url, block):
    res = rpc_request(rpc_url, "eth_getBlockByNumber", ['int' == type(block) and ('%#x' % block) or block, True])
    return res


# for precess incomes in serv_block_proc
def parse_tx_fields(rec):
    decimal.getcontext().prec = 18
    return dict(
        creator=rec['from'],
        recipient=rec['to'],
        amount=Decimal(int(rec['value'], 16)) * Decimal(1E-18),
        asset=1,  ## ETH one
        message=rec['input'][2:].decode('hex'),
        txid=rec['hash'],
        vout=0,
        block=rec['block'],
        timestamp=rec['timestamp'],
        confs=rec['confirmations']
    )


def get_transactions(token_system, from_block=2):
    rpc_url = token_system.connect_url
    conf = token_system.conf
    addr = token_system.account

    result = []

    res = rpc_request(rpc_url, "eth_blockNumber")
    try:
        height = int(res['result'], 16)
    except Exception as e:
        return result, None

    i = from_block
    timestamp = time.time()
    tx_count = 0

    ## TODO + confirmed HARD
    while i + conf <= height:

        # for each block too
        tx_count += 5

        if len(result) > 100 or i - from_block > 10000:
            break

        if tx_count > 10000:
            tx_count = 0
            if time.time() - timestamp > 20:
                # if time of process more then 10 sec - break!
                break

        i += 1

        try:
            res = rpc_request(rpc_url, "eth_getBlockByNumber", ['%#x' % i, True])
            block = res['result']
            recs = block['transactions']
            recs_count = len(recs)
        except Exception as e:
            print e
            print res
            log(current.db, 'get_transactions %s EXCEPTION: %s - %s' % (rpc_url, e, res))
            return result, i - 1

        if recs_count > 0:
            # print 'geth incomes - height: ', i, ' recs:', len(recs)
            pass
        else:
            continue

        incomes = []
        for rec in recs:

            ++tx_count

            if 'to' not in rec or 'value' not in rec or 'input' not in rec or rec['input'] == '0x' \
                    or 'from' not in rec or rec['to'] != addr:
                continue

            rec['block'] = i,
            rec['timestamp'] = int(block['timestamp'], 16)
            rec['confirmations'] = height - i
            rec['message'] = rec['input'][2:].decode('hex')

            incomes.append(rec)
            # print 'geth: ', rec

        result += incomes

    return result, i


## for Unlock: 	{"method": "personal_unlockAccount", "params": [string, string, number]}
def send(db, curr, xcurr, toAddr, amo, token_system, token=None, mess=None, sender=None, password=None):
    rpc_url = token_system.connect_url
    sender = sender or token_system.account
    txfee = token_system.txfee

    try:
        balance = get_balance(token_system, address=sender)
        # return balance
    except Exception as e:
        return {'error': 'connection lost - [%s]' % curr.abbrev}, None

    ##return dict(txfee=txfee, amo=amo, reserve=reserve)

    if amo + txfee > balance:
        return {'error': 'out off reserve:[%s]' % balance}, None

    decimal.getcontext().prec = 18  # WEI
    amo = amo

    # проверим готовность базы - is lock - и запишем за одно данные
    log_commit(db, 'try send: %s[%s] %s, fee: %s' % (amo, curr.abbrev, toAddr, txfee))
    if amo > txfee * 2:
        try:
            ##amo_to_pay = amo - txfee - it already inserted in GET_RATE by db.currs
            amo_to_pay = amo  # - txfee
            ## print 'res = geth.send(addr, amo - txfee)', amo_to_pay

            txfee = long(txfee * Decimal(1E10))  ## and x 1+E10 by gasPrice
            amo_to_pay = long(amo_to_pay * Decimal(1E18))  ## in WEI

            params = [{
                "from": sender,
                "to": toAddr,
                "value": '%#x' % amo_to_pay,
                "gas": '%#x' % txfee,
                "gasPrice": '%#x' % 1E11
            }]

            if mess:
                params[0]['data'] = '0x' + (mess.encode("hex"))

            ## print 'GETH', params

            if password:
                ## если это не основной счет в кошельке а сгенерированный с паролем - тонадо его UNLOCK
                res = rpc_request(rpc_url, "personal_unlockAccount", [sender, password, 3])
                if 'error' in res:
                    return res, balance

            res = rpc_request(rpc_url, "eth_sendTransaction", params)
            try:
                res = res['result']
            except Exception as e:
                return res, None

            if res == "0x0":
                # some error
                return {'error': ("%s" % res) + ' [%s]' % curr.abbrev}, None


        except Exception as e:
            error_message = current.CODE_UTF and str(e).decode(current.CODE_UTF, 'replace') or str(e)
            return {'error': error_message + ' [%s]' % curr.abbrev}, None
    else:
        # тут mess для того чтобы обнулить выход и зачесть его как 0
        res = {'mess': '< txfee', 'error': 'so_small', 'error_description': '%s < txfee %s' % (amo, txfee)}

    bal = get_balance(token_system, address=sender)

    return res, bal
