from setuptools import setup, find_packages

with open("requirements.txt") as f:
    install_requires = f.read().strip().split("\n")

# get version from __version__ variable in wix_integration/__init__.py
from wix_integration import __version__ as version

setup(
    name="wix_integration",
    version=version,
    description="Bidirectional sync between Wix eCommerce and ERPNext",
    author="Your Company",
    author_email="admin@yourcompany.com",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=install_requires
)
