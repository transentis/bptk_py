from BPTK_Py import BptkServer

from model import bptk_factory

# Calling the BptkServer class
application = BptkServer(__name__, bptk_factory)

if __name__ == "__main__":
    application.run()
