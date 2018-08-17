/*      _                   _ _
  _____| |__ ___ _ __  _ __(_| |___ _ _
 (_-/ _` / _/ _ | '  \| '_ | | / -_| '_|
 /__\__,_\__\___|_|_|_| .__|_|_\___|_|
                      |_|
 Copyright (c) 2013-2015 transentis management & consulting. All rights reserved.
*/
import _ from 'lodash'
import fs from 'fs'
import Plugins from '../plugins/sd'
import Parsers from '../parsers'
import { die } from '../helpers'
import generators from '../generators'

export const compiler = target => {
	// select appropriate compiler
	const compile = generators[ target ]
	if ( !compile ) {
		throw new Error( `Unknown compiler: "${target}"` )
	}
	return IR => Promise
		.resolve( IR )
		.then( compile )
		.catch( die( 'Error during compilation' ) )
}

export const parser = target => {
	// select appropriate parser
	const parser = Parsers[target]
	if ( !parser ) {
		throw new Error( `Unknown parser: "${target}"` )
	}
	return src => parser( src ).catch( die( 'Error while parsing input' ) )
}

export const plugins = ( ...names ) => {
	// load plugins
	const plugins = names.map( name => {
		const plugin = Plugins[name]
		if ( !plugin ) {
			throw new Error( `Plugin '${name}' does not exist in the plugin directory.` )
		}
		return plugin
	})
	return IR => {
		const [ head, ...tail ] = plugins
		return tail.reduce(
				( prev, next ) => prev.then( next ),
				head( IR )
			)
			.catch( die( 'Error while running plugins' ) )
	}
}
