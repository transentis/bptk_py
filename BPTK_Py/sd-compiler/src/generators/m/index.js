/*      _                   _ _
  _____| |__ ___ _ __  _ __(_| |___ _ _
 (_-/ _` / _/ _ | '  \| '_ | | / -_| '_|
 /__\__,_\__\___|_|_|_| .__|_|_\___|_|
                      |_|
 Copyright (c) 2013-2015 transentis management & consulting. All rights reserved.
*/
import fs from 'fs'
import _ from 'lodash'
import handlebars from 'handlebars'
import generator from '../ast'
import builtins from './transforms/builtins'
import operators from './transforms/operators'

const template = fs.readFileSync( `${__dirname}/templates/package.hbs`, 'utf8' )
const prefix = require( 'optimist' ).argv.p || ''
const seperator = '▸'

module.exports = function ( IR ) {
	// create a expression generate function with
	const generate = generator({
		builtins,
		operators,
		identifier: node => `${node.name}[t,dt]`,
		array: node => `${node.name}▸${node.args.join( '' )}[t,dt]`,
		comment: node => `(* ${node.args} *)`,
		constant: node => node.toString(),
		label: node => node.name,
		nothing: () => '',
		unknown: node => {
			if ( node ) {
				throw new Error( `Unknown node: ${JSON.stringify( node )}` )
			}
		}
	})

	// create a context for the template generator
	const ctx = {
		stocks: [],
		flows: [],
		converters: [],
		constants: [],
		gf: [],
		defaults: [],
		specs: IR.specs,
		dimensions: IR.dimensions,
		name: IR.name,
		prefix: prefix ? prefix + seperator : '',
		namespace: prefix || 'model'
	}
	// fill the context
	_.each( IR.models, function ( model ) {
		_.each( model.entities, function ( entity ) {
			const name = entity.name + ( entity.labels ? '▸' + entity.labels.join( '' ) : '' )
			// wrap expression into N to speedup the simulation in mathematica
			const expr = generate( entity.expression.parsed )
			if ( entity.type === 'stock' ) {
				ctx.stocks.push({
					name: name,
					// wrap expression into N to speedup the simulation in mathematica
					expression: `N[${expr}]`
				})
			}
			if ( entity.type === 'flow' ) {
				ctx.flows.push({
					name: name,
					// wrap expression into N to speedup the simulation in mathematica
					expression: `N[${expr}]`
				})
			}
			if ( entity.type === 'aux' ) {
				if ( _.isNumber( entity.expression.parsed ) ) {
					ctx.constants.push({
						name: name,
						// wrap expression into N to speedup the simulation in mathematica
						expression: `N[${expr}]`
					})
					ctx.defaults.push({
						name: name,
						expression: `N[${expr}]`
					})
				} else if ( entity.attributes.gf ) {
					if ( entity.attributes.extrapolate ) {
						throw new Error( 'Type of graphical function not supported: extrapolate' )
					}
					ctx.gf.push({
						name: name,
						// wrap expression into N to speedup the simulation in mathematica
						expression: `N[${expr}]`,
						points: '{'+entity.attributes.gf.map( p => `{${p}}` )+'}',
						discrete: entity.attributes.discrete,
						start: '{{'+[ IR.specs.start - 1, 0 ]+'}}',
						stop: '{{'+[ IR.specs.stop + 1, 0 ]+'}}'
					})
					ctx.defaults.push({
						name: name,
						expression: '{'+entity.attributes.gf.map( p => `{${p}}` )+'}'
					})
				} else {
					ctx.converters.push({
						name: name,
						// wrap expression into N to speedup the simulation in mathematica
						expression: `N[${expr}]`
					})
					ctx.defaults.push({
						name: name,
						expression: expr
					})
				}
			}
		})
	})

	return handlebars.compile( template )( ctx ).replace( /▸/g, '\\[RightPointer]'  )
}
