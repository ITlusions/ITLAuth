#!/usr/bin/env python3
"""
Setup script for kubectl-oidc-setup package
"""

from setuptools import setup, find_packages
import os
import re

# Read version from __init__.py
def get_version():
    init_path = os.path.join('src', 'itlc', '__init__.py')
    with open(init_path, 'r', encoding='utf-8') as f:
        content = f.read()
    version_match = re.search(r'^__version__ = [\'"]([^\'"]*)[\'"]', content, re.MULTILINE)
    if version_match:
        return version_match.group(1)
    raise RuntimeError('Unable to find version string.')

# Read README
def get_long_description():
    readme_path = 'README.md'
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "ITlusions Kubernetes OIDC Setup Tool"

setup(
    name='itlc',
    version=get_version(),
    author='ITlusions',
    author_email='info@itlusions.com',
    description='ITL Control Plane CLI - Keycloak authentication and resource management',
    long_description=get_long_description(),
    long_description_content_type='text/markdown',
    url='https://github.com/ITlusions/ITL.ControlPlane.Cli',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Topic :: System :: Systems Administration',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Internet :: WWW/HTTP :: Authentication',
    ],
    python_requires='>=3.8',
    install_requires=[
        'requests>=2.25.0',
        'pyyaml>=6.0',
        'colorama>=0.4.4',
        'click>=8.0.0',
    ],
    extras_require={
        'dev': [
            'pytest>=6.0',
            'pytest-cov>=2.0',
            'black>=21.0',
            'flake8>=3.8',
            'mypy>=0.900',
        ],
    },
    entry_points={
        'console_scripts': [
            'itlc=itlc.__main__:cli',
        ],
    },
    include_package_data=True,
    package_data={
        'itlc': ['*.yaml', '*.yml', '*.json', '*.html'],
    },
    keywords=[
        'kubernetes',
        'kubectl',
        'oidc',
        'keycloak',
        'authentication',
        'automation',
        'devops',
        'cloud',
        'itlusions',
    ],
    project_urls={
        'Bug Reports': 'https://github.com/ITlusions/ITLAuth/issues',
        'Source': 'https://github.com/ITlusions/ITLAuth',
        'Documentation': 'https://github.com/ITlusions/ITLAuth',
        'ITlusions': 'https://www.itlusions.com',
    },
)