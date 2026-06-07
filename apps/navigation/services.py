import requests
import logging
from django.conf import settings
from django.core.cache import cache
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


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
            cache.set(cache_key, coords, timeout=86400)  # 24시간 캐시
            logger.info(f'주소 변환 성공: {address} → ({coords["lat"]}, {coords["lng"]})')
            return coords

        logger.warning(f'주소 변환 실패: {address}')
        return None

    except requests.RequestException as e:
        logger.error(f'Kakao Geocoding API 오류 ({address}): {str(e)}')
        return None

CAMPUS_COORDS = {
    'seoul_campus': {
        'lat': 37.5803770223812,
        'lng': 126.921348530876,
        'name': '서울캠퍼스',
        'building': '종합관',
        'address': '서울특별시 서대문구 거북골로 34 종합관'
    },
    'yongin_campus': {
        'lat': 37.2218072639192,
        'lng': 127.190183727516,
        'name': '용인캠퍼스',
        'building': '학생회관',
        'address': '경기도 용인시 처인구 명지로 116 학생회관'
    },
}

TRANSFER_POINTS = {
    'giheungstation': {
        'name': '기흥역 5번 출구',
        'lat': 37.2746865309262,
        'lng': 127.115683230713,
    },
}


def get_transit_routes(origin_lat, origin_lng, dest_lat, dest_lng, date=None, time=None):
    """
    ODsay API를 통해 대중교통 경로를 조회한다.
    date, time 파라미터로 특정 출발 시간 지정 가능.
    동일 요청은 5분간 캐싱한다.
    """
    cache_key = f"route_{origin_lat}_{origin_lng}_{dest_lat}_{dest_lng}_{date}_{time}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    try:
        params = {
            "SX": origin_lng,
            "SY": origin_lat,
            "EX": dest_lng,
            "EY": dest_lat,
            "apiKey": settings.ODSAY_API_KEY,
        }

        # 출발 시간 지정 시 파라미터 추가
        if date:
            params["date"] = date
        if time:
            params["time"] = time

        response = requests.get(
            "https://api.odsay.com/v1/api/searchPubTransPathT",
            params=params,
            timeout=5
        )
        response.raise_for_status()
        data = response.json()
        cache.set(cache_key, data, 60 * 5)  # 5분 캐시
        return data
    except requests.RequestException as e:
        logger.error(f"ODsay API 오류: {e}")
        return None


def get_day_type(dt):
    """datetime 객체를 받아 weekday/saturday/sunday 반환"""
    try:
        import holidays
        kr_holidays = holidays.KR()
        if dt.date() in kr_holidays:
            return 'sunday'
    except ImportError:
        pass

    weekday = dt.weekday()
    if weekday == 5:
        return 'saturday'
    elif weekday == 6:
        return 'sunday'

    return 'weekday'


