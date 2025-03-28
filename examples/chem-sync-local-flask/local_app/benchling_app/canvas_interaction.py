from typing import cast
import requests
from benchling_sdk.apps.canvas.framework import CanvasBuilder
from benchling_sdk.apps.framework import App
from benchling_sdk.apps.status.errors import AppUserFacingError
from benchling_sdk.models import AppCanvasUpdate
from benchling_sdk.models.webhooks.v0 import CanvasInteractionWebhookV2
from benchling_sdk.models import (
    ButtonUiBlock,
    ButtonUiBlockType,
    MarkdownUiBlock,
    MarkdownUiBlockType,
    TextInputUiBlock,
    TextInputUiBlockType,
    SearchInputUiBlock,
    SearchInputUiBlockType,
    SearchInputUiBlockItemType
)
from benchling_sdk.models import CustomEntity
from benchling_sdk.services.v2.stable.custom_entity_service import CustomEntityService
from benchling_sdk.services.v2.stable.dna_sequence_service import DnaSequenceService
from benchling_sdk.services.v2.stable.registry_service import RegistryService
from benchling_sdk.services.v2.stable.blob_service import BlobService

from local_app.benchling_app.views.constants import (
PROCESS_BUTTON_ID,
TEXT_INPUT_ID
)

from local_app.lib.logger import get_logger
from pathlib import Path

logger = get_logger()


import csv

class UnsupportedButtonError(Exception):
    pass

def route_interaction_webhook(app: App, canvas_interaction: CanvasInteractionWebhookV2) -> None:
    canvas_id = canvas_interaction.canvas_id
    

    if canvas_interaction.button_id == PROCESS_BUTTON_ID:
        with app.create_session_context("Process Text", timeout_seconds=20) as session:
            session.attach_canvas(canvas_id)
            canvas_builder = _canvas_builder_from_canvas_id(app, canvas_id)
            canvas_inputs = canvas_builder.inputs_to_dict_single_value()


            canvas = app.benchling.apps.get_canvas_by_id(canvas_id)


            ent_id = canvas_inputs["input_block_1"]
            cust_serv = CustomEntityService(client=app.benchling._client)

            benchling_csv_ent = cust_serv.get_by_id(ent_id)

            properties = vars(benchling_csv_ent)
            for name, value in properties.items():
                print(f"{name}: {value}")

            blob_serv = BlobService(client = app.benchling._client)
            blob_id = benchling_csv_ent._fields['CSV'].value
            destination_path = Path("downloaded_files/test.csv")
            destination_path.parent.mkdir(parents=True, exist_ok=True)


            blob_csv = blob_serv.download_file(blob_id, destination_path)


            if not canvas_inputs.get(TEXT_INPUT_ID):
                raise AppUserFacingError("Please search for a CSV entity to proceed")
            
            # Process the text
            processed_text = process_text(canvas_inputs[TEXT_INPUT_ID])
            
            # Render results
            render_results_canvas(processed_text, canvas_id, canvas_builder, session)
    else:
        # Re-enable the Canvas, or it will stay disabled and the user will be stuck
        app.benchling.apps.update_canvas(canvas_id, AppCanvasUpdate(enabled=True))
        # Not shown to user by default, for our own logs cause we forgot to handle some button
        raise UnsupportedButtonError(
            f"Whoops, the developer forgot to handle the button {canvas_interaction.button_id}",
        )

def render_results_canvas(results: dict, canvas_id: str, canvas_builder: CanvasBuilder, session) -> None:
    """
    Render the results canvas with the processed text information.
    """
    # Create markdown for results
   
    
    # Create blocks for the results canvas
    results_blocks = [
        MarkdownUiBlock(
            id="results_display",
            type=MarkdownUiBlockType.MARKDOWN,
            value=results_markdown,
        ),
        ButtonUiBlock(
            id="back_button",
            text="Process Another Text",
            type=ButtonUiBlockType.BUTTON,
        ),
    ]
    
    # Update the canvas with the new blocks
    canvas_update = canvas_builder.with_blocks(results_blocks).to_update()
    session.app.benchling.apps.update_canvas(canvas_id, canvas_update)

def _canvas_builder_from_canvas_id(app: App, canvas_id: str) -> CanvasBuilder:
    current_canvas = app.benchling.apps.get_canvas_by_id(canvas_id)
    return CanvasBuilder.from_canvas(current_canvas)
