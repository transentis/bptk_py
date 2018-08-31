from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()


setup(name='BPTK_Py',
      version='0.3.6.1',
      description='A python simulation engine for System Dynamics models',
      long_description=long_description,
      long_description_content_type="text/markdown",
      url='https://www.transentis.com/products/business-prototyping-toolkit/',
      author='transentis labs GmbH',
      author_email='support@transentis.com',
      license='MIT',
      packages=['BPTK_Py', 'BPTK_Py.scenariomanager', "BPTK_Py.logger", "BPTK_Py.visualizations", "BPTK_Py.simulator",
                "BPTK_Py.config", "BPTK_Py.modelmonitor", "BPTK_Py.widgetdecorator", "BPTK_Py.modelchecker"],
      install_requires=[
          'pandas', 'matplotlib', 'ipywidgets', 'scipy', 'numpy',
      ],
      include_package_data=True,
      classifiers=(
          "Programming Language :: Python :: 3",
          'License :: OSI Approved :: MIT License',
          "Operating System :: OS Independent",
      ),


      zip_safe=False)
