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


import re
import logging

from ..contextBuilder import remove_nesting

def generate(IR):
    """
    The generator for python. Hands over the template and parseExpression function to the generic generator

    :param IR:
    :return:
    """
    from .jinja_template import template
    from ..contextBuilder import generate
    return generate(IR, template=template, parseExpression=parseExpression)


def parseExpression(expression):
    '''
    Parse expression / equation recursively and build code from IR (For python). You need to re-implement the return statements for getting it work for another target language
    :param expression:
    :return:
    '''
    lowercase_first_letter = lambda s: s[:1].lower() + s[1:] if s else ''

    '''
    Just make sure to lowercase module name
    '''
    if type(expression) is dict and expression["type"] == "identifier":
        expression["name"] = lowercase_first_letter(expression["name"])

    '''
    Remove "," from expression
    '''
    if not type(expression) is int and not type(expression) is float:
        if type(expression) is list or type(expression) is tuple:
            if "," in expression: expression.remove(",")

    '''
    Return if float or int
    '''
    if type(expression) is float or type(expression) is int:
        return expression

    '''
    Return if str
    '''
    if type(expression) is str:
        return expression

    '''
    Parse list (e.g. args) by joining parsing results for each element in list
    '''
    if type(expression) is list or type(expression) is tuple:
        result = []
        for elem in expression:
            result += [parseExpression(elem)]
            if len(result) == 0:
                return 0

        return ",".join([str(x) for x in result if str(x).replace(" ", "") != ","])

    '''
    Handle Identifiers
    '''
    if expression["type"] == 'identifier':
        return "self.memoize(\'{}\', t)".format(expression["name"])

    '''
    Handle Function Calls
    '''
    if expression["type"] == 'call':
        try:
            macro = builtins[expression["name"].lower()]
            return macro(expression["args"])
        except TypeError as e:
            raise e
        except KeyError as e:
            logging.warning(expression["name"].lower() + " has not been implemented yet! Skipping...")
            return "0"

    '''
    Handle Operators
    '''
    if expression["type"] == 'operator':
        try:
            conv = operators[expression["name"].lower().replace(" ", "")]

            # Some operators have 2 args (+,-,/), some only one (exp)
            try:
                return conv(expression["args"][0], expression["args"][1])
            except IndexError as e:
                return conv(expression["args"][0])

        except KeyError:
            raise Exception('Unknown Operator: {}'.format(expression))

    '''
    Array functions
    '''
    if expression["type"] == 'array':
        def array(name, args):

            vargs = []

            if type(args) is dict:
                args = [args]

            for elem in args:

                if "self.memoize" in elem:

                    vargs += ["\'+ " + parseExpression(elem) + "+\'"]
                else:
                    if type(elem) is dict:
                        elem = [elem]

                    if type(elem) is list and type(elem[0]) is dict and elem[0]["type"] == "call":
                        vargs += ["\'+ str(" + parseExpression(elem) + ")+\'"]
                    else:
                        vargs += [elem]

            return "self.memoize(\'{}[".format(name) + ",".join([str(parseExpression(x)) for x in vargs]) + "]\', t)"

        return str(array(expression["name"], expression["args"]))

    '''
    Comment
    '''
    if expression["type"] == 'comment':
        return "# " + str(" ".join(expression["args"]))

    '''
    Constants
    '''
    if expression["type"] == 'constant':
        return str(expression)

    '''
    Labels
    '''
    if expression["type"] == 'label':
        return expression["name"]

    '''
    Nothing
    '''
    if expression["type"].replace(" ", "") == '()':
        return 0

    raise Exception("Cannot parse expression: {}".format(expression))


