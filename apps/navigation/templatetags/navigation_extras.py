from django import template

register = template.Library()

# ── ODsay subwayCode(숫자) → 시그니처 색상 (maps.js와 동일하게 유지) ──
SUBWAY_CODE_COLORS = {
    1:   '#0052A4',  # 1호선
    2:   '#00A84D',  # 2호선
    3:   '#EF7C1C',  # 3호선
    4:   '#00A5DE',  # 4호선
    5:   '#996CAC',  # 5호선
    6:   '#CD7C2F',  # 6호선
    7:   '#747F00',  # 7호선
    8:   '#E6186C',  # 8호선
    9:   '#BDB092',  # 9호선
    11:  '#F5A200',  # 수인분당선
    16:  '#D4003B',  # 신분당선
    12:  '#77C4A3',  # 경의중앙선
    13:  '#0065B3',  # 공항철도
    109: '#6EBF46',  # 에버라인(용인경전철)
    100: '#9A1B5A',  # GTX-A
}

# 노선 이름 포함 여부로 매핑 (subwayCode 없을 때 fallback)
SUBWAY_NAME_COLORS = {
    '수인분당선': '#F5A200',
    '분당선':    '#F5A200',
    '신분당선':  '#D4003B',
    '경의중앙선': '#77C4A3',
    '공항철도':  '#0065B3',
    '에버라인':  '#6EBF46',
    '용인경전철': '#6EBF46',
    'GTX':      '#9A1B5A',
}

# 버스 번호별 명시적 색상 — ODsay type 없거나 알 수 없을 때 2단계 폴백
# 새 버스 추가 시 이 테이블에만 추가하면 됨
BUS_NUMBER_COLORS = {
    '5000': '#E60026',  # 경기 직행좌석  — 빨강
    '5005': '#E60026',  # 경기 직행좌석  — 빨강
    '7021': '#53B332',  # 경기 일반버스  — 초록
}

BUS_COLORS = {
    # ── 서울 버스 ──────────────────────────────────────
    '1':  '#0075C8',  # 간선버스            — 파랑
    '2':  '#53B332',  # 지선버스            — 초록
    '3':  '#F99D1C',  # 순환버스            — 노랑
    '4':  '#5BB025',  # 마을버스            — 연초록
    '5':  '#E60026',  # 직행좌석(빨간버스)  — 빨강 ★사용자 확인
    '6':  '#E60026',  # 광역버스(서울)      — 빨강
    '7':  '#53B332',  # 일반버스            — 초록 ★사용자 확인
    '8':  '#53B332',  # 경기버스(서울코드)  — 초록
    '9':  '#0052A4',  # 공항버스            — 남색
    '10': '#F99D1C',  # 투어버스            — 노랑
    # ── 경기·인천 버스 ──────────────────────────────────
    '11': '#E60026',  # 경기 직행좌석       — 빨강
    '12': '#0075C8',  # 경기 좌석버스       — 파랑
    '13': '#53B332',  # 경기 일반버스       — 초록
    '14': '#E60026',  # 경기 광역버스       — 빨강
    '15': '#5BB025',  # 따복버스(경기 마을) — 연초록
    '16': '#F99D1C',  # 경기 순환버스       — 노랑
    '21': '#E60026',  # 농어촌 직행좌석     — 빨강
    '22': '#0075C8',  # 농어촌 좌석         — 파랑
    '23': '#53B332',  # 농어촌 일반         — 초록
    '30': '#5BB025',  # 경기 마을버스       — 연초록
    # ── 고속·시외버스 ────────────────────────────────────
    '41': '#0052A4',  # 고속버스            — 남색
    '42': '#0052A4',  # 시외좌석            — 남색
    '43': '#0052A4',  # 시외일반            — 남색
}


def _normalize_lane(subpath):
    """ODsay lane 필드: 배열 또는 단일 객체 모두 처리 → dict 반환"""
    raw = subpath.get('lane')
    if isinstance(raw, list):
        return raw[0] if raw else {}
    if isinstance(raw, dict):
        return raw
    return {}


def _get_subway_code(lane0):
    """subwaycode(소문자, ODsay 공식) / subwayCode(대문자) 둘 다 탐색"""
    return lane0.get('subwaycode') or lane0.get('subwayCode')


def _resolve_subway_color(code=None, name=None):
    """ODsay subwayCode(숫자) 또는 노선 이름으로 색상 반환."""
    if code is not None:
        try:
            color = SUBWAY_CODE_COLORS.get(int(code))
            if color:
                return color
        except (ValueError, TypeError):
            pass
    if name:
        name_str = str(name)
        for key, color in SUBWAY_NAME_COLORS.items():
            if key in name_str:
                return color
        # "1호선" 형태처럼 첫 글자가 숫자인 경우
        if name_str and name_str[0].isdigit():
            try:
                return SUBWAY_CODE_COLORS.get(int(name_str[0]), '#0052A4')
            except (ValueError, TypeError):
                pass
    return '#0052A4'


