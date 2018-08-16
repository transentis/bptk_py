/*      _                   _ _
  _____| |__ ___ _ __  _ __(_| |___ _ _
 (_-/ _` / _/ _ | '  \| '_ | | / -_| '_|
 /__\__,_\__\___|_|_|_| .__|_|_\___|_|
                      |_|
 Copyright (c) 2013-2015 transentis management & consulting. All rights reserved.
*/
import { parser, plugins } from '../load'

export default src => Promise
	.resolve( src )
	.then( parser( 'xmile' ) )
	.then( plugins(
		'filterGhosts',
		'makeNameAbsolute',
		'sanitizeNames',
		'stockExpressions',
		'non_negative',
		'expandArrays',
		'sortEntities'
	))
