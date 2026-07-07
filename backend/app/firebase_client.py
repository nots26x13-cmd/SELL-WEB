"""
Firebase Admin SDK bootstrap. The service account JSON is read from a local
file path (FIREBASE_CREDENTIALS_PATH) - it is never hardcoded in source and
never sent to the frontend. Only the backend holds this credential.
"""
import firebase_admin
from firebase_admin import credentials, firestore

from .config import settings

_app = None
_db = None


def init_firebase():
    global _app, _db
    if _app is not None:
        return _app

    cred = credentials.Certificate(settings.firebase_credentials_path)
    _app = firebase_admin.initialize_app(
        cred,
        {"databaseURL": settings.firebase_database_url} if settings.firebase_database_url else None,
    )
    _db = firestore.client()
    return _app


def get_db():
    if _db is None:
        init_firebase()
    return _db