def get_shuttle_options(direction, departure_datetime):
    """
    direction: 'seoul_to_yongin' | 'yongin_to_seoul'
    departure_datetime: datetime 객체
    반환: 셔틀 옵션 리스트

    케이스:
    - A: 셔틀 있음
    - B: 당일 운행 종료 (다른 시간대엔 있음)
    - C: 해당 요일 운행 없음
    """
    from .models import ShuttleRoute, ShuttleSchedule

    day_type = get_day_type(departure_datetime)
    current_time = departure_datetime.time()
    options = []

    # 방향별 조회 노선 정의
    if direction == 'seoul_to_yongin':
        route_pks = [4]  # 기흥역→학교
    else:
        route_pks = [3]  # 학교→기흥역

    for pk in route_pks:
        try:
            route = ShuttleRoute.objects.get(pk=pk, is_active=True)
            next_sch = ShuttleSchedule.get_next_departure(
                route, current_time, day_type
            )

            # 이후 3개 시간표도 조회
            upcoming = ShuttleSchedule.objects.filter(
                route=route,
                day_type=day_type,
                is_active=True,
                departure_time__gte=current_time
            ).order_by('departure_time')[:4]

            if next_sch:
                # Case A: 셔틀 있음
                dep = next_sch.departure_time
                dep_dt = departure_datetime.replace(
                    hour=dep.hour, minute=dep.minute, second=0
                )
                minutes_until = int(
                    (dep_dt - departure_datetime).total_seconds() / 60
                )
                options.append({
                    'route_name': route.name,
                    'route_pk': route.pk,
                    'departure_time': dep,
                    'minutes_until': max(0, minutes_until),
                    'origin_name': route.get_origin_display(),
                    'destination_name': route.get_destination_display(),
                    'description': route.description,
                    'upcoming': list(upcoming[1:4]),  # 이후 3개
                    'no_service': False,
                })
            else:
                # Case B / C: 셔틀 없음 - 요일별 스케줄 확인
                day_schedules = ShuttleSchedule.objects.filter(
                    route=route,
                    day_type=day_type,
                    is_active=True
                ).order_by('departure_time')

                if day_schedules.exists():
                    # Case B: 당일 운행 종료 (다른 시간대엔 있음)
                    last_departure = day_schedules.last().departure_time
                    options.append({
                        'route_name': route.name,
                        'route_pk': route.pk,
                        'no_service': True,
                        'reason': 'ended',
                        'last_departure': last_departure,
                        'message': f'오늘 셔틀 운행이 종료되었습니다. (마지막 출발 {last_departure.strftime("%H:%M")})',
                    })
                else:
                    # Case C: 해당 요일 운행 없음
                    options.append({
                        'route_name': route.name,
                        'route_pk': route.pk,
                        'no_service': True,
                        'reason': 'no_schedule',
                        'message': '해당 날짜에는 셔틀이 운행하지 않습니다.',
                    })
        except ShuttleRoute.DoesNotExist:
            continue

    return options


