#                                                       /`-
# _                                  _   _             /####`-
# | |                                | | (_)           /########`-
# | |_ _ __ __ _ _ __  ___  ___ _ __ | |_ _ ___       /###########`-
# | __| '__/ _` | '_ \/ __|/ _ \ '_ \| __| / __|   ____ -###########/
# | |_| | | (_| | | | \__ \  __/ | | | |_| \__ \  |    | `-#######/
# \__|_|  \__,_|_| |_|___/\___|_| |_|\__|_|___/  |____|    `- # /
#
# Copyright (c) 2019 transentis labs GmbH
# MIT License


from parsimonious.grammar import Grammar, NodeVisitor

try:
    from ...plugins import sanitizeName
except: # Standalone Mode
    from plugins import sanitizeName

class SMILEVisitor(NodeVisitor):
    """
    This Visitor takes the parsed Elements and outputs them in the IR structure
    """

    def generic_visit(self, node, visited_children):
        """ The generic visit method. """
        return visited_children or node

    def visit_Equation(self, node, visited_children):
        return visited_children

    def visit_Sentence(self, node, visited_children):
        _, Sentence, _ = visited_children
        return Sentence[0]

    def visit_Comment(self, node, visited_children):
        _,_, comment,_, _ = visited_children
        return "0.0"


    def visit_ConditionalExpression(self, node, visited_children):
        if len(visited_children[0]) < 11:
            if_, _, Sentence, _, then_, _, t = visited_children[0]
            return {"name": "if", "type": "call", "args": [Sentence, t]}
        else:
            if_, _, Sentence, _, then_, _, t, _, else_, _, e = visited_children[0]
            return {"name": "if", "type": "call", "args": [Sentence, t, e]}

    def visit_ConditionalStatement(self, node, visited_children):

        if type(visited_children[0]) is dict:  #  (ComparisonExpression)
            op = visited_children[0]["name"]
            args = visited_children[0]["args"]
            return {"name": op.strip(), "type": 'operator', "args": args}

        else: # Exactly 3 Elements expected in tree
            left, op, right = visited_children[0] # (ComparisonExpression BooleanOperator ConditionalStatement)
            return {"name": op.strip(), "type": 'operator', "args": [left, right]}


    def visit_ComparisonExpression(self, node, visited_children):
        try: # (Expression ComparisonOperator Expression) The most common case
            left, op, right = visited_children[0]
            args = [left, right]
            return {"name": op.replace(" ","").lower(), "type": "operator", "args": args}
        except:
            #(Not "(" Expression ComparisonOperator Expression ")") --> NOT (x=10)
            _ , _ , left , op , right , _ = visited_children[0]
            args = [left, right]
            ComparisonExpression = {"name": op.replace(" ","").lower(), "type": "operator", "args": args}

            return  {"type": "operator","name": "not","args": [ComparisonExpression]}

    def visit_Expression(self, node, visited_children):
        if type(visited_children[0]) == list:
            left, op, right = visited_children[0]
            args = [left, right]

            return {"name": op.strip(), "type": 'operator', "args": args}

        return visited_children[0]

    def visit_Term(self, node, visited_children):
        if type(visited_children[0]) == list:
            left, op, right = visited_children[0]
            return {"name": op.strip().lower(), "type": 'operator', "args": [left, right]}
        return visited_children[0]

    def visit_Atom(self, node, visited_children):
        if type(visited_children[0]) == list:
            _, Sentence, _ = visited_children[0]
            return {"name": '()', "type": 'operator', "args": [Sentence]}
            # return Sentence
        return visited_children[0]

    '''
    Numbers
    '''

    def visit_NumericLiteral(self, node, visited_children):
        NumericLiteral = "".join(visited_children[0])
        return float(NumericLiteral)

    def visit_significant(self, node, visited_children):
        if type(visited_children[0]) == list:  # Sign
            sign, _, digits = visited_children[0]
            return sign.text + digits

        return visited_children[0]  # No Sign

    def visit_exponent(self, node, visited_children):
        e, digits = visited_children
        return e.text + digits

    def visit_fraction(self, node, visited_children):
        _, digits = visited_children
        return '.' + digits

    def visit_digits(self, node, visited_children):
        return node.text

    '''
    Functions
    '''

    def visit_FunctionExpression(self, node, visited_children):
        identifier, _, args, _ = visited_children
        identifier = identifier["name"]
        return {"name": sanitizeName(identifier.lower()), "type": 'call', "args": args}

    def visit_FunctionArguments(self, node, visited_children):
        if type(visited_children[0]) == float : return str(visited_children[0])
        result = self.visit_ArrayIndices(node,visited_children)
        return result

    def visit_FunctionArgument(self, node, visited_children):
        if type(visited_children[0]) is float or type(visited_children[0]) is str : return visited_children[0]
        if len(visited_children[0]) < 3: return visited_children[0]
        if type(visited_children[0]) is dict: return visited_children[0]

        # ((ArrayExpression or Expression) Operator Term)
        Expression, Operator, Term = visited_children[0]

        return {"name": Operator[0].replace(" ","").lower(), "type": "operator", "args": [Expression, Term]}


    def visit_SpecialFunction(self, node, visited_children):
        return {"name": node.text.lower(), "type": 'call', "args": []}


    '''
    Arrays
    '''
    def visit_ArrayExpression(self, node, visited_children):
        identifier, _, args, _ = visited_children
        identifier = identifier["name"]

        return {"name": identifier, "type": 'array', "args": args}

    def visit_ArrayIndices(self, node, visited_children):
        if (type(visited_children) is list and len(visited_children)==1 and type(visited_children[0])== dict): return visited_children
        if len(visited_children[0]) == 1: return visited_children[0]  # Exactly one Array Index
        result = []
        try:
            ArrayIndex , ArgGroups = visited_children[0]
        except:
            return visited_children

        result += [ArrayIndex]

        for elem in ArgGroups:
            sep, index = elem

            if type(index)!=list:
                index = [index]
            result += index

        return result

    def visit_ArrayIndex(self, node, visit_children):

        return visit_children[0]  # Only for completeness, shouldn't be required, covered by generic_visit

    def visit_Asterisk(self, node, visit_children):
        return "*"

    def visit_Range(self, node, visited_children):
        from_, operator, to_ = visited_children
        return {"name": operator.replace(" ","").lower(), "type": 'range', "args": [from_, to_]}

    def visit_Label(self, node, visited_children):
        return {"name": sanitizeName(node.text.lower()), "type": 'label'}

    '''
    Identifier
    '''

    def visit_Identifier(self, node, visited_children):
        return visited_children[0]

    def visit_EnclosedIdentifier(self,node, visited_children):
        return {"name":sanitizeName(node.text.lower()), "type": 'identifier'}

    def visit_SimpleIdentifier(self, node, visited_children):
        return {"name":sanitizeName(node.text.lower()), "type": 'identifier'}

    def visit_NamespacedIdentifier(self, node, visited_children):
        return {"name": sanitizeName(node.text.lower()), "type": 'identifier'}

    '''
    Operators
    '''

    def visit_Clocktime(self,node, visited_children):
        return {"name": "clocktime", "type": "call", "args": []}

    def visit_AdditiveOperator(self, node, visited_children):
        return node.text

    def visit_MultiplicativeOperator(self, node, visited_children):
        return node.text

    def visit_ComparisonOperator(self, node, visited_children):
        return node.text

    def visit_BooleanOperator(self, node, visited_children):
        return node.text

    '''
    Keywords
    '''

    def visit_Keyword(self, node, visited_children):
        return visited_children

    def visit_if(self, node, visited_children):
        return node.text.replace(" ","").lower()

    def visit_then(self, node, visited_children):
        return node.text.replace(" ","").lower()

    def visit_else(self, node, visited_children):
        return "else"

    def visit_and(self, node, visited_children):
        return "and"

    def visit_or(self, node, visited_children):
        return node.text.replace(" ","").lower()

    '''
    Misc Chars
    '''

    def visit_nothing(self, node, visited_children):
        return ''

    def visit__(self, node, visited_children):
        return ""

    def visit_strict_whitespace(self, node, visited_children):
        return ""

    def visit_Name(self, node, visited_children):
        return node.text

    def visit_RangeSeparator(self, node, visited_children):
        return node.text

    def visit_ArgumentSeparator(self, node, visited_children):
        return ","

    def visit_Not(self,node,visited_children):
        return "not"


