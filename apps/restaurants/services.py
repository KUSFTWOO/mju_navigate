import requests
import logging
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger(__name__)


CAMPUS_LOCATIONS = {
    'seoul': {
        'name': '서울캠퍼스',
        'address': '서울특별시 서대문구 거북골로 34 종합관',
        'building': '종합관'
    },
    'yongin': {
        'name': '용인캠퍼스',
        'address': '경기도 용인시 처인구 명지로 116 학생회관',
        'building': '학생회관'
    },
}

# 캠퍼스 정밀 좌표 (Kakao Geocoding 불필요, 하드코딩)
CAMPUS_COORDS = {
    'seoul': {'lat': 37.5803770223812, 'lng': 126.921348530876},
    'yongin': {'lat': 37.2218072639192, 'lng': 127.190183727516},
}

CATEGORY_KEYWORDS = {
    'all': '음식점',
    'korean': '한식당',
    'cafe': '카페',
    'chicken': '치킨',
    'chinese': '중국집',
    'japanese': '일식당',
    'western': '양식당',
    'fastfood': '패스트푸드',
}

CATEGORY_NAMES = {
    'all': '전체',
    'korean': '한식',
    'cafe': '카페',
    'chicken': '치킨',
    'chinese': '중식',
    'japanese': '일식',
    'western': '양식',
    'fastfood': '패스트푸드',
}


def get_coordinates_from_address(address):
    """주소를 좌표로 변환 (Kakao Geocoding API)"""
    cache_key = f'geocoding:{address}'
    cached_coords = cache.get(cache_key)
    if cached_coords is not None:
        return cached_coords

    headers = {
        'Authorization': f'KakaoAK {settings.KAKAO_API_KEY}'
    }

    params = {
        'query': address,
    }

    try:
        response = requests.get(
            'https://dapi.kakao.com/v2/local/search/address.json',
            headers=headers,
            params=params,
            timeout=5
        )
        response.raise_for_status()

        documents = response.json().get('documents', [])
        if documents:
            doc = documents[0]
            coords = {
                'lat': float(doc['y']),
                'lng': float(doc['x']),
            }
            # 24시간 캐시
            cache.set(cache_key, coords, timeout=86400)
            logger.info(f'주소 변환 성공: {address} → ({coords["lat"]}, {coords["lng"]})')
            return coords

        logger.warning(f'주소 변환 실패: {address}')
        return None

    except requests.RequestException as e:
        logger.error(f'Kakao Geocoding API 오류 ({address}): {str(e)}')
        return None


def get_nearby_restaurants(campus, category='all', radius=1000):
    """Kakao Local API를 호출하여 캠퍼스 근처 음식점을 조회한다."""

    if campus not in CAMPUS_LOCATIONS:
        return []

    # 캐시 키
    cache_key = f'restaurants:{campus}:{category}:{radius}'
    cached_data = cache.get(cache_key)
    if cached_data is not None:
        return cached_data

    location = CAMPUS_LOCATIONS[campus]
    address = location['address']

    # 주소로부터 좌표 조회
    coords = get_coordinates_from_address(address)
    if coords:
        lat = coords['lat']
        lng = coords['lng']
    else:
        logger.error(f'좌표 변환 실패: {address}')
        return []

    headers = {
        'Authorization': f'KakaoAK {settings.KAKAO_API_KEY}'
    }

    try:
        # 모든 카테고리를 keyword 검색으로 통일 (더 정확한 분류)
        query = CATEGORY_KEYWORDS.get(category, '음식점')

        params = {
            'query': query,
            'y': lat,
            'x': lng,
            'radius': radius,
            'sort': 'distance',
            'size': 15,
        }
        url = 'https://dapi.kakao.com/v2/local/search/keyword.json'

        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=5
        )
        response.raise_for_status()

        data = response.json().get('documents', [])
        logger.info(f'음식점 조회: {campus} {query} ({len(data)}개)')

        # 캐시 저장 (30분)
        cache.set(cache_key, data, timeout=1800)

        return data

    except requests.RequestException as e:
        logger.error(f'Kakao API 오류 ({campus}, {category}): {str(e)}')
        return []
