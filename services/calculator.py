import math


# 한글에서 한자로의 매핑
Gan_to_hanja = {
    '갑': '甲', '을': '乙', '병': '丙', '정': '丁', '무': '戊',
    '기': '己', '경': '庚', '신': '辛', '임': '壬', '계': '癸'
}
Ji_to_hanja = {    
    '자': '子', '축': '丑', '인': '寅', '묘': '卯', '진': '辰',
    '사': '巳', '오': '午', '미': '未', '신': '申', '유': '酉',
    '술': '戌', '해': '亥'
}

def gan_to_hanja(korean_text):
    return ''.join(Gan_to_hanja.get(char, char) for char in korean_text)


def ji_to_hanja(korean_text):
    return ''.join(Ji_to_hanja.get(char, char) for char in korean_text)


def descending_tens(n):
    # n이 소수일 경우 소수보다 큰 가장 가까운 정수로 변환
    rounded_n = round(n)
    start = rounded_n + 90  # 첫 번째 숫자를 계산
    # start부터 10*i씩 감소시킨 요소 9개를 생성
    result = [start - 10 * i for i in range(9)]
    # 마지막에 원래 수 n 추가
    result.append(n)
    return result

def find_ten_god(benchmark, other):
    # 천간 배열
    heavenly_stems = ['갑', '을', '병', '정', '무', '기', '경', '신', '임', '계']
    
    # 천간 인덱스 찾기
    index_b = heavenly_stems.index(benchmark)
    index_o = heavenly_stems.index(other)
    
    # 십성 관계 정의
    relationships = {
        0: '비견',   # 같은 것
        1: '겁재',   # 같은 것의 다른 측면 (긍정적/부정적)
        2: '식신',   # 생성하는 것
        3: '상관',   # 생성하려는 것을 제어
        4: '편재',   # 제어하려는 것의 다른 형태
        5: '정재',   # 제어하려는 것을 강화
        6: '편관',   # 강화하려는 것을 제압
        7: '정관',   # 제압하려는 것을 지원
        8: '편인',   # 지원하려는 것의 다른 형태
        9: '정인',   # 지원하려는 것을 생성
        -1: '정재',  # 생성하려는 것의 다른 형태
        -2: '편재',  # 강화하려는 것의 다른 형태
        -3: '정관',  # 제압하려는 것의 다른 형태
    }
    
    # 인덱스 차이 계산
    difference = (index_o - index_b) % 10
    
    # 십성 반환
    return relationships.get(difference, "관계 없음")


def find_stem_branch_ten_god(stem, branch):
    
    # 지지와 천간의 상호작용을 기반으로 십성을 정의하는 규칙 
    interaction = {
        '갑': {'인': '비견', '묘': '겁재', '사': '식신', '오': '상관', '진': '편재','술':'편재','축':'정재','미':'정재','신':'편관','유':'정관','해':'편인','자':'정인'},
        '을': {'묘': '비견', '인': '겁재', '오': '식신', '사': '상관', '축': '편재','미':'편재','진':'정재','술':'정재','유':'편관','신':'정관','자':'편인','해':'정인'},
        '병': {'사': '비견', '오': '겁재', '진': '식신', '술': '식신', '축': '상관','미':'상관','신':'편재','유':'정재','해':'편관','자':'정관','인':'편인','묘':'정인'},
        '정': {'오': '비견', '사': '겁재', '축': '식신', '미': '식신', '진': '상관','술':'상관','유':'편재','신':'정재','자':'편관','해':'정관','묘':'편인','인':'정인'},
        '무': {'진': '비견', '술': '비견', '축': '겁재', '미': '겁재', '신': '식신','유':'상관','해':'편재','자':'정재','인':'편관','묘':'정관','사':'편인','오':'정인'},
        '기': {'축': '비견', '미': '비견', '진': '겁재', '술': '겁재', '유': '식신','신':'상관','자':'편재','해':'정재','묘':'편관','인':'정관','오':'편인','사':'정인'},
        '경': {'신': '비견', '유': '겹재', '해': '식신', '자': '상관', '인': '편재','묘':'정재','사':'편관','오':'정관','진':'편인','술':'편인','축':'정인','미':'정인'},
        '신': {'유': '비견', '신': '겹재', '자': '식신', '해': '상관', '묘': '편재','인':'정재','오':'편관','사':'정관','축':'편인','미':'편인','진':'정인','술':'정인'},
        '임': {'해': '비견', '자': '겹재', '인': '식신', '묘': '상관', '사': '편재','오':'정재','진':'편관','술':'편관','축':'정관','미':'정관','신':'편인','유':'정인'},
        '계': {'자': '비견', '해': '겹재', '묘': '식신', '인': '상관', '오': '편재','사':'정재','축':'편관','미':'편관','진':'정관','술':'정관','유':'편인','신':'정인'},
    }
    
    # 천간을 기준으로 해당 지지의 십성을 찾기
    if stem in interaction and branch in interaction[stem]:
        return interaction[stem][branch]
    
    # 십성이 정의되지 않은 경우
    return "관계 없음"


