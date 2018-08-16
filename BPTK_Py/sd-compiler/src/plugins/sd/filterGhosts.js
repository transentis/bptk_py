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
		// filter ghost entities
		model.entities = _.filter( model.entities, entity => {
			const { access } = entity.attributes
			return _.isUndefined( access ) || access !== 'input'
		})
	})
	return Promise.resolve( IR )
}
