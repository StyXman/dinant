#! /usr/bin/env python

# -*- coding: utf-8 -*-

# (c) 2017 Marcos Dione <mdione@grulic.org.ar>
# for licensing details see the file LICENSE.txt

from distutils.core import setup

setup(
    name ='dinant',
    version = '0.2',
    description = 'An attempt to make regular expressions more readable.',
    author = 'Marcos Dione',
    author_email = 'mdione@grulic.org.ar',
    url = 'https://github.com/StyXman/dinant',
    py_modules = [ 'dinant' ],
    license = 'GPLv3',
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 3',
        'Topic :: Utilities',
        ],
    )
