import sys
import os
# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# # Load Client Secret securely from a file
# client_secret_path = os.path.expanduser("~/.benchling_client_secret")

# if os.path.exists(client_secret_path):
#     with open(client_secret_path, "r") as f:
#         CLIENT_SECRET = f.read().strip()
# else:
#     CLIENT_SECRET = None  # Handle missing secret gracefully

# # Load Client ID from environment variable
# CLIENT_ID = os.getenv("CLIENT_ID", "mDI9Ank6Lo")  # Replace if needed

import os
from dotenv import load_dotenv
from pathlib import Path

# Find .env file
root_dir = Path(__file__).parent.parent
dotenv_path = root_dir / '.env'

# Load environment variables
load_dotenv(dotenv_path=dotenv_path)

# Verify the variable is loaded
app_def_id = os.getenv("APP_DEFINITION_ID")
if not app_def_id:
    print("WARNING: APP_DEFINITION_ID is not set!")

from threading import Thread

from benchling_sdk.apps.helpers.webhook_helpers import verify
from flask import Flask, request

from local_app.benchling_app.handler import handle_webhook
from local_app.benchling_app.setup import app_definition_id
from local_app.lib.logger import get_logger

logger = get_logger()


def create_app() -> Flask:
    app = Flask("benchling-app")

    @app.route("/health")
    def health_check() -> tuple[str, int]:
        # Just a route allowing us to check that Flask itself is up and running
        return "OK", 200

    @app.route("/1/webhooks/<path:target>", methods=["POST"])
    def receive_webhooks(target: str) -> tuple[str, int]:  # noqa: ARG001
        # For security, don't do anything else without first verifying the webhook
        app_def_id = app_definition_id()

        # Important! To verify webhooks, we need to pass the body as an unmodified string
        # Flask's request.data is bytes, so decode to string. Passing bytes or JSON won't work
        verify(app_def_id, request.data.decode("utf-8"), request.headers)

        logger.debug("Received webhook message: %s", request.json)
        # Dispatch work and ACK webhook as quickly as possible
        _enqueue_work()
        # ACK webhook by returning 2xx status code so Benchling knows the app received the signal
        return "OK", 200

    return app


def _enqueue_work() -> None:
    # PRODUCTION NOTE: A high volume of webhooks may spawn too many threads and lead to processing failures
    # In production, we recommend a more robust queueing system for scale
    thread = Thread(
        target=handle_webhook,
        args=(request.json,),
    )
    thread.start()

if __name__ == "__main__":
    app = create_app()
    app.run(host='0.0.0.0', port=8000, debug=True)