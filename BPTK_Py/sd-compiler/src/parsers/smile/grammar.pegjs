/*      _                   _ _
  _____| |__ ___ _ __  _ __(_| |___ _ _
 (_-/ _` / _/ _ | '  \| '_ | | / -_| '_|
 /__\__,_\__\___|_|_|_| .__|_|_\___|_|
                      |_|
 Copyright (c) 2013-2016 transentis management & consulting. All rights reserved.

 PEG Grammar for SMILE Expressions
 http://www.iseesystems.com/community/support/SMILEv4.pdf

*/
{
  function concat ( chars ) {
    return chars.map( function ( char ) {
      return char instanceof Array ? concat( char ) : char
    }).join( '' )
  }
}

Equation
  = Sentence

Sentence
  = _ s:( Comment / ConditionalExpression / Expression / nothing ) _ { return s }

Comment
  = _ '{' c:[^\}]* '}' _   { return { name: concat(c), type: 'comment' } }

ConditionalExpression
  = if _ i:ConditionalStatement _ then _ t:Sentence _ else _ e:Sentence { return { name: 'if', type: 'call', args: [ i, t, e ] } }
  / if _ i:ConditionalStatement _ then _ t:Sentence                     { return { name: 'if', type: 'call', args: [ i, t ] } }

ConditionalStatement
  = left:ComparisonExpression op:BooleanOperator right:ConditionalStatement { return { name: op, type: 'operator', args: [ left, right ] } }
  / ComparisonExpression

ComparisonExpression
  = left:Expression op:ComparisonOperator right:Expression  { return { name: op, type: 'operator', args: [ left, right ] } }

Expression
  = left:Term op:AdditiveOperator right:Sentence      { return { name: op, type: 'operator', args: [ left, right ] } }
  / Term

Term
  = left:Atom op:MultiplicativeOperator right:Term    { return { name: op, type: 'operator', args: [ left, right ] } }
  / Atom

Atom
  = NumericLiteral
  / FunctionExpression
  / SpecialFunction
  / ArrayExpression
  / Identifier
  / '(' s:Sentence ')' { return { name: '()', type: 'operator', args: [ s ] } }
  / nothing            { return { name: '', type: 'nothing' } }


/*                     _
                      | |
 _ __  _   _ _ __ ___ | |__   ___ _ __ ___
| '_ \| | | | '_ ` _ \| '_ \ / _ \ '__/ __|
| | | | |_| | | | | | | |_) |  __/ |  \__ \
|_| |_|\__,_|_| |_| |_|_.__/ \___|_|  |___/
*/
NumericLiteral
  = s:significant f:fraction e:exponent  { return parseFloat(s+f+e) }
  / s:significant f:fraction             { return parseFloat(s+f) }
  / s:'-' f:fraction e:exponent          { return parseFloat(s+f+e) }
  / s:'-' f:fraction                     { return parseFloat(s+f) }
  / f:fraction                           { return parseFloat(f) }
  / s:significant e:exponent             { return parseFloat(s+e) }
  / s:significant                        { return parseFloat(s) }

significant
  = sign:'-' _ digits:digits         { return sign + digits }
  / digits:digits                    { return digits }

exponent
  = e:( 'e-'i / 'e'i ) digits:digits  { return e + digits }

fraction
  = '.' digits:digits                { return '.' + digits }

digits
  = digits:[0-9]+                    { return concat(digits) }



/*                          _
                           | |
  ___  _ __   ___ _ __ __ _| |_ ___  _ __ ___
 / _ \| '_ \ / _ \ '__/ _` | __/ _ \| '__/ __|
| (_) | |_) |  __/ | | (_| | || (_) | |  \__ \
 \___/| .__/ \___|_|  \__,_|\__\___/|_|  |___/
      | |
      |_|
*/
AdditiveOperator
  = _ op:( '+' / '-' ) _                             { return op }
MultiplicativeOperator
  = _ op:( '*' / '/' / '^' / 'MOD'i ) _              { return op }
ComparisonOperator
  = _ op:( '>=' / '=' / '<=' / '<>' / '<' / '>' ) _  { return op }
BooleanOperator
  = _ op:( and / or ) _                              { return op }


