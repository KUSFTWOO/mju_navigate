// 서버에서 동적으로 좌표 로드
let CAMPUS_LOCATIONS = {
  seoul: {
    name: '서울캠퍼스',
    address: '서울특별시 서대문구 거북골로 34 종합관',
    building: '종합관',
    lat: 37.5712,
    lng: 126.9258,
  },
  yongin: {
    name: '용인캠퍼스',
    address: '경기도 용인시 처인구 명지로 116 학생회관',
    building: '학생회관',
    lat: 37.3391,
    lng: 127.0955,
  },
};

let map;
let markers = [];
let currentCampus = 'seoul';
let campusMarker = null;
let selectedInfoWindow = null;
let htmxListenerAdded = false;

// 템플릿에서 좌표 정보를 받아 업데이트
function loadCampusCoordinates(coordsJson) {
  try {
    const coords = JSON.parse(coordsJson);
    for (const campus in coords) {
      if (CAMPUS_LOCATIONS[campus]) {
        CAMPUS_LOCATIONS[campus].lat = coords[campus].lat;
        CAMPUS_LOCATIONS[campus].lng = coords[campus].lng;
      }
    }
    console.log('캠퍼스 좌표 업데이트:', CAMPUS_LOCATIONS);
  } catch (e) {
    console.error('좌표 파싱 오류:', e);
  }
}

function initializeMap() {
  const mapContainer = document.getElementById('restaurant-map');
  if (!mapContainer) return;

  const initialLocation = CAMPUS_LOCATIONS[currentCampus];
  const mapOption = {
    center: new kakao.maps.LatLng(initialLocation.lat, initialLocation.lng),
    level: 4,
  };

  map = new kakao.maps.Map(mapContainer, mapOption);

  // 캠퍼스 마커 표시
  campusMarker = new kakao.maps.Marker({
    position: new kakao.maps.LatLng(initialLocation.lat, initialLocation.lng),
    title: initialLocation.name,
  });
  campusMarker.setMap(map);

  // HTMX afterSwap 이벤트 한 번만 등록
  if (!htmxListenerAdded) {
    document.addEventListener('htmx:afterSwap', () => {
      console.log('HTMX afterSwap 이벤트 발생');
      updateMarkers();
    });
    htmxListenerAdded = true;
  }

  // 초기 로드
  setTimeout(() => {
    const alpineElement = document.querySelector('[x-data]');
    if (alpineElement && alpineElement.__x) {
      console.log('초기 음식점 로드 시작');
      alpineElement.__x.loadRestaurants();
    }
  }, 100);
}

function updateMarkers() {
  if (!map) return;

  console.log('updateMarkers 실행');

  // 기존 마커 제거 (캠퍼스 마커 제외)
  markers.forEach((marker) => marker.setMap(null));
  markers = [];

  // 새로운 마커 추가
  const restaurantCards = document.querySelectorAll('[data-restaurant-id]');
  console.log(`음식점 마커 ${restaurantCards.length}개 추가`);

  restaurantCards.forEach((card) => {
    const lat = parseFloat(card.dataset.lat);
    const lng = parseFloat(card.dataset.lng);
    const name = card.querySelector('h4').textContent.trim();

    const marker = new kakao.maps.Marker({
      position: new kakao.maps.LatLng(lat, lng),
      title: name,
    });

    marker.setMap(map);
    markers.push(marker);

    // 마커 클릭 시 선택
    kakao.maps.event.addListener(marker, 'click', () => {
      selectRestaurant(lat, lng, name);
    });
  });

  // 모든 마커가 보이도록 지도 범위 조정
  if (markers.length > 0) {
    const bounds = new kakao.maps.LatLngBounds();
    const location = CAMPUS_LOCATIONS[currentCampus];

    if (location) {
      bounds.extend(new kakao.maps.LatLng(location.lat, location.lng));
    }

    markers.forEach((marker) => {
      bounds.extend(marker.getPosition());
    });

    map.setBounds(bounds);
  }
}

