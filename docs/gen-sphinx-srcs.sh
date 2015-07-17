#!/bin/bash

# Use sphinx-apidoc to automatically generate the Sphinx source files for
# various Python packages (including Django applications).  Only those
# packages without their own documentation sources are processed.

cmd_line_error() {
  echo "Error: $1"
  echo
  echo "Usage: $0 [ -f | --force ]"
  exit 1
}

overwrite=0
case "$1" in
  '') ;;
  --force | -f) overwrite=1 ;;
  -*) cmd_line_error "unknown option: $1" ;;
  *) cmd_line_error "unknown argument: $1" ;;
esac

PACKAGES="autoscotty VECNet cifer data_services datawarehouse \
          expert_openmalaria lib pie risk_mapper survey \
          transmission_simulator ts_emod"

PACKAGES_RST=modules/packages.rst
if [ $overwrite == 1 ] ; then
    rm -f $PACKAGES_RST
    options=--force
else
    options=
fi

for pkg in $PACKAGES ; do
    echo "Generating Sphinx source files for ../$pkg/ package ..."
    sphinx-apidoc -o modules --no-toc $options ../$pkg
done

if [ ! -f $PACKAGES_RST ] ; then
    cat > $PACKAGES_RST <<-EOT
	Packages
	========

	.. toctree::
	   :maxdepth: 3

	EOT
    for pkg in $PACKAGES ; do
        echo "   $pkg" >> $PACKAGES_RST
    done
    echo "Created $PACKAGES_RST"
fi
