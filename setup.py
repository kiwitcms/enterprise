# Copyright (c) 2020-2025 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

# pylint: disable=missing-docstring

from setuptools import setup, find_packages


def get_long_description():
    with open('README.md', 'r', encoding="utf-8") as file:
        return file.read()


def get_install_requires(path):
    requires = []

    with open(path, 'r', encoding="utf-8") as file:
        for line in file:
            if line.startswith('-r '):
                continue
            requires.append(line.strip())
        return requires


setup(
    name='kiwitcms-enterprise',
    version='14.3',
    description='Kiwi TCMS Enterprise Edition',
    long_description=get_long_description(),
    long_description_content_type='text/markdown',
    author='Kiwi TCMS',
    author_email='kiwitcms@mrsenko.com',
    url='https://github.com/MrSenko/kiwitcms-enterprise/',
    license='AGPLv3+',
    install_requires=get_install_requires('requirements.txt'),
    include_package_data=True,
    packages=find_packages(),
    zip_safe=False,
    entry_points={
        "kiwitcms.plugins": ["kiwitcms_enterprise = tcms_enterprise"]
    },
    classifiers=[
        'Framework :: Django',
        'Development Status :: 5 - Production/Stable',
        'Topic :: Software Development :: Quality Assurance',
        'Topic :: Software Development :: Testing',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: '
        'GNU Affero General Public License v3 or later (AGPLv3+)',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
    ],
)
