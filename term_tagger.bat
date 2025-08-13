@echo off
set app=csv_term_tagger.exe
echo Invoking %app% "%1"
echo Please wait for the tagged CSV file to be created.
echo This may take a while depending on the size of the input file.
echo When done, %app% will drop the tagged file into your Documents folder.
%HOMEDRIVE%%HOMEPATH%\.local\bin\%app% "%1"
pause