'''
The Actual Grammar
'''

grammar = Grammar(
    r"""
    equation                =  Sentence 
    Sentence                =  _  ( Comment / ConditionalExpression / ConditionalStatement / Expression / nothing ) _
    Comment                 = _ "{" ~"[\w\d\s]*"iu "}" _
    ConditionalExpression   =  (if _ Sentence _ then _ Sentence _ else _ Sentence)  / (if _ Sentence _ then _ Sentence)
    ConditionalStatement    = (ComparisonExpression BooleanOperator ConditionalStatement) / (ComparisonExpression)
    Not                     = ~"NOT"i 
    ComparisonExpression    = (Expression ComparisonOperator Expression ) / ( Not bracket_open Expression ComparisonOperator Expression bracket_closed )
    Expression              = (Term AdditiveOperator Sentence)  / (Term)
    Term                    = (Atom MultiplicativeOperator Term)  / (Atom)
    Atom                    = NumericLiteral
                              / FunctionExpression
                              / SpecialFunction
                              / ArrayExpression
                              / Identifier
                              / (bracket_open Sentence bracket_closed)
                              / nothing   
    NumericLiteral          = (significant fraction exponent)
                              / (significant fraction)            
                              / ('-' fraction exponent)    
                              / ('-' fraction)                   
                              / (fraction)                        
                              / (significant exponent)         
                              / (significant)
    significant             = ('-' _ digits) / (digits)  
    exponent                = ( 'e-' / 'e' ) digits 
    fraction                = '.'digits

    digits                  = ~"[\d]+"

    AdditiveOperator        = _ ('+' / '-' ) _  
    MultiplicativeOperator  = _ ( Asterisk / '/' / '^' / ~"MOD"i ) _    
    ComparisonOperator      = _ ( '>=' / '=' / '<=' / '<>' / '<' / '>' ) _ 
    BooleanOperator         = _ ( and / or ) _   

    FunctionExpression      = Identifier bracket_open FunctionArguments bracket_closed                 
    FunctionArguments       = (FunctionArgument ( ArgumentSeparator FunctionArgument )+)   / (Sentence)
    FunctionArgument        =  ( ((ArrayExpression) / (Expression)) ((AdditiveOperator) / (MultiplicativeOperator)) Term)  / ArrayExpression / Sentence                      
    SpecialFunction         = _ ( ~'starttime'i / ~'stoptime'i / ~'time'i / ~'dt'i / ~'pi'i / ~'clocktime'i / ~'nan'i / ~'inf'i ) !Name 

    Identifier              =  (EnclosedIdentifier) / (NamespacedIdentifier) / (SimpleIdentifier)
    EnclosedIdentifier      = BeginQuote NameWithSpecialChars EndQuote
    BeginQuote              = Quote
    EndQuote                = Quote
    Quote                   = '"'
    SimpleIdentifier        = !Keyword Name
    NamespacedIdentifier    = (!Keyword ( Name '.' Name )) / (!Keyword ( '.' Name ))

    ArrayExpression         = Identifier '[' ArrayIndices ']'
    ArrayIndices            = (ArrayIndex ( ArgumentSeparator ArrayIndex )+) / (ArrayIndex)
    ArrayIndex              = FunctionExpression / Asterisk / Range / Label / Identifier
    Asterisk                = '*' 
    Range                   = Label RangeSeparator Label 
    Label                   = !NamespacedIdentifier Name 

    Keyword                 = if / then / else / and / or
    if                      =  ~"IF"i &Separator
    then                    =  ~"THEN"i &Separator 
    else                    =  ~"ELSE"i &Separator
    and                     =  ~"AND"i &Separator
    or                      =  ~"OR"i &Separator


    Name                    = ~r"[\w\d_%$€£¥&§#']+"
    NameWithSpecialChars    = ~r"([\w\d_%$€£¥&§#'+\-*#<>\\.,;:–()]|(\\\"))+" 
    Separator               = strict_whitespace / bracket_open
    bracket_open            = '('
    bracket_closed          = ')'
    ArgumentSeparator       = _ ',' _
    RangeSeparator          = _ ':' _
    whitespace              = ~"[\t\v\f\r\n \u00A0\u2028\uFEFF]"
    _                       = whitespace*
    strict_whitespace       = whitespace+
    nothing                 = ''

    """
)

