#                                                       /`-
# _                                  _   _             /####`-
# | |                                | | (_)           /########`-
# | |_ _ __ __ _ _ __  ___  ___ _ __ | |_ _ ___       /###########`-
# | __| '__/ _` | '_ \/ __|/ _ \ '_ \| __| / __|   ____ -###########/
# | |_| | | (_| | | | \__ \  __/ | | | |_| \__ \  |    | `-#######/
# \__|_|  \__,_|_| |_|___/\___|_| |_|\__|_|___/  |____|    `- # /
#
# Copyright (c) 2019-2026 transentis labs GmbH
# MIT License

class WrongParamException(Exception):
    pass

class WrongTypeException(Exception):
    pass

class NoAgentAvailableException(Exception):
    pass

class NoSuchEquationException(Exception):
    pass

class NoDataProducedException(Exception):
    pass
class CyclicDependencyError(ValueError):
    """Elements that read one another within the same timestep, so none can go first.

    A stock or a `delay` reads an earlier step and breaks such a loop; without one, the
    model has no order to evaluate in. The message names the loop in the words the Rust
    engine uses for the same model, and is a `ValueError` for the same reason.
    """
    pass

class RustBackendError(Exception):
    """The Rust backend was asked for and cannot run this model.

    Raised instead of quietly computing the answer on the Python engine. Both engines
    produce the same numbers, which is what made the silence easy to live with - and
    dangerous: a run that was meant to be fast, or whose results were meant to come
    from the engine, looked exactly like one that had.

    Four things cause it, and the message says which: the model cannot be expressed in
    the engine's format, it is no `Model` and has no serialization at all,
    this installation has no Rust engine, or the engine failed while running.

    A user-defined function is not one of them. Such a model runs on the engine and
    calls back into Python at those nodes, says so at `[WARN]`, and continues.
    """
    pass


def rust_backend_error(error):
    """Build a `RustBackendError` whose message names the cause.

    The caller passes what actually went wrong; the wording is here so that the three
    places that run a model on the engine cannot drift apart.
    """
    if isinstance(error, ImportError):
        return RustBackendError(
            "This installation has no Rust engine, so backend='rust' cannot be served. "
            "The pure-Python wheel - the one micropip installs in a browser - carries no "
            "compiled engine. Ask for backend='python', or install a platform wheel. "
            "({})".format(error))

    if isinstance(error, AttributeError):
        return RustBackendError(
            "This model cannot be serialized for the Rust engine, so backend='rust' "
            "cannot be served. Only a BPTK-Py Model is serialized - a class of your own "
            "is not, and neither is a file transpiled from XMILE by a release before "
            "3.5.0 whose source is gone. Build the model as a Model, or ask for "
            "backend='python'. ({})".format(error))

    return RustBackendError(
        "The Rust engine cannot run this model: {}".format(error))
