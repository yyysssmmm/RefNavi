# backend/main.py

from api.metadata_endpoint import router as metadata_router

app.include_router(metadata_router, prefix="/metadata")
