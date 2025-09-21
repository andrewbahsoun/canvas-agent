#!/usr/bin/env python3
import os
from .google_drive_client import GoogleDriveClient

from dotenv import load_dotenv
load_dotenv()

def send_to_google_drive(content: str, title: str):
    token = os.getenv("DRIVE_API_KEY")

    client = GoogleDriveClient(access_token=token)

    doc = client.create_document(title)
    client.update_document_content(doc["id"], content)
    return doc["id"]

def read_from_google_drive():
    pass

