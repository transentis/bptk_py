/*      _                   _ _
  _____| |__ ___ _ __  _ __(_| |___ _ _
 (_-/ _` / _/ _ | '  \| '_ | | / -_| '_|
 /__\__,_\__\___|_|_|_| .__|_|_\___|_|
                      |_|
 Copyright (c) 2013-2015 transentis management & consulting. All rights reserved.
*/
import _ from 'lodash'
import fs from 'fs'
import xml2js from 'xml2js'
import smile_parser from '../smile'
import { log, die, denodeify } from '../../helpers'

// resolve the value for the given key
const getAll = ( node, key ) => node && node[ key ]
const get = ( node, key ) => {
	// resolve the value for the given key
	const value = getAll( node, key )
	// return the first child node if it is a single node
	return _.isArray( value ) && value.length === 1 ? _.first( value ) : value
}
const attr = ( node, name ) => node && node.$ && node.$[ name ]
const setAttr = ( node, name, value ) => {
	if ( node && node.$ ) {
		node.$[name] = value
	}
}
const createEntity = ( node, type ) => {
	const entity = {
		name: attr( node, 'name' ).replace( '\\n+', '_' ),
		type: type,
		expression: {},
		dimensions: false,
		attributes: {}
	}
	// parse dimensions
	let dims = get( get( node, 'dimensions' ), 'dim' )
	let labels = []
	const childtype = node.element ? 'element' : type
	if ( dims ) {
		dims = !_.isArray( dims ) ? [ dims ] : dims
		entity.dimensions = _.map( dims, dim => attr( dim, 'name' ) )
		// extract all array labels
		labels = _.map( getAll( node, childtype ), child => attr( child, 'subscript' ).split( /,\s*/ ) )
	}
	// parse equation
	if ( !_.isEmpty( labels ) ) {
		entity.expression.src = _.map( getAll( node, childtype ), child => get( child, 'eqn' ) )
		entity.labels = labels
	} else {
		entity.expression.src = get( node, 'eqn' )
	}
	// parse access field
	if ( !!attr( node, 'access' ) ) {
		entity.attributes.access = attr( node, 'access' )
	}
	// parse non_negative field
	if ( !!node.non_negative ) {
		entity.attributes.non_negative = true
	}
	// parse inflows
	if ( !!getAll( node, 'inflow' ) ) {
		entity.attributes.inflows = getAll( node, 'inflow' )
	}
	// parse outflows
	if ( !!getAll( node, 'outflow' ) ) {
		entity.attributes.outflows = getAll( node, 'outflow' )
	}
	// parse doc field
	if ( !!get( node, 'doc' ) ) {
		entity.attributes.doc = get( node, 'doc' )
	}
	//parse gf field
	if ( node.gf ) {
		let ypoints, xpoints
		let minX, maxX
		let gf = node.gf[0]
		// Read ypoints directly
		ypoints = gf.ypts[0].split( ',' ).map( parseFloat )
		// Create xpoints array, there are two possible notations
		if ( gf.xpts === undefined ) {
			// Walk from "min" to "max" attribute of xscale in ypoints.length steps
			xpoints = []
			minX = parseFloat( gf.xscale[0].$.min )
			maxX = parseFloat( gf.xscale[0].$.max )
			for ( let k = 0; k < ypoints.length; k += 1 ) {
				xpoints.push( minX + k * ( maxX - minX ) / ( ypoints.length - 1 ) )
			}
		}
		else {
			// Read xpoints directly
			xpoints = gf.xpts[0].split( ',' ).map( parseFloat )
		}
		entity.attributes.gf = _.zip( xpoints, ypoints )
		// parse type
		if ( !!attr( gf, 'type' ) ) {
			entity.attributes.discrete = attr( gf, 'type' ) === 'discrete'
			entity.attributes.extrapolate = attr( gf, 'type' ) === 'extrapolate'
		}
	}
	// parse event posters
	if ( !!get( node, 'event_poster' ) ) {
		const poster = get( node, 'event_poster' )
		if ( poster ) {
			entity.events = _.map( getAll( poster, 'threshold' ), threshold => {
				return {
					threshold: parseFloat( attr( threshold, 'value' ) ),
					direction: attr( threshold, 'direction' ) === 'decreasing' && '<' || '>',
					repeat: attr( threshold, 'repeat' ) || 'each',
					interval: parseFloat( attr( threshold, 'interval' ) ) || 0,
					messages: _.map( getAll( threshold, 'event' ), event => {
						const msg = get( event, 'text_box' )
						// only text_box message are supported
						return  msg ? {
							message: msg,
							action: attr( event, 'sim_action' ) || 'pause'
						} : null
					})
				}
			})
		}
	}
	return entity
}