@register.filter
def minutes_to_hhmm(minutes):
    """
    Convert minutes to HH시간 MM분 format.

    Examples:
        45 → "45분"
        60 → "1시간"
        92 → "1시간 32분"
        120 → "2시간"
    """
    try:
        minutes = int(minutes)
    except (ValueError, TypeError):
        return "정보 없음"

    if minutes < 60:
        return f"{minutes}분"

    hours, mins = divmod(minutes, 60)

    if mins == 0:
        return f"{hours}시간"

    return f"{hours}시간 {mins}분"


@register.filter
def get_station_count_text(subpath):
    """
    지하철 구간의 정거장 수를 텍스트로 반환.
    예: 4 → "4정거장"
    """
    try:
        count = int(subpath.get('stationCount', 0))
        return f"{count}정거장"
    except (ValueError, TypeError, AttributeError):
        return ""


@register.filter
def get_traffic_emoji(traffic_type):
    """
    trafficType별 이모지 반환.
    1 or 'subway': 🚇 (지하철)
    2 or 'bus': 🚌 (버스)
    3 or 'walk': 🚶 (도보)
    """
    traffic_emojis = {
        1: '🚇', 'subway': '🚇',
        2: '🚌', 'bus': '🚌',
        3: '🚶', 'walk': '🚶',
    }
    return traffic_emojis.get(traffic_type, '📍')


@register.filter
def get_subway_color(line_name):
    """
    노선 이름 문자열(subpath.name)로 지하철 시그니처 색상 반환.
    예: '수인분당선' → '#F5A200', '2호선' → '#00A84D'
    """
    return _resolve_subway_color(name=line_name)


@register.filter
def get_polyline_color(subpath):
    """
    subPath dict의 색상을 반환 (maps.js getPolylineStyle 과 동일 로직).
    ODsay 원본: lane[0].subwayCode / lane[0].type 를 1차 소스로 사용.
    전처리 데이터(subwayCode, busType 최상위)는 lane 없을 때 보조.
    trafficType 1=지하철, 2=버스, 3=도보.
    """
    traffic_type = subpath.get('trafficType')
    lane0 = _normalize_lane(subpath)

    if traffic_type == 1:  # 지하철
        # subwaycode(소문자, ODsay 공식) → subwayCode(대문자, 전처리) 순
        code = _get_subway_code(lane0) or subpath.get('subwaycode') or subpath.get('subwayCode')
        name = lane0.get('name') or subpath.get('name', '')
        return _resolve_subway_color(code=code, name=name)

    elif traffic_type == 2:  # 버스
        # ── 색상 결정 단계 ──────────────────────────────────────
        # 1단계: 버스 번호 명시 (BUS_NUMBER_COLORS)
        #        ODsay type 오분류 보정용 — 최우선
        # 2단계: 버스 종류 (BUS_COLORS[lane[0].type])
        #        ODsay type이 정확할 때 사용
        # 3단계: fallback #1B2A5E

        # 1단계: 번호 명시 테이블 (ODsay 오분류 보정)
        bus_nos = []
        raw_lane = subpath.get('lane')
        lane_list = raw_lane if isinstance(raw_lane, list) else ([raw_lane] if isinstance(raw_lane, dict) else [])
        for l in lane_list:
            no = str(l.get('busNo') or l.get('name') or '').strip()
            if no:
                bus_nos.append(no)
        for no in (subpath.get('lanes') or []):
            s = str(no).strip()
            if s and s not in bus_nos:
                bus_nos.append(s)

        for no in bus_nos:
            if no in BUS_NUMBER_COLORS:
                return BUS_NUMBER_COLORS[no]

        # 2단계: 버스 종류 (ODsay lane[0].type → BUS_COLORS)
        bus_type = lane0.get('type') if lane0 else None
        if bus_type is None:
            bus_type = subpath.get('busType')
        if bus_type is not None:
            type_color = BUS_COLORS.get(str(bus_type))
            if type_color:
                return type_color

        # 3단계: fallback
        return '#1B2A5E'

    elif traffic_type == 3:  # 도보
        return '#9ca3af'

    return '#666666'


@register.filter
def get_dict_value(obj, key):
    """
    Dictionary에서 키 값을 가져옴.
    템플릿에서 dict[key] 접근을 지원하기 위함.
    """
    try:
        if isinstance(obj, dict):
            return obj.get(key, '')
        return ''
    except (AttributeError, TypeError):
        return ''
