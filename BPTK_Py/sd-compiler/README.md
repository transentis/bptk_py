# Compiler

The compiler project is the heart of our whole business prototyping
infrastructre. Simulation models can be transformed into a target language (e.g. *Wolfram Language*, *Javascript*, etc.) and will be consumed by the
projects.

## Directories
All modules of the compiler can be found in the `src` directory. The purpose of the `target` directory is to define external interfaces (like the command line or web), that invoke the compiler pipeline with the source.

```
bin/
src/
	generators/
	parsers/
	plugins/
	strategies/
target/
	cli.js
test/
```



## Pipeline
Like most modern compilers nowadays, the compiler is heavily modularized.

* The *front end* parses the sources and generates an *intermediate representation* or IR.
* The *middle end* performs operations on the IR. These are organized as *plugins*.
* The *back end* generates code in the target language

The whole pipeline from the source to code is depicted as followed:

```
|    front end      |    middle end   |     back end      |

SOURCE -> parser -> IR -> plugins -> IR -> generator -> CODE
```

At each stage [Promises](https://www.promisejs.org/) are exchanged.


## Strategies
A strategy is basically a functional blueprint of how to plug the compiler pipeline together. Please remember, that the pipeline is a chain of promises. For more convenience and readability the three helper functions `parse`, `plugins` and `compile` wrap around a pile require statements. Strategies define how to parse a given source, what plugins to apply an what code generator to use.

```
Promise.resolve( src )
    // front end
	.then( parse( 'xmile' ) )
	// middle end
	.then( plugins(
		'sd/filterGhosts',
		'sd/stockExpressions',
		'sd/non_negative',
		'sd/expandArrays',
		'sd/makeNameAbsolute',
		'sd/sanitizeNames',
		'sd/sortEntities'
	))
	// back end
	.then( compile( 'js' ) )
```


## Plugins
Most of the smart logic the compiler has, is realized by individual plugins.

* **filterGhosts** removes any entity, that has a ghost attribute, from the IR
* **non_negative** wraps the parsed syntax tree for an entity with the non_negative attribute into a `MAX( …, 0 )`
* **sortEntities** sorts the list of entities for a model based on their names
* **expandArrays** alters the IR in such way, that arrayed entities are replaced by index/label-specific copies of it. Also the expressions of other entities, that use the same dimensions, are altered to reference the appropriate copy.
* **stockExpressions** creates an expression for each stock, based on its initial value as well as the in- and outflows. `stock(t) = if t < starttime then initial else stock(t-1) + dt * ∑Flows`
* **makeNameAbsolute** prefixes the name of an entity with its models name as well as in all expressions
* **sanitizeNames** stripes and replace bad characters from the entity names and expressions
* **nothing** does exactly nothing with the IR!


## Parser
Most of the heavy lifting the compiler has to do, takes place within the parser. Most notable, mathematical expressions need to be parsed into an abstract syntax tree (AST). Writing a parser by hand is tedious and error prone, so the compiler uses a parser generator ([PEG.js](http://pegjs.org/)) to create a parser with a comprehensive grammar (see `src/parser/smile/grammar.pegjs`). Please note, that the resulting AST is well-formed and part of the IR. Any changes may break plugins and generators, that work on this structure.



## IR
It is mandatory to know how the *intermediate representation* is structured – parsers generate it, plugins perform operations on it and generators consume it. For now, the IR resembles a lot of the semantics from XMILE. Please note, that this might change in the future as more parsers for different kind of simulation models enter the battlefield.


At the top level the IR object only has a few fields.

```
{
	name: 'simulation name',
	specs: { method: 'Euler', units: 'Months', start: 1, stop: 13, dt: 0.25 },
	dimensions: { … },
	models: [
		{ name: 'name', entities: [ … ] }, …
	]
}
```

Each model may have a number of entities. Beside the name and type fields, there some other fields, that need to be explained in more detail. First of all, `parsed` holds an object that represents the `src` expression as an abstract syntax tree (see later). As entities may have dimensions (which means they are arrayed), the two fields `dimensions` and `labels` contain the dimension names and specific labels for this entity. Any other attribute, that this entity may has, is described in `attributes`. E.g. a stock may have `inflows` and `outflows`, an auxiliary entity may only be `non_negative` and so on.

```
{
	name: 'stock',
	type: 'stock',
	expression: { src: '…', parsed: AST }
	dimensions: false,
	labels: null,
	attributes: { non_negative: true, inflows: [ 'inflow' ] },
	events: [ … ]
}
```


Additionally events may be definied for an entity. For more details, please read section *4.1.2 Message Posters* of the [XMILE specification](http://www.iseesystems.com/community/support/XMILEv4.pdf).

```
{
	threshold: 10,
	direction: '>',
	repeat: 'once',
	interval: 0,
	messages:[
		{ message: 'foobarrrrr!', action: 'pause' },
		{ message: 'howdy!', action: 'pause' }
	]
}
```

## AST
Mathematical expressions can be described as a tree of data – all leaves are atomic expressions like numbers and variables, whereas the branches may be operators, function calls, etc.. Any object within this AST has a certain shape:

```
{ name: '…', type: '…', args: [ … ] }
```

The **type** can be `call`, `operator`, `identifier`, `array`, `range` or `label`. Depending on the type of such an object, the **name** field has slightly different meanings. Operators are defined in the name field (e.g. "+" for an addition), whereas the name field for calls and identifiers actually define their names.

One might think of the programming language Lisp when looking at the `args` array. The expression `(+ 2 3)` in Lisp is equal to `{ name: '+', type: 'operator', args: [2, 3] }` in our AST. More complex expressions can be described by nesting such objects within the args.

Lets say a plugin wants change the name of all identifiers in an AST. Obviously it has to traverse through all objects and all its args looking for `type == identifier` and change their names. The `src/helpers` module has a function called `traverseAST` that walks recusively through an AST and calls (in post-order) a callback function for each node it encounters.

```
// define a walker
const walk = traverseAST( node => {
	if ( node.type == 'identifier' ) node.name = 'foo'
})
// call it with an AST
walk( AST )
```


## Generators
Generators form the *back end* of each compiler. They transform the IR into code. At the current state a generator basically performs two operations. First off, it has to convert an expression AST into code. Second, it has to wrap this code into the a skeleton for each entity and model. The module `src/generators/ast.js` provides a simple solution to generate code from ASTs. Like traverseAST it provides (type-specific) callbacks for each node of the AST an composes the returned Strings into code.

```
var ast_generator = require( 'src/generators/ast' )
// minimalistic code generator
var generateCode = ast_generator({
	operators: {
		'+': ( lhs, rhs ) => `${lhs} + ${rhs}`
	},
	constant: node => node.toString()
})
var AST = { name: '+', type: 'operator', args: [2, 3] }
generateCode( AST ) // returns '2 + 3'
```

After generating code from all ASTs, we use a template engine ([Handlebars](http://handlebarsjs.com/)) to stitch all code into a skeleton template. This step is similar to what a linker does for compiling executables.

Template engines need a context object to work on. So beside the expression code generation, the generator builds a `ctx` object, filled with all information needed to create the target code file. Given the context object:

```
var ctx = {
	flows: [
		{ name: 'foo', expression: '2 + 3' }
		{ name: 'foo', expression: '4 - 2' }
	]
}
```

with a template like this

```
(* flows *)
{{#each flows}}
	{{{name}}}[t_,dt_] := {{{name}}}[t,dt] = {{{expression}}};
{{/each}}
```

the result would be

```
(* flows *)
foo[t_,dt_] := foo[t,dt] = 2 + 3;
bar[t_,dt_] := bar[t,dt] = 4 - 2;
```

## Command Line Interface
The CLI is probably the most common way of using this compiler. But it might also be perfectly fine to require strategies (see above) directly from other node programs.

There are a few options for the command line interface

* `-i path/to/src` Input filename.
* `-o path/to/dest`  Output filename. If not specified, the result will be printed to *stdout*.
* `-t [ir|js|m]` Target language. Mandatory option unless a output filename is provided from which the target language can be inferred.
* `-p "name"` This option can be used to prefix every name (models and entities). It might be useful in environments like the wolfram language, that don't support namespacing.





### Debugging the IR
At some time it might be useful to see the generated IR. There is a specific strategy for is purpose, that prints the object to *stdout*.

```
#> sdcc -i model.itmx -t ir
```
