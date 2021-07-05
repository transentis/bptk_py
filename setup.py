from setuptools import setup
import conf, pytest

#########################
### LOAD REQUIREMENTS ###
#########################

requirements = []
req_file = open("requirements.txt","r")
for line in req_file.readlines():
    requirements += [line.replace("\n","")]


###################
### LOAD README ###
###################

with open("README.md", "r") as fh:
    long_description = fh.read()

#################
### BUILD EGG ###
#################


setup(name='BPTK_Py',
      version=conf.release,
      description='A python simulation engine for System Dynamics & Agent based models',
      long_description=long_description,
      long_description_content_type="text/markdown",
      url='https://www.transentis.com/business-prototyping-toolkit/en',
      author='transentis labs GmbH',
      author_email='support@transentis.com',
      license='MIT',
      packages=['BPTK_Py',
                'BPTK_Py.scenariomanager',
                "BPTK_Py.logger",
                "BPTK_Py.visualizations",
                "BPTK_Py.config",
                "BPTK_Py.xmile_wrapper",
                "BPTK_Py.modelmonitor",
                "BPTK_Py.widgets",
                "BPTK_Py.modeling",
                "BPTK_Py.modeling.datacollectors",
                "BPTK_Py.scenariorunners",
                "BPTK_Py.sddsl",
                "BPTK_Py.exceptions",
                "BPTK_Py.util",
                "BPTK_Py.modelparser",
                "BPTK_Py.sdcompiler",
                "BPTK_Py.sdcompiler.generator",
                "BPTK_Py.sdcompiler.generator.py",
                "BPTK_Py.sdcompiler.parsers",
                "BPTK_Py.sdcompiler.parsers.smile",
                "BPTK_Py.sdcompiler.parsers.xmile",
                "BPTK_Py.sdcompiler.plugins",
                "BPTK_Py.server"
                ],

      install_requires=requirements,
      setup_requires=["pytest-runner"],
        tests_require=["pytest"],
      include_package_data=True,

      classifiers=[
          "Programming Language :: Python :: 3",
          'License :: OSI Approved :: MIT License',
          "Operating System :: OS Independent",
      ],
      zip_safe=False)
