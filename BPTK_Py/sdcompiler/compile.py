#                                                       /`-
# _                                  _   _             /####`-
# | |                                | | (_)           /########`-
# | |_ _ __ __ _ _ __  ___  ___ _ __ | |_ _ ___       /###########`-
# | __| '__/ _` | '_ \/ __|/ _ \ '_ \| __| / __|   ____ -###########/
# | |_| | | (_| | | | \__ \  __/ | | | |_| \__ \  |    | `-#######/
# \__|_|  \__,_|_| |_|___/\___|_| |_|\__|_|___/  |____|    `- # /
#
# Copyright (c) 2020 transentis labs GmbH
# MIT License
try:
    from .parsers.xmile.xmile import parse_xmile
    from .plugins import StockExpressions,ExpandArrays, sortEntities,FindComplexFunctions, resolveSelf, resolveAsterisk, fixLabels, filterGhosts, replaceDimensionNames
    standalone = False

except:
    from parsers.xmile.xmile import parse_xmile
    from plugins import StockExpressions,ExpandArrays, sortEntities, FindComplexFunctions, resolveSelf, resolveAsterisk, fixLabels, filterGhosts, replaceDimensionNames
    standalone = True

import importlib

# Getting the generator module. Here I'd find the targets!
if standalone:
    mod = importlib.import_module("generator",package=".")
else:
    # Finding my own name and stripping it off to obtain my package name
    find = __name__.rfind(".compile")

    # Getting the generator module. Here I'd find the targets!
    mod = importlib.import_module(".generator", package=__name__[0:find])


def compile_xmile(src, dest, target):
    '''
    Main entry point. No need to ever change. It automagically finds all generators within the sd_compiler.generator package.
    Make sure to export from there.
    :param src:
    :param dest:
    :param target:
    :return:
    '''

    ## Check whether there is a generator for the target language
    if not hasattr(mod, target):
        class TargetNotSupportedException(Exception):
            pass
        raise TargetNotSupportedException("Target Language {} not (yet) supported".format(target))

    # Build Intermediate Representation

    IR = fixLabels(
        FindComplexFunctions(
            resolveAsterisk(
                sortEntities(
                    ExpandArrays(
                        filterGhosts(
                            resolveSelf(
                                replaceDimensionNames(
                                    StockExpressions(
                                            parse_xmile(src))))))))))

    # Get the Generator for the target language
    generator = getattr(mod,target)

    result = generator(IR)

    # Write out the file
    with open(dest,"w") as outfile:
        outfile.write(result)



