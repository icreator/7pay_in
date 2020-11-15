rem for icreator

set loc_ip=localhost
set app=ipay3

if "%2"=="" goto bal:

echo %1 : %2 >>log.txt
"C:\Program Files\bitcoin\daemon\bitcoin-cli.exe" -conf=client.conf sendtoaddress %1 %2 >>log.txt

rem update balance
..\..\curl.exe http://%loc_ip%:80/%app%/tools/block_proc/BTC -k

:bal

"C:\Program Files\bitcoin\daemon\bitcoin-cli.exe" -conf=client.conf getinfo
"C:\Program Files\bitcoin\daemon\bitcoin-cli.exe" -conf=client.conf getbalance

echo **** see TXID in log.txt

pause