from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(name='BPTK_Py',
      version='0.6.1',
      description='A python simulation engine for System Dynamics & Agent based models',
      long_description=long_description,
      long_description_content_type="text/markdown",
      url='https://www.transentis.com/products/business-prototyping-toolkit/',
      author='transentis labs GmbH',
      author_email='support@transentis.com',
      license='MIT',
      packages=['BPTK_Py',
                'BPTK_Py.scenariomanager',
                "BPTK_Py.logger",
                "BPTK_Py.visualizations",
                "BPTK_Py.sdsimulator",
                "BPTK_Py.config",
                "BPTK_Py.modelmonitor",
                "BPTK_Py.widgets",
                "BPTK_Py.modelchecker",
                "BPTK_Py.abm",
                "BPTK_Py.simulationrunners",
                "BPTK_Py.systemdynamics",
                "BPTK_Py.util"],
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