rem for icreator

set loc_ip=100.88.140.96
set p=C:\Program Files\Dash
set cli=dash-cli.exe
set app=shop
set addr=X12

if "%1"=="" goto bal:

"%p%\%cli%" -datadir=d:\blockchains\Dash -conf=%CD%\client.conf sendtoaddress %addr%  %1

rem update balance
rem ..\..\curl.exe https://%loc_ip%/%app%/tools/block_proc/DSH -k

:bal

"%p%\%cli%" -datadir=d:\blockchains\Dash -conf=%CD%\client.conf getinfo
"%p%\%cli%" -datadir=d:\blockchains\Dash -conf=%CD%\client.conf getbalance


pause