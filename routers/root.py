from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from core.dependencies import get_db
from services.saju_orchestrator import get_full_saju_data
from schemas.saju_analysis import SajuAnalysisResponse

router = APIRouter()

@router.get("/", response_model=SajuAnalysisResponse)
def get_calenda_data(
    year: int,
    month: str,
    day: str,
    hour: int,
    min: int,
    sl: str,
    gen: str,
    db: Session = Depends(get_db)
):
    """
    만세력 기본 분석 데이터를 가져옵니다.
    시간은 hour(시), min(분)으로 받고, 양음력(sl)은 sol, lun, lun_y 로 받습니다.
    """
    # 입력 월/일 숫자로 파싱하여 DB 저장 서식과 100% 일치 (예: "05" -> "5")
    try:
        clean_month = str(int(month))
        clean_day = str(int(day))
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="월(month)과 일(day)은 숫자 형식이어야 합니다."
        )

    if sl not in ("sol", "lun", "lun_y"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="sl 파라미터는 'sol', 'lun', 'lun_y' 중 하나이어야 합니다."
        )

    if gen not in ("남", "여"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="gen 파라미터는 '남' 또는 '여' 이어야 합니다."
        )

    result = get_full_saju_data(year, clean_month, clean_day, hour, min, sl, gen, db)
    return result

