#      _                   _ _
#  _____| |__ ___ _ __  _ __(_| |___ _ _
# (_-/ _` / _/ _ | '  \| '_ | | / -_| '_|
# /__\__,_\__\___|_|_|_| .__|_|_\___|_|
#                      |_|
# Copyright (c) 2013-2016 transentis management & consulting. All rights reserved.
#




import statistics
import math
import random

# linear interpolation between a set points
def LERP(x, points):
	first = 0
	last = len(points)-1

	def getX(i):
			return points[i][0]

	def getY(i):
			return points[i][1]

	def getOffset(x):
			for i in range(first,last):
					if x < getX(i): return i-1
			return last -1

	if x <= getX(first): return getY(first)
	if x >= getX(last): return getY(last)

	n = getOffset(x)
	x0 = getX(n)
	y0 = getY(n)
	x1 = getX(n+1)
	y1 = getY(n+1)

	return (y1 - y0) * (x - x0) / (x1 - x0) + y0


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
    self.dt = 1
    self.starttime = 1
    self.stoptime = 10
    self.equations = {
  	# Stocks 
  		'bar': lambda t : self.memoize('bar[1,1]', t) + self.memoize('bar[1,2]', t) + self.memoize('bar[1,3]', t) + self.memoize('bar[2,1]', t) + self.memoize('bar[2,2]', t) + self.memoize('bar[2,3]', t) + self.memoize('bar[3,1]', t) + self.memoize('bar[3,2]', t) + self.memoize('bar[3,3]', t),

  		'bar[1,1]': lambda t : max( 0, 0 if  t  <=  self.starttime  else self.memoize('bar[1,1]', t-self.dt) +  self.dt  * ( self.memoize('foo[1,1]', t-self.dt) - ( self.memoize('baz[1,1]', t) ) ) ),

  		'bar[1,2]': lambda t : max( 0, 0 if  t  <=  self.starttime  else self.memoize('bar[1,2]', t-self.dt) +  self.dt  * ( self.memoize('foo[1,2]', t-self.dt) - ( self.memoize('baz[1,2]', t) ) ) ),

  		'bar[1,3]': lambda t : max( 0, 0 if  t  <=  self.starttime  else self.memoize('bar[1,3]', t-self.dt) +  self.dt  * ( self.memoize('foo[1,3]', t-self.dt) - ( self.memoize('baz[1,3]', t) ) ) ),

  		'bar[2,1]': lambda t : max( 0, 0 if  t  <=  self.starttime  else self.memoize('bar[2,1]', t-self.dt) +  self.dt  * ( self.memoize('foo[2,1]', t-self.dt) - ( self.memoize('baz[2,1]', t) ) ) ),

  		'bar[2,2]': lambda t : max( 0, 0 if  t  <=  self.starttime  else self.memoize('bar[2,2]', t-self.dt) +  self.dt  * ( self.memoize('foo[2,2]', t-self.dt) - ( self.memoize('baz[2,2]', t) ) ) ),

  		'bar[2,3]': lambda t : max( 0, 0 if  t  <=  self.starttime  else self.memoize('bar[2,3]', t-self.dt) +  self.dt  * ( self.memoize('foo[2,3]', t-self.dt) - ( self.memoize('baz[2,3]', t) ) ) ),

  		'bar[3,1]': lambda t : max( 0, 0 if  t  <=  self.starttime  else self.memoize('bar[3,1]', t-self.dt) +  self.dt  * ( self.memoize('foo[3,1]', t-self.dt) - ( self.memoize('baz[3,1]', t) ) ) ),

  		'bar[3,2]': lambda t : max( 0, 0 if  t  <=  self.starttime  else self.memoize('bar[3,2]', t-self.dt) +  self.dt  * ( self.memoize('foo[3,2]', t-self.dt) - ( self.memoize('baz[3,2]', t) ) ) ),

  		'bar[3,3]': lambda t : max( 0, 0 if  t  <=  self.starttime  else self.memoize('bar[3,3]', t-self.dt) +  self.dt  * ( self.memoize('foo[3,3]', t-self.dt) - ( self.memoize('baz[3,3]', t) ) ) ),

  		'sink': lambda t : max( 0, 0 if  t  <=  self.starttime  else self.memoize('sink', t-self.dt) +  self.dt  * ( self.memoize('baz', t-self.dt) ) ),

  		'src': lambda t : max( 0, 100 if  t  <=  self.starttime  else self.memoize('src', t-self.dt) +  self.dt  * ( -1 * ( self.memoize('foo', t-self.dt) ) ) ),
    # flows 
  		'baz': lambda t : self.memoize('baz[1,1]', t) + self.memoize('baz[1,2]', t) + self.memoize('baz[1,3]', t) + self.memoize('baz[2,1]', t) + self.memoize('baz[2,2]', t) + self.memoize('baz[2,3]', t) + self.memoize('baz[3,1]', t) + self.memoize('baz[3,2]', t) + self.memoize('baz[3,3]', t),
  	
  		'baz[1,1]': lambda t : 0,
  	
  		'baz[1,2]': lambda t : 0,
  	
  		'baz[1,3]': lambda t : 0,
  	
  		'baz[2,1]': lambda t : 0,
  	
  		'baz[2,2]': lambda t : 0,
  	
  		'baz[2,3]': lambda t : 0,
  	
  		'baz[3,1]': lambda t : 0,
  	
  		'baz[3,2]': lambda t : 0,
  	
  		'baz[3,3]': lambda t : 0,
  	
  		'foo': lambda t : self.memoize('foo[1,1]', t) + self.memoize('foo[1,2]', t) + self.memoize('foo[1,3]', t) + self.memoize('foo[2,1]', t) + self.memoize('foo[2,2]', t) + self.memoize('foo[2,3]', t) + self.memoize('foo[3,1]', t) + self.memoize('foo[3,2]', t) + self.memoize('foo[3,3]', t),
  	
  		'foo[1,1]': lambda t : max( 0, self.memoize('hodor', t) + self.memoize('nix', t) + 1 / self.memoize('index[1,1]', t) ),
  	
  		'foo[1,2]': lambda t : max( 0, self.memoize('hodor', t) + self.memoize('nix', t) + 1 / self.memoize('index[1,2]', t) ),
  	
  		'foo[1,3]': lambda t : max( 0, self.memoize('hodor', t) + self.memoize('nix', t) + 1 / self.memoize('index[1,3]', t) ),
  	
  		'foo[2,1]': lambda t : max( 0, self.memoize('hodor', t) + self.memoize('nix', t) + 1 / self.memoize('index[2,1]', t) ),
  	
  		'foo[2,2]': lambda t : max( 0, self.memoize('hodor', t) + self.memoize('nix', t) + 1 / self.memoize('index[2,2]', t) ),
  	
  		'foo[2,3]': lambda t : max( 0, self.memoize('hodor', t) + self.memoize('nix', t) + 1 / self.memoize('index[2,3]', t) ),
  	
  		'foo[3,1]': lambda t : max( 0, self.memoize('hodor', t) + self.memoize('nix', t) + 1 / self.memoize('index[3,1]', t) ),
  	
  		'foo[3,2]': lambda t : max( 0, self.memoize('hodor', t) + self.memoize('nix', t) + 1 / self.memoize('index[3,2]', t) ),
  	
  		'foo[3,3]': lambda t : max( 0, self.memoize('hodor', t) + self.memoize('nix', t) + 1 / self.memoize('index[3,3]', t) ),
  		# converters 
  		'avg': lambda t : (self.memoize('bar[1,1]', t)+self.memoize('bar[1,2]', t)+self.memoize('bar[1,3]', t)+2)/4 + 1,

  		'index': lambda t : self.memoize('index[1,1]', t) + self.memoize('index[1,2]', t) + self.memoize('index[1,3]', t) + self.memoize('index[2,1]', t) + self.memoize('index[2,2]', t) + self.memoize('index[2,3]', t) + self.memoize('index[3,1]', t) + self.memoize('index[3,2]', t) + self.memoize('index[3,3]', t),

  		'maximum': lambda t : max( self.memoize('bar[1,1]', t), self.memoize('bar[1,2]', t), self.memoize('bar[1,3]', t), self.memoize('bar[2,1]', t), self.memoize('bar[2,2]', t), self.memoize('bar[2,3]', t), self.memoize('bar[3,1]', t), self.memoize('bar[3,2]', t), self.memoize('bar[3,3]', t) ),

  		'smallest': lambda t : [self.memoize('bar[1,1]', t),self.memoize('bar[1,2]', t),self.memoize('bar[1,3]', t)].index(sorted([self.memoize('bar[1,1]', t),self.memoize('bar[1,2]', t),self.memoize('bar[1,3]', t)])[1-1]),
    # gf 
  		'hodor': lambda t : LERP( t ,self.points['hodor']),
    #constants
  		'index[1,1]': lambda t : 1
      ,
  		'index[1,2]': lambda t : 1
      ,
  		'index[1,3]': lambda t : 1
      ,
  		'index[2,1]': lambda t : 2
      ,
  		'index[2,2]': lambda t : 2
      ,
  		'index[2,3]': lambda t : 2
      ,
  		'index[3,1]': lambda t : 3
      ,
  		'index[3,2]': lambda t : 3
      ,
  		'index[3,3]': lambda t : 3
      ,
  		'nix': lambda t : 0
      ,
    }

    self.points = {
  		'hodor': [ [1,0],[4,2],[7,0],[10,2] ],
  	 }

    self.dimensions = {
  		'foobar': {
  			'labels': [ '1','2','3' ],
  			'variables': [ 'bar','foo','baz','index' ]
  		},
  		'barfoo': {
  			'labels': [ '1','2','3' ],
  			'variables': [ 'bar','foo','baz','index' ]
  		},
  	 }

    self.stocks = ['bar','bar[1,1]','bar[1,2]','bar[1,3]','bar[2,1]','bar[2,2]','bar[2,3]','bar[3,1]','bar[3,2]','bar[3,3]','sink','src']
    self.flows = ['baz','baz[1,1]','baz[1,2]','baz[1,3]','baz[2,1]','baz[2,2]','baz[2,3]','baz[3,1]','baz[3,2]','baz[3,3]','foo','foo[1,1]','foo[1,2]','foo[1,3]','foo[2,1]','foo[2,2]','foo[2,3]','foo[3,1]','foo[3,2]','foo[3,3]']
    self.converters = ['avg','index','maximum','smallest']
    self.gf = ['hodor']
    self.constants= ['index[1,1]','index[1,2]','index[1,3]','index[2,1]','index[2,2]','index[2,3]','index[3,1]','index[3,2]','index[3,3]','nix']
    self.events = [
    	]

    self.memo = {}
    for key in list(self.equations.keys()):
      self.memo[key] = {}  # DICT OF DICTS!

  def specs(self):
    return self.starttime, self.stoptime, self.dt, 'Hours', 'Euler'

  def setDT(self,v):
    self.dt = v

  def setStarttime(self,v):
    self.starttime = v

  def setStoptime(self,v):
    self.stoptime = v

