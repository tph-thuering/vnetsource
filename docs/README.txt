Sphinx (http://sphinx-doc.org/) is required to generate the project's
documentation.

If building the documentation for the first time in a working copy,
then run these commands in this docs folder:

    make apidoc
    make html

To rebuild the documentation after editing a Sphinx source file, just
enter this command:

    make html


Auto-generated Sphinx source files
----------------------------------

The apidoc target automatically generates Sphinx source files for
packages listed in the gen-sphinx-srcs.sh shell script (see the
PACKAGES variable).  These auto-generated .rst files are placed in
modules/ subfolder.  There is one .rst file for each module in a
package.  For example, if the foo package has two modules, bar and
qux, then their auto-generated Sphinx files would be:

    docs/
        modules/
            foo.bar.rst
            foo.qux.rst
            foo.rst


Custom Sphinx source files
--------------------------

To replace the auto-generated Sphinx source files for a package, do
the following:

  1) Run "make apidoc" if you haven't already.

  2) Remove the package's name from the PACKAGES variable in the
     gen-sphinx-srcs.sh script.

  3) Copy the auto-generated *.rst files for the package from
     modules/ subfolder into the package's own folder.  You'll want
     to rename the files since they don't need to have the full
     module names in them.  You can choose to put them in the
     package's root folder, or into a docs/subfolder, for example:

         foo/
             docs/
                 index.rst  <-- copy of docs/modules/foo.rst
                 bar.rst    <-- copy of docs/modules/foo.bar.rst
                 qux.rst    <-- copy of docs/modules/foo.qux.rst

  4) Edit the docs/index.rst, and add an entry to the toctree
     directive.  The top entry is the auto-generated package
     documentation:

        modules/packages

     Leave that entry as the first one.  Add an entry for your
     package after it, for example:

        modules/packages
        foo/docs/index.rst

     or if your package has a single .rst file:

        modules/packages
        foo/doc.rst

  5) Customize the package's documentation by editing its *.rst
     files.


__init__ Methods
----------------

By default, the autoclass directive only includes the docstring for
the class itself.  The :members: option only includes public members
of the class (whose names do not start with an underscore).  To
include a special method like __init__, add the :special-members:
option.  For example,

    .. autoclass:: my.Class
                   :special-members: __init__
                   :members:
