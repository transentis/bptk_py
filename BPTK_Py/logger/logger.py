#                                                       /`-
# _                                  _   _             /####`-
#| |                                | | (_)           /########`-
#| |_ _ __ __ _ _ __  ___  ___ _ __ | |_ _ ___       /###########`-
#| __| '__/ _` | '_ \/ __|/ _ \ '_ \| __| / __|   ____ -###########/
#| |_| | | (_| | | | \__ \  __/ | | | |_| \__ \  |    | `-#######/
# \__|_|  \__,_|_| |_|___/\___|_| |_|\__|_|___/  |____|    `- # /
#
# Copyright (c) 2018 transentis labs GmbH
# MIT License

import datetime
import logging

# Configuration variables
loglevel = "WARN"
logfile = "bptk_py.log"
logmodes = ["logfile"]

# Logfire adapter support
logfire_adapter = None
logfire_enabled = False

try:
    from .logfire_adapter import LogfireAdapter, LOGFIRE_AVAILABLE
except ImportError:
    LOGFIRE_AVAILABLE = False
    LogfireAdapter = None



def configure_logfire(**logfire_config):
    """
    Configure and enable Pydantic Logfire logging.

    Args:
        **logfire_config: Configuration parameters to pass to logfire.configure()
                         Common options include:
                         - project_name: Name of your Logfire project
                         - token: Your Logfire API token
                         - environment: Environment name (e.g., 'development', 'production')

    Returns:
        bool: True if Logfire was successfully configured, False otherwise

    Example:
        >>> import BPTK_Py.logger.logger as logmod
        >>> logmod.configure_logfire(project_name="my_bptk_project")
    """
    global logfire_adapter, logfire_enabled

    if not LOGFIRE_AVAILABLE:
        if "logfile" in logmodes:
            with open(logfile, "a", encoding="UTF-8") as myfile:
                myfile.write(f"{datetime.datetime.now()}, [WARN] Logfire is not installed. "
                           "Install with: pip install logfire\n")
        return False

    try:
        logfire_adapter = LogfireAdapter(**logfire_config)
        logfire_enabled = True
        log("[INFO] Logfire logging enabled successfully")
        return True
    except Exception as e:
        if "logfile" in logmodes:
            with open(logfile, "a", encoding="UTF-8") as myfile:
                myfile.write(f"{datetime.datetime.now()}, [ERROR] Failed to configure Logfire: {e}\n")
        return False


def disable_logfire():
    """Disable Logfire logging."""
    global logfire_enabled
    logfire_enabled = False
    log("[INFO] Logfire logging disabled")


class FallbackSpan:
    """Fallback context manager for creating spans without Logfire."""

    def __init__(self, name, **attributes):
        self.name = name
        self.attributes = attributes
        self.start_time = None

    def __enter__(self):
        """Start the span."""
        # Log the span start
        attr_str = ", ".join(f"{k}={v}" for k, v in self.attributes.items())
        if attr_str:
            log(f"[INFO] SPAN_START: {self.name} ({attr_str})")
        else:
            log(f"[INFO] SPAN_START: {self.name}")

        # Track timing
        self.start_time = datetime.datetime.now()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """End the span."""
        # Calculate duration
        duration_ms = None
        if self.start_time:
            duration = datetime.datetime.now() - self.start_time
            duration_ms = duration.total_seconds() * 1000

        # Log the span end
        if duration_ms is not None:
            log(f"[INFO] SPAN_END: {self.name} (duration={duration_ms:.2f}ms)")
        else:
            log(f"[INFO] SPAN_END: {self.name}")

        return False  # Don't suppress exceptions


def span(name, **attributes):
    """
    Create a span context manager for tracing operations.

    Usage:
        with logger.span("database_query", query_type="SELECT"):
            # Your code here
            pass

    This will:
    - Create a native Logfire span if Logfire is enabled
    - Otherwise, create a fallback span that logs start/end times
    """
    
    # If Logfire is enabled and available, return the actual Logfire span directly
    if logfire_enabled and LOGFIRE_AVAILABLE:
        try:
            import logfire
            # Return the native Logfire span - no wrapping needed
            return logfire.span(name, **attributes)
        except Exception as e:
            log(f"[WARN] Failed to create Logfire span: {e}, falling back to basic span")

    # Otherwise, return our fallback span
    return FallbackSpan(name, **attributes)


def log(message):
    """logs all log messages either to file or stdout"""
    message = message.replace("\n", "")

    if loglevel == "ERROR":
        if not "ERROR" in message:
            return

    if loglevel == "WARN":
        if not "ERROR" in message and not "WARN" in message:
            return

    if "logfile" in logmodes:
        with open(logfile, "a", encoding="UTF-8") as myfile:
            myfile.write(str(datetime.datetime.now()) + ", " + message + "\n")

    if "print" in logmodes or "[ERROR]" in message:
        print(str(datetime.datetime.now()) + ", " + message)

    # Send to Logfire if enabled
    if logfire_enabled and logfire_adapter:
        try:
            logfire_adapter.log(message)
        except Exception as e:
            # Fail silently to avoid disrupting the main application
            # Optionally log this error to file
            if "logfile" in logmodes:
                with open(logfile, "a", encoding="UTF-8") as myfile:
                    myfile.write(f"{datetime.datetime.now()}, [WARN] Failed to send log to Logfire: {e}\n")