def find_twelve_luck(stem, branch):
    # 지지 배열
    earthly_branches = ['자', '축', '인', '묘', '진', '사', '오', '미', '신', '유', '술', '해']
    
    # 십이운성 배열
    twelve_lucks = ['장생', '목욕', '관대', '건록', '제왕', '쇠', '병', '사', '묘', '절', '태', '양']
    
    # 천간별 시작 지지와 순서 정의
    start_branches = {
        '갑': ('해', False), '을': ('미', True), '병': ('인', False),
        '정': ('술', True), '무': ('인', False), '기': ('술', True),
        '경': ('사', False), '신': ('축', True), '임': ('신', False),
        '계': ('진', True)
    }
    
    start_branch, reverse = start_branches[stem]
    start_index = earthly_branches.index(start_branch)
    
    # 지지의 순서 결정
    if reverse:
        ordered_branches = list(reversed(earthly_branches[start_index:] + earthly_branches[:start_index]))
    else:
        ordered_branches = earthly_branches[start_index:] + earthly_branches[:start_index]

    luck_index = ordered_branches.index(branch)
    return twelve_lucks[luck_index]
    

def determine_zodiac_hour_str(hour_str, minute_str):
    # 입력된 시간과 분을 정수형으로 변환
    try:
        hour = int(hour_str)
        minute = int(minute_str)
    except ValueError:
        return "잘못된 시간 형식입니다."

    # 시간과 분을 하나의 숫자로 결합하여 표현
    total_minutes = hour * 60 + minute

    # 12지지에 따른 시간 범위 설정
    time_ranges = [
        ((23*60 + 31, 24*60), "자"),  # 23:31 ~ 24:00 (자정까지)
        ((0, 1*60 + 30), "자"),       # 00:00 ~ 01:30
        ((1*60 + 31, 3*60 + 30), "축"),   # 01:31 ~ 03:30
        ((3*60 + 31, 5*60 + 30), "인"),   # 03:31 ~ 05:30
        ((5*60 + 31, 7*60 + 30), "묘"),   # 05:31 ~ 07:30
        ((7*60 + 31, 9*60 + 30), "진"),   # 07:31 ~ 09:30
        ((9*60 + 31, 11*60 + 30), "사"),  # 09:31 ~ 11:30
        ((11*60 + 31, 13*60 + 30), "오"), # 11:31 ~ 13:30
        ((13*60 + 31, 15*60 + 30), "미"), # 13:31 ~ 15:30
        ((15*60 + 31, 17*60 + 30), "신"), # 15:31 ~ 17:30
        ((17*60 + 31, 19*60 + 30), "유"), # 17:31 ~ 19:30
        ((19*60 + 31, 21*60 + 30), "술"), # 19:31 ~ 21:30
        ((21*60 + 31, 23*60 + 30), "해")  # 21:31 ~ 23:30
    ]

    # 입력된 시간이 해당하는 지지를 찾음
    for (start, end), zodiac in time_ranges:
        if start <= total_minutes <= end:
            return zodiac

    # 지정된 시간 범위 밖인 경우
    return "해당 시간에 대한 지지를 찾을 수 없음"


def generate_future_cycles(year, daeun):
    
    # 천간과 지지
    heavenly_stems = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
    earthly_branches = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
    
    # 대운수 반올림 처리 및 시작년도 계산
    rounded_daeun = round(daeun)
    start_year = year + rounded_daeun - 1
    
    # 결과를 저장할 리스트 초기화
    years = []
    heavenly_cycles = []
    earthly_cycles = []
    
    # 시작 년도의 육십갑자 천간과 지지 인덱스 찾기
    base_year = 1984  # 갑자년 시작
    offset = (start_year - base_year) % 60
    heavenly_index = offset % 10
    earthly_index = offset % 12

    # 100개의 년도, 천간, 지지 계산
    for i in range(100):
        years.append(start_year + i)
        heavenly_cycles.append(heavenly_stems[(heavenly_index + i) % 10])
        earthly_cycles.append(earthly_branches[(earthly_index + i) % 12])
    years = list(reversed(years))
    heavenly_cycles = list(reversed(heavenly_cycles))
    earthly_cycles = list(reversed(earthly_cycles))
    grouped_year = zip(years,heavenly_cycles,earthly_cycles)
    grouped_list = list(grouped_year)
    grouped_chunks = [grouped_list[i:i + 10] for i in range(0, len(grouped_list), 10)]
    return grouped_chunks


def generate_baby_cycles(year):
    # 천간과 지지
    heavenly_stems = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
    earthly_branches = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
    years = []
    heavenly_cycles = []
    earthly_cycles = []
    # 시작 년도의 육십갑자 천간과 지지 인덱스 찾기
    base_year = 1984  # 갑자년 시작
    offset = (year - base_year) % 60
    heavenly_index = offset % 10
    earthly_index = offset % 12
     # 10개의 년도, 천간, 지지 계산
    for i in range(10):
        years.append(year + i)
        heavenly_cycles.append(heavenly_stems[(heavenly_index + i) % 10])
        earthly_cycles.append(earthly_branches[(earthly_index + i) % 12])
    years = list(reversed(years))
    heavenly_cycles = list(reversed(heavenly_cycles))
    earthly_cycles = list(reversed(earthly_cycles))
    grouped_year = list(zip(years,heavenly_cycles,earthly_cycles))
    return grouped_year


