#Development environment setup

##Windows 7 x64
1. It is recommended to install [Visual Studio 2008 Express Edition](http://www.microsoft.com/en-us/download/details.aspx?id=7873) (python 2.7 was built using
2008 version).

2. Install libraries in VECNet/windows folder:
   * GDAL 1.9 (Note: GDAL 1.10 doesn't work with GeoDjango on Windows x64 for unknown reason)
   * LXML 3.3.6
   * Psycopg-2.5.4

   If necessary, newer versions can be downloaded at:
   * [GDAL](http://www.gisinternals.com/release.php)
   * [LXML](http://www.lfd.uci.edu/~gohlke/pythonlibs/#lxml)
   * [Psycopg](http://www.stickpeople.com/projects/python/win-psycopg/)

	If you get an error message like this:
	> ImproperlyConfigured: Could not import user-defined GEOMETRY_BACKEND "geos".

	then you may need to create a local settings file to accommodate this. The file should be called **settings_local.py**
	inside of the VECNet folder. In this file, type: 
	```
	GEOS_LIBRARY_PATH = "C:\\Program Files\\GDAL\\geos_c.dll"
	```

3. Install python packages required to run vecnet-ci project
   ```
   pip install -r requirements.txt
   ```

##CentOS/RedHat 6
*Note*: that VecNet-CI project requires python 2.**7**. It should be compiled from source on RedHat 6.x systems

*Note*: gdal in ELGIS repository is broken currently. It depends on libarmadillo.so.3, and this library has been
deprecated in EPEL repository and replaced with libarmadillo.so.4. Simply recompiling package should fix it, but this
fix should be promoted to ELGIS somehow.
gdal-1.9.2-5.el6.x86_64.rpm in VECNet\linux may work. Alternatively, skip yum install gdal for now

```bash
sudo yum install http://elgis.argeo.org/repos/6/elgis-release-6-6_0.noarch.rpm
sudo yum install http://download.fedoraproject.org/pub/epel/6/i386/epel-release-6-8.noarch.rpm
sudo yum install -y geos
sudo yum install gdal
sudo yum install -y libxml2 libxml2-devel libxslt libxslt-devel
sudo yum install postgresql-libs postgresql-devel
pip  install -r requirements.txt
```

##CentOS/RedHat 7
Note that ELGIS repository doesn't support CentOS/RedHat 7. However, GDAL has been backported to EPEL repository, so it
is no longer needed.

```bash
sudo yum -y install python-devel libjpeg-devel zlib-devel
sudo yum install  http://mirror.vcu.edu/pub/gnu_linux/epel/7/x86_64/e/epel-release-7-5.noarch.rpm
sudo yum install -y gdal
sudo yum install -y libxml2 libxml2-devel libxslt libxslt-devel postgresql-libs postgresql-devel
pip  install -r requirements.txt
```

*Note*: If running on VM, make sure that the django.log file has proper permissions to write to.

##Ubuntu
*Note*: It is necesary to install development tools (gcc) first.
```bash
sudo apt-get install build-essential
sudo apt-get install binutils libproj-dev gdal-bin
sudo apt-get install libxml2-dev libxslt-dev python-pip
pip install -r requirements.txt
   ```

##MAC OS X
1. Use the "GDAL 1.11 Complete" installer from [Kyng Chaos](http://www.kyngchaos.com/software/frameworks).
    To install the GDAL Python bindings to a virtualenv (if desired), add a path file, gdal.pth, to the virtualenv site-packages
    with the contents (for OS X):

	```python
    >>> import sys
    >>> sys.path.insert(0,'/Library/Frameworks/GDAL.framework/Versions/1.9/Python/2.7/site-packages')
	```

    This adds the python bindings that were built with GDAL to the virtualenv Python path on
    activation.  Adjust the path as needed.

2. Install [LXML library](http://lxml.de/build.html#building-lxml-on-macos-x):

	```bash
    $ STATIC_DEPS=true sudo pip install lxml
	```

    *Note*: this will download and build dependencies like libxml2 and libxslt

3. Install postgreSQL:

    Some versions of OS X may require that you install postgreSQL manually.
    To do so, you will need a package manager like [Homebrew](http://brew.sh)
    or [MacPorts](https://www.macports.org).

	```bash
    $ brew install postgresql
	```

4. Install project requirements:

	```bash
    $ sudo pip install -r requirements.txt
	```
