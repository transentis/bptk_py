/*      _                   _ _
  _____| |__ ___ _ __  _ __(_| |___ _ _
 (_-/ _` / _/ _ | '  \| '_ | | / -_| '_|
 /__\__,_\__\___|_|_|_| .__|_|_\___|_|
                      |_|
 Copyright (c) 2013-2015 transentis management & consulting. All rights reserved.
*/

import util from 'util'
import _ from 'lodash'

// Returns a function that can be used on a tree.
// The returned 'walk' applies 'callback' to all nodes (in post-order).
export const traverseAST = callback => {
	return function walk ( node ) {
		if ( node && node.args ) {
			node.args = node.args.map( walk )
		}
		return node && callback( node )
	}
}

export const die = msg => err => {
	const errmsg = `[SDCompiler] Fatal: ${msg}\n${err.stack.trim()}`
	// in node
	if ( process.stderr ) {
		process.stderr.write( errmsg + '\n' )
		process.exit( 1 )
	}
	// in a webworker
	else if ( self ) {
		self.console.log( err )
		self.postMessage({ status: 'error', message: JSON.stringify(err) /*errmsg*/ })
	}
	// default browser
	else {
		throw new Error( errmsg )
	}
}

export const log = ( arg, colors, depth ) => {
	if ( process.stdout ) {
		process.stdout.write( util.inspect( arg, { colors: colors, depth: depth } ) + '\n' )
	} else {
		console.log( arg )
	}
	return arg
}

export const denodeify = func => (...args) => new Promise( ( resolve, reject ) => {
	func( ...args, ( err, data ) => {
		if ( err ) { reject( err ) }
		else { resolve( data ) }
	})
})

export const joinedExpression = ( names, operator ) => {
	if ( !_.isString( operator ) ) {
		throw new Error( 'no operator provided' )
	}
	if ( !_.isArray( names ) || _.isEmpty( names ) ) {
		return { name: '', type: 'nothing' }
	}
	else if ( names.length === 1 ) {
		return { name: names[0], type: 'identifier' }
	}
	else if ( names.length === 2 ) {
		return {
			name: operator,
			type: 'operator',
			args: [
				{ name: names[0], type: 'identifier' },
				{ name: names[1], type: 'identifier' }
			]
		}
	} else if ( names.length > 2) {
		const tail = names.slice( -2 )
		const rest = names.slice( 0, -2 )
		return _.reduceRight( rest, ( lhs, rhs ) => {
			return {
				name: operator,
				type: 'operator',
				args: [ { name: rhs, type: 'identifier' }, lhs ]
			}
		}, {
			name: operator,
			type: 'operator',
			args: [
				{ name: tail[0], type: 'identifier' },
				{ name: tail[1], type: 'identifier' }
			]
		})
	}
}
