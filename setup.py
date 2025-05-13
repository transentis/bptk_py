from setuptools import setup

###################
### LOAD README ###
###################

with open("README.md", "r") as fh:
    long_description = fh.read()

#################
### BUILD EGG ###
#################

def get_version():
    return '2.1.0'

setup(version=get_version(),
     packages=['BPTK_Py',
                'BPTK_Py.scenariomanager',
                "BPTK_Py.logger",
                "BPTK_Py.visualizations",
                "BPTK_Py.config",
                "BPTK_Py.sdsimulation",
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
                "BPTK_Py.server",
                "BPTK_Py.externalstateadapter"
                ],
      include_package_data=True,
      zip_safe=False)
