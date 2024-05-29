from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from dependencies import get_db
from models.calenda_data import CalendaData
from daewoon import *
from calculator import *

router = APIRouter()

@router.get("/calendadata/")
def get_calenda_data(year: int, month: str, day: str, time: str, sl: str, gen: str, db: Session = Depends(get_db)):
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
            "year_gan_ch": data.cd_hyganjee[0],
            "year_ji_ch": data.cd_hyganjee[1],
            "year_gan_kr": data.cd_kyganjee[0],
            "year_ji_kr": data.cd_kyganjee[1],
            "month_gan_ch": data.cd_hmganjee[0],
            "month_ji_ch": data.cd_hmganjee[1],
            "month_gan_kr": data.cd_kmganjee[0],
            "month_ji_kr": data.cd_kmganjee[1],
            "day_gan_ch": data.cd_hdganjee[0],
            "day_ji_ch": data.cd_hdganjee[1],
            "day_gan_kr": data.cd_kdganjee[0],
            "day_ji_kr": data.cd_kdganjee[1],
            "ddi_kor": data.cd_ddi,
            "sol_plan": data.cd_sol_plan,
            "lunar_plan": data.cd_lun_plan,
    }
    outdata["time_ji_kr"] = time
    outdata["time_gan_kr"] = get_time_gan(
        outdata["day_gan_kr"], outdata["time_ji_kr"]
    )
    outdata["time_gan_ch"] = gankr_to_ch(outdata["time_gan_kr"])
    outdata["time_ji_ch"] = jikr_to_ch(outdata["time_ji_kr"])
    outdata["gender"] = gen
    outdata["daewoon"] = getDaewoon(
        outdata["gender"], outdata["year_gan_kr"],
        outdata["month_gan_kr"], outdata["month_ji_kr"]
    )
    outdata["daewoon_num"] = daewoonNum(
        year, month, day, sl, outdata["daewoon"][0], db
    )
    outdata["daewoon_num_list"] = descending_tens(outdata["daewoon_num"])
    outdata["time_gan10"] = find_ten_god(outdata["day_gan_kr"],outdata["time_gan_kr"])
    outdata["month_gan10"] = find_ten_god(outdata["day_gan_kr"],outdata["month_gan_kr"])
    outdata["year_gan10"] = find_ten_god(outdata["day_gan_kr"],outdata["year_gan_kr"])
    outdata["time_ji10"] = find_stem_branch_ten_god(outdata["day_gan_kr"],outdata["time_ji_kr"])
    outdata["day_ji10"] = find_stem_branch_ten_god(outdata["day_gan_kr"],outdata["day_ji_kr"])
    outdata["month_ji10"] = find_stem_branch_ten_god(outdata["day_gan_kr"],outdata["month_ji_kr"])
    outdata["year_ji10"] = find_stem_branch_ten_god(outdata["day_gan_kr"],outdata["year_ji_kr"])    
    outdata["cycles_100"] = generate_future_cycles(outdata["s_year"],outdata["daewoon_num"])
    outdata["baby_10"] = generate_baby_cycles(outdata["s_year"])
    
    return outdata
