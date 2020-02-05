from setuptools import setup

setup(name='allocate', version='1.0.0',
      packages=['allocate'],
      url='https://github.com/BraeWebb/allocate',
      license='MIT', author='Henry O\'Brien, Brae Webb',
      author_email = 'b.webb@uq.edu.au',
      description = 'Tutor allocation tool',
      entry_points = {
          'console_scripts': ['allocate=allocate.allocation:main'],
      },
      install_requires=[
          'ortools'
      ]
)
