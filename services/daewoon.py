from services.calculator import gan_to_hanja, ji_to_hanja
from fastapi import Depends
from sqlalchemy.orm import Session
from models.calenda_data import CalendaData
from core.dependencies import get_db
from datetime import date


def getDaewoon(gen, ygan, mgan, mji):
    YANGGAN = ["갑", "병", "무", "경", "임"]
    EUMGAN = ["을", "정", "기", "신", "계"]
    CHEONGAN = ["갑", "을", "병", "정", "무", "기", "경", "신", "임", "계"]
    JIJI = ["자", "축", "인", "묘", "진", "사", "오", "미", "신", "유", "술", "해"]

    if (gen == "남" and ygan in YANGGAN) or (gen == "여" and ygan in EUMGAN):
        data = ["순행"]
        data_gan = []
        data_ji = []
        for i in range(len(CHEONGAN)):
            if CHEONGAN[i] == mgan:
                start = i + 1
        for i in range(10):
            data_gan.append(CHEONGAN[start % 10])
            start += 1

        for i in range(len(JIJI)):
            if JIJI[i] == mji:
                start = i + 1

        for i in range(10):
            data_ji.append(JIJI[start % 12])
            start += 1

        data_gan = gan_to_hanja(data_gan)
        data_ji = ji_to_hanja(data_ji)
        data.append(list(data_gan))
        data.append(list(data_ji))

        return data

    elif (gen == "남" and ygan in EUMGAN) or (gen == "여" and ygan in YANGGAN):
        data = ["역행"]
        data_gan = []
        data_ji = []
        for i in range(len(CHEONGAN)):
            if CHEONGAN[i] == mgan:
                start = i - 1

        for i in range(10):
            data_gan.append(CHEONGAN[start % 10])
            start -= 1

        for i in range(len(JIJI)):
            if JIJI[i] == mji:
                start = i - 1

        for i in range(10):
            data_ji.append(JIJI[start % 12])
            start -= 1
        data_gan = gan_to_hanja(data_gan)
        data_ji = ji_to_hanja(data_ji)
        data.append(list(reversed(data_gan)))
        data.append(list(reversed(data_ji)))

        return data


def daewoonNum(year, month, day, calendar_type, direction, db: Session = Depends(get_db)):
    JEOLGI = ["입춘", "경칩", "청명", "입하", "망종", "소서",
              "입추", "백로", "한로", "입동", "대설", "소한"]
    
    # Query birthdate data based on calendar type
    if calendar_type == "양력":
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
        raise ValueError("No birth data found for the given date")
    
    birth_no = birthdata[0].cd_no
    start_spot = birth_no - 35
    
    # Query the data range needed
    temp_data_list = db.query(CalendaData).filter(
        CalendaData.cd_no > start_spot,
        CalendaData.cd_no < start_spot + 70
    ).all()
    
    # Filter for records that match JEOLGI terms
    jeolgi_dates = [data for data in temp_data_list if data.cd_kterms in JEOLGI]
    
    if direction == "순행":
        for jeolgi_date in jeolgi_dates:
            if birth_no < jeolgi_date.cd_no:
                daewoon_num = round((jeolgi_date.cd_no - birth_no) / 3, 1)
                return daewoon_num
    else:  # direction == "역행"
        for jeolgi_date in reversed(jeolgi_dates):
            if birth_no > jeolgi_date.cd_no:
                daewoon_num = round((birth_no - jeolgi_date.cd_no) / 3, 1)
                return daewoon_num
    
    raise ValueError("No suitable JEOLGI date found in the given range")

    
def get_time_gan(day_gan_kr, time_ji):
    CHEONGAN = ["갑", "을", "병", "정", "무", "기", "경", "신", "임", "계"]
    JIJI = ["자", "축", "인", "묘", "진", "사", "오", "미", "신", "유", "술", "해"]
    for i in range(len(JIJI)):
        if JIJI[i] == time_ji:
            time_ji_num = i

    if day_gan_kr == "갑" or day_gan_kr == "기":
        return CHEONGAN[time_ji_num % 10]
    if day_gan_kr == "을" or day_gan_kr == "경":
        return CHEONGAN[(time_ji_num + 2) % 10]
    if day_gan_kr == "병" or day_gan_kr == "신":
        return CHEONGAN[(time_ji_num + 4) % 10]
    if day_gan_kr == "정" or day_gan_kr == "임":
        return CHEONGAN[(time_ji_num + 6) % 10]
    if day_gan_kr == "무" or day_gan_kr == "계":
        return CHEONGAN[(time_ji_num + 8) % 10]

    
def gankr_to_ch(gankr):
    CHEONGAN = ["갑", "을", "병", "정", "무", "기", "경", "신", "임", "계"]
    CHEONGAN_CH = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
    for i in range(len(CHEONGAN)):
        if CHEONGAN[i] == gankr:
            return CHEONGAN_CH[i]

        
def jikr_to_ch(jikr):
    JIJI = ["자", "축", "인", "묘", "진", "사", "오", "미", "신", "유", "술", "해"]
    JIJI_CH = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
    for i in range(len(JIJI)):
        if JIJI[i] == jikr:
            return JIJI_CH[i]



def build_daewoon(
    direction_data,
    start_age,
    birth_year,
    current_year=None
):
    """
    direction_data:
    [
        "순행",
        ["壬","辛","庚","己","戊","丁","丙","乙","甲","癸"],
        ["戌","酉","申","未","午","巳","辰","卯","寅","丑"]
    ]
    """

    if current_year is None:
        current_year = date.today().year

    direction = direction_data[0]

    # 기존 데이터는 역순이므로 reverse
    gan_list = direction_data[1]
    ji_list = direction_data[2]

    daewoon_list = []

    current_age = current_year - birth_year

    current_daewoon = None

    for i in range(len(gan_list)):

        item_start_age = round(start_age + (i * 10), 1)
        item_end_age = round(item_start_age + 9.9, 1)

        start_year = birth_year + int(item_start_age)
        end_year = birth_year + int(item_end_age)

        item = {
            "index": i,
            "start_age": item_start_age,
            "end_age": item_end_age,
            "start_year": start_year,
            "end_year": end_year,
            "gan": gan_list[i],
            "ji": ji_list[i]
        }

        daewoon_list.append(item)

        # 현재 대운 계산
        if item_start_age <= current_age <= item_end_age:
            current_daewoon = {
                "index": i,
                "year": current_year,
                "age": current_age,
                "gan": gan_list[i],
                "ji": ji_list[i],
                "start_age": item_start_age,
                "end_age": item_end_age,
                "start_year": start_year,
                "end_year": end_year
            }

    return {
        "direction": direction,
        "start_age": start_age,
        "current": current_daewoon,
        "list": daewoon_list
    }