from services.calculator import gan_to_hanja, ji_to_hanja
from sqlalchemy.orm import Session
from models.calenda_data import CalendaData
from datetime import date

CHEONGAN = ["갑", "을", "병", "정", "무", "기", "경", "신", "임", "계"]
CHEONGAN_CH = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
JIJI = ["자", "축", "인", "묘", "진", "사", "오", "미", "신", "유", "술", "해"]
JIJI_CH = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

GAN_KR_TO_CH_MAP = dict(zip(CHEONGAN, CHEONGAN_CH))
JI_KR_TO_CH_MAP = dict(zip(JIJI, JIJI_CH))
JIJI_INDEX_MAP = {ji: idx for idx, ji in enumerate(JIJI)}


def getDaewoon(gen, ygan, mgan, mji):
    YANGGAN = ["갑", "병", "무", "경", "임"]
    EUMGAN = ["을", "정", "기", "신", "계"]

    if (gen == "남" and ygan in YANGGAN) or (gen == "여" and ygan in EUMGAN):
        data = ["순행"]
        data_gan = []
        data_ji = []
        start_g = (CHEONGAN.index(mgan) + 1) if mgan in CHEONGAN else 0
        for i in range(10):
            data_gan.append(CHEONGAN[(start_g + i) % 10])

        start_j = (JIJI.index(mji) + 1) if mji in JIJI else 0
        for i in range(10):
            data_ji.append(JIJI[(start_j + i) % 12])

        data_gan = gan_to_hanja(data_gan)
        data_ji = ji_to_hanja(data_ji)
        data.append(list(data_gan))
        data.append(list(data_ji))

        return data

    elif (gen == "남" and ygan in EUMGAN) or (gen == "여" and ygan in YANGGAN):
        data = ["역행"]
        data_gan = []
        data_ji = []
        start_g = (CHEONGAN.index(mgan) - 1) if mgan in CHEONGAN else 0
        for i in range(10):
            data_gan.append(CHEONGAN[(start_g - i) % 10])

        start_j = (JIJI.index(mji) - 1) if mji in JIJI else 0
        for i in range(10):
            data_ji.append(JIJI[(start_j - i) % 12])

        data_gan = gan_to_hanja(data_gan)
        data_ji = ji_to_hanja(data_ji)
        data.append(list(data_gan))
        data.append(list(data_ji))

        return data
    else:
        return ["순행", [], []]


def daewoonNum(birth_no: int, direction: str, db: Session):
    JEOLGI = ["입춘", "경칩", "청명", "입하", "망종", "소서",
              "입추", "백로", "한로", "입동", "대설", "소한"]
    
    start_spot = birth_no - 35
    
    # DB 레코드 검색 시 JEOLGI 절기 항목만 SQL IN 절로 직접 필터링
    jeolgi_dates = db.query(CalendaData).filter(
        CalendaData.cd_no > start_spot,
        CalendaData.cd_no < start_spot + 70,
        CalendaData.cd_kterms.in_(JEOLGI)
    ).all()
    
    if direction == "순행":
        for jeolgi_date in jeolgi_dates:
            if birth_no < jeolgi_date.cd_no:
                return round((jeolgi_date.cd_no - birth_no) / 3, 1)
    else:  # direction == "역행"
        for jeolgi_date in reversed(jeolgi_dates):
            if birth_no > jeolgi_date.cd_no:
                return round((birth_no - jeolgi_date.cd_no) / 3, 1)
    
    return 1.0

    
def get_time_gan(day_gan_kr: str, time_ji: str) -> str:
    time_ji_num = JIJI_INDEX_MAP.get(time_ji, 0)
    offset_map = {"갑": 0, "기": 0, "을": 2, "경": 2, "병": 4, "신": 4, "정": 6, "임": 6, "무": 8, "계": 8}
    offset = offset_map.get(day_gan_kr, 0)
    return CHEONGAN[(time_ji_num + offset) % 10]

    
def gankr_to_ch(gankr: str) -> str:
    return GAN_KR_TO_CH_MAP.get(gankr, gankr)

        
def jikr_to_ch(jikr: str) -> str:
    return JI_KR_TO_CH_MAP.get(jikr, jikr)


from services.calculator import get_ten_star_stem, get_ten_star_branch, get_stem_detail, get_branch_detail
from services.constants import UNSEONG_DATA

def build_daewoon(
    direction_data,
    start_age,
    birth_year,
    current_year=None,
    day_stem=None
):
    if current_year is None:
        current_year = date.today().year

    direction = direction_data[0]

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

        gan_char = gan_list[i]
        ji_char = ji_list[i]

        gan_detail = get_stem_detail(day_stem, gan_char)
        ji_detail = get_branch_detail(day_stem, ji_char)

        gan_tg = gan_detail["ten_god"]
        ji_tg = ji_detail["ten_god"]
        unseong = UNSEONG_DATA.get(day_stem, {}).get(ji_char, "") if day_stem else ""

        item = {
            "index": i,
            "start_age": item_start_age,
            "end_age": item_end_age,
            "start_year": start_year,
            "end_year": end_year,
            "gan": gan_char,
            "ji": ji_char,
            "gan_detail": gan_detail,
            "ji_detail": ji_detail,
            "gan_ten_god": gan_tg,
            "ji_ten_god": ji_tg,
            "unseong": unseong
        }

        daewoon_list.append(item)

        if item_start_age <= current_age <= item_end_age:
            current_daewoon = {
                "index": i,
                "year": current_year,
                "age": current_age,
                "gan": gan_char,
                "ji": ji_char,
                "gan_detail": gan_detail,
                "ji_detail": ji_detail,
                "gan_ten_god": gan_tg,
                "ji_ten_god": ji_tg,
                "unseong": unseong,
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