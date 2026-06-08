from django.views.generic import TemplateView, View
from django.shortcuts import render
from django.utils import timezone
from django.http import JsonResponse
from django.conf import settings
from django.core.cache import cache   # geocoding 캐시용 (services.py에서 사용)
import json
import logging
import urllib.parse
import requests as req_lib
from datetime import datetime
from .models import ShuttleRoute, ShuttleSchedule
from .services import get_transit_routes, CAMPUS_COORDS, get_coordinates_from_address, get_shuttle_options, get_day_type, get_combined_shuttle_routes

logger = logging.getLogger(__name__)


def get_shuttle_info(origin, destination):
    """셔틀버스 정보 조회"""
    try:
        now = datetime.now().time()
        weekday = timezone.now().weekday()

        # 요일별 day_type 결정
        if weekday < 5:  # 월-금
            day_type = 'weekday'
        elif weekday == 5:  # 토
            day_type = 'saturday'
        else:  # 일
            day_type = 'sunday'

        shuttle_list = []

        # 서울→용인 방향
        if origin == 'seoul_campus' and destination == 'yongin_campus':
            # 기흥역 통학버스 (pk=4)
            giheung_route = ShuttleRoute.objects.filter(
                origin='giheungstation',
                destination='yongin_campus',
                is_active=True
            ).first()

            if giheung_route:
                next_shuttle = ShuttleSchedule.get_next_departure(giheung_route, now, day_type)
                if next_shuttle:
                    shuttle_list.append({
                        'name': '기흥역 통학버스',
                        'from': '기흥역',
                        'to': '용인캠퍼스',
                        'depart_time': next_shuttle.departure_time.strftime('%H:%M'),
                        'icon': '🚌',
                    })

        # 용인→서울 방향
        elif origin == 'yongin_campus' and destination == 'seoul_campus':
            # 기흥역 통학버스 (pk=3 - 귀교 방향)
            giheung_return_route = ShuttleRoute.objects.filter(
                origin='yongin_campus',
                destination='giheungstation',
                is_active=True
            ).first()

            if giheung_return_route:
                next_shuttle = ShuttleSchedule.get_next_departure(giheung_return_route, now, day_type)
                if next_shuttle:
                    shuttle_list.append({
                        'name': '기흥역 귀교 버스',
                        'from': '용인캠퍼스',
                        'to': '기흥역',
                        'depart_time': next_shuttle.departure_time.strftime('%H:%M'),
                        'icon': '🚌',
                    })

        return shuttle_list if shuttle_list else None

    except Exception as e:
        logger.error(f'셔틀버스 정보 조회 오류: {str(e)}')
        return None


class NavigationView(TemplateView):
    template_name = 'navigation/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # 현재 시간 기반 타임카드 데이터
        try:
            now = datetime.now()
            now_time = now.time()
            day_type = get_day_type(now)

            # PK=4: 기흥역 → 용인캠퍼스
            giheung_to_yongin = ShuttleRoute.objects.filter(
                pk=4, is_active=True
            ).first()

            if giheung_to_yongin:
                next_giheung = ShuttleSchedule.get_next_departure(
                    giheung_to_yongin, now_time, day_type
                )
                context['next_giheung_shuttle'] = next_giheung

        except Exception as e:
            logger.warning(f'타임카드 조회 오류: {str(e)}')

        # 캠퍼스 좌표: services.py에 정밀 좌표가 이미 하드코딩되어 있음.
        # 매 요청마다 Kakao Geocoding API를 호출할 필요 없음 → 제거.
        context['campus_coords'] = CAMPUS_COORDS
        context['campus_coords_json'] = json.dumps(CAMPUS_COORDS)
        return context


