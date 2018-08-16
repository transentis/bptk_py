/*      _                   _ _
  _____| |__ ___ _ __  _ __(_| |___ _ _
 (_-/ _` / _/ _ | '  \| '_ | | / -_| '_|
 /__\__,_\__\___|_|_|_| .__|_|_\___|_|
                      |_|
 Copyright (c) 2013-2015 transentis management & consulting. All rights reserved.
*/
import fs from 'fs'
import _ from 'lodash'
import { inspect } from 'util'
import handlebars from 'handlebars'
import UglifyES from 'uglify-es'
import generator from '../ast'
import builtins from './transforms/builtins'
import operators from './transforms/operators'

const template = fs.readFileSync( `${__dirname}/templates/model.hbs`, 'utf8' )
const header = fs.readFileSync( `${__dirname}/templates/functions.txt`, 'utf8' )

const minify = function ( code ) {
	let minified = code
	// check if thie code is only a single number
	if ( !_.isNaN( code * 1 ) ) {
		return `${code}`
	}
	// Uses uglify-js to simplify js equations
	try {
		// Do the simplification
		minified = UglifyES.minify( `const a = ${code}`, { mangle: false } ).code
		minified = minified
			// remove 'const a='
			.substring( 8 )
			// remove trailing semicolon
			.replace( /;$/, '' )
			.replace( /"/g, '\'' )
	}
	catch ( e ) {
		console.error( `uglify-js: Error while minifying "${code}". ${e}` )
		minified = code
	}
	finally {
		return minified
	}
}


module.exports = function ( IR ) {
	// create a expression generate function with
	var generate = generator({

		builtins,
		operators,

		identifier: node => `m['${node.name}'](t)`,
		array: node => {
			var args = _.map( node.args, arg => {
				return /m\[/.test( arg ) ? `'+(${arg})+'` : arg
			})
			return `m['${node.name}[${args}]'](t)`
		},
		comment: node => `/* ${node.args} */`,
		constant: node => node.toString(),
		label: node => node.name,
		nothing: () => '',
		unknown: node => {
			if ( node ) {
				const s = inspect( node, { depth: null, colors: true } )
				throw new Error( `Unknown node: ${s}` )
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
		events: [],
		specs: IR.specs,
		dimensions: IR.dimensions,
		header: ''
	}
	let functions_used = false
	// fill the context
	_.each( IR.models, model => {
		_.each( model.entities, entity => {
			const src = entity.expression.src
			let name = entity.name
			let expr = minify( generate( entity.expression.parsed ) )
			if ( entity.labels ) {
				name += `[${entity.labels}]`
			}
			// prepend zeros if uglify eats them
			if ( expr.indexOf( '.' ) === 0 ) {
				expr = '0' + expr
			}
			if ( entity.type === 'stock' ) {
				ctx.stocks.push({
					name: name,
					expression: expr,
					src
				})
			}
			if ( entity.type === 'flow' ) {
				ctx.flows.push({
					name: name,
					expression: expr,
					src
				})
			}
			if ( entity.type === 'aux' ) {
				if ( _.isNumber( entity.expression.parsed ) ) {
					ctx.constants.push({
						name: name,
						expression: expr,
						src
					})
				} else if ( entity.attributes.gf ){
					functions_used = true
					if ( entity.attributes.discrete ) {
						throw new Error( 'Type of graphical function not supported: discrete' )
					}
					if ( entity.attributes.extrapolate ) {
						throw new Error( 'Type of graphical function not supported: extrapolate' )
					}
					ctx.gf.push({
						name: name,
						expression: expr,
						src,
						points: entity.attributes.gf
					})
				} else {
					ctx.converters.push({
						name: name,
						expression: expr,
						src
					})
				}
			}
			if ( entity.events ) {
				_.each( entity.events, event => {
					event.entity = entity.name
					ctx.events.push( event )
				})
			}
		})
	})
	if ( functions_used ) {
		ctx.header = header
	}
	return handlebars.compile( template )( ctx )
}
