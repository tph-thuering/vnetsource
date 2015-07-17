class Version(object):
    """
    This is the programmatic interface for the VecNet data services module
    """

    def __init__(self, major, minor):
        """
        Here we set the major and minor version numbers for the data services module

        For example, version 2.3 has a Major release number of 2 and a minor release number of 3

        :param major: Major Version release number (2 from the above example)
        :type major: int
        :param minor: Minor Version release number (3 from the above example)
        """
        self.major = major
        self.minor = minor

    def __cmp__(self, operand):
        """
        Python built-in for comparing two objects of the same type. Allows use of <, >, and = operators.

        :param operand: The right-side operand in a comparison.
        :return: An integer. Negative integers mean the left-side operand is smaller. Positive integers mean the
                 left-side operand is greater. Zero means the two operands are equal.
        """
        if self.major < operand.major:
            return -1
        elif self.major > operand.major:
            return 1
        else:
            if self.minor < operand.minor:
                return -1
            elif self.minor > operand.minor:
                return 1
        return 0

    def __str__(self):
        return "%d.%d" % (self.major, self.minor)

    def __repr__(self):
        return "%s(%d, %d)" % (self.__class__.__name__, self.major, self.minor)

#: Current version of data services, so code can easily test for a particular range of versions.
#: For example::
#:
#:   from data services import VERSION, Version
#:   if VERSION >= Version(1, 2):
#:        # Do something for version 1.2 and later versions
VERSION = Version(1, 5)

#: The releases of version *major.minor* are numbered sequentially.  For example, for the third release, RELEASE = 3.
RELEASE = 0

#: Version and release information in a long format for display purposes.
LONG_FORM = 'version %s, release %02d' % (VERSION, RELEASE)

#: Version and release information in a short format (i.e., abbreviated form).  Useful for version-control tags for
#: example.
SHORT_FORM = '%s,r%02d' % (VERSION, RELEASE)
