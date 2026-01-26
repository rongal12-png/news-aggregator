from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Source
from app.schemas import SourceResponse, SourceCreate

router = APIRouter()


@router.get("", response_model=list[SourceResponse])
def list_sources(db: Session = Depends(get_db)):
    sources = db.query(Source).filter(Source.is_active == True).all()
    return sources


@router.post("", response_model=SourceResponse, status_code=201)
def create_source(source: SourceCreate, db: Session = Depends(get_db)):
    # Check if source already exists
    existing = db.query(Source).filter(Source.feed_url == source.feed_url).first()
    if existing:
        raise HTTPException(status_code=400, detail="Source with this feed URL already exists")

    db_source = Source(**source.model_dump())
    db.add(db_source)
    db.commit()
    db.refresh(db_source)
    return db_source


@router.delete("/{source_id}", status_code=204)
def delete_source(source_id: int, db: Session = Depends(get_db)):
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    db.delete(source)
    db.commit()
