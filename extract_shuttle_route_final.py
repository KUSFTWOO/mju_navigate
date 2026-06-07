#!/usr/bin/env python
"""
기흥역 5번 출구 기반 셔틀버스 경로 추출 및 정리
- 기흥역 ↔ 명지대학교 자연과학캠퍼스만 유지
- 다른 셔틀 정류장 제거
"""
import requests
import json
import os

def load_env():
    env_file = '.env'
    if os.path.exists(env_file):
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

load_env()
KAKAO_API_KEY = os.getenv('KAKAO_API_KEY')

print("=" * 70)
print("기흥역 5번 출구 기반 셔틀 경로 추출 및 데이터 정리")
print("=" * 70)

# 기흥역 5번 출구 좌표
giheung_exit5_lat = 37.2746865309262
giheung_exit5_lng = 127.115683230713

# 명지대 자연과학캠퍼스 좌표
yongin_lat = 37.22310279940008
yongin_lng = 127.1868373866789

print(f"\n[경로 설정]")
print(f"출발: 기흥역 5번 출구 (lat={giheung_exit5_lat}, lng={giheung_exit5_lng})")
print(f"도착: 명지대학교 자연과학캠퍼스 (lat={yongin_lat}, lng={yongin_lng})")

# Kakao Navi API로 경로 추출
print("\n[진행중] Kakao Navi API 호출...")
navi_response = requests.post(
    'https://apis-navi.kakaomobility.com/v1/waypoints/directions',
    headers={'Authorization': f'KakaoAK {KAKAO_API_KEY}'},
    json={
        'origin': {'x': giheung_exit5_lng, 'y': giheung_exit5_lat},
        'destination': {'x': yongin_lng, 'y': yongin_lat}
    }
)

if navi_response.status_code == 200:
    navi_data = navi_response.json()

    if 'routes' in navi_data and navi_data['routes']:
        route = navi_data['routes'][0]

        # vertexes 추출
        coordinates = []

        if 'sections' in route:
            for section in route['sections']:
                if 'roads' in section:
                    for road in section['roads']:
                        if 'vertexes' in road:
                            vertexes = road['vertexes']
                            for i in range(0, len(vertexes), 2):
                                if i + 1 < len(vertexes):
                                    lng = vertexes[i]
                                    lat = vertexes[i + 1]
                                    coordinates.append({'lat': lat, 'lng': lng})

        print(f"✓ 추출된 좌표 포인트: {len(coordinates)}개")
        print(f"  첫 점: ({coordinates[0]['lat']:.6f}, {coordinates[0]['lng']:.6f})")
        print(f"  마지막 점: ({coordinates[-1]['lat']:.6f}, {coordinates[-1]['lng']:.6f})")

        if len(coordinates) > 0:
            # static/js/shuttleRoute.js 업데이트 (정리된 내용)
            print("\n[진행중] static/js/shuttleRoute.js 업데이트...")

            js_content = """// 셔틀버스 경로 좌표 (기흥역 5번 출구 ↔ 명지대학교 자연과학캠퍼스)
// Kakao Navi API로 추출한 """ + str(len(coordinates)) + """개 포인트

const SHUTTLE_GIHEUNG_TO_YONGIN = [
"""

            for coord in coordinates:
                js_content += f"  {{ lat: {coord['lat']}, lng: {coord['lng']} }},\n"

            js_content += """];

// 역방향 (용인 → 기흥역)
const SHUTTLE_YONGIN_TO_GIHEUNG = [...SHUTTLE_GIHEUNG_TO_YONGIN].reverse();

// 셔틀버스 색상
const SHUTTLE_ROUTE_COLOR = '#FF6B35';
"""

            with open('static/js/shuttleRoute.js', 'w', encoding='utf-8') as f:
                f.write(js_content)

            print(f"✓ 파일 업데이트 완료: static/js/shuttleRoute.js")

            # 최종 확인
            print("\n" + "=" * 70)
            print("✅ 최종 구성 확인")
            print("=" * 70)
            print(f"✓ 출발점: 기흥역 5번 출구")
            print(f"  ({coordinates[0]['lat']:.6f}, {coordinates[0]['lng']:.6f})")
            print(f"✓ 도착점: 명지대학교 자연과학캠퍼스")
            print(f"  ({coordinates[-1]['lat']:.6f}, {coordinates[-1]['lng']:.6f})")
            print(f"✓ 경로 포인트: {len(coordinates)}개")
            print(f"✓ 경유지: 없음 (직접 이동)")
            print(f"✓ 관련 정류장: 기흥역 5번 출구, 명지대 자연과학캠퍼스만 유지")
            print("=" * 70)

        else:
            print("✗ 경로 좌표를 추출할 수 없습니다")
    else:
        print(f"✗ Navi API 응답 오류")
else:
    print(f"✗ Navi API 오류: {navi_response.status_code}")
