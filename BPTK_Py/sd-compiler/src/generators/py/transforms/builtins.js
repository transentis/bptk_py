/*      _                   _ _
  _____| |__ ___ _ __  _ __(_| |___ _ _
 (_-/ _` / _/ _ | '  \| '_ | | / -_| '_|
 /__\__,_\__\___|_|_|_| .__|_|_\___|_|
                      |_|
 Copyright (c) 2013-2015 transentis management & consulting. All rights reserved.
*/
'use strict';

// Builtin Reference:
// http://www.iseesystems.com/Helpv10/Content/Reference/Builtins/Overview_Builtins.htm
module.exports = {

	// Simulation Buildins
	'dt': function () { return ' self.dt ' },
	'starttime': function () { return ' self.starttime ' },
	'stoptime': function () { return ' self.stoptime ' }, // TODO this does not exist in the model
	'time': function () { return ' t ' },
	'pi': function () { return ' math.pi ' },


	// Array builtins
	// http://www.iseesystems.com/Helpv10/Content/Reference/Builtins/Array_builtins.htm
	'size': function ( name ) {
		var vargs = [].slice.call( arguments, 0 )
		return vargs.length.toString()
	},
	'stddev': function ( name ) {
		(function(){var $avg=1;return 1+$avg})()
		var vargs = [].slice.call( arguments, 0 )
		var mean = '('+ vargs.join( '+' ) +')/'+vargs.length
		var v = vargs.map( function ( varg ) {
			return 'pow('+varg+'-$e,2)'
		}).join('+') + '/' + ( vargs.length - 1 )
		return '( statistics.stdev(' + vargs.join( ',' ) + '))'
	},
	'sum': function () {
		var vargs = [].slice.call( arguments, 0 )
		return '('+ vargs.join( '+' ) +')'
	},
	'mean': function () {
		var vargs = [].slice.call( arguments, 0 )
		return '('+ vargs.join( '+' ) +')/'+vargs.length
	},
	'rank': function () {
		var args = [].slice.call( arguments, 0 )
		var vargs = args.slice( 0, args.length - 1 )
		var pos = args.slice( -1 )
		return '[' + vargs +  '].index(sorted([' + vargs +  '])['+ pos + '-1])'
	},



	// Data builtins
	// http://www.iseesystems.com/Helpv10/Content/Reference/Builtins/Data_builtins.htm
	'previous': function ( body, initial ) {
		// append -dt to all variable invokations within the body
		// examples:
		//		self.memoize(equation, t) will become foo(t-dt)
		//		bar(t-self.dt) will become bar(t-self.dt-self.dt)
		//body = ( '' + body ).replace(", t",", t-self.dt")
		body = ( '' + body ).replace( /\, ([selfdt+\-\.]+)\)/g, ',$1-self.dt)' )


		return initial ?
			'(' + initial + ') if t <= self.starttime  else ' + '('  + body + ')' :
			body

	},



	// Mathematical builtins
	// http://www.iseesystems.com/Helpv10/Content/Reference/Builtins/Mathematical_builtins.htm
	'abs': function ( body ) {
		return 'abs( ' + body + ' )'
	},
	'max': function () {
		var vargs = [].slice.call( arguments, 0 )
		return 'max( ' + vargs.join( ', ' ) + ' )'
	},
	'min': function () {
		var vargs = [].slice.call( arguments, 0 )
		return 'min( ' + vargs.join( ', ' ) + ' )'
	},
	'int': function ( body ) {
		return 'math.floor( ' + body + ' )'
	},
	'sin': function( body ) {
		return 'math.sin(' + body + ' )'
	},
	'cos': function ( body ) {
		return 'math.cos(' + body + ')'
	},
	'round': function ( body ) {
		return 'round(' + body + ')'
	},
	'savediv': function ( nominator, denominator, onzero ) {
		onzero = onzero || 0
		return onzero + ' if ' + denominator + ' == 0 else ' + nominator + ' / ' + denominator
	},


	// Logical builtins
	// http://www.iseesystems.com/Helpv10/Content/Reference/Builtins/Logical_builtins.htm
	'if': function ( condition, then, otherwise ) {
		return '( (' + then + ') if (' + condition + ') else (' + otherwise + ') )'
	},



	// Delay builtins
	// http://www.iseesystems.com/Helpv10/Content/Reference/Builtins/Delay_builtins.htm
	'delay': function ( input, offset, initial ) {
		// Increase delay by adding "- offset" to all "t" occurences
		var tDelayed = input.replace( /(^|[^a-zA-Z_\\.])t($|[^a-zA-Z_\\.])/g, '$1( t - (' + offset + ') )$2' )
		if ( initial === undefined ) {
			return tDelayed
		}
		return  '(' + initial + ')  if t - self.starttime < (' +  offset + ') else (' +  tDelayed + ')'
	},


	// Data builtins
	// http://www.iseesystems.com/Helpv10/Content/Reference/Builtins/Data_builtins.htm
	'init': function ( item ) {
		return item.replace( /\, ([selfdt+\-\.]+)\)/g, ' ,self.starttime) ' )
	},



	// Statistical builtins
	// http://www.iseesystems.com/Helpv10/Content/Reference/Builtins/Statisticall_builtins.htm
	'normal': function ( mean, dev, seed ) {
		/*if ( seed !== undefined ) {
			TODO something like this: http://stackoverflow.com/questions/521295/javascript-random-seeds
		}*/
		// Box-Muller transform
		var normal = 'math.sqrt( -2 * math.log( random.random() ) ) * math.cos( 2 * math.pi * random.random() )'
		return '(((' +  normal + ') * (' + dev + ')) + (' + mean + '))'
	},
	'random': function ( min, max, seed ) {
		if ( seed ) {
			throw new Error( 'RANDOM with <seed> is currently not supported' )
		}
		return '(random.random() * (('+max+') - ('+min+')) + ('+min+'))'
	},



	// Test input builtins
	// http://www.iseesystems.com/Helpv10/Content/Reference/Builtins/Test_input_builtins.htm
	'pulse': function ( volume, first, interval ) {
		if ( first === undefined && interval === undefined ) {
			// Constant value
			return '( ' + volume + ' ) / self.dt'
		}
		if ( first === undefined ) {
			// Start immediately
			first = ' self.starttime '
		}
		if ( interval === undefined ) {
			// Repeat every dt
			return  + volume +' /self.dt if ' + first + ' <= t else 0'
		}
		if ( interval === 0 ) {
			// No repeat
			return  volume +' /self.dt if ' + first + ' == t else 0'
		}
		// Default case
		return  volume + '/ self.dt if ' + first + ' <= t and ((t -' + first + ') % ' + interval + ') == 0 else 0'
		//return '((((' + first + ') <= t) && (t - (' + first + ')) % (' + interval + ') === 0) ? (( ' + volume + ' ) / dt) : 0 )'
	},
	'step': function( height, time ) {
		return ' 0 if t < ' + time +' else '+ height
		//return '( t < ' + time + ' ? 0 : ' + height + ' )'
	}
}
