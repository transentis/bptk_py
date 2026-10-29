#                                                       /`-
# _                                  _   _             /####`-
# | |                                | | (_)           /########`-
# | |_ _ __ __ _ _ __  ___  ___ _ __ | |_ _ ___       /###########`-
# | __| '__/ _` | '_ \/ __|/ _ \ '_ \| __| / __|   ____ -###########/
# | |_| | | (_| | | | \__ \  __/ | | | |_| \__ \  |    | `-#######/
# \__|_|  \__,_|_| |_|___/\___|_| |_|\__|_|___/  |____|    `- # /
#
# Copyright (c) 2026 transentis labs GmbH
# MIT License

"""The `json-rust-engine` target: an XMILE model as the Rust engine's JSON.

Derived from the `py-sddsl` target: its code is built in memory and run, and the model it
builds is written with `Model.to_json()` - the JSON every SD DSL model gives the engine. So
the two targets share one translation of every builtin, and a model computes the same
whichever of them it took.
"""

from ..sddsl.sddsl import GeneratorError, _Generator


def generate(IR):
    generator = _Generator(IR)
    source = generator.module()
    if generator.functions:
        # A user-defined function is answered by Python while the model runs; the JSON is
        # meant for the engine on its own
        raise GeneratorError("Model '{}' calls {}, which Python computes while the model runs: the "
                             "engine's JSON has to run without Python - compile it with py-sddsl".format(
                                 IR.get("name"), ", ".join(name.upper() for name in generator.functions)))
    namespace = {}
    exec(compile(source, "<py-sddsl of {}>".format(IR.get("name")), "exec"), namespace)
    return namespace["simulation_model"]().to_json()
