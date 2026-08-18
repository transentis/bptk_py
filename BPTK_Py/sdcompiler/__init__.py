#                                                       /`-
# _                                  _   _             /####`-
# | |                                | | (_)           /########`-
# | |_ _ __ __ _ _ __  ___  ___ _ __ | |_ _ ___       /###########`-
# | __| '__/ _` | '_ \/ __|/ _ \ '_ \| __| / __|   ____ -###########/
# | |_| | | (_| | | | \__ \  __/ | | | |_| \__ \  |    | `-#######/
# \__|_|  \__,_|_| |_|___/\___|_| |_|\__|_|___/  |____|    `- # /
#
# Copyright (c) 2018 transentis labs GmbH
# MIT License

"""The XMILE compiler: transpiles Stella/iThink models into Python.

This package deliberately imports nothing at module level. Its parsers and
generator pull parsimonious, xmltodict and jinja2, which ship as the optional
`bptk-py[xmile]` extra - keeping them out of the import path of `import BPTK_Py`
is the point of the `compile_xmile` wrapper below.
"""

XMILE_EXTRA_HINT = (
    "Compiling XMILE models requires the xmile extra. "
    "Install it with: pip install bptk-py[xmile]"
)


def compile_xmile(*args, **kwargs):
    """Compile an XMILE model, importing the compiler on first use.

    A thin wrapper around `BPTK_Py.sdcompiler.compile.compile_xmile` that does
    two things the direct import cannot: it keeps the compiler's dependencies
    out of `import BPTK_Py`, and it turns a missing extra into an instruction
    rather than a traceback about parsimonious.

    Args:
        src: Path to the XMILE source file.
        dest: Path the generated Python model is written to.
        target: The target language, "py".
    """
    try:
        from .compile import compile_xmile as _compile_xmile
    except ImportError as error:
        raise ImportError(XMILE_EXTRA_HINT) from error

    return _compile_xmile(*args, **kwargs)
