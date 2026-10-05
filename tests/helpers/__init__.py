"""What the tests share and that is no test itself: building models and engine JSON,
running a model on both engines, reading the logfile, the external state settings.

Nothing in here imports the Rust engine at module level, so a test module may import
from here on a platform without the engine - the browser - without failing collection.
"""