'''
Lambdas for operators
'''
operators = {
    "+": lambda lhs, rhs: "{} + {}".format(parseExpression(lhs), parseExpression(rhs)),
    "-": lambda lhs, rhs: "{} - {}".format(parseExpression(lhs), parseExpression(rhs)),
    "*": lambda lhs, rhs: "{} * {}".format(parseExpression(lhs), parseExpression(rhs)),
    "/": lambda lhs, rhs: "{} / {}".format(parseExpression(lhs), parseExpression(rhs)),
    "^": lambda lhs, rhs: "{} ** {}".format(parseExpression(lhs), parseExpression(rhs)),
    "=": lambda lhs, rhs: "{} == {}".format(parseExpression(lhs), parseExpression(rhs)),
    ">": lambda lhs, rhs: "{} > {}".format(parseExpression(lhs), parseExpression(rhs)),
    "<": lambda lhs, rhs: "{} < {}".format(parseExpression(lhs), parseExpression(rhs)),
    ">=": lambda lhs, rhs: "{} >= {}".format(parseExpression(lhs), parseExpression(rhs)),
    "<=": lambda lhs, rhs: "{} <= {}".format(parseExpression(lhs), parseExpression(rhs)),
    "<>": lambda lhs, rhs: "{} != {}".format(parseExpression(lhs), parseExpression(rhs)),
    "mod": lambda lhs, rhs: "{} % {}".format(parseExpression(lhs), parseExpression(rhs)),
    "()": lambda body: "( {} )".format(parseExpression(body)),
    "and": lambda lhs, rhs: "{} and {}".format(parseExpression(lhs), parseExpression(rhs)),
    "or": lambda lhs, rhs: "{} or {}".format(parseExpression(lhs), parseExpression(rhs)),
    "exp": lambda body: "np.exp( {} )".format(parseExpression(body)),
    "not" : lambda body : "(not {})".format(parseExpression(body))
}

def endval_(*args):
    args = remove_nesting(args)
    input = 0
    try:
        input = args[0]["name"]
    except:
        logging.error("Problem obtaining identifier for ENDVAL input. Currently, ENDVAL only supports identifiers, not complex computations. Erroneous input was: {}".format(args[0]))
        return "0"
    initial = "self.equation(\"{}\",self.starttime)".format(input) if len(args) == 1 else parseExpression(args[1])

    return "( self.memo[\"{}\"][self.stoptime] if self.stoptime in self.memo[\"{}\"].keys() else {} )".format(input,input,initial)

def pulse(*args):
    args = remove_nesting(args)
    volume = parseExpression(args[0])

    first = None if len(args) == 1 else parseExpression(args[1])

    interval = None if len(args) <= 2 else parseExpression(args[2])

    if first == interval == None:
        return '(( ' + str(volume) + ' ) / self.dt)'

    if first == None:
        first = ' self.starttime '

    if interval == None:
        return '('+str(volume) + ' /self.dt if ' + str(first) + ' <= t else 0)'

    if int(interval) == 0:
        return '('+ str(volume) + ' /self.dt if ' + str(first) + ' == t else 0)'

    return '('+str(volume) + '/ self.dt if ' + str(first) + ' <= t and ((t -' + str(first) + ') % ' + str(
        interval) + ') == 0 else 0)'


def derivn_(*args):
    args = remove_nesting(args)

    equation = "\"{}\"".format(args[0]["name"]) if type(args[0]) is dict else args[0]
    order = parseExpression(args[1])
    return "(self.derivn({}, int({}), t) )".format(equation, order)

def previous(*args):
    args = remove_nesting(args)
    res = parseExpression(args)

    body = res

    initial = None if (not type(res) is list) else res[1]
    pattern_selfdt = r"\(?\,?(self.[dt+\-]+)\)"
    body = re.sub(pattern_selfdt, "(self.dt-self.dt)", str(body))

    pattern_t = r"\(?\,? ([t+\-]+)\)"
    body = re.sub(pattern_t, ",t-self.dt)", body)

    if initial:

        return '((' + str(initial) + ') if t <= self.starttime else ' + '(' + str(body) + '))' if initial else str(body)
    else:

        return str(body)

def ramp_(*args):
    args = remove_nesting(args)
    slope = parseExpression(args[0])
    start = "None" if len(args)==1 else parseExpression(args[1])
    return "( self.ramp({},{},t ) )".format(slope,start)

