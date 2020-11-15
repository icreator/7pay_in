
set cmd=%1
if "%1"=="" set cmd=getbalance

"C:\Program Files\Dogecoin\daemon\dogecoin-cli.exe" -conf=%CD%\client.conf %cmd% %2 %3 %4 %5


pause