#!/usr/bin/env python
"""
기흥역 5번 출구 좌표 검색
"""
import requests
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

print("=" * 60)
print("기흥역 5번 출구 좌표 검색")
print("=" * 60)

search_queries = ["기흥역 5번 출구", "기흥역 5번출구"]

for query in search_queries:
    print(f"\n검색: {query}")
    response = requests.get(
        'https://dapi.kakao.com/v2/local/search/keyword.json',
        headers={'Authorization': f'KakaoAK {KAKAO_API_KEY}'},
        params={'query': query}
    )

    if response.status_code == 200:
        data = response.json()
        if data['documents']:
            for doc in data['documents'][:2]:
                lat = float(doc['y'])
                lng = float(doc['x'])
                place_name = doc.get('place_name', '')
                address = doc.get('address_name', '')
                print(f"✓ {place_name}")
                print(f"  좌표: lat={lat}, lng={lng}")
                print(f"  주소: {address}")
            break

print("\n" + "=" * 60)
print("참고: 4번 출구 좌표")
print("=" * 60)
print(f"lat=37.27473106382641, lng=127.116213231901")