def delay(*args):
    args = remove_nesting(args)
    input = str(parseExpression(args[0]))
    offset = str(parseExpression(args[1]))

    try:
        initial = str(parseExpression(args[2]))
    except:
        pattern = r"(^|[^a-zA-Z_\\.])t($|[^a-zA-Z_\\.])"
        clean = re.compile(pattern)
        initial = re.sub(clean, r'\1(self.starttime)\2', input)


    pattern = r"(^|[^a-zA-Z_\\.])t($|[^a-zA-Z_\\.])"
    clean = re.compile(pattern)

    tDelayed = re.sub(clean, r'\1( t - (' + str(offset) + r') )\2', input)

    return tDelayed if not initial else "self.delay( {},{},{},t)".format(tDelayed,offset,initial)


def if_(expression):
    condition = parseExpression(expression[0])
    then = parseExpression(expression[1])
    if type(then) is list and len(then) > 0: then = then[0]

    if then == "":
        then = "0"
    otherwise = parseExpression(expression[2])

    return '( (' + str(then) + ') if (' + str(condition) + ') else (' + str(otherwise) + ') )'

def sum_(*args):
    args = remove_nesting(args)
    if len(args) > 1:
        return 'sum([' + " , ".join([str(parseExpression(x)) for x in remove_nesting(args) if x != "," or x != ", "]) + '])'
    return 'sum(' + " , ".join([str(parseExpression(x)) for x in remove_nesting(args) if x != "," or x != ", "]) + ')'



def min_(*args):
    args = remove_nesting(args)
    if len(args) > 1:
        return 'min([' + " , ".join([str(parseExpression(x)) for x in remove_nesting(args) if x != "," or x != ", "]) + '])'
    return 'min(' + " , ".join([str(parseExpression(x)) for x in remove_nesting(args) if x != "," or x != ", "]) + ')'


def max_(*args):
    args = remove_nesting(args)
    if len(args) > 1:
        return 'max([' + " , ".join([str(parseExpression(x)) for x in remove_nesting(args) if x != "," or x != ", "]) + '])'
    else:
        return 'max( ' + " , ".join([str(parseExpression(x)) for x in remove_nesting(args) if x != "," or x != ", "]) + ')'

def size_(*args):
    args = remove_nesting(args)

    if type(args) is float or type(args) is int:
        return args

    if type(args) is dict:
        args = [args]

    if type(args) is list:
        if len(args) == 1:
            try:
                length = float(parseExpression(args[0]))
                return length
            except:
                return "(len({}))".format(parseExpression(args[0]))
        else:
            return '(len([' + " , ".join([str(parseExpression(x)) for x in args]) + ']))'

def interpolate_(*args):
    args = remove_nesting(args)
    try: variable = "\"{}\"".format(args[0]["name"])
    except: variable =parseExpression(args[0]) # Unpredictable behavior! Usually, args[0] should be an identifier

    args = args[1:]
    return "( self.interpolate({}, t, {}) )".format(variable, ", ".join([str(x) for x in args]))

def mean_(*args):
    args = remove_nesting(args)

    if len(args) > 1:
        return 'np.mean([' + " , ".join([str(parseExpression(x)) for x in args]) + '])'
    else:
        return 'np.mean(' + " , ".join([str(parseExpression(x)) for x in args]) + ')'

def prod_(*args):
    args = remove_nesting(args)
    if len(args) > 1:
        return 'np.product([' + "+".join([str(parseExpression(x)) for x in args]) + '])'
    return 'np.product(' + " , ".join([str(parseExpression(x)) for x in args]) + ')'


def montecarlo_(*args):
    args = remove_nesting(args)

    probability = parseExpression(args[0])
    seed = "None" if len(args) ==1 else parseExpression(args[1])

    return "(self.montecarlo({},{}, t))".format(probability,seed)

def negbinomial_(*args):
    args = remove_nesting(args)

    successes = parseExpression(args[0])
    p = parseExpression(args[1])

    if len(args) > 2:
        seed = parseExpression(args[2])
        return '( self.negbinomial_with_seed({}, {}, {}, t) )'.format(successes,p, seed)

    return '(np.random.negative_binomial({}, {}) )'.format(successes,p)

def poisson_(*args):
    args = remove_nesting(args)
    mu = parseExpression(args[0])

    if len(args) > 1:
        seed = parseExpression(args[1])
        return '( self.poisson_with_seed({},{}, t) )'.format(mu, seed)

    return '(np.random.poisson({}) )'.format(mu)

