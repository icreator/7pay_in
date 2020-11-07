#!/bin/sh

(python /home/www-data/web2py/web2py.py -S 7pay_in -M -R applications/7pay_in/modules/serv_rates.py -A True 60 &)
