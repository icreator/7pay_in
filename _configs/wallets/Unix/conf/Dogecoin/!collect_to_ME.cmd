rem for icreator

set loc_ip=100.88.140.96
set app=shop

if "%1"=="" goto bal:

rem update inputs with 1 confirms
rem ..\..\curl.exe https://%loc_ip%/%app%/tools/block_proc/BTC -k

"C:\Program Files\Dogecoin\daemon\dogecoin-cli.exe" -conf=client.conf sendtoaddress 1........ %1


:bal

"C:\Program Files\Dogecoin\daemon\bitcoin-cli.exe" -conf=client.conf getinfo
"C:\Program Files\Dogecoin\daemon\bitcoin-cli.exe" -conf=client.conf getbalance


pause