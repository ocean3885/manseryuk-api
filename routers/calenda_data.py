from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from dependencies import get_db
from models.calenda_data import CalendaData
from schemas.calenda_data import CalendaDataResponse

router = APIRouter()

@router.get("/calendadata/", response_model=CalendaDataResponse)
def get_calenda_data(year: int, month: str, day: str, sl: str, gen: str, db: Session = Depends(get_db)):
    if sl == "양력":
        birthdata = db.query(CalendaData).filter(
            CalendaData.cd_sy == year,
            CalendaData.cd_sm == month,
            CalendaData.cd_sd == day
        ).all()
    else:
        birthdata = db.query(CalendaData).filter(
            CalendaData.cd_ly == year,
            CalendaData.cd_lm == month,
            CalendaData.cd_ld == day
        ).all()

    if not birthdata:
        raise HTTPException(status_code=404, detail="Data not found")

    if sl == "음력윤달" and len(birthdata) > 1:
        data = birthdata[1]
    else:
        data = birthdata[0]

    return data
