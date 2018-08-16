/*      _                   _ _
  _____| |__ ___ _ __  _ __(_| |___ _ _
 (_-/ _` / _/ _ | '  \| '_ | | / -_| '_|
 /__\__,_\__\___|_|_|_| .__|_|_\___|_|
                      |_|
 Copyright (c) 2013-2015 transentis management & consulting. All rights reserved.
*/

// Builtin Reference:
// http://www.iseesystems.com/Helpv10/Content/Reference/Builtins/Overview_Builtins.htm
export default {

	// Simulation Buildins
	'dt': () => 'dt',
	'starttime': () => 'starttime',
	'stoptime': () => 'stoptime', // TODO this does not exist in the model
	'time': () => 't',
	'pi': () => 'Math.PI',


	// Array builtins
	// http://www.iseesystems.com/Helpv10/Content/Reference/Builtins/Array_builtins.htm
	'size': function ( name ) {
		var vargs = [].slice.call( arguments, 0 )
		return vargs.length.toString()
	},
	'stddev': function ( name ) {
		(function(){var $avg=1;return 1+$avg})()
		const vargs = [].slice.call( arguments, 0 )
		const mean = '('+ vargs.join( '+' ) +')/'+vargs.length
		const v = vargs.map( function ( varg ) {
			return 'Math.pow('+varg+'-$e,2)'
		}).join('+') + '/' + ( vargs.length - 1 )
		return '(function(){var $e='+mean+';return '+v+'}())'
	},
	'sum': ( ...args ) => `(${args.join( '+' )})`,
	'mean': ( ...args ) => `(${args.join( '+' )})/${args.length}`,
	'rank': ( ...args ) => `[${args}].map((v,i) => [v,i+1]).sort((a,b) => a[0]>b[0])[${args.slice( -1 )}-1][1]`,



	// Data builtins
	// http://www.iseesystems.com/Helpv10/Content/Reference/Builtins/Data_builtins.htm
	'previous': function ( body, initial ) {
		// append -dt to all variable invokations within the body
		// examples:
		//		foo(t) will become foo(t-dt)
		//		bar(t-dt) will become bar(t-dt-dt)
		body = ( '' + body ).replace( /\(([dt+\-]+)\)/g, '($1-dt)' )
		return initial ?
			`t < starttime ? (${initial}) : (${body})` :
			body
	},



	// Mathematical builtins
	// http://www.iseesystems.com/Helpv10/Content/Reference/Builtins/Mathematical_builtins.htm
	'abs': body => `Math.abs(${body})`,
	'max': ( ...args ) => `Math.max(${args.join( ', ' )})`,
	'min': ( ...args ) => `Math.min(${args.join( ', ' )})`,
	'int': body => `Math.floor(${body})`,
	'sin': body => `Math.sin(${body} )`,
	'cos': body => `Math.cos(${body})`,
	'round': body => `Math.round(${body})`,
	'savediv': ( nominator, denominator, onzero = 0 ) =>
		`((${denominator} === 0 ) ? (${onzero}) : (${nominator}/${denominator}))`,


	// Logical builtins
	// http://www.iseesystems.com/Helpv10/Content/Reference/Builtins/Logical_builtins.htm
	'if': ( condition, then, otherwise ) =>
		`((${condition}) ? (${then}) : (${otherwise}))`,



	// Delay builtins
	// http://www.iseesystems.com/Helpv10/Content/Reference/Builtins/Delay_builtins.htm
	'delay': ( input, offset, initial ) => {
		// Increase delay by adding "- offset" to all "t" occurences
		var tDelayed = input.replace( /(^|[^a-zA-Z_\\.])t($|[^a-zA-Z_\\.])/g, '$1( t - (' + offset + ') )$2' )
		if ( initial === undefined ) {
			return tDelayed
		}
		return `(t - starttime < (${offset}) ? (${initial}) : (${tDelayed}))`
	},


	// Data builtins
	// http://www.iseesystems.com/Helpv10/Content/Reference/Builtins/Data_builtins.htm
	'init': item => item.replace( /\([dt+\-]+\)/g, '(starttime)' ),



	// Statistical builtins
	// http://www.iseesystems.com/Helpv10/Content/Reference/Builtins/Statisticall_builtins.htm
	'normal': ( mean, dev, seed ) => {
		/*if ( seed !== undefined ) {
			TODO something like this: http://stackoverflow.com/questions/521295/javascript-random-seeds
		}*/
		// Box-Muller transform
		const normal = 'Math.sqrt( -2 * Math.log( Math.random() ) ) * Math.cos( 2 * Math.PI * Math.random() )'
		return `((${normal} * (${dev})) + (${mean}))`
	},
	'random': ( min, max, seed ) => {
		if ( seed ) {
			throw new Error( 'RANDOM with <seed> is currently not supported' )
		}
		return `(Math.random() * ((${max}) - (${min})) + (${min}))`
	},



	// Test input builtins
	// http://www.iseesystems.com/Helpv10/Content/Reference/Builtins/Test_input_builtins.htm
	'pulse': ( volume, first, interval ) => {
		if ( first === undefined && interval === undefined ) {
			// Constant value
			return `(${volume})/dt`
		}
		if ( first === undefined ) {
			// Start immediately
			first = 'starttime'
		}
		if ( interval === undefined ) {
			// Repeat every dt
			return `(((${first}) <= t) ? ((${volume}) / dt) : 0 )`
		}
		if ( interval === 0 ) {
			// No repeat
			return `(((${first}) === t) ? ((${volume}) / dt) : 0 )`
		}
		// Default case
		return `((((${first}) <= t) && (t - (${first})) % (${interval}) === 0) ? ((${volume}) / dt) : 0 )`
	},
	'step': ( height, time ) => `( t < ${time} ? 0 : ${height} )`
}
