@echo off
timeit -begin

:: NOTE(fuzes): Parsing the command line arguments
set buildType=%1
if "%buildType%"=="" (set buildType=Debug)

set mayaVersion=%2
if "%mayaVersion%"=="" (set mayaVersion=2017)

set projectName=debugDraw

set outputName=%projectName%.mll
set debugName=%projectName%.pdb
set hostEntryPoint=..\..\code\plugin.cpp
if "%buildType%"=="Release" (
	set hostEntryPoint=..\..\..\code\plugin.cpp
)
set mayaBasePath=C:/Program Files/Autodesk/Maya%mayaVersion%
if "%mayaVersion%"=="2017" (
	::set visualStudioLibPaths="C:/Program Files (x86)/Microsoft Visual Studio 11.0\VC\lib\amd64"
	set visualStudioLibPaths="C:\Program Files (x86)\Microsoft Visual Studio\2017\Community\VC\Tools\MSVC\14.15.26726\lib\x64"
) else (
	set visualStudioLibPaths="C:/Program Files (x86)/Microsoft Visual Studio 14.0\VC\lib\amd64"
)

:: NOTE(fuzes): Compiler Flags
set commonCompilerFlags=/nologo /Oi /FC /c /EHsc /EHa- -wd4505 /DMAYA%mayaVersion% /DCOMMAND_LINE=1 /W4 /wd4100 /wd4189

set commonCompilerFlags=%commonCompilerFlags% /I"%mayaBasePath%/include"

set commonCompilerFlagsDebug=/Z7 /Od %commonCompilerFlags%
set commonCompilerFlagsRelease=/O2 %commonCompilerFlags%

set commonCompilerFlagsHostDebug=%commonCompilerFlagsDebug% %hostEntryPoint%
set commonCompilerFlagsHostRelease=%commonCompilerFlagsRelease% %hostEntryPoint%

:: NOTE(fuzes): Linker flags
set commonLinkerFlags=/DLL /OPT:REF /NOLOGO /MACHINE:X64
:: Same here for the lib include paths should change depending on the version
set commonLinkerFlags=%commonLinkerFlags% /LIBPATH:"%mayaBasePath%/lib" /LIBPATH:%visualStudioLibPaths%
set commonLinkerFlags=%commonLinkerFlags% Foundation.lib OpenMaya.lib OpenMayaAnim.lib OpenMayaUI.lib OpenMayaRender.lib OpenMayaFX.lib odbccp32.lib odbc32.lib opengl32.lib

set commonLinkerFlagsDebug= /DEBUG %commonLinkerFlags%
set commonLinkerFlagsRelease=%commonLinkerFlags%

set entryPointPath=plugin.obj

::  /PDB:%debugName%
set commonLinkerFlagsHostDebug=%commonLinkerFlagsDebug% %entryPointPath% /OUT:%outputName%
set commonLinkerFlagsHostRelease=%commonLinkerFlagsRelease% %entryPointPath% /OUT:%outputName%

if not exist ..\build mkdir ..\build
if not exist ..\build\%buildType% mkdir ..\build\%buildType%

if "%buildType%"=="Debug" (
	pushd ..\build\%buildType%
	set compilerFlags=%commonCompilerFlagsHostDebug%
	
	set linkerFlags=%commonLinkerFlagsHostDebug%

) else (
	
	if not exist ..\build\%buildType%\%mayaVersion% mkdir ..\build\%buildType%\%mayaVersion%
	pushd ..\build\%buildType%\%mayaVersion%
	
	set compilerFlags=%commonCompilerFlagsHostRelease%
	
	set linkerFlags=%commonLinkerFlagsHostRelease%
)


cl %compilerFlags%
link %linkerFlags%
echo -------------- Build Info --------------
echo Maya: %mayaVersion%
echo Type: %buildType%
echo Path: %CD%\%outputName%
popd
timeit -end
echo.
echo ----------------------------------------



