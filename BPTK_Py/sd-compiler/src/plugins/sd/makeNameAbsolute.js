/*      _                   _ _
  _____| |__ ___ _ __  _ __(_| |___ _ _
 (_-/ _` / _/ _ | '  \| '_ | | / -_| '_|
 /__\__,_\__\___|_|_|_| .__|_|_\___|_|
                      |_|
 Copyright (c) 2013-2015 transentis management & consulting. All rights reserved.
*/
import _ from 'lodash'
import { traverseAST } from '../../helpers.js'


const prefix = require( 'optimist' ).argv.p || ''
const seperator = '.'
const normalizeName = name => name
		.replace( /\s+/g, '_' )
		.replace( /"/g, '' )


export default IR => {
	// Prepends the module name, if the name contains no dot
	const makeNameAbsolute = ( module, variable ) => {
		var $prefix = prefix ? prefix + seperator : ''
		// return the variable unless module is not empty
		var name = module === '' ? variable :
			// compose module and variable unless the variable name already contains the module
			variable.indexOf( seperator ) < 0 ? module + seperator + variable :
			variable.indexOf( seperator ) < 1 ? variable.substring(1) :
			// otherwise return the variable
			variable
		return $prefix + ( IR.assignments[name] || name )
	}

	const LABEL_CACHE = {}
	// in all dimensions
	_.each( IR.dimensions, dimension => {
		// each variable
		_.each( dimension.variables, variable => {
			variable.name =  makeNameAbsolute( variable.model, variable.name )
			// fill label cache for that variable
			LABEL_CACHE[normalizeName( variable.name )] = _.reduce( dimension.labels, ( hash, label ) => {
				hash[label] = true
				return hash
			}, {})
		})
	})

	// in all models
	_.each( IR.models, model => {
		// each entity
		_.each( model.entities, entity => {
			// sanitize entity names
			entity.name = makeNameAbsolute( model.name, entity.name )
			// sanitize in-/outflows
			if ( entity.attributes.inflows ) {
				entity.attributes.inflows = _.map( entity.attributes.inflows, makeNameAbsolute.bind( null, model.name ) )
			}
			if ( entity.attributes.outflows ) {
				entity.attributes.outflows = _.map( entity.attributes.outflows, makeNameAbsolute.bind( null, model.name ) )
			}
			// resolve array labels/identifiers ambigiouties
			const resolveLabelsToIdentifiers = traverseAST( node => {
				// look at each array
				if ( node.type === 'array' ) {
					_.each( node.args, arg => {
						// and their labels
						if ( arg.type === 'label' ) {
							// that are not a valid label for that arrayed constiale
							if ( !LABEL_CACHE[normalizeName( node.name )][arg.name] ) {
								// convert to an identifer
								arg.name = makeNameAbsolute( model.name, arg.name )
								arg.type = 'identifier'
							}
						}
					})
				}
				return node
			})
			// sanitize identifier and arrays in its expression(s)
			var makeExpressionAbsolute = traverseAST( node => {
				if ( node.type === 'identifier' || node.type === 'array' ) {
					if ( node.name === 'SELF' ) {
						node.name = entity.name
					}
					node.name = makeNameAbsolute( model.name, node.name )
					resolveLabelsToIdentifiers( node )
				}
				return node
			})
			// single expression definition
			if ( entity.expression.parsed !== undefined ) {
				if ( _.isArray( entity.expression.parsed ) ) {
					_.each( entity.expression.parsed, makeExpressionAbsolute )
				}
				else {
					makeExpressionAbsolute( entity.expression.parsed )
				}
			// array of expressions
			} else {
				_.each( entity.expression, expression => {
					if ( expression.parsed.args ) {
						makeExpressionAbsolute( expression.parsed )
					}
				})
			}
		})
	})

	return Promise.resolve( IR )
}
