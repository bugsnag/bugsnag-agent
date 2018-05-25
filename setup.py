#!/usr/bin/env python

"""
Forwards reports from your server to bugsnag.com or an on-premise Bugsnag
installation. Used to avoid any latency impact that might occur if you
need to make a call over the network in every exception handler.
"""

from setuptools import setup, find_packages

setup(
    name='bugsnag-agent',
    version='1.2.1',
    description='A forwarding agent for Bugsnag to minimize reporting impact',
    long_description=__doc__,
    url='https://github.com/bugsnag/bugsnag-agent',
    author='Delisa Mason',
    author_email='iskanamagus@gmail.com',
    license='MIT',
    packages=find_packages(),
    entry_points={
        'console_scripts': (
            'bugsnag-agent = bugsnag_agent:main',
        )
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development'
    ]
)
