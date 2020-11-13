rem for BTC-e

set loc_ip=localhost:80
set app=ipay3

if "%1"=="" goto bal:

rem update inputs with 1 confirms
..\..\curl.exe http://%loc_ip%/%app%/tools/block_proc/LTC -k

"C:\Program Files\Litecoin\daemon\litecoin-cli.exe" -conf=client.conf sendtoaddress L.............. %1 >>log.txt

rem update balance
..\..\curl.exe http://%loc_ip%/%app%/tools/block_proc/LTC -k
echo *** see TXID in log.txt

:bal
"C:\Program Files\Litecoin\daemon\litecoin-cli.exe" -conf=client.conf getbalance


pause