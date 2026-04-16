from fastapi import HTTPException
from sqlalchemy.orm import Session
from models.calenda_data import CalendaData
from services.daewoon import getDaewoon, daewoonNum, get_time_gan, gankr_to_ch, jikr_to_ch
from services.calculator import descending_tens, find_ten_god, find_stem_branch_ten_god, generate_future_cycles, generate_baby_cycles, determine_zodiac_hour_str
from services.analysis import analyze_palja_integrated

def get_full_saju_data(year: int, month: str, day: str, hour: int, min: int, sl: str, gen: str, db: Session):
    # sl 매핑 (sol -> 양력, lun -> 음력, lun_y -> 음력윤달)
    if sl == "sol":
        calendar_type_str = "양력"
    elif sl == "lun":
        calendar_type_str = "음력"
    elif sl == "lun_y":
        calendar_type_str = "음력윤달"
    else:
        raise HTTPException(status_code=400, detail="Invalid sl value. Use 'sol', 'lun', or 'lun_y'")

    if calendar_type_str == "양력":
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

    if calendar_type_str == "음력윤달" and len(birthdata) > 1:
        data = birthdata[1]
    else:
        data = birthdata[0]

    # ── 날짜 및 4주 기본값 추출 ──
    year_gan_kr  = data.cd_kyganjee[0]
    year_ji_kr   = data.cd_kyganjee[1]
    month_gan_kr = data.cd_kmganjee[0]
    month_ji_kr  = data.cd_kmganjee[1]
    day_gan_kr   = data.cd_kdganjee[0]
    day_ji_kr    = data.cd_kdganjee[1]

    # ── 시간 간지 변환 ──
    time_zodiac = determine_zodiac_hour_str(str(hour), str(min))
    if len(time_zodiac) > 1:  # 에러 문자열이면 기본값 자(子)시 처리
        time_zodiac = "자"

    time_ji_kr  = time_zodiac
    time_gan_kr = get_time_gan(day_gan_kr, time_ji_kr)
    time_gan_ch = gankr_to_ch(time_gan_kr)
    time_ji_ch  = jikr_to_ch(time_ji_kr)

    stems = [data.cd_hyganjee[0], data.cd_hmganjee[0], data.cd_hdganjee[0], time_gan_ch]
    branches = [data.cd_hyganjee[1], data.cd_hmganjee[1], data.cd_hdganjee[1], time_ji_ch]
    analysis_result = analyze_palja_integrated(stems, branches)

    # ── 대운 계산 ──
    daewoon         = getDaewoon(gen, year_gan_kr, month_gan_kr, month_ji_kr)
    daewoon_num     = daewoonNum(year, month, day, calendar_type_str, daewoon[0], db)
    daewoon_num_list = descending_tens(daewoon_num)

    # ── 최종 결과 (도메인별 그룹화) ──
    return {
        # 1. 달력 정보
        "calendar": {
            "solar":       { "year": data.cd_sy, "month": data.cd_sm, "day": data.cd_sd },
            "lunar":       { "year": data.cd_ly, "month": data.cd_lm, "day": data.cd_ld },
            "solar_plan":  data.cd_sol_plan,
            "lunar_plan":  data.cd_lun_plan,
        },

        # 2. 사주 4주 (년주 / 월주 / 일주 / 시주)
        "four_pillars": {
            "year":  { "gan": {"kr": year_gan_kr,  "ch": data.cd_hyganjee[0]}, "ji": {"kr": year_ji_kr,  "ch": data.cd_hyganjee[1]} },
            "month": { "gan": {"kr": month_gan_kr, "ch": data.cd_hmganjee[0]}, "ji": {"kr": month_ji_kr, "ch": data.cd_hmganjee[1]} },
            "day":   { "gan": {"kr": day_gan_kr,   "ch": data.cd_hdganjee[0]}, "ji": {"kr": day_ji_kr,   "ch": data.cd_hdganjee[1]} },
            "time":  { "gan": {"kr": time_gan_kr,  "ch": time_gan_ch},          "ji": {"kr": time_ji_kr,  "ch": time_ji_ch} },
        },

        # 3. 십신
        "ten_gods": {
            "year_gan":  find_ten_god(day_gan_kr, year_gan_kr),
            "year_ji":   find_stem_branch_ten_god(day_gan_kr, year_ji_kr),
            "month_gan": find_ten_god(day_gan_kr, month_gan_kr),
            "month_ji":  find_stem_branch_ten_god(day_gan_kr, month_ji_kr),
            "day_ji":    find_stem_branch_ten_god(day_gan_kr, day_ji_kr),
            "time_gan":  find_ten_god(day_gan_kr, time_gan_kr),
            "time_ji":   find_stem_branch_ten_god(day_gan_kr, time_ji_kr),
        },

        # 4. 대운
        "daewoon": {
            "direction": daewoon,
            "start_age": daewoon_num,
            "age_list":  daewoon_num_list,
        },

        # 5. 분석 결과 (신규 추가!) --------------------------------------
        "analysis": {
            "summary": analysis_result['summary'], # 합충 관계 등 요약
            "details": analysis_result['pillars']  # 각 기둥별 통근, 점수, 허실, 12운성
        },

        # 6. 운세 사이클
        "cycles": {
            "future_100": generate_future_cycles(data.cd_sy, daewoon_num),
            "baby_10":    generate_baby_cycles(data.cd_sy),
        },

        # 7. 기타 메타
        "meta": {
            "gender": gen,
            "ddi":    data.cd_ddi,
        },
    }
