/*      _                   _ _
  _____| |__ ___ _ __  _ __(_| |___ _ _
 (_-/ _` / _/ _ | '  \| '_ | | / -_| '_|
 /__\__,_\__\___|_|_|_| .__|_|_\___|_|
                      |_|
 Copyright (c) 2013-2015 transentis management & consulting. All rights reserved.
*/
import _ from 'lodash'
import { traverseAST } from '../../helpers.js'

// Sanitizes iThink names
const sanitizeName = name =>
	name
		// replace namespace delimiter
		.replace( /\./g, '▸' )
		// remove quotes and dashes
		.replace( /['"\-]/g, '' )
		// replace all % with pct
		.replace( /%/g, 'PCT' )
		// replace \\n with _
		.replace( /[\\]+n/g, '_' )
		// replace witespaces with _
		.replace( /\s+/g, '_' )
		// Merge underscores
		.replace( /_+/g, '_' )
		// replace multiple spaces
		.replace( /[ ]+/g, ' ' )
		// replace currency symbols with ISO 4217 currency names
		.replace( /\$/g, 'USD' )
		.replace( /€/g, 'EUR' )
		.replace( /£/g, 'GBP')
		.replace( /¥/g,'JPY' )
		.toLowerCase()
		// Camel casing
		.split( '_' )
		.map( function ( word, i ) {
			return i === 0 ? word : word.charAt(0).toUpperCase() + word.slice(1)
		})
		.join( '' )


export default IR => {
	// in all models
	_.each( IR.models, model => {
		model.name = sanitizeName( model.name )
		// each entity
		_.each( model.entities, entity => {
			// sanitize entity names
			entity.name = sanitizeName( entity.name )
			// sanitize in-/outflows
			if ( entity.attributes.inflows ) {
				entity.attributes.inflows = _.map( entity.attributes.inflows, sanitizeName )
			}
			if ( entity.attributes.outflows ) {
				entity.attributes.outflows = _.map( entity.attributes.outflows, sanitizeName )
			}
			// sanitize identifier/arrays in its expression(s)
			const sanitizeExpression = traverseAST( node => {
				if ( node.type === 'identifier' || node.type === 'array' ) {
					node.name = sanitizeName( node.name )
				}
				return node
			})
			// single expression definition
			if ( entity.expression.parsed !== undefined ) {
				if ( _.isArray( entity.expression.parsed ) ) {
					_.each( entity.expression.parsed, sanitizeExpression )
				} else {
					sanitizeExpression( entity.expression.parsed )
				}
			// array of expressions
			} else {
				_.each( entity.expression, expression => {
					if ( expression.parsed.args ) {
						expression.parsed = sanitizeExpression( expression.parsed )
					}
				})
			}
		})
	})
	// in all dimensions
	_.each( IR.dimensions, function ( dimension ) {
		// each variable
		_.each( dimension.variables, function ( variable ) {
			// sanitite model name
			variable.model =  sanitizeName( variable.model )
			// sanitize variable name
			variable.name =  sanitizeName( variable.name )
		})
	})
	return Promise.resolve( IR )
}
