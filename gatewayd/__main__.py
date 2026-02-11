"""Entry point for running gatewayd as a module."""

import os
from gatewayd.app import create_app

if __name__ == "__main__":
    app = create_app()
    debug_mode = os.getenv("DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=5000, debug=debug_mode)