def logistic_(*args):
    args = remove_nesting(args)

    mean = parseExpression(args[0])
    scale = parseExpression(args[1])

    if len(args) > 2:
        seed = parseExpression(args[2])
        return '( self.logistic_with_seed({}, {}, {}, t) )'.format(mean,scale, seed)

    return '(np.random.logistic({}, {}) )'.format(mean, scale)

def lognormal_(*args):
    args = remove_nesting(args)

    mean = parseExpression(args[0])
    stdev = parseExpression(args[1])

    if len(args) > 2:
        seed = parseExpression(args[2])
        return '( self.lognormal_with_seed({}, {}, {}, t) )'.format(mean,stdev, seed)

    return '(np.random.lognormal({}, {}) )'.format(mean, stdev)


def normalcdf_(*args):
    args = remove_nesting(args)
    left = parseExpression(args[0])
    right = parseExpression(args[1])
    mean = 0 if len(args) <= 2 else parseExpression(args[2])
    sigma = 1 if len(args) <= 3 else parseExpression(args[3])

    return "(self.normalcdf({},{},{},{}) )".format(left, right, mean, sigma)

def random_(*args):
    args = remove_nesting(args)

    min = parseExpression(args[0] )
    max =  parseExpression(args[1])
    if len(args) > 2:
        seed = parseExpression(args[2])

        return '(self.random_with_seed({}, t) * (('.format(seed) + str(max) + ') - (' + str(min) + ')) + (' + str(min) + '))'

    return '(random.random() * ((' + str(max) + ') - (' + str(min) + ')) + (' + str(min) + '))'

def beta_(*args):
    args = remove_nesting(args)
    for elem in args:
        try:
            elem.remove(",")
        except:
            pass

    a = parseExpression(args[0])
    b = parseExpression(args[1])

    if len(args) > 2:
        seed = parseExpression(args[2])
        return '(self.beta_with_seed({},{},{},t) )'.format(a,b,seed)

    return 'np.random.beta({},{})'.format(a,b)

def combinations_(*args):
    args = remove_nesting(args)
    for elem in args:
        try:
            elem.remove(",")
        except:
            pass

    n = parseExpression(args[0])
    r = parseExpression(args[1])

    return '(math.factorial({}) / (math.factorial({}) * math.factorial({}-{})))'.format(n,r,n,r)

def binomial_(*args):
    args = remove_nesting(args)
    for elem in args:
        try:
            elem.remove(",")
        except:
            pass

    n = parseExpression(args[0])
    p = parseExpression(args[1])

    if len(args) > 2:
        seed = parseExpression(args[2])
        return '(self.binomial_with_seed( {}, {}, {}, t) )'.format(n,p,seed)

    return 'np.random.binomial({},{})'.format(n,p)

def weibull_(*args):
    args = remove_nesting(args)
    for elem in args:
        try:
            elem.remove(",")
        except:
            pass

    shape = parseExpression(args[0])
    scale = parseExpression(args[1])

    if len(args) > 2:
        seed = parseExpression(args[2])
        return '(self.weibull_with_seed( {}, {}, {}, t) )'.format(shape,scale,seed)

    return '(np.random.weibull({}) * {} )'.format(shape,scale)


def pareto_(*args):
    args = remove_nesting(args)
    for elem in args:
        try:
            elem.remove(",")
        except:
            pass

    shape = parseExpression(args[0])
    scale = parseExpression(args[1])

    if len(args) > 2:
        seed = parseExpression(args[2])
        return '(np.nan if {} == 0 else self.pareto_with_seed( {}, {}, {}, t) )'.format(scale,shape,scale,seed)

    return '(np.nan if ({} == 0) else (np.random.pareto({}) * {} ) )'.format(scale,shape,scale)

def exprnd_(*args):
    args = remove_nesting(args)
    for elem in args:
        try:
            elem.remove(",")
        except:
            pass

    lambda_ = parseExpression(args[0])


    if len(args) == 2:
        seed = parseExpression(args[1])
        return '(self.exprnd_with_seed({}, {}, t) )'.format(lambda_,seed)

    return 'np.random.exponential({})'.format(lambda_)