class RouteSearchView(View):
    def get(self, request):
        origin = request.GET.get('origin')
        destination = request.GET.get('destination')
        departure_mode = request.GET.get('departure_mode', 'now')
        departure_time = request.GET.get('departure_time')
        tab = request.GET.get('tab', 'transit')  # 탭 선택: shuttle or transit

        logger.info(f'길찾기 요청: origin={origin}, destination={destination}, tab={tab}')

        if not origin or not destination:
            return render(request, 'navigation/partials/route_error.html', {
                'error': '출발지와 도착지를 선택하세요.'
            }, status=400)

        # 출발 시간 datetime 객체 준비
        departure_dt = datetime.now()
        if departure_mode == 'specified' and departure_time:
            try:
                departure_dt = datetime.fromisoformat(departure_time)
            except ValueError as e:
                logger.warning(f'출발 시간 파싱 오류: {e}')

        # 셔틀 포함 탭 처리 (대중교통 + 셔틀버스 조합 경로)
        if tab == 'shuttle':
            shuttle_routes = get_combined_shuttle_routes(origin, destination, departure_dt)

            # JSON 배열 직렬화 (onclick에서 JavaScript 변수로 안전하게 사용)
            shuttle_routes_json = json.dumps(
                shuttle_routes,
                ensure_ascii=False,
                default=str
            )

            context = {
                'shuttle_routes': shuttle_routes,
                'shuttle_routes_json': shuttle_routes_json,
                'origin': origin,
                'destination': destination,
                'origin_name': CAMPUS_COORDS[origin]['name'],
                'destination_name': CAMPUS_COORDS[destination]['name'],
            }
            logger.info(f'셔틀버스 포함 경로 조회: {origin} → {destination}, {len(shuttle_routes)}개')
            return render(request, 'navigation/partials/shuttle_results.html', context)

        # 캠퍼스 좌표 가져오기
        origin_coords = CAMPUS_COORDS.get(origin)
        dest_coords = CAMPUS_COORDS.get(destination)

        if not origin_coords or not dest_coords:
            return render(request, 'navigation/partials/route_error.html', {
                'error': '유효하지 않은 캠퍼스입니다.'
            }, status=400)

        logger.info(f'출발지 좌표: {origin_coords}, 도착지 좌표: {dest_coords}')

        # 출발 시간 파라미터 준비
        api_date = None
        api_time = None

        if departure_mode == 'specified' and departure_time:
            try:
                # datetime-local 형식: "2026-06-07T14:30"
                dt_obj = datetime.fromisoformat(departure_time)
                api_date = dt_obj.strftime('%Y%m%d')
                api_time = dt_obj.strftime('%H%M')
                logger.info(f'출발 시간 지정: {api_date} {api_time}')
            except ValueError as e:
                logger.warning(f'출발 시간 파싱 오류: {e}')

        # ODsay API 호출
        routes = get_transit_routes(
            origin_coords['lat'],
            origin_coords['lng'],
            dest_coords['lat'],
            dest_coords['lng'],
            date=api_date,
            time=api_time
        )

        if not routes:
            logger.error('ODsay API 응답 실패')
            return render(request, 'navigation/partials/route_error.html', {
                'error': 'API 키가 설정되지 않았거나 경로를 찾을 수 없습니다.'
            }, status=400)

        logger.info(f'ODsay API 응답 성공, 경로 개수: {len(routes.get("result", {}).get("path", []))}')

        # 경로 파싱
        try:
            all_paths = routes.get('result', {}).get('path', [])
            logger.info(f'ODsay 반환 경로: {len(all_paths)}개')

            # 상위 5개 경로만 사용 (응답 크기 최적화)
            paths = all_paths[:5]
            logger.info(f'최종 경로 데이터: {len(paths)}개 경로')

            try:
                # ─────────────────────────────────────────────────────────
                # 경로 데이터를 DB 세션에 저장.
                # locmem 캐시는 gunicorn 워커별로 독립되어
                # 멀티워커 환경(Render)에서 다른 워커가 조회 시 None 반환.
                # DB 세션은 모든 워커가 공유하므로 안전함.
                # ─────────────────────────────────────────────────────────
                request.session['cached_routes'] = paths
                request.session['route_origin'] = origin
                request.session['route_destination'] = destination
                logger.info(f'경로 데이터 세션 저장 완료: {origin}→{destination}, {len(paths)}개')
            except Exception as session_error:
                logger.error(f'세션 저장 오류: {str(session_error)}')
                raise

            simplified_paths = []
            for idx, path in enumerate(paths):
                # 상세 경로 정보 추출 (처음 4개 subPath만)
                detailed_subpaths = []
                for sub_idx, subpath in enumerate(path.get('subPath', [])):
                    if sub_idx >= 4:  # 처음 4개만 표시
                        break

                    # lane: 배열 또는 단일 객체 모두 정규화
                    raw_lane = subpath.get('lane')
                    lane_list = raw_lane if isinstance(raw_lane, list) else ([raw_lane] if isinstance(raw_lane, dict) else [])
                    lane0 = lane_list[0] if lane_list else {}

                    # lane에서 필요한 정보 추출
                    lanes_info = []
                    bus_type = None
                    for idx, lane in enumerate(lane_list):
                        lane_name = lane.get('busNo') or lane.get('name') or ''
                        if lane_name:
                            lanes_info.append(lane_name)
                        if idx == 0 and lane.get('type'):
                            bus_type = lane.get('type')

                    # trafficType 및 추가 정보
                    traffic_type = subpath.get('trafficType')
                    start_name = subpath.get('startName', '')
                    end_name = subpath.get('endName', '')

                    if not start_name or not end_name:
                        start_name = start_name or '시작'
                        end_name = end_name or '종료'

                    subpath_data = {
                        'trafficType': traffic_type,
                        'lanes': lanes_info,
                        'startName': start_name,
                        'endName': end_name,
                        'distance': subpath.get('distance'),
                        'sectionTime': subpath.get('sectionTime'),
                    }

                    # 지하철: subwaycode(소문자, ODsay 공식) / subwayCode(대문자) 모두 탐색
                    if traffic_type == 1:
                        if lane0:
                            subpath_data['subwayCode'] = lane0.get('subwaycode') or lane0.get('subwayCode') or ''
                            subpath_data['name'] = lane0.get('name', '')
                        subpath_data['stationCount'] = subpath.get('stationCount', 0)

                    # 버스인 경우 타입 추가
                    if traffic_type == 2 and bus_type:
                        subpath_data['busType'] = bus_type

                    detailed_subpaths.append(subpath_data)

                # ODsay 응답에서 추가 정보 추출
                info = path.get('info', {})
                total_walk = info.get('totalWalk', 0)
                bus_transit_count = info.get('busTransitCount', 0)
                subway_transit_count = info.get('subwayTransitCount', 0)

                simplified = {
                    'index': idx,  # 경로 인덱스
                    'pathType': path.get('pathType'),  # 1=버스, 2=지하철, 3=혼합
                    'totalTime': info.get('totalTime'),  # 전체 소요시간
                    'fare': info.get('payment'),  # 요금
                    'totalWalk': total_walk,  # 총 도보 거리 (미터)
                    'busTransitCount': bus_transit_count,  # 버스 환승 횟수
                    'subwayTransitCount': subway_transit_count,  # 지하철 환승 횟수
                    'subPath': detailed_subpaths,  # 상세 경로 정보
                }
                simplified_paths.append(simplified)

            # 셔틀버스 정보 추가
            shuttle_info = get_shuttle_info(origin, destination)

            context = {
                'routes': simplified_paths,
                'shuttle_info': shuttle_info,
            }
            logger.info(f'최종 응답: {len(simplified_paths)}개 경로 + 셔틀정보')
            return render(request, 'navigation/partials/route_results.html', context)
        except Exception as e:
            logger.exception(f'경로 파싱 오류')  # 전체 스택 트레이스 기록
            logger.error(f'오류 메시지: {str(e)}')
            return render(request, 'navigation/partials/route_error.html', {
                'error': f'경로 정보를 처리하는 중 오류가 발생했습니다: {str(e)}'
            }, status=400)


