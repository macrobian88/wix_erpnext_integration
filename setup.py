# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

with open('requirements.txt') as f:
	requirements = f.read().strip().split('\n')

setup(
	name='wix_integration',
	version='1.0.0',
	description='Bidirectional sync between Wix website and ERPNext',
	author='Wix ERPNext Integration Team',
	author_email='support@wixerpnext.com',
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=requirements
)