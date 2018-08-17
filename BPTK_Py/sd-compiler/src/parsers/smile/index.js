/*      _                   _ _
  _____| |__ ___ _ __  _ __(_| |___ _ _
 (_-/ _` / _/ _ | '  \| '_ | | / -_| '_|
 /__\__,_\__\___|_|_|_| .__|_|_\___|_|
                      |_|
 Copyright (c) 2013-2015 transentis management & consulting. All rights reserved.
*/
import fs from  'fs'
import pegjs from 'pegjs'
import _ from 'lodash'

const grammar = fs.readFileSync( `${__dirname}/grammar.pegjs`, 'utf8' )
const parser = pegjs.generate( grammar )

export default expression => {
	expression = expression && expression.trim() || ''
	// Some expressions are not defined
	expression = /{ .+ \\.\\.\\. }/.test( expression )
		? ''
		: expression
	try {
		return parser.parse( expression )
	} catch ( e ) {
		throw new Error( `Unable to parse "${expression}"\n${e}` )
	}
}
