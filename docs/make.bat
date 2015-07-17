@ECHO OFF

REM Command file for Sphinx documentation

if "%SPHINXBUILD%" == "" (
	set SPHINXBUILD=sphinx-build
)
set BUILDDIR=_build
set SPHINXOPTS=%SPHINXOPTS% -c .
set ALLSPHINXOPTS=-d %BUILDDIR%/doctrees %SPHINXOPTS%
set I18NSPHINXOPTS=%SPHINXOPTS%
if NOT "%PAPER%" == "" (
	set ALLSPHINXOPTS=-D latex_paper_size=%PAPER% %ALLSPHINXOPTS%
	set I18NSPHINXOPTS=-D latex_paper_size=%PAPER% %I18NSPHINXOPTS%
)
set SOURCEDIR=..

if "%1" == "" goto help

if "%1" == "help" (
	:help
	echo.Please use `make ^<target^>` where ^<target^> is one of
	echo.  html       to make standalone HTML files
	echo.  dirhtml    to make HTML files named index.html in directories
	echo.  singlehtml to make a single large HTML file
	echo.  pickle     to make pickle files
	echo.  json       to make JSON files
	echo.  htmlhelp   to make HTML files and a HTML help project
	echo.  qthelp     to make HTML files and a qthelp project
	echo.  devhelp    to make HTML files and a Devhelp project
	echo.  epub       to make an epub
	echo.  latex      to make LaTeX files, you can set PAPER=a4 or PAPER=letter
	echo.  text       to make text files
	echo.  man        to make manual pages
	echo.  texinfo    to make Texinfo files
	echo.  gettext    to make PO message catalogs
	echo.  changes    to make an overview over all changed/added/deprecated items
	echo.  xml        to make Docutils-native XML files
	echo.  pseudoxml  to make pseudoxml-XML files for display purposes
	echo.  linkcheck  to check all external links for integrity
	echo.  doctest    to run all doctests embedded in the documentation if enabled
	echo.  clean      to clean out the build directory: %BUILDDIR%
	echo.  clean-all  to clean out the build and modules directories
	echo.  wc-rev     to store Subversion revision info for project's working copy
	echo.  apidoc     to run sphinx-apidoc for Python packages with no sphinx sources
	echo.  apidoc-ow  to run 'apidoc' target so it overwrites existing sphinx sources
	goto end
)

if "%1" == "clean" (
    :clean
	for /d %%i in (%BUILDDIR%\*) do rmdir /q /s %%i
	del /q /s %BUILDDIR%\*
	goto end
)

if "%1" == "clean-all" (
	del /q modules\*.rst
	goto clean
)


%SPHINXBUILD% 2> nul
if errorlevel 9009 (
	echo.
	echo.The 'sphinx-build' command was not found. Make sure you have Sphinx
	echo.installed, then set the SPHINXBUILD environment variable to point
	echo.to the full path of the 'sphinx-build' executable. Alternatively you
	echo.may add the Sphinx directory to PATH.
	echo.
	echo.If you don't have Sphinx installed, grab it from
	echo.http://sphinx-doc.org/
	exit /b 1
)

if "%1" == "apidoc" (
	echo.ERROR: This target has not been implemented yet for Windows.
	exit /b 1
)

if "%1" == "apidoc-ow" (
	echo.ERROR: This target has not been implemented yet for Windows.
	exit /b 1
)


if "%1" == "html" (
	call :wc_rev
	%SPHINXBUILD% -b html %ALLSPHINXOPTS% %SOURCEDIR% %BUILDDIR%/html
	if errorlevel 1 exit /b 1
	echo.
	echo.Build finished. The HTML pages are in %BUILDDIR%/html.
	goto end
)

if "%1" == "dirhtml" (
	call :wc_rev
	%SPHINXBUILD% -b dirhtml %ALLSPHINXOPTS% %SOURCEDIR% %BUILDDIR%/dirhtml
	if errorlevel 1 exit /b 1
	echo.
	echo.Build finished. The HTML pages are in %BUILDDIR%/dirhtml.
	goto end
)

if "%1" == "singlehtml" (
	call :wc_rev
	%SPHINXBUILD% -b singlehtml %ALLSPHINXOPTS% %SOURCEDIR% %BUILDDIR%/singlehtml
	if errorlevel 1 exit /b 1
	echo.
	echo.Build finished. The HTML pages are in %BUILDDIR%/singlehtml.
	goto end
)

if "%1" == "pickle" (
	call :wc_rev
	%SPHINXBUILD% -b pickle %ALLSPHINXOPTS% %SOURCEDIR% %BUILDDIR%/pickle
	if errorlevel 1 exit /b 1
	echo.
	echo.Build finished; now you can process the pickle files.
	goto end
)

if "%1" == "json" (
	call :wc_rev
	%SPHINXBUILD% -b json %ALLSPHINXOPTS% %SOURCEDIR% %BUILDDIR%/json
	if errorlevel 1 exit /b 1
	echo.
	echo.Build finished; now you can process the JSON files.
	goto end
)

if "%1" == "htmlhelp" (
	call :wc_rev
	%SPHINXBUILD% -b htmlhelp %ALLSPHINXOPTS% %SOURCEDIR% %BUILDDIR%/htmlhelp
	if errorlevel 1 exit /b 1
	echo.
	echo.Build finished; now you can run HTML Help Workshop with the ^
.hhp project file in %BUILDDIR%/htmlhelp.
	goto end
)

