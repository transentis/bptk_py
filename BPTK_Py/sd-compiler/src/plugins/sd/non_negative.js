/*      _                   _ _
  _____| |__ ___ _ __  _ __(_| |___ _ _
 (_-/ _` / _/ _ | '  \| '_ | | / -_| '_|
 /__\__,_\__\___|_|_|_| .__|_|_\___|_|
                      |_|
 Copyright (c) 2013-2015 transentis management & consulting. All rights reserved.
*/
import _ from 'lodash'

export default IR => {
	// in all models
	_.each( IR.models, model => {
		// find entities
		_.each( model.entities, entity => {
			// handle non negative attribute
			if ( entity.attributes.non_negative ) {
				// wrap all non trivial expressions
				if ( !_.isNumber( entity.expression.parsed ) ) {
					entity.expression.parsed = {
						name: 'max', type: 'call', args: [ 0, entity.expression.parsed ]
					}
				}
				else {
					entity.expression.parsed = Math.max( 0, entity.expression.parsed )
				}
			}
		})
	})
	return Promise.resolve( IR )
}