const getEntities = _.curry( ( model, type ) => {
	const elements = get( model, 'variables' ) || model
	const entities = []
	// first of all, find all directly defined entities
	const direct = getAll( elements, type )
	_.each( direct, node => {
		const entity = createEntity( node, type )
		entities.push( entity )
	})
	// then search in all array definitions of that type
	const arrays = getAll( elements, 'array' )
	_.each( arrays, node => {
		// skip array of other types
		if ( _.isUndefined( get( node, type ) ) ) return
		const entity = createEntity( node, type )
		entities.push( entity )
	})
	return entities
})


// Parses a given xml2js Object-Structure into IR
const parseXMILE = xml => {
	const xmile = xml.xmile
	if ( !xmile ) throw new Error( 'Parsed xml file is no XMILE' )
	const header = get( xmile, 'header' )
	const specs = get( xmile, 'sim_specs' )
	const IR = {
		name: get( header, 'name' ),
		models: [],
		assignments: {},
		dimensions: {},
		specs: {
			method: attr( specs, 'method' ) || '',
			units: attr( specs, 'time_units' ) || '',
			start: parseFloat( get( specs, 'start' ) ),
			stop: parseFloat( get( specs, 'stop' ) ),
			dt: attr( get( specs, 'dt' ), 'reciprocal' ) === 'true' ?
				1/parseFloat( get( specs, 'dt' )._ ) :
				parseFloat( get( specs, 'dt' ) )
		}
	}

	// parse dimensions
	var dimensions = get( xmile, 'dimensions' )
	if ( dimensions ) {
		_.each( dimensions.dim, dim => {
			var name = attr( dim, 'name' )
			var size = attr( dim, 'size' )
			var dimension = IR.dimensions[ name ] = { name: name, labels: null, variables: [] }
			// list of all names within the dimension (can be any
			// arbitrary name or number)
			dimension.labels = _.isUndefined( size ) ?
				// if no size attribute is given, map all element labels
				_.map( dim.elem, elem => {
					return attr( elem, 'name' )
				}) :
				// otherwise create a list of string numbers
				_.times( size, n => ( n + 1 ) + '' )
		})
	}

	// parse all arrayed variables
	_.each( xmile.model, model => {
		const name = attr( model, 'name' ) || ''
		const variables = get( model, 'variables' ) || model
		// parse each models childnodes
		_.each( variables, function ( entities, type ) {
			// only parse stocks, flows, aux and arrays
			if ( !/stock|flow|aux|array/.test( type ) ) { return }
			_.each( entities, function ( entity ) {
				const dims = get( get( entity, 'dimensions' ), 'dim' )
				if ( dims ) {
					// add entity to the dimensions index
					_.each( dims, dim => {
						const dimension = dim.name || attr( dim, 'name' )
						const variable = attr( entity, 'name' )
						IR.dimensions[ dimension ].variables.push({
							model: name,
							name: variable
						})
					})
				}
			})
		})
	})

	// parse assignments
	_.each( xmile.model, model => {
		// skip all non-root models
		if ( !_.isUndefined( attr( model, 'name' ) ) ) { return }
		// extract assignments
		const variables = get( model, 'variables' )
		_.each( get( variables, 'module' ), module => {
			const connects = getAll( module, 'connect' )
			if ( connects ) {
				_.each( connects, connect => {
					const from = attr( connect, 'from' )
					const to = attr( connect, 'to' )
					if ( !from || !to ) { return }
					IR.assignments[ to ] = from
				})
			}
		})
	})

	// Run through the XML and extract all the stuff we need
	IR.models = _.map( xmile.model, module => {
		const model = {
			name: attr( module, 'name' ) || '',
			entities: []
		}
		// create a localized version
		const $getEntities = getEntities( module )
		// Stocks
		model.entities.push( ...$getEntities( 'stock' ) )
		// Flows
		model.entities.push( ...$getEntities( 'flow' ) )
		// Converters
		model.entities.push( ...$getEntities( 'aux' ) )
		return model
	})

	return Promise.resolve( IR )
}

// parses all expressions for all entities in the IR
const parseSMILE = IR => {
	_.each( IR.models, model => {
		_.each( model.entities, entity => {
			if ( entity.labels ) {
				entity.expression.parsed = _.map( entity.expression.src, smile_parser )
			} else {
				entity.expression.parsed = smile_parser( entity.expression.src )
			}
		})
	})
	return Promise.resolve( IR )
}

export default file => {
	const xml2jsParser = new xml2js.Parser()
	const parseXML = denodeify( xml2jsParser.parseString )
	return parseXML( file )
		.catch( die( 'Error while parsing XML file' ) )
		.then( parseXMILE )
		.catch( die( 'Error while parsing XMILE document' ) )
		.then( parseSMILE )
		.catch( die( 'Error while parsing SMILE expressions' ) )
}
