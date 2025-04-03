from benchling_sdk.apps.framework import App
from pathlib import Path
from benchling_sdk.models import CustomEntity
from benchling_sdk.services.v2.stable.custom_entity_service import CustomEntityService
from benchling_sdk.services.v2.stable.dna_sequence_service import DnaSequenceService
from benchling_sdk.services.v2.stable.registry_service import RegistryService
from benchling_sdk.services.v2.stable.blob_service import BlobService
from benchling_sdk.models import CustomEntityCreate, BlobCreate
from benchling_sdk.helpers.serialization_helpers import fields
import csv

def download_csv(app: App, entit_id: str, destination_path: Path) -> None:
    #Create a new custom entity service
    cust_serv = CustomEntityService(client=app.benchling._client)
    #Get the entity proper through the custom entity service
    benchling_csv_ent = cust_serv.get_by_id(entit_id)

    #blob service to get the CSV from it's ID Via the entity ID
    existing_blob_serv = BlobService(client = app.benchling._client)

    #get the blob ID
    blob_id = benchling_csv_ent._fields['CSV'].value

    destination_path.parent.mkdir(parents=True, exist_ok=True)

    #Download the csv
    blob_csv = existing_blob_serv.download_file(blob_id, destination_path)
    print("File dowloaded to " + str(destination_path))

def upload_csv(app: App, path:Path, new_filename: str, new_entity_name:str, folder_id: str, schema_id = "ts_WDtkRWgc") -> CustomEntity:
    #Make a new blob and customentity service
    new_blob_service = BlobService(client=app.benchling._client)
    custom_entity_service = CustomEntityService(client=app.benchling._client)
    uploaded_blob = new_blob_service.create_from_file(path, name=new_filename, mime_type="text/csv")

        # Replace with your folder ID
    schema_id = "ts_WDtkRWgc" 
    entity_fields = fields({
        "CSV": {"value": uploaded_blob.id}  # Assuming 'CSV' is the schema field for the blob link
    })

    new_entity = CustomEntityCreate(
        name=new_entity_name,
        folder_id=folder_id,
        schema_id=schema_id,
        fields=entity_fields
    )

    created_entity = custom_entity_service.create(new_entity)
    print(f"Created entity: {created_entity.name} with ID: {created_entity.id}")
    return(created_entity)
def process_csv(file_path):
    new_row = ["Row3", "Hello again"]
    with open(file_path, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(new_row)
    print(f"Appended row: {new_row}")

def delete_csvs(file_path):
    os.remove(file_path)
