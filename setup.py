#for macOS use: python setup.py py2app
from setuptools import setup
APP = ['Translator.py']
DATA_FILES = []
OPTIONS = {
    'iconfile':'icons/Translator.icns',
    'argv_emulation':True,
    'packages':['certifi']}
setup(app=APP,
      data_files=DATA_FILES,
      options={'py2app':OPTIONS},
      setup_requires=['py2app'],)