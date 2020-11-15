
@echo off
rem тут первая строка с кодировкой UTF-8 как команда вставет - не обращаем внимания


set app=ipay3

if NOT "%3"=="test" @echo off
set to_out=!notify_log.txt
if "%3"=="test" set to_out=con

rem запуск обработки блока но не чаще чем указано в timeout
rem это нужно чтобы при загрузке цепочки блоков не было кучи вызовов этой команды

rem keys: -s silent

rem check on run process
c:
cd C:\web2py-m\applications\wallets--spay
if exist .lock_%1 exit
REM. > .lock_%1

rem echo ---- %to_out%
rem echo wert

time /T >>%to_out%
echo %1 %2 %3 %4 >>%to_out%

rem public IP - 137.117.132.51
rem local IP - 100.88.128.24 - for admin tools

rem обработка блоков для данной валюты - находим входящие транзакции на счета кошелька
rem start /B /LOW /MIN curl http://127.0.0.1:80/%app%/tools/block_proc/%1/%2 -s >>!notify_log.txt
rem curl http://127.0.0.1:80/%app%/tools/block_proc/%1/%2
rem start /B /LOW /MIN curl http://localhost:90/%app%/tools/block_proc/%1/%2 -k >>%to_out%

rem echo wert

rem https://www.7pay.in/%app%/tools/block_proc/BTC
rem start /B /LOW /MIN curl https://www.7pay.in/%app%/tools/block_proc/%1/%2 -k >>!notify_log.txt
rem start /B /LOW /MIN curl https://100.88.128.24/%app%/tools/block_proc/%1/%2 -k >>!notify_log.txt
rem сейчас можно по локалхост без ссл заходить на порт 90
rem start /B /LOW /MIN curl_nossl http://localhost:90/%app%/tools/block_proc/%1/%2 -k >>!notify_log.txt

rem start /B /LOW /MIN curl_nossl http://localhost:90/%app%/tools/block_proc/%1/%2 --connect-timeout 7 -m 7 --no-keepalive --no-sessionid -j >>%to_out%
rem curl_nossl http://localhost:90/%app%/tools/block_proc/%1/%2 --connect-timeout 30 -m 100 --no-keepalive --no-sessionid -j >>%to_out%
curl_nossl http://localhost:80/%app%/tools/block_proc/%1/%2 --connect-timeout 60 -m 100 --no-keepalive --no-sessionid -j >>%to_out%


rem tak kak esli proverka platega Yandex visit 30sec
rem to moget 2-j blok_proc zapustit OPLATU eche raz ((
if NOT "%3"=="test" timeout /t 40

echo _ >>!notify_log.txt
del .lock_%1 >nul

if NOT "%3"=="test" exit
if "%3"=="test" pause

