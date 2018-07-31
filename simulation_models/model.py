#      _                   _ _
#  _____| |__ ___ _ __  _ __(_| |___ _ _
# (_-/ _` / _/ _ | '  \| '_ | | / -_| '_|
# /__\__,_\__\___|_|_|_| .__|_|_\___|_|
#                      |_|
# Copyright (c) 2013-2016 transentis management & consulting. All rights reserved.
#





class simulation_model():
  def memoize(self, equation, arg):
    mymemo = self.memo[equation]
    if arg in mymemo.keys():
      return mymemo[arg]
    else:
      result = self.equations[equation](arg)
      mymemo[arg] = result
      return result

  def __init__(self):
    # Simulation Buildins
    self.dt = 0.25
    self.starttime = 1
    self.stoptime = 13
    self.equations = {
  	# Stocks     # flows 	# converters     # gf     #constants
  		'bazFoo': lambda t : 3
      ,
  		'fooBar': lambda t : 1
      ,
  		'fooBarBaz': lambda t : 5
      ,
  		'fooBaz': lambda t : 2
      ,
  		'fooeur': lambda t : 7
      ,
  		'foogbp': lambda t : 8
      ,
  		'foopct': lambda t : 4
      ,
  		'foousd': lambda t : 8
      ,
    }

    self.points = {
  	 }

    self.dimensions = {
  	 }

    self.stocks = []
    self.flows = []
    self.converters = []
    self.gf = []
    self.constants= ['bazFoo','fooBar','fooBarBaz','fooBaz','fooeur','foogbp','foopct','foousd']
    self.events = [
    	]

    self.memo = {}
    for key in list(self.equations.keys()):
      self.memo[key] = {}  # DICT OF DICTS!

  def specs(self):
    return self.starttime, self.stoptime, self.dt, 'Months', 'Euler'

  def setDT(self,v):
    self.dt = v

  def setStarttime(self,v):
    self.starttime = v

  def setStoptime(self,v):
    self.stoptime = v

