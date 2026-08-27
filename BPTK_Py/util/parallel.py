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

import sys
from threading import Thread

from ..logger import log


def start_or_run(target, args=()):
    """Start `target` in a thread, or run it inline where threads are unavailable.

    Emscripten - Pyodide, i.e. BPTK running in the browser - has no thread model:
    `Thread.start()` raises `RuntimeError: can't start new thread`. Without this,
    `bptk.run_scenarios()` fails there for both SD and agent-based models, which
    is most of the documented API.

    Running in sequence is safe for the callers that use this. They fan out and
    join together without the workers exchanging anything, so the result does not
    depend on the order or on any overlap. Threads buy little here in any case:
    the work is CPU-bound Python, which the GIL serialises anyway.

    The condition is checked rather than the platform, so any environment without
    threads is covered - including a normal one that has run out of them, where
    computing slowly beats failing.

    Emscripten is the one platform checked by name, because there the condition
    cannot be trusted. A host may replace `threading.Thread` with a shim that
    schedules on the browser event loop - marimo does this in its notebook
    runtime - so `start()` succeeds and only `join()` fails, one step later and
    with a message about JSPI. Threads are synthetic under Pyodide either way:
    no OS threads, no parallel bytecode. Running inline costs nothing there and
    keeps the browsers without JSPI, Safari among them, working.

    **Note on exceptions.** An exception raised in a thread never reaches whoever
    joins it; run inline, it propagates to the caller. That difference is left
    open deliberately: this only changes environments where the threaded path
    does not run at all.

    Args:
        target: The callable to run.
        args: Positional arguments for it.

    Returns:
        The started `Thread`, or `None` when it has already run inline.
    """
    if sys.platform == "emscripten":
        log("[INFO] No usable thread model in the browser, running in sequence "
            "instead. Results are unaffected.")
        target(*args)
        return None

    thread = Thread(target=target, args=args)

    try:
        thread.start()
    except RuntimeError as error:
        log("[WARN] Cannot start a thread ({}), running in sequence instead. "
            "Results are unaffected.".format(error))
        target(*args)
        return None

    return thread


def start_or_skip(target, args=(), what="background task"):
    """Start `target` in a thread, or skip it where threads are unavailable.

    The counterpart to `start_or_run`, and the distinction matters: the callers
    here watch a file in an endless loop, so running inline would never return.
    Skipping is the only sensible degradation - and no loss in the browser, where
    nobody is editing the scenario files being watched.

    Emscripten is checked by name for the same reason as in `start_or_run`, and
    the stakes are higher: under a shim that schedules threads on the browser
    event loop, an endless monitor loop would take that loop over and freeze the
    page.

    Args:
        target: The callable to run.
        args: Positional arguments for it.
        what: Named in the log line when the thread cannot be started.

    Returns:
        The started `Thread`, or `None` when it was skipped.
    """
    if sys.platform == "emscripten":
        log("[INFO] No usable thread model in the browser, continuing without {}.".format(what))
        return None

    thread = Thread(target=target, args=args)

    try:
        thread.start()
    except RuntimeError as error:
        log("[WARN] Cannot start a thread ({}), continuing without {}.".format(error, what))
        return None

    return thread