def gamma_(*args):
    args = remove_nesting(args)
    for elem in args:
        try:
            elem.remove(",")
        except:
            pass

    shape = parseExpression(args[0])

    if (len(args) == 2):
        scale = parseExpression(args[1])
        return 'np.random.gamma({},{})'.format(shape, scale)

    if len(args) > 2:
        scale = parseExpression(args[1])
        seed = parseExpression(args[2])
        return '(self.gamma_with_seed({}, {}, {}, t) )'.format(shape,scale,seed)

    return 'np.random.gamma({})'.format(shape)

def geometric_(*args):
    args = remove_nesting(args)
    for elem in args:
        try:
            elem.remove(",")
        except:
            pass

    p = parseExpression(args[0])

    if len(args) == 2:
        seed = parseExpression(args[1])
        return '(self.geometric_with_seed({}, {}, t) )'.format(p,seed)

    return 'np.random.geometric({})'.format(p)

def normal_(*args):
    args = remove_nesting(args)
    for elem in args:
        try:
            elem.remove(",")
        except:
            pass
    mean = args[0] if type(args[0]) is str or type(args[0]) is float else args[0][0]
    dev = args[1] if type(args[1]) is str or type(args[1]) is float else args[1][0]

    if len(args) > 2:
        seed = parseExpression(args[2])
        return ' ((( math.sqrt( -2 * math.log( self.random_with_seed({}, t) ) ) * math.cos( 2 * math.pi * self.random_with_seed({}, t) )) * ('.format(
            seed, seed) + str(
            dev) + ')) + (' + str(mean) + '))'

    return ' ((( math.sqrt( -2 * math.log( random.random() ) ) * math.cos( 2 * math.pi * random.random() )) * (' + str(
        dev) + ')) + (' + str(mean) + '))'

def gammaln_(*args):
    args = remove_nesting(args)
    for elem in args:
        try:
            elem.remove(",")
        except:
            pass
    if len(args) > 1:
        print("GAMMALM only supported with one argument. Skipping all other arguments")

    x = parseExpression(args[0])

    return 'gammaln({})'.format(x)

def factorial_(*args):
    args = remove_nesting(args)
    for elem in args:
        try:
            elem.remove(",")
        except:
            pass
    n = parseExpression(args[0])
    return "math.factorial(int({}))".format(n)

def step_(*args):
    args = remove_nesting(args)
    for elem in args:
        try:
            elem.remove(",")
        except:
            pass
    height = parseExpression(args[0])
    time = parseExpression(args[1])

    return "(0 if t < " + str(time) + " else " + str(height) + ")"

def safediv_(*args):
    args = remove_nesting(args)

    nominator = parseExpression(args[0])
    denominator = parseExpression(args[1])
    onzero = None if len(args) ==2 else parseExpression(args[2])

    if onzero is not None:
        return "(( "+ str(onzero) + ")" + ' if (' + str(denominator) + ') == 0 else (' + str(nominator) + ' / ' + str(denominator) + "))"
    else:
        return "((0)" + ' if (' + str(denominator) + ') == 0 else (' + str(nominator) + ' / ' + str(
            denominator) + "))"

def history_(*args):
    args = remove_nesting(args)

    for elem in args:
        try:
            elem.remove(",")
        except:
            pass

    name = args[0]["name"]

    t = parseExpression(args[1])
    if "self.memoize" in t:
        return "self.memoize(\”{}\",\' {} \')".format(name,t)
    return "self.memoize(\"{}\", {})".format(name,t)

def rank_(*args):
    args = remove_nesting(args)

    for elem in args:
        try:
            elem.remove(",")
        except:
            pass

    rank = remove_nesting(args[-1])
    if (type(rank)) is list:
        for elem in rank:
            try:
                elem.remove(",")
            except:
                pass

    rank = parseExpression(rank)
    if len(args) > 2:
        return "self.rank([" + ",".join(parseExpression(arg) for arg in args[:-1]) + "], " + str(rank) + ")"

    return "self.rank(" + ",".join(parseExpression(arg) for arg in args[:-1]) + ", " + str(rank) + ")"

def permutations_(*args):
    args = remove_nesting(args)

    n = parseExpression(args[0])
    r = parseExpression(args[1])

    return "( math.factorial( int({}) ) / math.factorial( int({}) - int({}) ) )".format(n,n,r)

