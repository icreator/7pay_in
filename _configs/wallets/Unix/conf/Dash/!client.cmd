
set cmd=%1
if "%1"=="" set cmd=getbalance

"C:\Program Files\Dash\dash-cli.exe" -datadir=d:\blockchains\Dash -conf=%CD%\client.conf %cmd%


pause