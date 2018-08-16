/*      _                   _ _
  _____| |__ ___ _ __  _ __(_| |___ _ _
 (_-/ _` / _/ _ | '  \| '_ | | / -_| '_|
 /__\__,_\__\___|_|_|_| .__|_|_\___|_|
                      |_|
 Copyright (c) 2013-2015 transentis management & consulting. All rights reserved.
*/
import _ from 'lodash'
import { traverseAST } from '../helpers'

// Identity checks
const isIdentifier = node => typeof node === 'object' && node.type && node.type === 'identifier'
const isOperator = node => typeof node === 'object' && node.type && node.type === 'operator'
const isCall = node => typeof node === 'object' && node.type && node.type === 'call'
const isArray = node => typeof node === 'object' && node.type && node.type === 'array'
const isNothing = node => typeof node === 'object' && node.type && node.type === 'nothing'
const isComment = node => typeof node === 'object' && node.type && node.type === 'comment'
const isLabel = node => typeof node === 'object' && node.type && node.type === 'label'
const isConstant = node => typeof node === 'number'
// Context Checks
const inArray = node => !!node && ( isArray( node.parent ) || inArray( node.parent ) )
const inCall = node => isCall( node.parent ) || inCall( node.parent )

// transforms a node from the syntax tree into something else
const transformNode = _.curry( ( options, node ) => {
	if ( isIdentifier( node ) ) {
		const transform = options.builtins[ node.name.toLowerCase() ]
		return transform ?
			transform.apply( null, node.args ) :
			options.identifier( node )
	}
	else if ( isOperator( node ) ) {
		const conv = options.operators[ node.name.toLowerCase() ]
		if ( conv )
			return conv.apply( null, node.args )
		else
			throw new Error( 'Unknown Operator: ' + JSON.stringify(node) )
	}
	else if ( isCall( node ) ) {
		const macro = options.builtins[ node.name.toLowerCase() ]
		if ( macro )
			return macro.apply( null, node.args )
		else
			throw new Error( 'Unknown Function Call: ' + JSON.stringify(node) )
	}
	else if ( isArray( node ) ) {
		return options.array( node )
	}
	else if ( isComment( node ) ) {
		return options.comment( node )
	}
	else if ( isConstant( node ) ) {
		return options.constant( node )
	}
	else if ( isLabel( node ) ) {
		return options.label( node )
	}
	else if ( isNothing( node ) ) {
		return options.nothing( node )
	}
	else {
		return options.unknown( node )
	}
})

export default opts => {
	const unimplemented = () => { throw new Error( 'not implemented' ) }
	const defaults = {
		builtins: undefined,
		operators: undefined,
		unknown: unimplemented,
		nothing: unimplemented,
		label: unimplemented,
		constant: unimplemented,
		array: unimplemented,
		comment: unimplemented,
		accessor: unimplemented,
		identifier: unimplemented
	}
	const options = _.merge( defaults, opts )
	// return a compiler function that excepts expressions
	return traverseAST( transformNode( options ) )
}
