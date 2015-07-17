from setuptools import setup, find_packages

description="""
Core module of django orm extensions package. Is a collection of third party plugins build in one unified package.
"""

setup(
    name = "djorm-ext-pgbytea",
    version = "0.6.0",
    url = "https://github.com/niwibe/djorm-ext-pgbytea",
    license = "BSD",
    platforms = ["OS Independent"],
    description = description.strip(),
    author = "Andrey Antukh",
    author_email = "niwi@niwi.be",
    maintainer = "Andrey Antukh",
    maintainer_email = "niwi@niwi.be",
    packages = find_packages(),
    include_package_data = False,
    install_requires = [
        "six >= 1.5"
    ],
    zip_safe = False,
    classifiers = [
        "Development Status :: 4 - Beta",
        "Framework :: Django",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Internet :: WWW/HTTP",
    ]
)
