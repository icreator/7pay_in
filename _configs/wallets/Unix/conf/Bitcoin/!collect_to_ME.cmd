rem for icreator

set loc_ip=localhost
set app=ipay
set n=bitcoin
set p=C:\Program Files\Bitcoin\daemon
set e=%n%-cli

if "%1"=="" goto bal:

"%p%\%e%.exe" -conf=client.conf sendtoaddress 1......... %1

rem update balance
..\..\curl.exe http://%loc_ip%/%app%/tools/block_proc/BTC -k

:bal

"%p%\%e%.exe" -conf=client.conf getinfo
"%p%\%e%.exe" -conf=client.conf getbalance


pause