class RouteSelectView(View):
    """경로 선택 시 상세 정보(pathCoords 포함) 반환"""
    def get(self, request):
        route_index = request.GET.get('index')

        if route_index is None:
            return JsonResponse({'error': '경로 인덱스가 필요합니다'}, status=400)

        try:
            route_index = int(route_index)

            # 세션에서 경로 데이터 조회 (DB 세션 — 멀티워커 안전)
            routes = request.session.get('cached_routes')
            if not routes:
                logger.error('세션에 경로 데이터 없음')
                return JsonResponse({'error': '경로 데이터를 찾을 수 없습니다. 다시 검색해주세요.'}, status=400)

            if route_index < 0 or route_index >= len(routes):
                logger.error(f'경로 인덱스 범위 초과: {route_index}, 저장된 경로 수: {len(routes)}')
                return JsonResponse({'error': '유효하지 않은 경로 인덱스입니다'}, status=400)

            selected_route = routes[route_index]
            logger.info(f'경로 선택: index={route_index}')

            # ODsay 공식 가이드 구조 기반으로 표준 필드 주입
            # (lab.odsay.com/guide/guide 응답 예시 기준)
            # - 지하철(trafficType=1): lane = 단일 객체 { name, subwaycode }
            # - 버스(trafficType=2):   lane = 배열    [{ busNo, type }]
            for subpath in selected_route.get('subPath', []):
                traffic_type = subpath.get('trafficType')
                raw_lane = subpath.get('lane')

                # lane 정규화: 단일 객체 → 리스트, 배열 → 그대로
                if isinstance(raw_lane, dict):
                    lane_list = [raw_lane]
                elif isinstance(raw_lane, list):
                    lane_list = raw_lane
                else:
                    lane_list = []
                lane0 = lane_list[0] if lane_list else {}

                if traffic_type == 1:  # 지하철: lane이 단일 객체
                    subpath.setdefault('subwayCode',
                        lane0.get('subwaycode') or lane0.get('subwayCode'))
                    subpath.setdefault('name', lane0.get('name', ''))

                elif traffic_type == 2:  # 버스: lane이 배열
                    subpath.setdefault('busType', lane0.get('type'))
                    bus_numbers = [
                        l.get('busNo') or l.get('name', '')
                        for l in lane_list
                        if l.get('busNo') or l.get('name')
                    ]
                    subpath.setdefault('busNumbers', bus_numbers)

            # pathCoords 확인
            has_path_coords = False
            for subpath in selected_route.get('subPath', []):
                if subpath.get('pathCoords'):
                    has_path_coords = True
                    break
            logger.debug(f'선택된 경로 데이터: pathType={selected_route.get("pathType")}, subPath={len(selected_route.get("subPath", []))}, pathCoords={has_path_coords}')

            # JSON 응답
            return JsonResponse(selected_route, safe=True)

        except (ValueError, TypeError) as e:
            logger.error(f'경로 선택 오류: {str(e)}')
            return JsonResponse({'error': '요청 처리 중 오류가 발생했습니다'}, status=400)


