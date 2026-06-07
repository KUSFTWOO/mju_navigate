#!/usr/bin/env python
"""
기흥역 4번 출구 좌표로 셔틀버스 도로 경로 재추출
"""
import requests
import json
import os

# .env 파일에서 환경변수 로드
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

print("=" * 60)
print("기흥역 4번 출구 기반 셔틀 경로 재추출")
print("=" * 60)

# 기흥역 4번 출구 좌표 (새로 검색한 좌표)
giheung_exit4_lat = 37.27473106382641
giheung_exit4_lng = 127.116213231901

# 명지대 자연과학캠퍼스 좌표 (동일)
yongin_lat = 37.22310279940008
yongin_lng = 127.1868373866789

print(f"\n출발: 기흥역 4번 출구 (lat={giheung_exit4_lat}, lng={giheung_exit4_lng})")
print(f"도착: 명지대 자연과학캠퍼스 (lat={yongin_lat}, lng={yongin_lng})")

# Kakao Navi API로 경로 추출
print("\n[진행중] Kakao Navi API 호출...")
navi_response = requests.post(
    'https://apis-navi.kakaomobility.com/v1/waypoints/directions',
    headers={'Authorization': f'KakaoAK {KAKAO_API_KEY}'},
    json={
        'origin': {'x': giheung_exit4_lng, 'y': giheung_exit4_lat},
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

        if len(coordinates) > 0:
            print(f"  첫 점: ({coordinates[0]['lat']:.6f}, {coordinates[0]['lng']:.6f})")
            print(f"  마지막 점: ({coordinates[-1]['lat']:.6f}, {coordinates[-1]['lng']:.6f})")

            # constants/shuttleRoute.ts 업데이트
            print("\n[진행중] static/js/shuttleRoute.js 업데이트...")

            js_content = """// 셔틀버스 실제 도로 경로 좌표 (기흥역 4번 출구 기준)
// 기흥역 → 명지대 자연과학캠퍼스 (단방향)
// Kakao Navi API로 추출한 """ + str(len(coordinates)) + """개 포인트

const SHUTTLE_GIHEUNG_TO_YONGIN = [
"""

            for coord in coordinates:
                js_content += f"  {{ lat: {coord['lat']}, lng: {coord['lng']} }},\n"

            js_content += """];

// 역방향 (용인 → 기흥)
const SHUTTLE_YONGIN_TO_GIHEUNG = [...SHUTTLE_GIHEUNG_TO_YONGIN].reverse();

// 셔틀버스 색상
const SHUTTLE_ROUTE_COLOR = '#FF6B35'; // 주황색 (임시)
"""

            js_file_path = 'static/js/shuttleRoute.js'
            with open(js_file_path, 'w', encoding='utf-8') as f:
                f.write(js_content)

            print(f"✓ 파일 업데이트 완료: {js_file_path}")

            # 최종 확인
            print("\n" + "=" * 60)
            print("✅ 최종 확인")
            print("=" * 60)
            print(f"✓ 출발점: 기흥역 4번 출구")
            print(f"  ({coordinates[0]['lat']:.6f}, {coordinates[0]['lng']:.6f})")
            print(f"✓ 도착점: 명지대 자연과학캠퍼스")
            print(f"  ({coordinates[-1]['lat']:.6f}, {coordinates[-1]['lng']:.6f})")
            print(f"✓ 경로 포인트: {len(coordinates)}개")
            print("=" * 60)

        else:
            print("✗ 경로 좌표를 추출할 수 없습니다")
    else:
        print(f"✗ Navi API 응답 오류: {json.dumps(navi_data, ensure_ascii=False, indent=2)}")
else:
    print(f"✗ Navi API 오류: {navi_response.status_code}")
    print(f"  응답: {navi_response.text}")
