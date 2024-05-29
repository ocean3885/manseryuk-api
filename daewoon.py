from calculator import gan_to_hanja, ji_to_hanja
from fastapi import Depends
from sqlalchemy.orm import Session
from models.calenda_data import CalendaData
from dependencies import get_db


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
        data.append(list(reversed(data_gan)))
        data.append(list(reversed(data_ji)))

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