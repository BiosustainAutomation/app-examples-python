import os
import logging
from threading import Thread
from typing import Any, Dict, Tuple

from flask import Flask, request
from dotenv import load_dotenv
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("simple-benchling-app")

# Constants for Canvas elements
TEXT_INPUT_ID = "text_input"
TRANSFORM_BUTTON_ID = "transform_button"

# Load environment variables
root_dir = Path(__file__).parent.parent
dotenv_path = root_dir / '.env'
load_dotenv(dotenv_path=dotenv_path)

# Import Benchling SDK components
from benchling_sdk.apps.framework import App
from benchling_sdk.apps.canvas.framework import CanvasBuilder
from benchling_sdk.apps.helpers.webhook_helpers import verify
from benchling_sdk.models import (
    AppCanvasUpdate, 
    AppBlock, 
    AppBlockText, 
    AppBlockTextInput, 
    AppBlockButton
)
from benchling_sdk.models.webhooks.v0 import (
    WebhookEnvelopeV0,
    CanvasInitializeWebhookV2,
    CanvasInteractionWebhookV2,
    CanvasCreatedWebhookV2Beta
)

def create_app():
    app = Flask("simple-benchling-app")
    
    @app.route("/health")
    def health_check() -> Tuple[str, int]:
        return "OK", 200
    
    @app.route("/1/webhooks/<path:target>", methods=["POST"])
    def receive_webhooks(target: str) -> Tuple[str, int]:
        app_def_id = os.getenv("APP_DEFINITION_ID")
        if not app_def_id:
            logger.error("APP_DEFINITION_ID environment variable not set")
            return "Missing APP_DEFINITION_ID", 500
            
        # Log the raw webhook for inspection
        logger.info("Received webhook headers: %s", dict(request.headers))
        logger.info("Received webhook body: %s", request.data.decode("utf-8"))
        
        try:
            # Verify the webhook
            verify(app_def_id, request.data.decode("utf-8"), request.headers)
            
            # Log the parsed JSON
            logger.info("Parsed webhook JSON: %s", request.json)
            
            # Start a thread to handle the webhook
            thread = Thread(
                target=handle_webhook,
                args=(request.json,),
            )
            thread.start()
            
            return "OK", 200
        except Exception as e:
            logger.error("Error processing webhook: %s", str(e), exc_info=True)
            return "Error", 500
    
    return app

def handle_webhook(webhook_dict: Dict[str, Any]) -> None:
    try:
        logger.debug("Handling webhook with payload: %s", webhook_dict)
        webhook = WebhookEnvelopeV0.from_dict(webhook_dict)
        
        # Initialize app from webhook
        app = init_app(webhook)
        
        # Route based on webhook type
        if isinstance(webhook.message, CanvasInitializeWebhookV2):
            logger.info("Handling Canvas Initialize webhook")
            render_input_canvas(app, webhook.message)
        elif isinstance(webhook.message, CanvasInteractionWebhookV2):
            logger.info("Handling Canvas Interaction webhook with button ID: %s", 
                       webhook.message.button_id)
            handle_button_interaction(app, webhook.message)
        elif isinstance(webhook.message, CanvasCreatedWebhookV2Beta):
            logger.info("Handling Canvas Created webhook")
            render_input_canvas_for_created(app, webhook.message)
        else:
            logger.warning("Received unsupported webhook type: %s", type(webhook.message))
    except Exception as e:
        logger.error("Error handling webhook: %s", str(e), exc_info=True)

def init_app(webhook: WebhookEnvelopeV0) -> App:
    """Initialize the Benchling App from webhook data"""
    tenant_id = webhook.tenant_id
    app_def_id = os.getenv("APP_DEFINITION_ID")
    
    # Get API credentials from environment
    api_url = os.getenv("BENCHLING_API_URL", "https://benchling.com/api/v2")
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    
    logger.debug(f"Initializing app with tenant_id={tenant_id}, app_def_id={app_def_id}")
    
    # Create App instance
    app = App.from_api_credentials(
        tenant_id=tenant_id,
        app_definition_id=app_def_id,
        client_id=client_id,
        client_secret=client_secret,
        api_url=api_url
    )
    
    return app

def create_input_blocks() -> list[AppBlock]:
    """Create the input blocks for the Canvas"""
    blocks = [
        AppBlockText(text="Enter some text to transform:"),
        AppBlockTextInput(
            id=TEXT_INPUT_ID,
            placeholder="Enter text here..."
        ),
        AppBlockButton(
            id=TRANSFORM_BUTTON_ID,
            text="Transform Text"
        )
    ]
    return blocks

def render_input_canvas(app: App, webhook: CanvasInitializeWebhookV2) -> None:
    """Render the initial Canvas with input fields"""
    canvas_id = webhook.canvas_id
    canvas_update = AppCanvasUpdate(
        enabled=True,
        blocks=create_input_blocks(),
    )
    app.benchling.apps.update_canvas(canvas_id, canvas_update)

def render_input_canvas_for_created(app: App, webhook: CanvasCreatedWebhookV2Beta) -> None:
    """Render the Canvas for newly created Canvas"""
    canvas_id = webhook.canvas_id
    canvas_update = AppCanvasUpdate(
        enabled=True,
        blocks=create_input_blocks(),
    )
    app.benchling.apps.update_canvas(canvas_id, canvas_update)

def handle_button_interaction(app: App, webhook: CanvasInteractionWebhookV2) -> None:
    """Handle button interactions on the Canvas"""
    canvas_id = webhook.canvas_id
    button_id = webhook.button_id
    
    logger.info(f"Handling button interaction with button_id={button_id}")
    
    if button_id == TRANSFORM_BUTTON_ID:
        with app.create_session_context("Transform Text", timeout_seconds=10) as session:
            session.attach_canvas(canvas_id)
            
            # Get the current Canvas
            current_canvas = app.benchling.apps.get_canvas_by_id(canvas_id)
            canvas_builder = CanvasBuilder.from_canvas(current_canvas)
            
            # Get user input
            inputs = canvas_builder.inputs_to_dict_single_value()
            user_text = inputs.get(TEXT_INPUT_ID, "")
            
            logger.info(f"User input: {user_text}")
            
            # Transform the text (uppercase as a simple example)
            transformed_text = transform_text(user_text)
            
            # Create response blocks
            result_blocks = [
                AppBlockText(text="Original Text:"),
                AppBlockText(text=user_text),
                AppBlockText(text="Transformed Text:"),
                AppBlockText(text=transformed_text),
                AppBlockButton(
                    id="reset_button",
                    text="Start Over"
                )
            ]
            
            # Update the Canvas with the results
            canvas_update = canvas_builder.with_enabled()\
                .with_blocks(result_blocks)\
                .to_update()
            app.benchling.apps.update_canvas(canvas_id, canvas_update)
    elif button_id == "reset_button":
        # Reset the Canvas
        canvas_update = AppCanvasUpdate(
            enabled=True,
            blocks=create_input_blocks(),
            session_id=None  # Clear session
        )
        app.benchling.apps.update_canvas(canvas_id, canvas_update)
    else:
        logger.warning(f"Unhandled button ID: {button_id}")
        # Re-enable the Canvas
        app.benchling.apps.update_canvas(canvas_id, AppCanvasUpdate(enabled=True))

def transform_text(text: str) -> str:
    """Apply a simple transformation to the text"""
    # Simple transformation: uppercase + reverse the text
    return text.upper()[::-1]

if __name__ == "__main__":
    app = create_app()
    app.run(host='0.0.0.0', port=8000, debug=True)