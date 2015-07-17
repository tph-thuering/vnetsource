class Version:
    """
    Represents a version. Versions have a major and minor number. For example, version 1.2 has a
    major version of 1 and minor version of 2. This class allows accurate comparison of two versions.
    """
    def __init__(self, major, minor):
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


#: Current version of job services, so code can easily test for a particular range of versions.
#: For example::
#:
#:   from job_services import VERSION, Version
#:   if VERSION >= Version(1, 2):
#:        # Do something for version 1.2 and later versions
VERSION = Version(2, 2)

#: The releases of version *major.minor* are numbered sequentially.  For example, for the third release, RELEASE = 3.
RELEASE = 1

#: Version and release information in a long format for display purposes.
LONG_FORM = 'version %s, release %02d' % (VERSION, RELEASE)

#: Version and release information in a short format (i.e., abbreviated form).  Useful for version-control tags for
#: example.
SHORT_FORM = '%s,r%02d' % (VERSION, RELEASE)