rem locasl clearing...
rem ----- start !clear_sessions.cmd
rem start !clear_errors.cmd

set pp=%CD%
cd ..\wallets--spay
start !!start_wallets.cmd

rem Clear for POLZA
rem ------ cd ..\polza
rem ------ start !clear_sessions.cmd
rem start !clear_errors_sessions.cmd

cd %pp%

timeout /t 10

set prog=web2py.py
set app=ipay
set not_local=True
set interval=10
set interval60=60


:rep
c:\python27\python ..\..\%prog% -S %app% -M -R applications/%app%/modules/serv_rates.py -A %not_local% %interval60%


timeout /t 30
goto rep

pause