from fastapi import HTTPException
from sqlalchemy.orm import Session
from datetime import date
from models.calenda_data import CalendaData
from services.daewoon import getDaewoon, daewoonNum, get_time_gan, gankr_to_ch, jikr_to_ch, build_daewoon
from services.calculator import (
    descending_tens, find_ten_god, find_stem_branch_ten_god, 
    generate_future_cycles, generate_baby_cycles, determine_zodiac_hour_str,
    get_stem_detail, get_branch_detail, get_jijanggan_details
)
from services.constants import UNSEONG_DATA
from services.analysis import analyze_palja_integrated, analyze_advanced_tonggeun
from services.interaction_matrix import build_interaction_matrix
from services.xu_shi import analyze_xu_shi_dynamics
from services.bin_zhu import analyze_bin_zhu_dynamics
from services.five_elements import analyze_five_elements
from services.special_stars import analyze_special_stars


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

    year_gan_ch  = data.cd_hyganjee[0]
    year_ji_ch   = data.cd_hyganjee[1]
    month_gan_ch = data.cd_hmganjee[0]
    month_ji_ch  = data.cd_hmganjee[1]
    day_gan_ch   = data.cd_hdganjee[0]
    day_ji_ch    = data.cd_hdganjee[1]

    # ── 시간 간지 변환 ──
    time_zodiac = determine_zodiac_hour_str(str(hour), str(min))
    if len(time_zodiac) > 1:  # 에러 문자열이면 기본값 자(子)시 처리
        time_zodiac = "자"

    time_ji_kr  = time_zodiac
    time_gan_kr = get_time_gan(day_gan_kr, time_ji_kr)
    time_gan_ch = gankr_to_ch(time_gan_kr)
    time_ji_ch  = jikr_to_ch(time_ji_kr)

    stems = [year_gan_ch, month_gan_ch, day_gan_ch, time_gan_ch]
    branches = [year_ji_ch, month_ji_ch, day_ji_ch, time_ji_ch]
    day_stem_ch = day_gan_ch

    analysis_result = analyze_palja_integrated(stems, branches)

    # ── 고급 명리학 AI 분석 (오행, 신살, 합충형해파, 허실, 빈주) ──
    tonggeun_results = analyze_advanced_tonggeun(stems, branches)
    five_elements_data = analyze_five_elements(stems, branches, tonggeun_results)
    special_stars_data = analyze_special_stars(stems, branches)
    interaction_data = build_interaction_matrix(stems, branches, day_stem_ch)
    xu_shi_data = analyze_xu_shi_dynamics(stems, branches, day_stem_ch, tonggeun_results, interaction_data['matrix'])
    bin_zhu_data = analyze_bin_zhu_dynamics(stems, branches, day_stem_ch, interaction_data['matrix'])

    # 신살 기둥별 맵핑
    special_stars_by_pillar = {
        "year": [st["name"] for st in special_stars_data if st["pillar"] == "year"],
        "month": [st["name"] for st in special_stars_data if st["pillar"] == "month"],
        "day": [st["name"] for st in special_stars_data if st["pillar"] == "day"],
        "hour": [st["name"] for st in special_stars_data if st["pillar"] == "hour"],
    }

    # AI 상담 프롬프트 전용 핵심 가이드 생성
    ai_consultation_prompts = []
    ai_consultation_prompts.append(f"【오행 분포】 {five_elements_data['summary']}")
    if special_stars_data:
        stars_summary = ", ".join([f"{st['name']}({st['position']})" for st in special_stars_data[:3]])
        ai_consultation_prompts.append(f"【주요 신살 및 길신】 {stars_summary}")
    ai_consultation_prompts.append(f"【사주 기후】 {interaction_data['climate']} (긴장도: {interaction_data['tension_score']}, 조화도: {interaction_data['harmony_score']})")
    ai_consultation_prompts.append(f"【허실 변화】 {xu_shi_data['overall_status']}")
    ai_consultation_prompts.extend(bin_zhu_data['ai_prompt_bullets'])
    for sm in interaction_data['summary_list'][:3]:
        ai_consultation_prompts.append(f"【주요 상호작용】 {sm}")

    # ── 대운 계산 ──
    daewoon         = getDaewoon(gen, year_gan_kr, month_gan_kr, month_ji_kr)
    daewoon_num     = daewoonNum(data.cd_no, daewoon[0], db)
    daewoon_result = build_daewoon(
        direction_data=daewoon,
        start_age=daewoon_num,
        birth_year=data.cd_sy,
        day_stem=day_stem_ch
    )

    # ── 메타 사용자 정보 계산 ──
    today = date.today()
    birth_solar_date = date(data.cd_sy, int(data.cd_sm), int(data.cd_sd))
    age_man = today.year - birth_solar_date.year - (
        (today.month, today.day) < (birth_solar_date.month, birth_solar_date.day)
    )
    age_korean = today.year - birth_solar_date.year + 1
    weekday_names = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
    birth_weekday = weekday_names[birth_solar_date.weekday()]

    # ── 프론트엔드 최적화 완성형 기둥 구성 ──
    four_pillars_data = {
        "year": {
            "gan": get_stem_detail(day_stem_ch, year_gan_ch, is_day_gan=False),
            "ji": get_branch_detail(day_stem_ch, year_ji_ch),
            "unseong": UNSEONG_DATA.get(day_stem_ch, {}).get(year_ji_ch, ""),
            "unseong_self": UNSEONG_DATA.get(year_gan_ch, {}).get(year_ji_ch, ""),
            "jijanggan": get_jijanggan_details(day_stem_ch, year_ji_ch),
            "special_stars": special_stars_by_pillar["year"]
        },
        "month": {
            "gan": get_stem_detail(day_stem_ch, month_gan_ch, is_day_gan=False),
            "ji": get_branch_detail(day_stem_ch, month_ji_ch),
            "unseong": UNSEONG_DATA.get(day_stem_ch, {}).get(month_ji_ch, ""),
            "unseong_self": UNSEONG_DATA.get(month_gan_ch, {}).get(month_ji_ch, ""),
            "jijanggan": get_jijanggan_details(day_stem_ch, month_ji_ch),
            "special_stars": special_stars_by_pillar["month"]
        },
        "day": {
            "gan": get_stem_detail(day_stem_ch, day_gan_ch, is_day_gan=True),
            "ji": get_branch_detail(day_stem_ch, day_ji_ch),
            "unseong": UNSEONG_DATA.get(day_stem_ch, {}).get(day_ji_ch, ""),
            "unseong_self": UNSEONG_DATA.get(day_gan_ch, {}).get(day_ji_ch, ""),
            "jijanggan": get_jijanggan_details(day_stem_ch, day_ji_ch),
            "special_stars": special_stars_by_pillar["day"]
        },
        "hour": {
            "gan": get_stem_detail(day_stem_ch, time_gan_ch, is_day_gan=False),
            "ji": get_branch_detail(day_stem_ch, time_ji_ch),
            "unseong": UNSEONG_DATA.get(day_stem_ch, {}).get(time_ji_ch, ""),
            "unseong_self": UNSEONG_DATA.get(time_gan_ch, {}).get(time_ji_ch, ""),
            "jijanggan": get_jijanggan_details(day_stem_ch, time_ji_ch),
            "special_stars": special_stars_by_pillar["hour"]
        },
    }

    # ── 최종 결과 (도메인별 그룹화) ──
    return {
        # 1. 달력 정보
        "calendar": {
            "solar":       { "year": data.cd_sy, "month": data.cd_sm, "day": data.cd_sd },
            "lunar":       { "year": data.cd_ly, "month": data.cd_lm, "day": data.cd_ld },
            "solar_plan":  data.cd_sol_plan,
            "lunar_plan":  data.cd_lun_plan,
        },

        # 2. 사주 4주 완성형 원국
        "four_pillars": four_pillars_data,

        # 3. 십신 (기존 호환성 유지)
        "ten_gods": {
            "year_gan":  four_pillars_data["year"]["gan"]["ten_god"],
            "year_ji":   four_pillars_data["year"]["ji"]["ten_god"],
            "month_gan": four_pillars_data["month"]["gan"]["ten_god"],
            "month_ji":  four_pillars_data["month"]["ji"]["ten_god"],
            "day_gan":   "일간",
            "day_ji":    four_pillars_data["day"]["ji"]["ten_god"],
            "time_gan":  four_pillars_data["hour"]["gan"]["ten_god"],
            "time_ji":   four_pillars_data["hour"]["ji"]["ten_god"],
        },

        # 4. 대운
        "daewoon": daewoon_result,

        # 5. 분석 결과
        "analysis": {
            "summary": analysis_result['summary'],
            "details": analysis_result['pillars']
        },

        # 6. 고급 명리학 AI 상담 분석
        "advanced_analysis": {
            "five_elements": five_elements_data,
            "special_stars": special_stars_data,
            "special_stars_by_pillar": special_stars_by_pillar,
            "interactions": interaction_data,
            "xu_shi_dynamics": xu_shi_data,
            "bin_zhu_dynamics": bin_zhu_data,
            "ai_consultation_prompts": ai_consultation_prompts
        },

        # 7. 운세 사이클
        "cycles": {
            "future_100": generate_future_cycles(data.cd_sy, daewoon_num, day_stem_ch),
            "baby_10":    generate_baby_cycles(data.cd_sy, day_stem_ch),
        },

        # 8. 기타 메타
        "meta": {
            "gender": gen,
            "ddi": data.cd_ddi,
            "birth_date_solar": f"{data.cd_sy:04d}-{int(data.cd_sm):02d}-{int(data.cd_sd):02d}",
            "birth_time": f"{hour:02d}:{min:02d}",
            "age_man": age_man,
            "age_korean": age_korean,
            "birth_weekday": birth_weekday,
        },
    }


