/*      _                   _ _
  _____| |__ ___ _ __  _ __(_| |___ _ _
 (_-/ _` / _/ _ | '  \| '_ | | / -_| '_|
 /__\__,_\__\___|_|_|_| .__|_|_\___|_|
                      |_|
 Copyright (c) 2013-2018 transentis management & consulting. All rights reserved.
*/
module.exports = () => {



// Simulation Buildins
let dt = 0.25
let starttime = 1
let stoptime = 13
let m, p, d

return {
	equations: m = {
		/* stocks */
		'foo': t => Math.max(0,t<=starttime?10:m.foo(t-dt)+dt*(-1*m.bar(t-dt))),
	
		'm1▸foo1': t => Math.max(0,t<=starttime?11:m['m1▸foo1'](t-dt)+dt*(-1*m['m1▸bar1'](t-dt))),
	
		'm3▸foo3': t => Math.max(0,t<=starttime?13:m['m3▸foo3'](t-dt)+dt*(-1*m['m3▸bar3'](t-dt))),
	
		'm2▸foo2': t => Math.max(0,t<=starttime?12:m['m2▸foo2'](t-dt)+dt*(-1*m['m2▸bar2'](t-dt))),
		/* flows */
		'bar': t => 1,

		'm1▸bar1': t => Math.max(0,m.foo(t)/10),

		'm3▸bar3': t => Math.max(0,m['m1▸foo1'](t)/10),

		'm2▸bar2': t => Math.max(0,m.foo(t)/10),

		/* converters */	/* gf */
		/* constants */	},
	points: p = {
	 },
	dimensions: d = {
	 },
	stocks: ['foo','m1▸foo1','m3▸foo3','m2▸foo2'],
	flows: ['bar','m1▸bar1','m3▸bar3','m2▸bar2'],
	converters: [],
	gf: [],
	constants: [],
	events: [
	],
	specs: () => ({
		starttime: starttime,
		stoptime: stoptime,
		dt: dt,
		time_units: 'Months',
		method: 'Euler'
	}),
	setDT: v => { dt = v },
	setStarttime: v => { starttime = v },
	setStoptime: v => { stoptime = v }
}

}

