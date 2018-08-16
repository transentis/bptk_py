/*      _                   _ _
  _____| |__ ___ _ __  _ __(_| |___ _ _
 (_-/ _` / _/ _ | '  \| '_ | | / -_| '_|
 /__\__,_\__\___|_|_|_| .__|_|_\___|_|
                      |_|
 Copyright (c) 2013-2015 transentis management & consulting. All rights reserved.
*/

// A map to translate SMILE operators to JS operators
export default {
	'+': ( lhs, rhs ) => `${lhs} + ${rhs}`,
	'-': ( lhs, rhs ) => `${lhs} - ${rhs}`,
	'*': ( lhs, rhs ) => `${lhs} * ${rhs}`,
	'/': ( lhs, rhs ) => `${lhs} / ${rhs}`,
	'^': ( lhs, rhs ) => `Math.pow(${lhs},${rhs})`,
	'=': ( lhs, rhs ) => `((${lhs}) === (${rhs}))`,
	'>': ( lhs, rhs ) => `((${lhs}) > (${rhs}))`,
	'<': ( lhs, rhs ) => `((${lhs}) < (${rhs}))`,
	'>=': ( lhs, rhs ) => `((${lhs}) >= (${rhs}))`,
	'<=': ( lhs, rhs ) => `((${lhs}) <= (${rhs}))`,
	'<>': ( lhs, rhs ) => `((${lhs}) !== (${rhs}))`,
	'mod': ( lhs, rhs ) => `((${lhs}) % (${rhs}))`,
	'()': ( body ) => `(${body})`,
	'and': ( lhs, rhs ) => `((${lhs}) && (${rhs}))`,
	'or': ( lhs, rhs ) => `((${lhs}) || (${rhs}))`
}
