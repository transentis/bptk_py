#                                                       /`-
# _                                  _   _             /####`-
# | |                                | | (_)           /########`-
# | |_ _ __ __ _ _ __  ___  ___ _ __ | |_ _ ___       /###########`-
# | __| '__/ _` | '_ \/ __|/ _ \ '_ \| __| / __|   ____ -###########/
# | |_| | | (_| | | | \__ \  __/ | | | |_| \__ \  |    | `-#######/
# \__|_|  \__,_|_| |_|___/\___|_| |_|\__|_|___/  |____|    `- # /
#
# Copyright (c) 2018-2026 transentis labs GmbH
# MIT License

"""The XMILE compiler: transpiles Stella/iThink models into the SD DSL.

This package deliberately imports nothing at module level, so that the compiler stays
out of the import path of `import BPTK_Py` until a model is compiled.
"""


def compile_xmile(*args, **kwargs):
    """Compile an XMILE model, importing the compiler on first use.

    A thin wrapper around `BPTK_Py.sdcompiler.compile.compile_xmile` that keeps the
    compiler out of `import BPTK_Py`.

    Args:
        src: Path to the XMILE source file.
        dest: Path the generated model is written to.
        target: "py-sddsl" - an SD DSL model - or "json-rust-engine" - the Rust engine's JSON.
    """
    from .compile import compile_xmile as _compile_xmile

    return _compile_xmile(*args, **kwargs)
