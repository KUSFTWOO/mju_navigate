#!/usr/bin/env python
"""
Kakao Navi API를 사용해서 셔틀버스 실제 도로 경로 좌표 추출
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
print("셔틀버스 도로 경로 좌표 추출")
print("=" * 60)

# 1단계: 기흥역 좌표 검색 (지역명+지하철 검색)
print("\n[1단계] 기흥역 좌표 검색...")
print(f"API 키 확인: {KAKAO_API_KEY[:20]}...")
giheung_response = requests.get(
    'https://dapi.kakao.com/v2/local/search/keyword.json',
    headers={'Authorization': f'KakaoAK {KAKAO_API_KEY}'},
    params={'query': '기흥역'}
)

print(f"응답 상태: {giheung_response.status_code}")

if giheung_response.status_code == 200:
    giheung_data = giheung_response.json()
    print(f"응답 데이터: {json.dumps(giheung_data, ensure_ascii=False)[:200]}...")
    if giheung_data['documents']:
        doc = giheung_data['documents'][0]
        giheung_lat = float(doc['y'])
        giheung_lng = float(doc['x'])
        print(f"✓ 기흥역: ({giheung_lat}, {giheung_lng})")
        print(f"  주소: {doc['address_name']}")
    else:
        print("✗ 기흥역을 찾을 수 없습니다")
        print(f"전체 응답: {json.dumps(giheung_data, ensure_ascii=False)}")
        exit(1)
else:
    print(f"✗ API 오류: {giheung_response.status_code}")
    print(f"응답: {giheung_response.text}")
    exit(1)

# 2단계: 명지대학교 자연과학캠퍼스 좌표 검색
print("\n[2단계] 명지대학교 자연과학캠퍼스 좌표 검색...")
yongin_response = requests.get(
    'https://dapi.kakao.com/v2/local/search/keyword.json',
    headers={'Authorization': f'KakaoAK {KAKAO_API_KEY}'},
    params={'query': '명지대학교 자연과학캠퍼스'}
)

if yongin_response.status_code == 200:
    yongin_data = yongin_response.json()
    if yongin_data['documents']:
        doc = yongin_data['documents'][0]
        yongin_lat = float(doc['y'])
        yongin_lng = float(doc['x'])
        print(f"✓ 명지대 용인캠퍼스: ({yongin_lat}, {yongin_lng})")
        print(f"  주소: {doc['address_name']}")
    else:
        print("✗ 명지대 용인캠퍼스를 찾을 수 없습니다")
        exit(1)
else:
    print(f"✗ API 오류: {yongin_response.status_code}")
    exit(1)

# 3단계: Kakao Navi API로 경로 좌표 추출
print("\n[3단계] Kakao Navi API로 경로 추출...")
navi_response = requests.post(
    'https://apis-navi.kakaomobility.com/v1/waypoints/directions',
    headers={'Authorization': f'KakaoAK {KAKAO_API_KEY}'},
    json={
        'origin': {'x': giheung_lng, 'y': giheung_lat},
        'destination': {'x': yongin_lng, 'y': yongin_lat}
    }
)

if navi_response.status_code == 200:
    navi_data = navi_response.json()

    if 'routes' in navi_data and navi_data['routes']:
        route = navi_data['routes'][0]

        # vertexes 추출 (모든 sections의 roads의 vertexes)
        coordinates = []

        if 'sections' in route:
            for section in route['sections']:
                if 'roads' in section:
                    for road in section['roads']:
                        if 'vertexes' in road:
                            # vertexes는 [lng, lat, lng, lat, ...] 형태
                            vertexes = road['vertexes']
                            for i in range(0, len(vertexes), 2):
                                if i + 1 < len(vertexes):
                                    lng = vertexes[i]
                                    lat = vertexes[i + 1]
                                    coordinates.append({'lat': lat, 'lng': lng})

        print(f"✓ 추출된 좌표 포인트: {len(coordinates)}개")

        if len(coordinates) > 0:
            print(f"  첫 점: {coordinates[0]}")
            print(f"  마지막 점: {coordinates[-1]}")

            # 4단계: constants 파일 생성
            print("\n[4단계] constants/shuttleRoute.ts 파일 생성...")

            # constants 디렉토리 생성
            constants_dir = 'C:\\sw\\final\\static\\constants'
            os.makedirs(constants_dir, exist_ok=True)

            # TypeScript 파일 생성
            ts_content = f"""// 셔틀버스 실제 도로 경로 좌표
// 추출일시: {requests.post.__doc__ or 'API 추출'}
// 기흥역 → 명지대 자연과학캠퍼스 (단방향)

export const SHUTTLE_GIHEUNG_TO_YONGIN: {{ lat: number; lng: number }}[] = [
"""

            for coord in coordinates:
                ts_content += f"  {{ lat: {coord['lat']}, lng: {coord['lng']} }},\n"

            ts_content += """];

// 역방향 (용인 → 기흥)
export const SHUTTLE_YONGIN_TO_GIHEUNG = [...SHUTTLE_GIHEUNG_TO_YONGIN].reverse();

// 셔틀버스 색상
export const SHUTTLE_COLOR = '#FF6B35'; // 주황색 (임시)
"""

            ts_file_path = os.path.join(constants_dir, 'shuttleRoute.ts')
            with open(ts_file_path, 'w', encoding='utf-8') as f:
                f.write(ts_content)

            print(f"✓ 파일 생성: {ts_file_path}")
            print(f"  좌표 포인트: {len(coordinates)}개")

            # 5단계: 확인
            print("\n[5단계] 최종 확인")
            print("=" * 60)
            print(f"✓ 기흥역 좌표: lat={giheung_lat}, lng={giheung_lng}")
            print(f"✓ 명지대 좌표: lat={yongin_lat}, lng={yongin_lng}")
            print(f"✓ 경로 포인트: {len(coordinates)}개 추출 완료")
            print(f"✓ 파일 생성: constants/shuttleRoute.ts")
            print("=" * 60)

        else:
            print("✗ 경로 좌표를 추출할 수 없습니다")
    else:
        print(f"✗ Navi API 응답 오류: {json.dumps(navi_data, ensure_ascii=False, indent=2)}")
else:
    print(f"✗ Navi API 오류: {navi_response.status_code}")
    print(f"  응답: {navi_response.text}")
