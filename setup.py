import codecs
from setuptools import setup, find_packages

entry_points = {
    'console_scripts': [
    ],
}

TESTS_REQUIRE = [
    'nti.testing',
    'zope.dottedname',
    'zope.testrunner',
]


def _read(fname):
    with codecs.open(fname, encoding='utf-8') as f:
        return f.read()


setup(
    name='plone.namedfile',
    version=_read('version.txt').strip(),
    author='Laurence Rowe, Martin Aspeli',
    author_email='plone-developers@lists.sourceforge.net',
    description="File types and fields for images, files and blob files with filenames",
    long_description=(_read('README.rst') + '\n\n' + _read('CHANGES.rst')),
    license="BSD",
    keywords='plone named file image blob',
    classifiers=[
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        "License :: OSI Approved :: BSD License",
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
    ],
    url="https://github.com/NextThought/nti.plone.namedfile",
    zip_safe=True,
    packages=find_packages("src"),
    package_dir={'': 'src'},
    include_package_data=True,
    install_requires=[
        'setuptools',
        'piexif',
        'Pillow',
        'persistent',
        'six',
        'ZODB',
        'zope.component',
        'zope.copy',
        'zope.interface',
        'zope.schema',
        'zope.security',
        'zope.traversing',
    ],
    test_suite="plone.namedfile.tests",
    extras_require={
        'test': TESTS_REQUIRE,
        'docs': [
            'Sphinx',
            'repoze.sphinx.autointerface',
            'sphinx_rtd_theme',
        ],
    },
)
