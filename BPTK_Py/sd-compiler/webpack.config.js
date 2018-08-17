const path = require( 'path' )

module.exports = {
	target: 'node',
	entry: path.resolve( __dirname, './src/cli.js' ),
	output: {
		filename: 'sdcc.js',
		path: path.resolve( __dirname, 'dist' )
	},
	mode: 'production',
	module: {
		rules: [
			{
				test: /\.js/,
				exclude: /node_modules/,
				loader: 'babel-loader'
			},
			{
				test: /\.node$/,
				use: 'node-loader'
			},
			{
				test: /\.(hbs|pegjs|txt)$/,
				use: 'raw-loader'
			}
		]
	},
	resolve: {
		alias: {
			handlebars: 'handlebars/dist/handlebars.js'
		}
	},
	externals: [ 'babel-core' ]//Object.keys( externals || {} )
}