def triangular_(*args):
    args = remove_nesting(args)
    if len(args) > 4:
        logging.warning("TRIANGULAR is currently only supported for a maximum of 4 arguments: <lower bound>, <mode>, <upper bound>, [<seed>]")

    left = parseExpression(args[0])
    mode = parseExpression(args[1])
    right = parseExpression(args[2])

    if len(args) == 4:
        seed = parseExpression(args[3])
        return "( self.triangular_with_seed({}, {}, {}, {}, t) )".format(left, mode, right, seed)
    else:
        return "(np.random.triangular({}, {}, {}) ) ".format(left, mode, right)



def percent_(*args):
    args = remove_nesting(args)
    for elem in args:
        try:
            elem.remove(",")
        except:
            pass
    return "({}*100)".format(parseExpression(args[0]))

def counter_(*args):
    args = remove_nesting(args)
    for elem in args:
        try:
            elem.remove(",")
        except:
            pass
    return "self.counter({},{},t)".format(parseExpression(args[0]),parseExpression(args[1]))

''' Financial Builtins '''
def npv_(*args):
    args = remove_nesting(args)
    initial = parseExpression(args[0])
    p = parseExpression(args[1])
    return "self.npv({},{},t)".format(initial,p)

def pmt_(*args):
    args = remove_nesting(args)
    p = parseExpression(args[0])
    n = parseExpression(args[1])
    C = parseExpression(args[2])
    fv = parseExpression(args[3])

    if fv == "0" or fv == 0:
        return "( -{} * ( ( 1+ {})**{}*{}) / ( ( 1+{})**{}-1) ) ".format(C,p,n,p,p,n)
    print("PMT with Future Value argument not yet supported!")
    return "0"

def fv_(*args):
    args = remove_nesting(args)
    p = parseExpression(args[0])
    n = parseExpression(args[1])
    pmt = parseExpression(args[2])
    pv = parseExpression(args[3])

    if pv == "0" or pv == 0:
        return "(-sum([ {}* (1 + {} ) **t for t in range(0, int( {}) )]) )".format(pmt,p,n)
    print("FV with Present Value argument not yet supported!")
    return "0"

def pv_(*args):
    args = remove_nesting(args)
    p = parseExpression(args[0])
    n = parseExpression(args[1])
    pmt = parseExpression(args[2])
    fv = parseExpression(args[3])

    if fv == "0" or fv == 0:
        return "(- ({} * ( 1 - (( 1+{})**(-{}))) / {}))".format(pmt, p, n , p)

    print("PV with Future Value argument not yet supported!")
    return "0"

def irr_(*args):
    args = remove_nesting(args)

    if type(args[0]) is dict and args[0]["type"] == "identifier":
        stock_name = args[0]["name"]

        missing = parseExpression(args[1]) if len(args) > 1 else "None"
        myname = args[2]

        return "( self.irr(\'{}\', {}, t, \'{}\') )".format(stock_name,missing,myname)

    else:
        import logging
        logging.error("First Argument of IRR needs to be a Stock or Flow identifier! No terms are supported here.")
        return "0"

def smth3_(*args):
    args = remove_nesting(args)
    inputstream = parseExpression(args[0])
    try:
        inputstream = "\"{}\"".format(args[0]["name"])
    except:
        pass

    averaging_time = parseExpression(args[1])
    initial = "None" if len(args) < 3 else parseExpression(args[2])

    return "self.smthn({}, {}, {}, 3, t)".format(inputstream,averaging_time,initial)

def smth1_(*args):
    args = remove_nesting(args)
    inputstream = parseExpression(args[0])
    try:
        inputstream = "\"{}\"".format(args[0]["name"])
    except:
        pass

    averaging_time = parseExpression(args[1])
    initial = "None" if len(args) < 3 else parseExpression(args[2])

    return "self.smthn({}, {}, {}, 1, t)".format(inputstream,averaging_time,initial)

def smthn_(*args):
    args = remove_nesting(args)
    inputstream = parseExpression(args[0])
    try:
        inputstream = "\"{}\"".format(args[0]["name"])
    except:
        pass

    averaging_time = parseExpression(args[1])
    n = parseExpression(args[2])
    initial = "None" if len(args) < 4 else parseExpression(args[3])

    return "self.smthn({}, {}, {}, {}, t)".format(inputstream,averaging_time,initial,n)

