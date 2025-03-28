# canvas_initialize.py
from benchling_sdk.apps.canvas.framework import CanvasBuilder
from benchling_sdk.apps.canvas.types import UiBlock
from benchling_sdk.apps.framework import App
from benchling_sdk.models import (
    ButtonUiBlock,
    ButtonUiBlockType,
    MarkdownUiBlock,
    MarkdownUiBlockType,
    SearchInputUiBlock,
    SearchInputUiBlockType,
    SearchInputUiBlockItemType,
    TextInputUiBlock,
    TextInputUiBlockType,
)
from local_app.benchling_app.views.constants import (
PROCESS_BUTTON_ID,
TEXT_INPUT_ID
)
from benchling_sdk.models.webhooks.v0 import (
    CanvasCreatedWebhookV2Beta,
    CanvasInitializeWebhookV2,
)


# Constants to use across files


def render_text_canvas(app: App, canvas_initialized: CanvasInitializeWebhookV2) -> None:
    with app.create_session_context("Text Processor App", timeout_seconds=20):
        canvas_builder = CanvasBuilder(
            app_id=app.id,
            feature_id=canvas_initialized.feature_id,
            resource_id=canvas_initialized.resource_id,
        )
        canvas_builder.blocks.append(input_blocks())
        app.benchling.apps.create_canvas(canvas_builder.to_create())


def render_text_canvas_for_created_canvas(app: App, canvas_created: CanvasCreatedWebhookV2Beta) -> None:
    with app.create_session_context("Text Processor App", timeout_seconds=20):
        canvas_builder = CanvasBuilder(app_id=app.id, feature_id=canvas_created.feature_id)
        canvas_builder.blocks.append(input_blocks())
        app.benchling.apps.update_canvas(canvas_created.canvas_id, canvas_builder.to_update())


def input_blocks() -> list[UiBlock]:
    return [
        MarkdownUiBlock(
            id="instructions",
            type=MarkdownUiBlockType.MARKDOWN,
            value="# Text Processing App\nEnter CSV Entity in search box below",
        ),
        SearchInputUiBlock(
            id="input_block_1",
            type=SearchInputUiBlockType.SEARCH_INPUT, 
            item_type=SearchInputUiBlockItemType.CUSTOM_ENTITY,
            value=None,
            schema_id=None,
            enabled=True
        ),
        ButtonUiBlock(
            id=PROCESS_BUTTON_ID,
            text="Process CSV",
            type=ButtonUiBlockType.BUTTON,
        ),
    ]
