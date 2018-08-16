/*      _                   _ _
  _____| |__ ___ _ __  _ __(_| |___ _ _
 (_-/ _` / _/ _ | '  \| '_ | | / -_| '_|
 /__\__,_\__\___|_|_|_| .__|_|_\___|_|
                      |_|
 Copyright (c) 2013-2015 transentis management & consulting. All rights reserved.
*/
import fs from 'fs'
import path from 'path'
import minimist from 'minimist'
import { log, die, denodeify } from './helpers'
import strategies from './strategies'

const cwd = process.cwd()
const args = minimist( process.argv.slice( 2 ) )


	// .usage(
	// 	'\n        _                   _ _\n' +
	// 	'  _____| |__ ___ _ __  _ __(_| |___ _ _\n' +
	// 	' (_-/ _` / _/ _ | \'  \\| \'_ | | / -_| \'_|\n' +
	// 	' /__\\__,_\\__\\___|_|_|_| .__|_|_\\___|_|\n' +
	// 	'                      |_|\n' +
	// 	'Usage: sdcc -i srcpath [-o dstpath] [-t target] [-p prefix]' )
	// .string( 'i' )
	// .string( 'o' )
	// .string( 't' )
	// .string( 'p' )
	// .boolean( 'c' )
	// .describe( 'i', 'Input model file' )
	// .describe( 'o', 'Output filename. If not specified, the result will be printed to console.' )
	// .describe( 't', 'Compiler target language. Mandatory option unless a output filename is provided.' )
	// .describe( 'p', 'Prefix for all variables' )
	// .describe( 'c', 'color output' )
	// .demand( [ 'i' ] )
	// .argv
const read = denodeify( fs.readFile )
const write = denodeify( fs.writeFile )
const srcpath = args.i ? path.isAbsolute( args.i ) ? args.i : path.resolve( cwd, args.i ) : null
const dstpath = args.o ? path.isAbsolute( args.o ) ? args.o : path.resolve( cwd, args.o ) : null
const srcext = path.extname( srcpath )
const dstext = dstpath ? path.extname( dstpath ) : '.' + args.t

const isXMILE = srcext === '.itmx' || srcext === '.stmx'

const strategy = ( isXMILE && dstext === '.m' ) ?
					strategies.m :
				( isXMILE && dstext === '.js' ) ?
					strategies.js :
				( isXMILE && dstext === '.ir' ) ?
					strategies.ir :
				( isXMILE && dstext === '.py' ) ?
					strategies.py :
				( isXMILE && dstext === '.json' ) ?
					strategies.ir :
					false

if ( !strategy ) {
	process.stderr.write( `No appropriate compile strategy found. (${srcext},${dstext})\n` )
	process.exit( 1 )
}

read( srcpath )
	.catch( die( 'Error while reading src path' ) )
	.then( strategy )
	.catch( die( 'Error while compilation' ) )
	.then( code => {
		if ( dstpath ) {
			return write( dstpath, code, 'utf8' )
		} else {
			if ( args.t === 'ir' ) {
				return log( code, args.c )
			} else if ( args.t === 'json' ) {
				return process.stdout.write( JSON.stringify( code ) + '\n' )
			} else {
				return process.stdout.write( code + '\n' )
			}
		}
	})
	.catch( die( 'Error during output' ) )
	.then( () => process.exit( 0 ) )
