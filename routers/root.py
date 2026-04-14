from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.dependencies import get_db
from services.saju_orchestrator import get_full_saju_data
from schemas.calenda_data import SajuAnalysisResponse

router = APIRouter()

@router.get("/", response_model=SajuAnalysisResponse)
def get_calenda_data(year: int, month: str, day: str, hour: int, min: int, sl: str, gen: str, db: Session = Depends(get_db)):
    """
    만세력 기본 분석 데이터를 가져옵니다.
    시간은 hour(시), min(분)으로 받고, 양음력(sl)은 sol, lun, lun_y 로 받습니다.
    로직은 services/saju_orchestrator.py 에 분리되어 있습니다.
    """
    result = get_full_saju_data(year, month, day, hour, min, sl, gen, db)
    return result