def get_combined_shuttle_routes(origin, destination, departure_datetime):
    """
    대중교통 + 셔틀버스 조합 경로 반환
    origin, destination: 'seoul_campus' | 'yongin_campus'
    departure_datetime: datetime 객체
    """
    from .models import ShuttleRoute, ShuttleSchedule

    day_type = get_day_type(departure_datetime)

    # ✅ ODsay API 호출용 date/time 파라미터 변환
    api_date = departure_datetime.strftime('%Y%m%d')
    api_time = departure_datetime.strftime('%H%M')
    logger.info(f'셔틀 조합 경로 검색: date={api_date}, time={api_time}')

    results = []

    if origin == 'seoul_campus' and destination == 'yongin_campus':
        combinations = [
            {
                'transit_dest': 'giheungstation',
                'shuttle_pk': 4,
                'label': '기흥역 통학버스 경유',
            },
        ]
        for combo in combinations:
            tp = TRANSFER_POINTS[combo['transit_dest']]

            # 1. ODsay: 서울캠 → 환승거점
            transit = get_transit_routes(
                CAMPUS_COORDS['seoul_campus']['lat'],
                CAMPUS_COORDS['seoul_campus']['lng'],
                tp['lat'],
                tp['lng'],
                date=api_date,  # ✅ 사용자 선택 시간 기준
                time=api_time,
            )
            if not transit or not transit.get('result', {}).get('path'):
                logger.warning(f'ODsay API 응답 없음: 서울캠 → {combo["transit_dest"]}')
                continue

            best_path = transit['result']['path'][0]

            # API 응답 검증: subPath와 info 필드 확인
            if not best_path.get('subPath') or not best_path.get('info'):
                logger.warning(f'ODsay API 응답 불완전: subPath={bool(best_path.get("subPath"))}, info={bool(best_path.get("info"))}')
                continue

            # subPath 정제: 버스/지하철 번호 추출 및 분리
            bus_subpaths = []
            subway_subpaths = []

            for subpath in best_path.get('subPath', []):
                traffic_type = subpath.get('trafficType')

                # 버스(2) 또는 지하철(1)인 경우만 처리
                if traffic_type in [1, 2]:
                    refined_subpath = dict(subpath)

                    # lane: 배열 또는 단일 객체 모두 정규화
                    raw_lane = subpath.get('lane')
                    lane_list = raw_lane if isinstance(raw_lane, list) else ([raw_lane] if isinstance(raw_lane, dict) else [])
                    lane0 = lane_list[0] if lane_list else {}

                    # 버스인 경우: lane에서 번호 및 타입 추출
                    if traffic_type == 2:
                        if lane_list:
                            bus_nos = []
                            bus_type = None
                            for idx, lane in enumerate(lane_list):
                                bus_no = lane.get('busNo') or lane.get('name')
                                if bus_no:
                                    bus_nos.append(bus_no)
                                if idx == 0 and lane.get('type'):
                                    bus_type = lane.get('type')
                            if bus_nos:
                                refined_subpath['busNumbers'] = bus_nos
                                refined_subpath['name'] = bus_nos[0]
                            if bus_type:
                                refined_subpath['busType'] = bus_type
                        bus_subpaths.append(refined_subpath)

                    # 지하철인 경우: lane 정보가 있는 실제 노선만 포함
                    elif traffic_type == 1:
                        if lane0.get('name'):
                            refined_subpath = dict(subpath)
                            refined_subpath['name'] = lane0.get('name', '')
                            # subwaycode(소문자, ODsay 공식) / subwayCode(대문자) 모두 탐색
                            refined_subpath['subwayCode'] = lane0.get('subwaycode') or lane0.get('subwayCode')
                            subway_subpaths.append(refined_subpath)

            transit_minutes = best_path['info']['totalTime']
            transit_arrival = departure_datetime + timedelta(minutes=transit_minutes)

            # 2. 다음 셔틀 출발 시각 조회
            route = ShuttleRoute.objects.filter(
                pk=combo['shuttle_pk'], is_active=True
            ).first()
            if not route:
                continue

            next_shuttle = ShuttleSchedule.get_next_departure(
                route, transit_arrival.time(), day_type
            )
            if not next_shuttle:
                continue

            shuttle_dep = transit_arrival.replace(
                hour=next_shuttle.departure_time.hour,
                minute=next_shuttle.departure_time.minute,
                second=0,
            )
            wait_minutes = int(
                (shuttle_dep - transit_arrival).total_seconds() / 60
            )
            shuttle_duration = 15
            total_minutes = transit_minutes + wait_minutes + shuttle_duration

            arrival = shuttle_dep + timedelta(minutes=shuttle_duration)
            results.append({
                'label': combo['label'],
                'total_minutes': total_minutes,
                'direction': 'seoul_to_yongin',
                'transit_segment': best_path,
                'bus_subpaths': bus_subpaths,
                'subway_subpaths': subway_subpaths,
                'transit_minutes': transit_minutes,
                'transfer_point': tp['name'],
                'transfer_lat': tp['lat'],
                'transfer_lng': tp['lng'],
                'origin_lat': CAMPUS_COORDS['seoul_campus']['lat'],
                'origin_lng': CAMPUS_COORDS['seoul_campus']['lng'],
                'destination_lat': CAMPUS_COORDS[destination]['lat'],
                'destination_lng': CAMPUS_COORDS[destination]['lng'],
                'wait_minutes': wait_minutes,
                'shuttle_route_name': route.name,
                'shuttle_route_id': route.pk,
                'shuttle_departure': next_shuttle.departure_time.strftime('%H:%M'),
                'shuttle_duration': shuttle_duration,
                'arrival_time': arrival.strftime('%H:%M'),
                'is_shuttle_combo': True,
            })

    elif origin == 'yongin_campus' and destination == 'seoul_campus':
        combinations = [
            {
                'transit_origin': 'giheungstation',
                'shuttle_pk': 3,
                'label': '기흥역 통학버스 경유',
            },
        ]
        for combo in combinations:
            tp = TRANSFER_POINTS[combo['transit_origin']]

            # 1. 다음 셔틀 조회 (용인캠 → 환승거점)
            route = ShuttleRoute.objects.filter(
                pk=combo['shuttle_pk'], is_active=True
            ).first()
            if not route:
                continue

            next_shuttle = ShuttleSchedule.get_next_departure(
                route, departure_datetime.time(), day_type
            )
            if not next_shuttle:
                continue

            shuttle_duration = 15
            shuttle_dep = departure_datetime.replace(
                hour=next_shuttle.departure_time.hour,
                minute=next_shuttle.departure_time.minute,
                second=0,
            )
            shuttle_arrival = shuttle_dep + timedelta(minutes=shuttle_duration)

            # ✅ 셔틀 도착 시간을 기준으로 대중교통 검색
            shuttle_arrival_date = shuttle_arrival.strftime('%Y%m%d')
            shuttle_arrival_time = shuttle_arrival.strftime('%H%M')

            # 2. ODsay: 환승거점 → 서울캠
            transit = get_transit_routes(
                tp['lat'], tp['lng'],
                CAMPUS_COORDS['seoul_campus']['lat'],
                CAMPUS_COORDS['seoul_campus']['lng'],
                date=shuttle_arrival_date,  # ✅ 셔틀 도착 시간 기준
                time=shuttle_arrival_time,
            )
            if not transit or not transit.get('result', {}).get('path'):
                logger.warning(f'ODsay API 응답 없음: {combo["transit_origin"]} → 서울캠')
                continue

            best_path = transit['result']['path'][0]

            # API 응답 검증: subPath와 info 필드 확인
            if not best_path.get('subPath') or not best_path.get('info'):
                logger.warning(f'ODsay API 응답 불완전: subPath={bool(best_path.get("subPath"))}, info={bool(best_path.get("info"))}')
                continue

            # subPath 정제: 버스/지하철 번호 추출 및 분리
            bus_subpaths = []
            subway_subpaths = []

            for subpath in best_path.get('subPath', []):
                traffic_type = subpath.get('trafficType')

                # 버스(2) 또는 지하철(1)인 경우만 처리
                if traffic_type in [1, 2]:
                    refined_subpath = dict(subpath)

                    # lane: 배열 또는 단일 객체 모두 정규화
                    raw_lane = subpath.get('lane')
                    lane_list = raw_lane if isinstance(raw_lane, list) else ([raw_lane] if isinstance(raw_lane, dict) else [])
                    lane0 = lane_list[0] if lane_list else {}

                    # 버스인 경우: lane에서 번호 및 타입 추출
                    if traffic_type == 2:
                        if lane_list:
                            bus_nos = []
                            bus_type = None
                            for idx, lane in enumerate(lane_list):
                                bus_no = lane.get('busNo') or lane.get('name')
                                if bus_no:
                                    bus_nos.append(bus_no)
                                if idx == 0 and lane.get('type'):
                                    bus_type = lane.get('type')
                            if bus_nos:
                                refined_subpath['busNumbers'] = bus_nos
                                refined_subpath['name'] = bus_nos[0]
                            if bus_type:
                                refined_subpath['busType'] = bus_type
                        bus_subpaths.append(refined_subpath)

                    # 지하철인 경우: lane 정보가 있는 실제 노선만 포함
                    elif traffic_type == 1:
                        if lane0.get('name'):
                            refined_subpath = dict(subpath)
                            refined_subpath['name'] = lane0.get('name', '')
                            # subwaycode(소문자, ODsay 공식) / subwayCode(대문자) 모두 탐색
                            refined_subpath['subwayCode'] = lane0.get('subwaycode') or lane0.get('subwayCode')
                            subway_subpaths.append(refined_subpath)

            transit_minutes = best_path['info']['totalTime']
            total_minutes = int(
                (shuttle_dep - departure_datetime).total_seconds() / 60
            ) + shuttle_duration + transit_minutes

            arrival = shuttle_arrival + timedelta(minutes=transit_minutes)
            results.append({
                'label': combo['label'],
                'total_minutes': total_minutes,
                'direction': 'yongin_to_seoul',
                'shuttle_route_name': route.name,
                'shuttle_route_id': route.pk,
                'shuttle_departure': next_shuttle.departure_time.strftime('%H:%M'),
                'shuttle_duration': shuttle_duration,
                'transfer_point': tp['name'],
                'transfer_lat': tp['lat'],
                'transfer_lng': tp['lng'],
                'origin_lat': CAMPUS_COORDS[origin]['lat'],
                'origin_lng': CAMPUS_COORDS[origin]['lng'],
                'destination_lat': CAMPUS_COORDS['seoul_campus']['lat'],
                'destination_lng': CAMPUS_COORDS['seoul_campus']['lng'],
                'transit_segment': best_path,
                'bus_subpaths': bus_subpaths,
                'subway_subpaths': subway_subpaths,
                'transit_minutes': transit_minutes,
                'wait_minutes': 0,
                'arrival_time': arrival.strftime('%H:%M'),
                'is_shuttle_combo': True,
            })

    # 총 소요시간 기준 정렬
    results.sort(key=lambda x: x['total_minutes'])
    return results
