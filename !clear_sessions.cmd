
set sleep=7200
set /a sleep3=%sleep%/3

:rep

c:\python27\python ..\..\web2py.py -S ipay -M -R scripts/sessions2trash.py -A -o -x %sleep% -f -v

timeout /t %sleep3%

rem restart walets if it crash
rem start "reload wallets" "..\wallets--spay\!!start_wallets.cmd" reload

goto rep

pause


goto end
@REM clear all errors/
@del /Q .\sessions\*
rem dir .\sessions\*
rem pause

:end