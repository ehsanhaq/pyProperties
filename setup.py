"""
Created on Apr 29, 2013

@author: ehsan
"""

try:
    from setuptools import setup
except:
    from distutils.core import setup
    
setup(name='properties',
      version='1.0',
      description='Java like Properties Implementation.',
      author = 'Ehsanul Haque',
      author_email = 'm.ehsan.haq@gmail.com',
      url='No url yet.',
      py_modules=['properties'],
      )
