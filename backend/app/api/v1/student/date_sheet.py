from fastapi import APIRouter

from app.api.deps import SessionDep, SettingsDep, StudentDep
from app.schemas.planner import DateSheetOut, DateSheetSave, PlannerOut
from app.services import date_sheet_service

router = APIRouter(tags=["student"])


@router.get("/planner", response_model=PlannerOut)
def read_planner(student: StudentDep, db: SessionDep, settings: SettingsDep) -> PlannerOut:
    return PlannerOut(**date_sheet_service.read_planner(db, settings, student))


@router.put("/date-sheet", response_model=DateSheetOut)
def save_date_sheet(
    body: DateSheetSave, student: StudentDep, db: SessionDep, settings: SettingsDep
) -> DateSheetOut:
    return DateSheetOut(
        **date_sheet_service.save_date_sheet(db, settings, student.id, body)
    )


@router.get("/date-sheet", response_model=DateSheetOut)
def read_date_sheet(student: StudentDep, db: SessionDep, settings: SettingsDep) -> DateSheetOut:
    return DateSheetOut(**date_sheet_service.read_date_sheet(db, settings, student.id))
