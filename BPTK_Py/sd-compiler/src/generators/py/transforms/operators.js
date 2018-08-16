/*      _                   _ _
  _____| |__ ___ _ __  _ __(_| |___ _ _
 (_-/ _` / _/ _ | '  \| '_ | | / -_| '_|
 /__\__,_\__\___|_|_|_| .__|_|_\___|_|
                      |_|
 Copyright (c) 2013-2015 transentis management & consulting. All rights reserved.
*/
'use strict';

// A map to translate SMILE operators to JS operators
module.exports = {
	'+': function ( lhs, rhs ) {
		return lhs + ' + ' + rhs
	},
	'-': function ( lhs, rhs ) {
		return lhs + ' - ' + rhs
	},
	'*': function ( lhs, rhs ) {
		return lhs + ' * ' + rhs
	},
	'/': function ( lhs, rhs ) {
		return lhs + ' / ' + rhs
	},
	'^': function ( lhs, rhs ) {
		return  lhs + '**' + rhs
	},
	'=': function ( lhs, rhs ) {
		return  lhs + ' == ' + rhs
	},
	'>': function ( lhs, rhs ) {
		return  lhs + ' > ' + rhs
	},
	'<': function ( lhs, rhs ) {
		return  lhs + ' < ' + rhs
	},
	'>=': function ( lhs, rhs ) {
		return lhs + ' >= ' + rhs
	},
	'<=': function ( lhs, rhs ) {
		return  lhs + ' <= ' + rhs
	},
	'<>': function ( lhs, rhs ) {
		return lhs + ' != ' + rhs
	},
	'mod': function ( lhs, rhs ) {
		return  lhs + ' % ' + rhs
	},
	'()': function ( body ) {
		return '( ' + body + ' )'
	},
	'and': function ( lhs, rhs ) {
		return  lhs + ' and ' + rhs
	},
	'or': function ( lhs, rhs ) {
		return  lhs + ' or ' + rhs 
	}
}
