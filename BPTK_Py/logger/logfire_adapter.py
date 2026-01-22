#                                                       /`-
# _                                  _   _             /####`-
#| |                                | | (_)           /########`-
#| |_ _ __ __ _ _ __  ___  ___ _ __ | |_ _ ___       /###########`-
#| __| '__/ _` | '_ \/ __|/ _ \ '_ \| __| / __|   ____ -###########/
#| |_| | | (_| | | | \__ \  __/ | | | |_| \__ \  |    | `-#######/
# \__|_|  \__,_|_| |_|___/\___|_| |_|\__|_|___/  |____|    `- # /
#
# Copyright (c) 2024 transentis labs GmbH
# MIT License

import datetime

try:
    import logfire
    LOGFIRE_AVAILABLE = True
except ImportError:
    LOGFIRE_AVAILABLE = False


class LogfireAdapter:
    """
    Adapter for routing BPTK logs to Pydantic Logfire.
    """

    def __init__(self, **logfire_config):
        """
        Initialize the Logfire adapter.

        Args:
            **logfire_config: Configuration parameters to pass to logfire.configure()
                            Common options include:
                            - project_name: Name of your Logfire project
                            - token: Your Logfire API token
                            - environment: Environment name (e.g., 'development', 'production')
        """
        if not LOGFIRE_AVAILABLE:
            raise ImportError(
                "Logfire is not installed. "
                "Please install it with: pip install logfire"
            )

        self.configured = False
        self.logfire_config = logfire_config
        self._configure()

    def _configure(self):
        """Configure Logfire with the provided settings."""
        if not self.configured:
            logfire.configure(**self.logfire_config)
            self.configured = True

    def log(self, message: str):
        """
        Send a log message to Logfire.

        Args:
            message: The log message (may contain [ERROR], [WARN], [INFO] prefixes)
        """
        if not self.configured:
            self._configure()

        # Parse the log level from the message if it contains a bracket pattern
        level = "INFO"  # default
        if "[ERROR]" in message:
            level = "ERROR"
        elif "[WARN]" in message:
            level = "WARN"
        elif "[INFO]" in message:
            level = "INFO"
      

        # Clean the message by removing the level brackets if present
        clean_message = message
        for bracket_level in ["[ERROR]", "[WARN]", "[INFO]"]:
            clean_message = clean_message.replace(bracket_level, "").strip()

        # Escape curly braces to prevent Logfire from interpreting them as format strings
        # This is needed when logging dictionaries or JSON-like content
        clean_message = clean_message.replace("{", "{{").replace("}", "}}")

        # Send to Logfire with appropriate level
        # Pass the message directly without underscore parameters to avoid Logfire errors
        if level == "ERROR":
            logfire.error(clean_message)
        elif level == "WARN":
            logfire.warn(clean_message)
        else:  # INFO or default
            logfire.info(clean_message)