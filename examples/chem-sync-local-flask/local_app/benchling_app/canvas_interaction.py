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
from benchling_sdk.models import CustomEntityCreate, BlobCreate
from benchling_sdk.helpers.serialization_helpers import fields

from local_app.benchling_app.csv_utils import download_csv, upload_csv, process_csv
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
    
    #When the button is pressed, do this here:
    if canvas_interaction.button_id == PROCESS_BUTTON_ID:
        with app.create_session_context("Process CSV", timeout_seconds=20) as session:
            
            session.attach_canvas(canvas_id)
            canvas_builder = _canvas_builder_from_canvas_id(app, canvas_id)
            canvas_inputs = canvas_builder.inputs_to_dict_single_value()

            #Pull the entity ID
            canvas = app.benchling.apps.get_canvas_by_id(canvas_id)
            ent_id = canvas_inputs["input_block_1"]

            destination_path = Path("downloaded_files/downloaded_csv.csv")

            download_csv(app=app, entit_id=ent_id, destination_path = destination_path)


            #This is the function to modify the CSV
            process_csv(destination_path)
            folder_id = "lib_dn9tmFzU"


            created_entity = upload_csv(app = app, 
            path = destination_path, 
            new_filename = "ModifiedCSV.csv", 
            new_entity_name = "Modified CSV",
            folder_id = folder_id)

            destination_path.unlink()

            # Render results
            render_results_canvas(f"Successfully created entity: [{created_entity.name}]({created_entity.web_url})", canvas_id, canvas_builder, session)

    else:
        # Re-enable the Canvas, or it will stay disabled and the user will be stuck
        app.benchling.apps.update_canvas(canvas_id, AppCanvasUpdate(enabled=True))
        # Not shown to user by default, for our own logs cause we forgot to handle some button
        raise UnsupportedButtonError(
            f"Whoops, the developer forgot to handle the button {canvas_interaction.button_id}",
        )

def render_results_canvas(results_markdown: str, canvas_id: str, canvas_builder: CanvasBuilder, session) -> None:
    """
    Render the results canvas with the processed text information.
    """
    results_blocks = [
        MarkdownUiBlock(
            id="results_display",
            type=MarkdownUiBlockType.MARKDOWN,
            value=results_markdown,
        )
    ]

    canvas_update = canvas_builder.with_blocks(results_blocks).to_update()
    session.app.benchling.apps.update_canvas(canvas_id, canvas_update)


def _canvas_builder_from_canvas_id(app: App, canvas_id: str) -> CanvasBuilder:
    current_canvas = app.benchling.apps.get_canvas_by_id(canvas_id)
    return CanvasBuilder.from_canvas(current_canvas)