/*
  __                  _   _
 / _|_   _ _ __   ___| |_(_) ___  _ __  ___
| |_| | | | '_ \ / __| __| |/ _ \| '_ \/ __|
|  _| |_| | | | | (__| |_| | (_) | | | \__ \
|_|  \__,_|_| |_|\___|\__|_|\___/|_| |_|___/
*/
FunctionExpression
  = identifier:Identifier _ '(' args:FunctionArguments ')'                 { return { name: identifier.name, type: 'call', args: args } }

FunctionArguments
  = head:FunctionArgument tail:( ArgumentSeparator a:FunctionArgument  { return a } )+     { return [ head ].concat( tail ) }
  / s:Sentence                                                             { return [ s ] }

FunctionArgument
  = arg:( ArrayExpression / Sentence )                                     { return arg }

SpecialFunction
  = _ name:( 'starttime'i / 'stoptime'i / 'time'i / 'dt'i / 'pi'i ) !Name { return { name: name, type: 'call', args: [] } }


/*
  __ _ _ __ _ __ __ _ _   _ ___
 / _` | '__| '__/ _` | | | / __|
| (_| | |  | | | (_| | |_| \__ \
 \__,_|_|  |_|  \__,_|\__, |___/
                      |___/
*/
ArrayExpression
  = identifier:Identifier '[' args:ArrayIndices ']'
    { return { name: identifier.name, type: 'array', args: args } }

ArrayIndices
  = head:ArrayIndex tail:( ArgumentSeparator s:ArrayIndex { return s } )+
    { return [ head ].concat( tail ) }
  / a:ArrayIndex
    { return [a] }

ArrayIndex
  = Asterisk / Range / Label / Identifier

Asterisk
  = '*' { return { name: '*', type: 'asterisk' } }

Range
  = from:Label RangeSeparator to:Label { return { name: ':', type: 'range', args:[ from, to ] } }

Label
  = !NamespacedIdentifier chars:Name { return { name: concat(chars), type: 'label' } }


/*
 _     _            _   _  __ _
(_)   | |          | | (_)/ _(_)
 _  __| | ___ _ __ | |_ _| |_ _  ___ _ __
| |/ _` |/ _ \ '_ \| __| |  _| |/ _ \ '__|
| | (_| |  __/ | | | |_| | | | |  __/ |
|_|\__,_|\___|_| |_|\__|_|_| |_|\___|_|
*/
Identifier
  = NamespacedIdentifier / SimpleIdentifier

SimpleIdentifier
  = !Keyword chars:Name
    { return { name: concat(chars), type: 'identifier' } }

NamespacedIdentifier
  = !Keyword chars:( Name '.' Name )
    { return { name: concat(chars), type: 'identifier' } }
  / !Keyword chars:( '.' Name )
    { return { name: concat(chars), type: 'identifier' } }

/*
 _                                    _
| |                                  | |
| | _____ _   ___      _____  _ __ __| |___
| |/ / _ \ | | \ \ /\ / / _ \| '__/ _` / __|
|   <  __/ |_| |\ V  V / (_) | | | (_| \__ \
|_|\_\___|\__, | \_/\_/ \___/|_|  \__,_|___/
           __/ |
          |___/
*/
Keyword
  = if / then / else / and / or

if
  = 'if'i __   { return 'if' }

then
  = 'then'i __ { return 'then' }

else
  = 'else'i __ { return 'else' }

and
  = 'and'i __  { return 'and' }

or
  = 'or'i __   { return 'or' }


/*         _                 _
          (_)               | |
 _ __ ___  _ ___  ___    ___| |__   __ _ _ __ ___
| '_ ` _ \| / __|/ __|  / __| '_ \ / _` | '__/ __|
| | | | | | \__ \ (__  | (__| | | | (_| | |  \__ \
|_| |_| |_|_|___/\___|  \___|_| |_|\__,_|_|  |___/
*/
Name
  = name:( [\"]? [a-zA-Z0-9_%\$€£¥&§']+ [\"]? ) { return name }

ArgumentSeparator
  = _ ',' _

RangeSeparator
  = _ ':' _

_ 'whitespace'
  = [\t\v\f\r\n \u00A0\uFEFF]*

__ 'strict whitespace'
  = [\t\v\f\r\n \u00A0\uFEFF]+

nothing
  = ''
