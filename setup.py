from setuptools import setup

setup(name='BPTK_Py',
      version='0.2',
      description='A python simulation engine for system dynamics models',
      url='http://github.com/storborg/funniest',
      author='Dominik Schroeck / transentis',
      author_email='dominik.schroeck@transentis.com',
      license='MIT',
      packages=['BPTK_Py', 'BPTK_Py.scenario_manager', "BPTK_Py.logger", "BPTK_Py.Visualizations", "BPTK_Py.simulator",
                "BPTK_Py.config", "BPTK_Py.model_monitor"],
      install_requires=[
          'pandas', 'matplotlib'
      ],
      include_package_data=True,
      zip_safe=False)


