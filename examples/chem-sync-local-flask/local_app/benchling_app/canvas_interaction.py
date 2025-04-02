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
        with app.create_session_context("Process Text", timeout_seconds=20) as session:
            
            session.attach_canvas(canvas_id)
            canvas_builder = _canvas_builder_from_canvas_id(app, canvas_id)
            canvas_inputs = canvas_builder.inputs_to_dict_single_value()

            #Pull the entity ID
            canvas = app.benchling.apps.get_canvas_by_id(canvas_id)
            ent_id = canvas_inputs["input_block_1"]
            cust_serv = CustomEntityService(client=app.benchling._client)
            #Get the entity
            benchling_csv_ent = cust_serv.get_by_id(ent_id)

            #blob service to get the CSV from it's ID Via the entity ID
            blob_serv = BlobService(client = app.benchling._client)
            blob_id = benchling_csv_ent._fields['CSV'].value
            destination_path = Path("downloaded_files/test.csv")
            destination_path.parent.mkdir(parents=True, exist_ok=True)

            #Download the csv
            blob_csv = blob_serv.download_file(blob_id, destination_path)

            append_row_to_csv("/home/lajamu/app-examples-python/downloaded_files/test.csv")

            

            blob_service = BlobService(client=app.benchling._client)
            custom_entity_service = CustomEntityService(client=app.benchling._client)
            blob_name = "modified_data.csv"
            file_path = destination_path
            uploaded_blob = blob_service.create_from_file(file_path, name=blob_name, mime_type="text/csv")
            entity_name = "Modified Data Entity"
            folder_id = "lib_dn9tmFzU" # Replace with your folder ID
            schema_id = "ts_WDtkRWgc" 
            entity_fields = fields({
                "CSV": {"value": uploaded_blob.id}  # Assuming 'CSV' is the schema field for the blob link
            })

            new_entity = CustomEntityCreate(
                name=entity_name,
                folder_id=folder_id,
                schema_id=schema_id,
                fields=entity_fields
            )

            created_entity = custom_entity_service.create(new_entity)
            print(f"Created entity: {created_entity.name} with ID: {created_entity.id}")


            # if not canvas_inputs.get(TEXT_INPUT_ID):
            #     raise AppUserFacingError("Please search for a CSV entity to proceed")
            

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
        ),
        ButtonUiBlock(
            id="back_button",
            text="Process Another CSV",
            type=ButtonUiBlockType.BUTTON,
        ),
    ]

    canvas_update = canvas_builder.with_blocks(results_blocks).to_update()
    session.app.benchling.apps.update_canvas(canvas_id, canvas_update)


def _canvas_builder_from_canvas_id(app: App, canvas_id: str) -> CanvasBuilder:
    current_canvas = app.benchling.apps.get_canvas_by_id(canvas_id)
    return CanvasBuilder.from_canvas(current_canvas)

def append_row_to_csv(file_path):
    new_row = ["Row3", "Hello again"]
    with open(file_path, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(new_row)
    print(f"Appended row: {new_row}")