class LoadLaneView(View):
    """ODsay loadLane API proxy — mapObj로 정밀 그래픽 좌표 반환"""
    def get(self, request):
        route_index = request.GET.get('index')
        if route_index is None:
            return JsonResponse({'error': 'index 필요'}, status=400)

        try:
            route_index = int(route_index)
            # 세션에서 경로 데이터 조회 (DB 세션 — 멀티워커 안전)
            routes = request.session.get('cached_routes')
            if not routes:
                return JsonResponse({'error': '경로 데이터를 찾을 수 없습니다. 다시 검색해주세요.'}, status=400)

            if route_index < 0 or route_index >= len(routes):
                return JsonResponse({'error': '인덱스 범위 초과'}, status=400)

            map_obj = routes[route_index].get('info', {}).get('mapObj', '')
            if not map_obj:
                return JsonResponse({'error': 'mapObj 없음'}, status=400)

            encoded_key = urllib.parse.quote(settings.ODSAY_API_KEY)
            url = (
                f'https://api.odsay.com/v1/api/loadLane'
                f'?mapObject=0:0@{map_obj}&apiKey={encoded_key}'
            )

            resp = req_lib.get(url, timeout=8)
            resp.raise_for_status()
            return JsonResponse(resp.json(), safe=False)

        except Exception as e:
            logger.error(f'loadLane 오류: {e}')
            return JsonResponse({'error': str(e)}, status=500)


class ShuttleView(View):
    def get(self, request):
        route_id = request.GET.get('route_id')
        day_type = request.GET.get('day_type', 'weekday')

        if not route_id:
            return render(request, 'navigation/partials/route_error.html', {
                'error': '노선을 선택하세요.'
            }, status=400)

        try:
            route = ShuttleRoute.objects.get(id=route_id, is_active=True)
        except ShuttleRoute.DoesNotExist:
            return render(request, 'navigation/partials/route_error.html', {
                'error': '해당 노선을 찾을 수 없습니다.'
            }, status=404)

        schedules = ShuttleSchedule.objects.filter(
            route=route,
            day_type=day_type,
            is_active=True
        ).order_by('departure_time')

        now = datetime.now().time()
        next_shuttle = ShuttleSchedule.get_next_departure(route, now, day_type)

        context = {
            'route': route,
            'schedules': schedules,
            'next_shuttle': next_shuttle,
            'day_type': day_type,
        }

        return render(request, 'navigation/partials/shuttle_schedule.html', context)


class ShuttleTimetableView(View):
    """셔틀버스 시간표 조회"""
    def get(self, request):
        route_pk = request.GET.get('route_pk', '2')
        day_type = request.GET.get('day_type', 'weekday')

        try:
            route = ShuttleRoute.objects.get(pk=route_pk, is_active=True)
        except ShuttleRoute.DoesNotExist:
            return render(request, 'navigation/partials/route_error.html', {
                'error': '해당 노선을 찾을 수 없습니다.'
            }, status=404)

        schedules = ShuttleSchedule.objects.filter(
            route=route,
            day_type=day_type,
            is_active=True
        ).order_by('departure_time')

        now = datetime.now().time()
        next_shuttle = ShuttleSchedule.get_next_departure(route, now, day_type)

        # 모든 노선 조회 (탭에서 선택용)
        all_routes = ShuttleRoute.objects.filter(is_active=True).order_by('name')

        context = {
            'route': route,
            'schedules': schedules,
            'all_routes': all_routes,
            'day_type': day_type,
            'now': now,
            'next_shuttle': next_shuttle,
            'next_departure': next_shuttle.departure_time if next_shuttle else None,
        }

        return render(request, 'navigation/partials/shuttle_timetable.html', context)
