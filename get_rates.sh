#!/bin/sh

(/usr/bin/python /opt/web-apps/web2py/web2py.py -S 7pay_in -M -R applications/7pay_in/modules/serv_rates.py -A True 300 &)
