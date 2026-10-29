#                                                       /`-
# _                                  _   _             /####`-
# | |                                | | (_)           /########`-
# | |_ _ __ __ _ _ __  ___  ___ _ __ | |_ _ ___       /###########`-
# | __| '__/ _` | '_ \/ __|/ _ \ '_ \| __| / __|   ____ -###########/
# | |_| | | (_| | | | \__ \  __/ | | | |_| \__ \  |    | `-#######/
# \__|_|  \__,_|_| |_|___/\___|_| |_|\__|_|___/  |____|    `- # /
#
# Copyright (c) 2020-2026 transentis labs GmbH
# MIT License

try:
    from .parsers.xmile.xmile import parse_xmile
    from .plugins import sortEntities, resolveSelf, fillEmptyEquations, replaceDimensionNames
    standalone = False

except ImportError as package_import_error:
    # The relative imports fail when this module is loaded outside the package
    # (standalone, exercised by tests/unittests/test_sdcompiler_*.py). Should the
    # absolute imports fail too, the original says more than "No module named
    # 'parsers'", so it is the one re-raised.
    try:
        from parsers.xmile.xmile import parse_xmile
        from plugins import sortEntities, resolveSelf, fillEmptyEquations, replaceDimensionNames
        standalone = True
    except ImportError:  # pragma: no cover - the package is always importable here
        raise package_import_error from None

import importlib

# Getting the generator module. Here I'd find the targets!
if standalone:
    mod = importlib.import_module("generator",package=".")
else:
    # Finding my own name and stripping it off to obtain my package name
    find = __name__.rfind(".compile")

    # Getting the generator module. Here I'd find the targets!
    mod = importlib.import_module(".generator", package=__name__[0:find])


def _structure_chain(IR):
    """The plugins that keep the model's structure: stocks stay stocks with their flows,
    arrays arrays, the builtins what they are."""
    return sortEntities(fillEmptyEquations(resolveSelf(replaceDimensionNames(IR))))


def _targets():
    return {"py-sddsl": (_structure_chain, getattr(mod, "py_sddsl")),
            "json-rust-engine": (_structure_chain, getattr(mod, "json_rust_engine"))}


def compile_xmile(src, dest, target):
    '''
    Compile the XMILE model `src` for `target` and write the result to `dest`.
    :param src: the XMILE file
    :param dest: the file to write
    :param target: "py-sddsl" - an SD DSL model - or "json-rust-engine" - the Rust
        engine's JSON, derived from the SD DSL model
    :return:
    '''
    targets = _targets()
    if target not in targets:
        class TargetNotSupportedException(Exception):
            pass
        removed = " - the target 'py' was removed in 3.5.0" if target == "py" else ""
        raise TargetNotSupportedException("Target Language {} not supported{}: use {}".format(
            target, removed, " or ".join("'{}'".format(name) for name in targets)))

    chain, generator = targets[target]
    result = generator(chain(parse_xmile(src)))

    # Write out the file. Python reads its source as UTF-8 whatever the platform's own
    # encoding is, and a name may carry an umlaut
    with open(dest, "w", encoding="utf-8") as outfile:
        outfile.write(result)
