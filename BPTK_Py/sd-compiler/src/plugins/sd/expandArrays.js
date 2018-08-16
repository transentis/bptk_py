/*      _                   _ _
  _____| |__ ___ _ __  _ __(_| |___ _ _
 (_-/ _` / _/ _ | '  \| '_ | | / -_| '_|
 /__\__,_\__\___|_|_|_| .__|_|_\___|_|
                      |_|
 Copyright (c) 2013-2015 transentis management & consulting. All rights reserved.
*/
import _ from 'lodash'
import { traverseAST, log } from '../../helpers'


const cartesianProduct = ( a, b, ...rest ) =>
	_.isUndefined( b ) ?
		// no need to build a cartesion product
		// instead simply return a
		a :
		// otherwise return the product of all
		// values in the arguments
		_.reduce( [ a, b, ...rest ], ( a, b ) =>
			_.flatten(
				_.map( a, x => _.map( b, y => x.concat( [y] ) ) )
			),
			[[]]
		)

const toLabelObjects = labels =>
	_.isArray( labels )
		? labels.map( label => ({ name: label, type: 'label' }) )
		: [ { name: labels, type: 'label' } ]


export default IR => {
	// in all models
	_.each( IR.models, model => {
		// find entities
		_.each( model.entities, entity => {
			let $entities = null
			// if entity expressions are arrayed
			if ( _.isArray( entity.expression.src ) ) {
				// for each expression clone entity
				$entities = _.times( entity.expression.src.length, idx => {
					const $entity = _.cloneDeep( entity )
					$entity.labels = entity.labels[idx]
					$entity.expression.src = entity.expression.src[idx]
					$entity.expression.parsed = entity.expression.parsed[idx]
					model.entities.push( $entity )
					return $entity
				})
			// if entity has dimensions
			} else if ( entity.dimensions ) {
				// get all labels for each dimension
				const labels = _.map( entity.dimensions, name => IR.dimensions[name].labels )
				// build the cartesian product of these labels
				const products = cartesianProduct( ...labels )
				// for each product, clone the entity
				$entities = _.map( products, ( product, idx ) => {
					const $entity = _.cloneDeep( entity )
					$entity.labels = product
					// if its a stock entity
					if ( $entity.type === 'stock' ) {
						// search for the if expression
						traverseAST( node => {
							if ( node.name === 'IF' ) {
								// TODO: Why? This obviously breaks :(
								// and pick the right initial value
								// node.args[1] = node.args[1][idx]
							}
							return node
						})( $entity.expression.parsed )
					}
					model.entities.push( $entity )
					return $entity
				})
			}
			// if we have cloned entities
			if ( $entities ) {
				// alter the expression of the origin entity to be the sum of all cloned entities
				// in theory dimensions could only have one label
				if ( $entities.length === 1 ) {
					// the expression is simply the array
					entity.expression = {
						parsed: {
							name: $entities[0].name,
							type: 'array',
							args: toLabelObjects( $entities[0].expression.labels )
						}
					}
				}
				// dimension of two labels
				else if ( $entities.length === 2 ) {
					// the expressions is the sum of both accessors
					entity.expression = {
						parsed: {
							name: '+',
							type: 'operator',
							args: [
								{ name: $entities[0].name, type: 'array', args: toLabelObjects( $entities[0].expression.labels ) },
								{ name: $entities[1].name, type: 'array', args: toLabelObjects( $entities[1].expression.labels ) }
							]
						}
					}
				// default case where the number of labels is greater than two
				} else if ( $entities.length > 2 ) {
					// split the cloned entities into a tail of two entites,
					// which will form the first addition and the rest,
					// that will be recusivly added two the syntax tree
					const tail = $entities.slice( -2 )
					const rest = $entities.slice( 0, -2 )
					const sum = _.reduceRight( rest, function ( lhs, rhs ) {
						return {
							name: '+',
							type: 'operator',
							args: [ { name: rhs.name, type: 'array', args: toLabelObjects( rhs.labels ) }, lhs ]
						}
					}, {
						name: '+',
						type: 'operator',
						args: [
							{ name: tail[0].name, type: 'array', args: toLabelObjects( tail[0].labels ) },
							{ name: tail[1].name, type: 'array', args: toLabelObjects( tail[1].labels ) }
						]
					})
					// write the sum into the expression into original entity
					entity.expression = { parsed: sum }
					// remove labels
					delete entity.labels
				}
				// alter the identifier in the expressions of the cloned entities
				// for each cloned entity
				_.each( $entities, $entity => {
					// traverse the parsed expression
					traverseAST( node => {
						// and watch for identifer
						if ( node.type === 'identifier' ) {
							const labels = []
							// look at each dimension
							_.each( $entity.dimensions, ( name, index ) => {
								const dimension = IR.dimensions[ name ]
								// if the identifier is also of that dimension
								const found = _.filter( dimension.variables, variable =>
									variable.model === model.name && variable.name === node.name
								).length > 0
								// add the corresponding label
								if ( found ) {
									labels.push( $entity.labels[ index ] )
								}
							})
							// if we've found labels
							if ( !_.isEmpty( labels ) ) {
								// alter the node's type to array
								node.type = 'array'
								// and set the args to be the list of found labels
								node.args = toLabelObjects( labels )
							}
						}
						return node
					})( $entity.expression.parsed )
				})
			}
			// spread function arguments
			traverseAST( node => {
				// look for function calls
				if ( node.type === 'call' ) {
					// and their arguments
					const args = []
					// look at each argument
					_.each( node.args, arg => {
						// if the argument is an identifier for an arrayed variable
						// it will be converted to an array with asterisks for each dimension
						//
						// example: lets say 'bar' has two dimensions
						//     bar -> bar[*,*]
						if ( arg.type === 'identifier' ) {
							// for each dimension
							const asterisks = _.filter( IR.dimensions, dimension =>
								// the variable has
								_.filter( dimension.variables, variable =>
									variable.model === model.name && variable.name === arg.name
								).length > 0
							).map( () => (
								// map to an asterisk object
								{ name: '*', type: 'asterisk' }
							))
							// and if the if the variable as dimension
							if ( !_.isEmpty( asterisks ) ) {
								// alter the node's type to array
								arg.type = 'array'
								// and set the args to be the list of asterisks
								arg.args = asterisks
							}
						}
						// if it is an array expression
						if ( arg.type === 'array' ) {
							const dimensions = _.compact( _.map( IR.dimensions, dimension =>
								dimension.variables.filter( variable =>
									variable.model === model.name && variable.name === arg.name
								).length > 0 && dimension.labels
							))
							// create new args
							const products = cartesianProduct( ...arg.args.map( ( $arg, index ) => {
								const $labels = dimensions[index]
								if ( $arg.type === 'asterisk' ) {
									return $labels
								}
								else if ( $arg.type === 'range' ) {
									const range = _.map( $arg.args, arg => arg.name )
									const start = _.lastIndexOf( $labels, range[0] )
									const end = _.lastIndexOf( $labels, range[1] ) + 1
									return _.slice( $labels, start, end )
								}
								else if ( $arg.type === 'label' ) {
									return $arg.name
								} else if ( $arg.type === 'identifier' ) {
									return $arg
								}
								else {
									throw new Error( 'Expressions in Array are not supported yet.' )
								}
							}))
							_.each( products, product => {
								args.push({
									name: arg.name,
									type: 'array',
									args: toLabelObjects( product )
								})
							})
						}
						// otherwise just add the argument
						else {
							args.push( arg )
						}
					})
					// set args
					node.args = args
				}
				return node
			})( entity.expression.parsed )
		})
	})
	return Promise.resolve( IR )
}
