## this file is generated from settings in build.vel

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

# from options["setup"] in build.vel
config = {'description': 'A book compiler for programmers where code and prose are separate.', 'author': 'Zed A. Shaw', 'author_email': 'zedshaw@zedshaw.com', 'url': 'http://www.zedshaw.com/projects/zapps', 'version': '0.5', 'scripts': ['bin/zapps'], 'packages': ['zapps'], 'name': 'zapps'}
setup(**config)