if "%1" == "qthelp" (
	call :wc_rev
	%SPHINXBUILD% -b qthelp %ALLSPHINXOPTS% %SOURCEDIR% %BUILDDIR%/qthelp
	if errorlevel 1 exit /b 1
	echo.
	echo.Build finished; now you can run "qcollectiongenerator" with the ^
.qhcp project file in %BUILDDIR%/qthelp, like this:
	echo.^> qcollectiongenerator %BUILDDIR%\qthelp\VECNet-CI.qhcp
	echo.To view the help file:
	echo.^> assistant -collectionFile %BUILDDIR%\qthelp\VECNet-CI.ghc
	goto end
)

if "%1" == "devhelp" (
	call :wc_rev
	%SPHINXBUILD% -b devhelp %ALLSPHINXOPTS% %SOURCEDIR% %BUILDDIR%/devhelp
	if errorlevel 1 exit /b 1
	echo.
	echo.Build finished.
	goto end
)

if "%1" == "epub" (
	call :wc_rev
	%SPHINXBUILD% -b epub %ALLSPHINXOPTS% %SOURCEDIR% %BUILDDIR%/epub
	if errorlevel 1 exit /b 1
	echo.
	echo.Build finished. The epub file is in %BUILDDIR%/epub.
	goto end
)

if "%1" == "latex" (
	call :wc_rev
	%SPHINXBUILD% -b latex %ALLSPHINXOPTS% %SOURCEDIR% %BUILDDIR%/latex
	if errorlevel 1 exit /b 1
	echo.
	echo.Build finished; the LaTeX files are in %BUILDDIR%/latex.
	goto end
)

if "%1" == "latexpdf" (
	call :wc_rev
	%SPHINXBUILD% -b latex %ALLSPHINXOPTS% %SOURCEDIR% %BUILDDIR%/latex
	cd %BUILDDIR%/latex
	make all-pdf
	cd %BUILDDIR%/..
	echo.
	echo.Build finished; the PDF files are in %BUILDDIR%/latex.
	goto end
)

if "%1" == "latexpdfja" (
	call :wc_rev
	%SPHINXBUILD% -b latex %ALLSPHINXOPTS% %SOURCEDIR% %BUILDDIR%/latex
	cd %BUILDDIR%/latex
	make all-pdf-ja
	cd %BUILDDIR%/..
	echo.
	echo.Build finished; the PDF files are in %BUILDDIR%/latex.
	goto end
)

if "%1" == "text" (
	call :wc_rev
	%SPHINXBUILD% -b text %ALLSPHINXOPTS% %SOURCEDIR% %BUILDDIR%/text
	if errorlevel 1 exit /b 1
	echo.
	echo.Build finished. The text files are in %BUILDDIR%/text.
	goto end
)

if "%1" == "man" (
	call :wc_rev
	%SPHINXBUILD% -b man %ALLSPHINXOPTS% %SOURCEDIR% %BUILDDIR%/man
	if errorlevel 1 exit /b 1
	echo.
	echo.Build finished. The manual pages are in %BUILDDIR%/man.
	goto end
)

if "%1" == "texinfo" (
	call :wc_rev
	%SPHINXBUILD% -b texinfo %ALLSPHINXOPTS% %SOURCEDIR% %BUILDDIR%/texinfo
	if errorlevel 1 exit /b 1
	echo.
	echo.Build finished. The Texinfo files are in %BUILDDIR%/texinfo.
	goto end
)

if "%1" == "gettext" (
	call :wc_rev
	%SPHINXBUILD% -b gettext %I18NSPHINXOPTS% %SOURCEDIR% %BUILDDIR%/locale
	if errorlevel 1 exit /b 1
	echo.
	echo.Build finished. The message catalogs are in %BUILDDIR%/locale.
	goto end
)

if "%1" == "changes" (
	call :wc_rev
	%SPHINXBUILD% -b changes %ALLSPHINXOPTS% %SOURCEDIR% %BUILDDIR%/changes
	if errorlevel 1 exit /b 1
	echo.
	echo.The overview file is in %BUILDDIR%/changes.
	goto end
)

if "%1" == "linkcheck" (
	call :wc_rev
	%SPHINXBUILD% -b linkcheck %ALLSPHINXOPTS% %SOURCEDIR% %BUILDDIR%/linkcheck
	if errorlevel 1 exit /b 1
	echo.
	echo.Link check complete; look for any errors in the above output ^
or in %BUILDDIR%/linkcheck/output.txt.
	goto end
)

if "%1" == "doctest" (
	call :wc_rev
	%SPHINXBUILD% -b doctest %ALLSPHINXOPTS% %SOURCEDIR% %BUILDDIR%/doctest
	if errorlevel 1 exit /b 1
	echo.
	echo.Testing of doctests in the sources finished, look at the ^
results in %BUILDDIR%/doctest/output.txt.
	goto end
)

if "%1" == "xml" (
	call :wc_rev
	%SPHINXBUILD% -b xml %ALLSPHINXOPTS% %SOURCEDIR% %BUILDDIR%/xml
	if errorlevel 1 exit /b 1
	echo.
	echo.Build finished. The XML files are in %BUILDDIR%/xml.
	goto end
)

if "%1" == "pseudoxml" (
	call :wc_rev
	%SPHINXBUILD% -b pseudoxml %ALLSPHINXOPTS% %SOURCEDIR% %BUILDDIR%/pseudoxml
	if errorlevel 1 exit /b 1
	echo.
	echo.Build finished. The pseudo-XML files are in %BUILDDIR%/pseudoxml.
	goto end
)

echo.Error: Unknown target: "%1"
echo.Enter "make help" to see a list of available targets.
exit /b 1

:wc_rev
	svnversion > svnversion.out
	echo.Created svnversion.out file
	type svnversion_out
	goto end

:end
