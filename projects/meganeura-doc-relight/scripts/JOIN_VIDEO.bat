@echo off
title Join video parts
cd /d "%~dp0"
set "OUT=Documentary_v3_no_chapters.mp4"
set "EXPECTED=1290432964"
echo.
echo  Joining the 4 parts into %OUT% ...
echo  (put this file and all 4 parts .001 .002 .003 .004 in the same folder)
echo.
for %%P in (001 002 003 004) do (
  if not exist "%OUT%.%%P" (
    echo  MISSING: %OUT%.%%P  - download all 4 parts into this folder first.
    echo.
    pause
    exit /b 1
  )
)
copy /b "%OUT%.001"+"%OUT%.002"+"%OUT%.003"+"%OUT%.004" "%OUT%" >nul
for %%A in ("%OUT%") do set "SIZE=%%~zA"
echo.
if "%SIZE%"=="%EXPECTED%" (
  echo  DONE. %OUT% is complete: full quality, 1080p, 14:35.
  echo  You can delete the 4 part files now.
) else (
  echo  Something went wrong: the joined file is %SIZE% bytes, expected %EXPECTED%.
  echo  Re-download the parts and run this again.
)
echo.
pause
