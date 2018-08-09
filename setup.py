from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(name='BPTK_Py',
      version='0.2',
      description='A python simulation engine for Stela system dynamics models',
      long_description=long_description,
      long_description_content_type="text/markdown",
      url='https://bitbucket.org/transentis/bptk_py/',
      author='Dominik Schroeck / transentis',
      author_email='dominik.schroeck@transentis.com',
      license='MIT',
      packages=['BPTK_Py', 'BPTK_Py.scenariomanager', "BPTK_Py.logger", "BPTK_Py.visualizations", "BPTK_Py.simulator",
                "BPTK_Py.config", "BPTK_Py.modelmonitor","BPTK_Py.widgetmanager"],
      install_requires=[
          'pandas', 'matplotlib'
      ],
      include_package_data=True,
      classifiers=(
          "Programming Language :: Python :: 3",
          "License :: OSI Approved :: MIT License",
          "Operating System :: OS Independent",
      ),
      zip_safe=False)
