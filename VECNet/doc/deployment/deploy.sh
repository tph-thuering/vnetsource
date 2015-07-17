#!/bin/bash

# Application server for VecNet-CI project
# Deploy second virtual host to apache

if [ -z $VENV ]; then
VENV=nd.pro
fi
if [ -z $VHOST ]; then
VHOST=vecnet.org
fi
VDIR=/opt/vecnetsource/web/$VENV.$VHOST

echo "Checking output toolkit"
sudo svn co https://redmine.crc.nd.edu/svn/vecnetts/toolkit  /opt/toolkit
sudo mkdir -p "$VDIR"
sudo chown apache:adm "$VDIR"

echo "Checking output vnetsource trunk"
sudo svn co https://redmine.crc.nd.edu/svn/vnetsource/trunk "$VDIR"

echo $PATH
sudo chown apache:adm "$VDIR"
source /opt/python2.7/bin/virtualenvwrapper.sh
mkvirtualenv $VENV -p /opt/python2.7/bin/python2.7
workon $VENV
pip install -r "$VDIR/requirements.txt"

/opt/toolkit/update/update.sh $VENV

# Generate vhost for apache
python -c 'from string import Template; print Template(open("VECNet/deployment/vhost.template").read()).substitute(vhost="$VHOST",venv="$VENV")'

echo "TODO: "
echo "1. Create apache virtual host (see VECNet/deployment/vhost as an example)"
echo "2. Configure SSO"
echo "3. Configure SSL"
echo "4. Configure settings_local.py (see settings_local_example.py)"
