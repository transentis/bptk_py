/*      _                   _ _
  _____| |__ ___ _ __  _ __(_| |___ _ _
 (_-/ _` / _/ _ | '  \| '_ | | / -_| '_|
 /__\__,_\__\___|_|_|_| .__|_|_\___|_|
                      |_|
 Copyright (c) 2013-2015 transentis management & consulting. All rights reserved.
*/
'use strict';

// hacked: optional model prefixes
// for starttime and stoptime
var prefix = require( 'optimist' ).argv.p || ''
prefix = prefix ? prefix + '▸' : ''

var starttime = prefix + 'starttime'
var stoptime = prefix + 'stoptime'


// Builtin Reference:
// http://www.iseesystems.com/Helpv10/Content/Reference/Builtins/Overview_Builtins.htm
module.exports = {

	// Simulation Buildins
	'dt': function () { return 'dt' },
	'starttime': function () { return starttime },
	'stoptime': function () { return stoptime }, // TODO this does not exist in the model
	'time': function () { return 't' },
	'pi': function () { return 'Pi' },


	// Array builtins
	// http://www.iseesystems.com/Helpv10/Content/Reference/Builtins/Array_builtins.htm
	'size': function () {
		var vargs = [].slice.call( arguments, 0 )
		return vargs.length.toString()
	},
	'stddev': function () {
		var vargs = [].slice.call( arguments, 0 ).join( ',' )
		return 'StandardDeviation[{'+ vargs +'}]'
	},
	'sum': function () {
		var sum = [].slice.call( arguments, 0 ).join( ',' )
		return 'Total[{'+ sum +'}]'
	},
	'mean': function () {
		var vargs = [].slice.call( arguments, 0 ).join( ',' )
		return 'Mean[{'+ vargs +'}]'
	},
	'rank': function ( list ) {
		var args = [].slice.call( arguments, 0 )
		var vargs = args.slice( 0, args.length - 1 )
		var pos = args.slice( -1 )
		return 'SortBy[MapIndexed[{#1,First@#2}&,{'+ vargs +'}],First][['+ pos +',2]]'
	},


	// Data builtins
	// http://www.iseesystems.com/Helpv10/Content/Reference/Builtins/Data_builtins.htm
	'previous': function ( body, initial ) {
		// append -dt to all variable invokations within the body
		// examples:
		//		foo[t,dt] will become foo[t-dt,dt]
		//		bar[t-dt] will become bar[t-dt-dt,dt]
		body = ( '' + body ).replace( /\[([dt+\-]+),dt\]/g, '[$1-dt,dt]' )
		return initial ?
			'If[t < '+ starttime +','+ initial +','+ body +']' :
			body
	},

	// Mathematical builtins
	// http://www.iseesystems.com/Helpv10/Content/Reference/Builtins/Mathematical_builtins.htm
	'abs': function ( body ) {
		return 'Abs[' + body + ']'
	},
	'max': function () {
		var args = [].slice.call( arguments, 0 ).join( ',' )
		return 'Max[' + args + ']'
	},
	'min': function () {
		var args = [].slice.call( arguments, 0 ).join( ',' )
		return 'Min[' + args + ']'
	},
	'int': function ( body ) {
		return 'Floor[' + body + ']'
	},
	'sin': function ( body ) {
		return 'Sin[' + body + ']'
	},
	'cos': function ( body ) {
		return 'Cos[' + body + ']'
	},
	'round': function ( body ) {
		return 'Round[' + body + ']'
	},



	// Logical builtins
	// http://www.iseesystems.com/Helpv10/Content/Reference/Builtins/Logical_builtins.htm
	'if': function ( condition, then, otherwise ) {
		return 'If[' + condition + ',' + then + ',' + otherwise + ']'
	},




	// Delay builtins
	// http://www.iseesystems.com/Helpv10/Content/Reference/Builtins/Delay_builtins.htm
	'delay': function ( body, offset, initial ) {
		// Increase delay by adding "- offset" to all "t" occurences
		body = body.replace( /\[([dt+\-]+),dt\]/g, '[$1-('+ offset +'),dt]' )
		return initial === undefined ? body :
			'If[ t - '+ starttime +' < '+ offset +','+ initial +','+ body +']'
	},



	// Data builtins
	// http://www.iseesystems.com/Helpv10/Content/Reference/Builtins/Data_builtins.htm
	'init': function ( body ) {
		return body.replace( /\[[dt+\-]+,dt\]/g, '['+ starttime +',dt]' )
	},



	// Statistical builtins
	// http://www.iseesystems.com/Helpv10/Content/Reference/Builtins/Statisticall_builtins.htm
	'normal': function ( mean, dev, seed ) {
		if ( seed !== undefined ) {
			// TODO http://reference.wolfram.com/language/ref/SeedRandom.html
			throw new Error( 'seeding not implemented' )
		}
		// Box-Muller transform
		var normal = 'Sqrt[ -2 * Log@RandomReal[] ) * Cos[ 2 * Pi * RandomReal[] ]'
		return '(('+ normal +'*'+ dev +') +'+ mean +')'
	},
	'random': function ( min, max, seed ) {
		if ( seed !== undefined ) {
			throw new Error( 'seeding not implemented' )
		}
		return 'RandomReal[{'+ min +','+ max +'}]'
	},



	// Test input builtins
	// http://www.iseesystems.com/Helpv10/Content/Reference/Builtins/Test_input_builtins.htm
	'pulse': function ( volume, first, interval ) {
		if ( first === undefined && interval === undefined ) {
			// Constant value
			return '(( ' + volume + ' ) / dt)'
		}
		if ( first === undefined ) {
			// Start immediately
			first = starttime
		}
		if ( interval === undefined ) {
			// Repeat every dt
			return 'If[ ('+ first +') <= t, (('+ volume +') / dt), 0 ]'
		}
		if ( interval === 0 ) {
			// No repeat
			return 'If[ ('+ first +') == t, (('+ volume +') / dt), 0 ]'
		}
		// Default case
		return 'If[ ('+ first +') <= t && Mod[t - ('+ first +'),'+ interval +'] == 0, (('+ volume +') / dt), 0 ]'
	},
	'step': function( height, time ) {
		return 'If[ t < '+ time +', 0,'+ height +']'
	}
}
