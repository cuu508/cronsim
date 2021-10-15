# coding: utf-8

from setuptools import find_packages, setup

setup(
    name="cronsim",
    version="1.0",
    url="https://github.com/cuu508/cronsim",
    license="BSD",
    author="Pēteris Caune",
    author_email="cuu508@gmail.com",
    description="Cron expression parser and evaluator",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    include_package_data=True,
    platforms="any",
    install_requires=["pytz"],
    classifiers=[
        # As from http://pypi.python.org/pypi?%3Aaction=list_classifiers
        # 'Development Status :: 1 - Planning',
        # 'Development Status :: 2 - Pre-Alpha',
        # "Development Status :: 3 - Alpha",
        # "Development Status :: 4 - Beta",
        "Development Status :: 5 - Production/Stable",
        # 'Development Status :: 6 - Mature',
        # 'Development Status :: 7 - Inactive',
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: POSIX",
        "Operating System :: MacOS",
        "Operating System :: Unix",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
