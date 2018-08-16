/*      _                   _ _
  _____| |__ ___ _ __  _ __(_| |___ _ _
 (_-/ _` / _/ _ | '  \| '_ | | / -_| '_|
 /__\__,_\__\___|_|_|_| .__|_|_\___|_|
                      |_|
 Copyright (c) 2013-2015 transentis management & consulting. All rights reserved.
*/
import _ from 'lodash'
import { joinedExpression } from '../../helpers'


export default IR => {
	const method = IR.specs.method.toLowerCase()
	if ( method !== 'euler' ) {
		throw new Error( 'currently only Euler\'s approximation is supported' )
	}
	// in all models
	_.each( IR.models, model => {
		// find entities
		_.each( model.entities, entity => {
			// that are stocks
			if ( entity.type !== 'stock' ) return
			// ∑Flows
			const inflows = joinedExpression( entity.attributes.inflows, '+' )
			const outflows = joinedExpression( entity.attributes.outflows, '+' )
			let sum = 0
			// only inflows
			if ( inflows.type !== 'nothing' && outflows.type === 'nothing' ) {
				sum = { name: '()', type: 'operator', args: [ inflows ] }
			// only outflow
			} else if ( inflows.type === 'nothing' && outflows.type !== 'nothing' ) {
				sum = { name: '()', type: 'operator', args: [
					{ name: '*', type: 'operator', args: [
						-1,
						{ name: '()', type: 'operator', args: [ outflows ]}
					]}
				]}
			// no flows
			} else if ( inflows.type === 'nothing' && outflows.type === 'nothing'  ) {
				sum = 0
			// inflows and outflow
			} else {
				sum = { name: '()', type: 'operator', args: [
					{ name: '-', type: 'operator', args: [
						inflows,
						{ name: '()', type: 'operator', args: [ outflows ]}
					]}
				]}
			}
			// stock(t) = if t < starttime then initial else stock(t-1) + dt * ∑Flows
			const expression = {
			 name: 'IF', type: 'call', args: [
				{ name: '<=', type: 'operator', args: [
					{ name: 'TIME', type: 'call', args: []  },
					{ name: 'STARTTIME', type: 'call', args: [] }
				]},
				entity.expression.parsed, // initial
				{ name: '+', type: 'operator', args: [
					{ name: 'PREVIOUS', type: 'call', args: [
						{ name: entity.name, type: 'identifier' }
					]},
					{ name: '*', type: 'operator', args: [
						{ name: 'DT', type: 'call', args: [] },
						{ name: 'PREVIOUS', type: 'call', args: [ sum ]}
					]}
				]}
			]}
			entity.expression = { parsed: expression }
		})
	})
	return Promise.resolve( IR )
}
