from benchling_sdk.apps.canvas.framework import CanvasBuilder
from benchling_sdk.apps.canvas.types import UiBlock
from benchling_sdk.apps.framework import App
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
from benchling_sdk.models.webhooks.v0 import (
    CanvasCreatedWebhookV2Beta,
    CanvasInitializeWebhookV2,
)

from local_app.benchling_app.views.constants import SEARCH_BUTTON_ID, SEARCH_TEXT_ID


def render_search_canvas(app: App, canvas_initialized: CanvasInitializeWebhookV2) -> None:
    with app.create_session_context("Show Sync Search", timeout_seconds=20):
        canvas_builder = CanvasBuilder(
            app_id=app.id,
            feature_id=canvas_initialized.feature_id,
            resource_id=canvas_initialized.resource_id,
        )
        canvas_builder.blocks.append(input_blocks())
        app.benchling.apps.create_canvas(canvas_builder.to_create())


def render_search_canvas_for_created_canvas(app: App, canvas_created: CanvasCreatedWebhookV2Beta) -> None:
    with app.create_session_context("Show Sync Search", timeout_seconds=20):
        canvas_builder = CanvasBuilder(app_id=app.id, feature_id=canvas_created.feature_id)
        canvas_builder.blocks.append(input_blocks())
        app.benchling.apps.update_canvas(canvas_created.canvas_id, canvas_builder.to_update())


def input_blocks() -> list[UiBlock]:
    return [
        MarkdownUiBlock(
            id="top_instructions",
            type=MarkdownUiBlockType.MARKDOWN,
            value="Test Canvas Entity Search",
        ),
        SearchInputUiBlock(
            id="input_block_1",
            type=SearchInputUiBlockType.SEARCH_INPUT,  # Use the enum instead of a string
            item_type=SearchInputUiBlockItemType.DNA_SEQUENCE,
            value=None,
            schema_id=None,
            enabled=True
        ),
        ButtonUiBlock(
            id=SEARCH_BUTTON_ID,
            text="Search entities",
            type=ButtonUiBlockType.BUTTON,
        ),
    ]
