

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
class RustBackendError(Exception):
    """The Rust backend was asked for and cannot run this model.

    Raised instead of quietly computing the answer on the Python engine. Both engines
    produce the same numbers, which is what made the silence easy to live with - and
    dangerous: a run that was meant to be fast, or whose results were meant to come
    from the engine, looked exactly like one that had.

    Four things cause it, and the message says which: the model cannot be expressed in
    the engine's format, it is a compiled XMILE model and has no serialization at all,
    this installation has no Rust engine, or the engine failed while running.

    A user-defined function is not one of them. Such a model runs on the engine and
    calls back into Python at those nodes, says so at `[WARN]`, and continues.
    """
    pass


def rust_backend_error(error):
    """Build a `RustBackendError` whose message says which of the four cases this is.

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
            "cannot be served. A model compiled from XMILE is a plain Python class with "
            "no serialization; such models reach the engine in a later release. Ask for "
            "backend='python'. ({})".format(error))

    return RustBackendError(
        "The Rust engine cannot run this model: {}".format(error))
