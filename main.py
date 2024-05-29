# main.py
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal, CalendaData

app = FastAPI()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/calendadata/")
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

    outdata = {
        "s_year": data.cd_sy,
        "s_month": data.cd_sm,
        "s_day": data.cd_sd,
        "l_year": data.cd_ly,
        "l_month": data.cd_lm,
        "l_day": data.cd_ld,
        "hyganjee": data.cd_hyganjee,
        "kyganjee": data.cd_kyganjee,
        "hmganjee": data.cd_hmganjee,
        "kmganjee": data.cd_kmganjee,
        "hdganjee": data.cd_hdganjee,
        "kdganjee": data.cd_kdganjee,
        "hweek": data.cd_hweek,
        "kweek": data.cd_kweek,
        "stars": data.cd_stars,
        "moon_state": data.cd_moon_state,
        "moon_time": data.cd_moon_time,
        "leap_month": data.cd_leap_month,
        "month_size": data.cd_month_size,
        "hterms": data.cd_hterms,
        "kterms": data.cd_kterms,
        "terms_time": data.cd_terms_time,
        "keventday": data.cd_keventday,
        "ddi": data.cd_ddi,
        "sol_plan": data.cd_sol_plan,
        "lun_plan": data.cd_lun_plan,
        "holiday": data.holiday
    }

    return outdata