def forcst_(*args):
    args = remove_nesting(args)

    inputstream = parseExpression(args[0])
    averaging_time = parseExpression(args[1])
    horizon = parseExpression(args[2])
    initial = 0 if len(args) < 4 else parseExpression(args[3])

    return "(self.forcst({},{},{},{},t))".format(inputstream,averaging_time,horizon, initial)


builtins = {

    # Simulation Buildins
    'dt': lambda *args: 'self.dt',
    'starttime': lambda *args: ' self.starttime ',
    'stoptime': lambda *args: ' self.stoptime ',
    'time': lambda *args: ' t ',
    'pi': lambda *args: ' math.pi ',

    # Array builtins
    # http://www.iseesystems.com/Helpv10/Content/Reference/Builtins/Array_builtins.htm
    'size': lambda *args: size_(args) ,

    'stddev': lambda *args: 'np.std(' + ','.join([str(parseExpression(x)) for x in args]) + ')',

    'sum': lambda *args: 'np.sum(' + "+".join([str(parseExpression(x)) for x in args]) + ')',

    'mean': lambda *args: mean_(args),

    'rank': lambda *args : rank_(args),

    'interpolate' : lambda *args : interpolate_(args),

    # Data builtins
    # http://www.iseesystems.com/Helpv10/Content/Reference/Builtins/Data_builtins.htm
    'previous': lambda args: previous(args),

    # Mathematical builtins
    # http://www.iseesystems.com/Helpv10/Content/Reference/Builtins/Mathematical_builtins.htm
    'abs': lambda body: '(abs( ' + ",".join(parseExpression(body)) + ' ))' if type(parseExpression(body)) is list else '(abs({}))'.format(parseExpression(body)),

    'max': lambda *args: max_(args),

    'min': lambda *args: min_(args),

    'prod': lambda *args: prod_(args),

    'int': lambda body: 'math.floor( ' + parseExpression(body)+ ' )',

    'sin': lambda body: 'math.sin(' + parseExpression(body) + ' )',

    'cos': lambda body:  'math.cos(' + parseExpression(body) + ')',

    'tan': lambda body: 'math.tan(' + parseExpression(body) + ')',

    'round': lambda body: 'round(' + parseExpression(body) + ')',

    'arccos' : lambda body: 'np.arccos(' + parseExpression(body) + ')',

    'arcsin' : lambda body: 'np.arcsin(' + parseExpression(body) + ')',

    'arctan': lambda body: 'np.arctan(' + parseExpression(body) + ')',

    'safediv': lambda *args: safediv_(args),

    'step': lambda *args: step_(args),

    'rootn' : lambda *args: "( self.rootn({}, {}) )".format(parseExpression(remove_nesting(args)[0]) ,parseExpression(remove_nesting(args)[1] )),

    'sqrt': lambda *args: "({} ** 0.5 )".format(parseExpression(remove_nesting(args))),

    'log10': lambda *args: "(np.log10({}))".format(parseExpression(remove_nesting(args))),

    'ln': lambda *args: "(np.log({}))".format(parseExpression(remove_nesting(args))),

    'sinwave' : lambda *args : "( np.sin(2*np.pi / {} * (t-self.starttime) ) * {} )".format(parseExpression(remove_nesting(args)[1]),parseExpression(remove_nesting(args)[0])),

    'coswave': lambda *args: "( np.cos(2*np.pi / {} * (t-self.starttime) ) * {} )".format(
        parseExpression(remove_nesting(args)[1]), parseExpression(remove_nesting(args)[0])),

    # Logical builtins
    # http://www.iseesystems.com/Helpv10/Content/Reference/Builtins/Logical_builtins.htm
    'if': lambda expression: if_(expression),
    # then, condition, otherwise :  '( (' + then + ') if (' + condition + ') else (' + otherwise + ') )',

    # Delay builtins
    # http://www.iseesystems.com/Helpv10/Content/Reference/Builtins/Delay_builtins.htm
    'delay': lambda *args: delay(args),

    'exp': operators['exp'],

    'delay1': lambda *args : smth1_(args),

    'delay3' : lambda *args:  smth3_(args),

    'delayn' :lambda *args:  smthn_(args),

    'smth3' : lambda *args:  smth3_(args),

    'smthn' : lambda *args:  smthn_(args),

    # Data builtins
    # http://www.iseesystems.com/Helpv10/Content/Reference/Builtins/Data_builtins.htm
    'init': lambda *args: parseExpression(args).replace(", t", ", self.starttime"),

    'endval' : lambda *args : endval_(args),

    # Statistical builtins
    # http://www.iseesystems.com/Helpv10/Content/Reference/Builtins/Statisticall_builtins.htm
    'normalcdf' : lambda *args : normalcdf_(args),

    'normal': lambda *args: normal_(args),

    'derivn' : lambda *args : derivn_(args),

    'random': lambda *args: random_(args),

    'uniform': lambda *args: random_(args),

    'montecarlo' : lambda *args : montecarlo_(args),

    'beta': lambda *args : beta_(args),

    'binomial' : lambda *args : binomial_(args),

    'weibull' : lambda *args : weibull_(args),

    'pareto' : lambda *args : pareto_(args),

    'logistic': lambda *args : logistic_(args),

    'combinations' : lambda *args: combinations_(args),

    'counter': lambda *args : counter_(args),

    'gamma' : lambda *args: gamma_(args),

    'factorial': lambda *args: factorial_(args),

    'exprnd' : lambda *args : exprnd_(args),

    'gammaln' : lambda *args : gammaln_(args),

    'geometric' : lambda *args : geometric_(args),

    'history' : lambda *args : history_(args),

    'percent' : lambda *args : percent_(args),

    'negbinomial' : lambda *args : negbinomial_(args),

    'triangular': lambda *args : triangular_(args),

    'lognormal': lambda *args : lognormal_(args),

    'poisson' : lambda *args : poisson_(args),

    'invnorm' : lambda *args : "(norm.ppf({}))".format(parseExpression(remove_nesting(args)[0])),

    'permutations' : lambda *args : permutations_(args),# "( math.factorial( {} ) / math.factorial( {} - {} )   )".format(parseExpression(remove_nesting(args[0])),parseExpression(remove_nesting(args[0])),parseExpression(remove_nesting(args[1]))),# permutations_(args),

    # Financial Builtins
    # https://www.iseesystems.com/resources/help/v1-9/default.htm#08-Reference/07-Builtins/Financial_builtins.htm#kanchor1089
    'npv' : lambda *args : npv_(args),

    'pmt' : lambda *args : pmt_(args),

    'fv' : lambda *args : fv_(args),

    'pv' : lambda *args : pv_(args),

    'irr' : lambda *args : irr_(args),

    'nan' : lambda *args : 'np.nan',

    # Test input builtins
    # http://www.iseesystems.com/Helpv10/Content/Reference/Builtins/Test_input_builtins.htm
    'pulse': lambda *args: pulse(args),

    'clocktime' : lambda *args : 'int(datetime.utcnow().timestamp())',

    # Misc Builtins
    # https://www.iseesystems.com/resources/help/v1-9/default.htm#08-Reference/07-Builtins/Miscellaneous_builtins.htm#kanchor419
    
    'forcst' : lambda *args: forcst_(args),

    'lookup' : lambda *args : "( self.memoize(\"{}\", {}) )".format(remove_nesting(args)[0]["name"],parseExpression(remove_nesting(args)[1])),

    'lookupinv' : lambda *args : "( self.lookupinv(\"{}\", {}) )".format(remove_nesting(args)[0]["name"],parseExpression(remove_nesting(args)[1])),

    'lookuparea' : lambda *args : "(np.trapz([LERP(  i , self.points[\"{}\"]) for i in np.arange(self.starttime,{} + self.dt,self.dt)], dx=self.dt)) ".format(remove_nesting(args)[0]["name"],parseExpression(remove_nesting(args)[1])),

    'ramp' : lambda *args : ramp_(args),

    'inf' : lambda *args : "np.inf",

    'cgrowth' : lambda *args : " ( self.cgrowth( {} / 100) )".format(parseExpression(remove_nesting(args)[0])),

}
