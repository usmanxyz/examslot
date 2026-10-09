import uuid
from typing import Annotated

from fastapi import APIRouter, Query, Response, status

from app.api.deps import SessionDep, SettingsDep
from app.schemas.common import Page
from app.schemas.slot import SlotCreate, SlotDetailOut, SlotListQuery, SlotOut, SlotUpdate
from app.services import slot_service

router = APIRouter(prefix="/slots", tags=["admin"])


@router.get("", response_model=Page[SlotOut])
def list_slots(
    query: Annotated[SlotListQuery, Query()], db: SessionDep, settings: SettingsDep
) -> Page[SlotOut]:
    return Page[SlotOut](**slot_service.list_slots(db, settings, query))


@router.post("", response_model=SlotDetailOut, status_code=status.HTTP_201_CREATED)
def create_slot(body: SlotCreate, db: SessionDep, settings: SettingsDep) -> SlotDetailOut:
    return SlotDetailOut(**slot_service.create_slot(db, settings, body))


@router.get("/{slot_id}", response_model=SlotDetailOut)
def read_slot(slot_id: uuid.UUID, db: SessionDep, settings: SettingsDep) -> SlotDetailOut:
    return SlotDetailOut(**slot_service.read_slot(db, settings, slot_id))


@router.patch("/{slot_id}", response_model=SlotDetailOut)
def update_slot(
    slot_id: uuid.UUID, body: SlotUpdate, db: SessionDep, settings: SettingsDep
) -> SlotDetailOut:
    return SlotDetailOut(**slot_service.update_slot(db, settings, slot_id, body))


@router.delete("/{slot_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_slot(slot_id: uuid.UUID, db: SessionDep) -> Response:
    slot_service.delete_slot(db, slot_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
