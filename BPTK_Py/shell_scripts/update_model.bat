@ECHO OFF
REM PARAMS: SCRIPT_HOME IN OUT
SET CURRENT_HOME=%cd%
REM ARg1: Path of sd-compile
set arg1=%1
REM arg2: Path of source model
set arg2=%2
REM arg3: Path of final python model
set arg3=%3
cd "%arg1%"

"C:\Program Files\nodejs\node" -r babel-register src\cli.js -i "%CURRENT_HOME%\%arg2%" -t py -c > "%CURRENT_HOME%\%arg3%"