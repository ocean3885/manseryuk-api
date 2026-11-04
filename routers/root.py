from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.dependencies import get_db
from services.saju_orchestrator import get_full_saju_data
from services.character_relation_index import assemble_character_relation_index_from_response
from schemas.character_relation_index import CharacterRelationIndex
from schemas.saju_analysis import SajuAnalysisResponse
from schemas.character_details import CharacterDetails
from services.character_details import assemble_character_details
from schemas.cycle_analysis import CycleAnalysis
from services.cycle_analysis import assemble_cycle_analysis
from core.api_errors import selection_error
from schemas.api_error import ApiErrorResponse
from schemas.analysis_summary import AnalysisSummary
from services.analysis_summary import assemble_analysis_summary

router = APIRouter(responses={code: {'model': ApiErrorResponse} for code in (400, 404, 422, 500)})


@router.get('/analysis-summary', response_model=AnalysisSummary)
def get_analysis_summary(
    year: int, month: str, day: str, hour: int, min: int, sl: str, gen: str,
    daewoon_index: int | None = None, sewoon_year: int | None = None,
    db: Session = Depends(get_db),
):
    """원국 구조 또는 선택한 운의 추가 관계를 근거에 연결해 요약한다."""
    if daewoon_index is not None and sewoon_year is not None:
        raise selection_error()
    response = get_calenda_data(year, month, day, hour, min, sl, gen, db)
    return assemble_analysis_summary(response, daewoon_index=daewoon_index, sewoon_year=sewoon_year)


@router.get('/cycle-analysis', response_model=CycleAnalysis)
def get_cycle_analysis(
    year: int, month: str, day: str, hour: int, min: int, sl: str, gen: str,
    daewoon_index: int | None = None, sewoon_year: int | None = None,
    db: Session = Depends(get_db),
):
    """선택한 운의 글자와 소속 간 관계 후보를 조회한다. 통근 영향은 미평가다."""
    if (daewoon_index is None) == (sewoon_year is None):
        raise selection_error()
    response = get_calenda_data(year, month, day, hour, min, sl, gen, db)
    return assemble_cycle_analysis(response, daewoon_index=daewoon_index, sewoon_year=sewoon_year)


@router.get('/character-details', response_model=CharacterDetails)
def get_character_details(
    year: int, month: str, day: str, hour: int, min: int, sl: str, gen: str,
    db: Session = Depends(get_db),
):
    """원국 글자별 속성·통근·투간·관계를 소속이 있는 공통 구조로 조회한다."""
    return assemble_character_details(get_calenda_data(year, month, day, hour, min, sl, gen, db))

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
    return get_full_saju_data(year, month, day, hour, min, sl, gen, db)


@router.get('/relation-index', response_model=CharacterRelationIndex)
def get_relation_index(
    year: int,
    month: str,
    day: str,
    hour: int,
    min: int,
    sl: str,
    gen: str,
    db: Session = Depends(get_db),
):
    """기존 원국 분석에서 관계 사실만 조회한다."""
    response = get_calenda_data(year, month, day, hour, min, sl, gen, db)
    return assemble_character_relation_index_from_response(response)

