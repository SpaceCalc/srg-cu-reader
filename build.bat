pyinstaller ^
--onefile --windowed ^
--specpath spec ^
--distpath spec/dist ^
--workpath spec/build ^
--name srg-cu-reader.exe ^
--icon ../icon.ico ^
app.py