// 음식점 선택 함수
function selectRestaurant(lat, lng, name) {
  if (!map) return;

  console.log(`음식점 선택: ${name} (${lat}, ${lng})`);

  // 기존 선택 인포윈도우 닫기
  if (selectedInfoWindow) {
    selectedInfoWindow.close();
  }

  // 지도 중심 이동 (확대 수준 높임)
  const restaurantLatLng = new kakao.maps.LatLng(lat, lng);
  map.setCenter(restaurantLatLng);
  map.setLevel(2); // 더 확대

  // 선택된 음식점 강조 표시
  selectedInfoWindow = new kakao.maps.InfoWindow({
    content: `
      <div style="padding:10px;font-size:13px;width:220px;text-align:center;">
        <strong>${name}</strong>
        <div style="color:#666;font-size:11px;margin-top:5px;">
          📍 선택됨
        </div>
      </div>
    `,
  });
  selectedInfoWindow.open(map, restaurantLatLng);

  // 선택된 음식점 카드 강조
  document.querySelectorAll('[data-restaurant-id]').forEach(card => {
    card.classList.remove('border-brand-500', 'shadow-lg', 'bg-brand-50');
  });

  // 정확한 좌표 매칭으로 카드 선택
  const cardLat = lat.toFixed(6);
  const cardLng = lng.toFixed(6);

  document.querySelectorAll('[data-restaurant-id]').forEach(card => {
    const cardDataLat = parseFloat(card.dataset.lat).toFixed(6);
    const cardDataLng = parseFloat(card.dataset.lng).toFixed(6);

    if (cardDataLat === cardLat && cardDataLng === cardLng) {
      card.classList.add('border-brand-500', 'shadow-lg', 'bg-brand-50');
      card.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  });
}

// 캠퍼스 선택 시 지도 업데이트
function selectCampusMap(campusCode) {
  if (!map) return;

  const location = CAMPUS_LOCATIONS[campusCode];
  if (!location) return;

  console.log(`캠퍼스 선택: ${location.name}`);

  // 현재 캠퍼스 업데이트
  currentCampus = campusCode;

  // 기존 선택 인포윈도우 닫기
  if (selectedInfoWindow) {
    selectedInfoWindow.close();
    selectedInfoWindow = null;
  }

  // 캠퍼스 마커 위치 업데이트
  if (campusMarker) {
    campusMarker.setPosition(new kakao.maps.LatLng(location.lat, location.lng));
  }

  // 지도 중심 이동
  const campusLatLng = new kakao.maps.LatLng(location.lat, location.lng);
  map.setCenter(campusLatLng);
  map.setLevel(4); // 캠퍼스 전체 보기 레벨

  // 캠퍼스 마커에 인포윈도우 표시
  if (campusMarker) {
    const infoWindow = new kakao.maps.InfoWindow({
      content: `<div style="padding:8px;font-size:12px;font-weight:bold;text-align:center;">${location.name}</div>`,
    });
    infoWindow.open(map, campusMarker);

    // 1.5초 후 자동 닫기
    setTimeout(() => {
      infoWindow.close();
    }, 1500);
  }

  // 음식점 카드 선택 해제
  document.querySelectorAll('[data-restaurant-id]').forEach(card => {
    card.classList.remove('border-brand-500', 'shadow-lg', 'bg-brand-50');
  });
}

// Kakao Maps SDK 로드 대기 함수
function waitForKakaoMaps(callback, maxAttempts = 100) {
  let attempts = 0;

  const check = () => {
    attempts++;
    console.log(`Kakao SDK 확인 시도 ${attempts}: window.kakao = ${typeof window.kakao}, maps = ${typeof window.kakao?.maps}`);

    if (typeof window.kakao !== 'undefined' &&
        window.kakao.maps &&
        typeof window.kakao.maps.LatLng === 'function') {
      console.log('✓ Kakao Maps SDK 로드 완료!');
      callback();
    } else if (attempts < maxAttempts) {
      setTimeout(check, 100);
    } else {
      console.error('✗ Kakao Maps SDK 로드 실패! KAKAO_JS_KEY를 확인하세요.');
      console.error('API 키 상태:', {
        scriptLoaded: !!document.querySelector('script[src*="dapi.kakao.com"]'),
        kakaoObject: typeof window.kakao,
        kakaoMaps: typeof window.kakao?.maps,
      });
    }
  };

  check();
}

// 좌표 로드 대기 후 지도 초기화
function initializeMapWhenReady() {
  // Kakao SDK와 좌표 모두 준비 확인
  if (typeof window.kakao !== 'undefined' &&
      window.kakao.maps &&
      typeof window.kakao.maps.LatLng === 'function' &&
      CAMPUS_LOCATIONS['seoul'].lat !== 37.5712) {
    // 좌표가 업데이트됨
    console.log('좌표 업데이트 확인:', CAMPUS_LOCATIONS);
    initializeMap();
  } else if (typeof window.kakao !== 'undefined' &&
             window.kakao.maps &&
             typeof window.kakao.maps.LatLng === 'function') {
    // Kakao SDK만 로드됨, 기본값으로 진행
    console.log('기본 좌표로 지도 초기화');
    initializeMap();
  } else {
    // 다시 확인
    setTimeout(initializeMapWhenReady, 100);
  }
}

// 페이지 로드 시 지도 초기화
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM 로드 완료, 지도 초기화 준비...');
    waitForKakaoMaps(initializeMapWhenReady);
  });
} else {
  console.log('DOM 이미 로드됨, 지도 초기화 준비...');
  waitForKakaoMaps(initializeMapWhenReady);
}
