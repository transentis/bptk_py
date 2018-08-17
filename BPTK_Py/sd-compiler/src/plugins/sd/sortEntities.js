/*      _                   _ _
  _____| |__ ___ _ __  _ __(_| |___ _ _
 (_-/ _` / _/ _ | '  \| '_ | | / -_| '_|
 /__\__,_\__\___|_|_|_| .__|_|_\___|_|
                      |_|
 Copyright (c) 2013-2015 transentis management & consulting. All rights reserved.
*/
import _ from 'lodash'

const sortByName = ( a, b ) =>
	a.name > b.name ? 1 :
	a.name < b.name ? -1 :
	(a.labels || '') + '' > (b.labels || '') + '' ? 1 : -1

export default IR => {
	// for each model
	_.each( IR.models, model => {
		// sort entities
		model.entities.sort( sortByName )
	})
	return Promise.resolve( IR )
}
