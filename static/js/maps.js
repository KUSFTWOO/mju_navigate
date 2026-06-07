let map;
let campusMarkers = [];
window.currentPolylines = [];  // 경로 선택 후 방향 전환 시 초기화하기 위해 전역으로

// 기본 캠퍼스 정보 (Django context에서 받을 때까지 사용)
let CAMPUS_DATA = {
  seoul_campus: {
    name: '서울캠퍼스',
    building: '종합관',
    lat: null,
    lng: null,
    color: '#1B2A5E',
  },
  yongin_campus: {
    name: '용인캠퍼스',
    building: '학생회관',
    lat: null,
    lng: null,
    color: '#0057A8',
  },
};

// Django context에서 받은 좌표 데이터 업데이트
function updateCampusCoordinates(coordsJson) {
  try {
    const coords = JSON.parse(coordsJson);

    // 정확한 키 매핑
    if (coords.seoul_campus) {
      CAMPUS_DATA.seoul_campus.lat = coords.seoul_campus.lat;
      CAMPUS_DATA.seoul_campus.lng = coords.seoul_campus.lng;
      console.log('✓ 서울캠퍼스 좌표 업데이트:', coords.seoul_campus);
    }
    if (coords.yongin_campus) {
      CAMPUS_DATA.yongin_campus.lat = coords.yongin_campus.lat;
      CAMPUS_DATA.yongin_campus.lng = coords.yongin_campus.lng;
      console.log('✓ 용인캠퍼스 좌표 업데이트:', coords.yongin_campus);
    }

    console.log('✓ 캠퍼스 좌표 업데이트 완료:', CAMPUS_DATA);

    // 만약 지도가 이미 초기화되었다면, 마커 다시 그리기
    if (map) {
      addCampusMarkers();
    }
  } catch (e) {
    console.error('좌표 파싱 오류:', e);
  }
}

// 지도 초기화
function initializeMap() {
  const mapContainer = document.getElementById('map');
  if (!mapContainer) {
    console.error('지도 컨테이너를 찾을 수 없습니다');
    return;
  }

  // 출발지 기준으로 지도 중심 설정
  let centerLat = 37.45;
  let centerLng = 127;
  let useOriginAsCenter = false;

  // SessionStorage에서 선택된 출발지 조회
  const selectedOrigin = sessionStorage.getItem('selectedOrigin') || 'seoul_campus';
  console.log('선택된 출발지:', selectedOrigin);

  if (CAMPUS_DATA && CAMPUS_DATA[selectedOrigin]) {
    // 출발지 기준으로 지도 중심 설정
    const originData = CAMPUS_DATA[selectedOrigin];
    if (originData.lat && originData.lng) {
      centerLat = originData.lat;
      centerLng = originData.lng;
      useOriginAsCenter = true;
      console.log(`✓ 출발지 기준 지도 중심: ${originData.name} (${centerLat}, ${centerLng})`);
    }
  } else {
    console.warn('CAMPUS_DATA를 사용할 수 없습니다');
  }

  const mapOption = {
    center: new kakao.maps.LatLng(centerLat, centerLng),
    level: useOriginAsCenter ? 9 : 10,  // 출발지 중심이면 더 자세히 보이도록
  };

  map = new kakao.maps.Map(mapContainer, mapOption);
  console.log('✓ 지도 초기화 완료');

  // 캠퍼스 마커 표시 및 bounds 자동 조정
  addCampusMarkers();
  adjustMapBounds();
}

// 두 캠퍼스가 모두 보이도록 지도 범위 자동 조정
function adjustMapBounds() {
  if (!map || !CAMPUS_DATA) {
    console.warn('지도가 초기화되지 않았거나 CAMPUS_DATA가 없습니다');
    return;
  }

  const bounds = new kakao.maps.LatLngBounds();
  let hasValidCoords = false;

  for (const code in CAMPUS_DATA) {
    const campus = CAMPUS_DATA[code];
    if (campus.lat && campus.lng) {
      bounds.extend(new kakao.maps.LatLng(campus.lat, campus.lng));
      hasValidCoords = true;
    }
  }

  if (hasValidCoords) {
    map.setBounds(bounds, 100, 100, 100, 100);  // padding: 100px
    console.log('✓ 지도 범위 조정 완료 (두 캠퍼스 모두 표시)');
  }
}

// 캠퍼스 마커 추가
function addCampusMarkers() {
  if (!map) {
    console.warn('지도가 초기화되지 않았습니다');
    return;
  }

  if (!CAMPUS_DATA) {
    console.warn('CAMPUS_DATA가 아직 초기화되지 않았습니다');
    return;
  }

  // 기존 마커 제거
  campusMarkers.forEach(marker => marker.setMap(null));
  campusMarkers = [];

  // 새 마커 추가
  for (const code in CAMPUS_DATA) {
    const campus = CAMPUS_DATA[code];

    // 좌표가 없으면 스킵
    if (!campus.lat || !campus.lng) {
      console.warn(`${code}의 좌표가 없습니다`);
      continue;
    }

    const markerPosition = new kakao.maps.LatLng(campus.lat, campus.lng);

    const marker = new kakao.maps.Marker({
      position: markerPosition,
      title: campus.name,
    });

    marker.setMap(map);
    campusMarkers.push(marker);

    // 인포윈도우 (건물명 포함)
    const infoContent = `
      <div style="padding:8px;font-size:12px;text-align:center;">
        <strong>${campus.name}</strong><br/>
        <span style="color:#666;font-size:11px;">${campus.building}</span>
      </div>
    `;

    const infowindow = new kakao.maps.InfoWindow({
      content: infoContent,
    });

    infowindow.open(map, marker);

    // 마커 클릭 시 정보 표시
    kakao.maps.event.addListener(marker, 'click', () => {
      // 기존 인포윈도우 닫기
      document.querySelectorAll('.kakao-infowindow-close').forEach(btn => {
        if (btn.parentElement) {
          btn.click();
        }
      });
      infowindow.open(map, marker);
    });

    console.log(`✓ ${campus.name} 마커 추가: (${campus.lat}, ${campus.lng})`);
  }
}

// 지하철 호선별 공식 색상 (ODsay subwayCode 숫자 기준)
const SUBWAY_CODE_COLORS = {
  1:   '#0052A4',  // 1호선
  2:   '#00A84D',  // 2호선
  3:   '#EF7C1C',  // 3호선
  4:   '#00A5DE',  // 4호선
  5:   '#996CAC',  // 5호선
  6:   '#CD7C2F',  // 6호선
  7:   '#747F00',  // 7호선
  8:   '#E6186C',  // 8호선
  9:   '#BDB092',  // 9호선
  11:  '#F5A200',  // 수인분당선
  16:  '#D4003B',  // 신분당선
  12:  '#77C4A3',  // 경의중앙선
  13:  '#0065B3',  // 공항철도
  109: '#6EBF46',  // 에버라인(용인경전철)
  100: '#9A1B5A',  // GTX-A
};

// 노선 이름 포함 여부로 매핑 (subwayCode 없을 때 fallback)
const SUBWAY_NAME_COLORS = {
  '수인분당선': '#F5A200',
  '분당선':    '#F5A200',
  '신분당선':  '#D4003B',
  '경의중앙선': '#77C4A3',
  '공항철도':  '#0065B3',
  '에버라인':  '#6EBF46',
  '용인경전철': '#6EBF46',
  'GTX':      '#9A1B5A',
};

/**
 * ODsay lane 필드 정규화
 * - 배열: lane[0] 반환
 * - 단일 객체: 그대로 반환 (공식 가이드 예시 포맷)
 */
function normalizeLane(lane) {
  if (!lane) return null;
  if (Array.isArray(lane)) return lane.length > 0 ? lane[0] : null;
  if (typeof lane === 'object') return lane;
  return null;
}

/**
 * ODsay subwaycode 필드 취득
 * - 공식 필드명: subwaycode (소문자 c)
 * - 대소문자 혼용 응답 대비 fallback 포함
 */
function getSubwayCode(lane0) {
  if (!lane0) return null;
  return lane0.subwaycode ?? lane0.subwayCode ?? null;
}

function resolveSubwayColor(code, name) {
  if (code !== undefined && code !== null) {
    const c = SUBWAY_CODE_COLORS[parseInt(code)];
    if (c) return c;
  }
  if (name) {
    for (const key of Object.keys(SUBWAY_NAME_COLORS)) {
      if (name.includes(key)) return SUBWAY_NAME_COLORS[key];
    }
    // "2호선" 같이 첫 글자가 숫자인 경우
    const first = parseInt(name);
    if (!isNaN(first) && SUBWAY_CODE_COLORS[first]) return SUBWAY_CODE_COLORS[first];
  }
  return '#0052A4';
}

// 버스 번호별 명시적 색상 — ODsay type 없거나 알 수 없을 때 2단계 폴백
// 새 버스 추가 시 이 테이블에만 추가하면 됨
const BUS_NUMBER_COLORS = {
  '5000': '#E60026',  // 경기 직행좌석  — 빨강
  '5005': '#E60026',  // 경기 직행좌석  — 빨강
  '7021': '#53B332',  // 경기 일반버스  — 초록
};

// 버스 타입별 색상 — ODsay lane[0].type 정의 기준
// 서울(1~10) / 경기(11~) 지역 구분 반영
// ★ = 사용자 실측 확인값
const BUS_COLORS = {
  // ── 서울 버스 ──────────────────────────────────────
  '1':  '#0075C8',  // 간선버스            — 파랑
  '2':  '#53B332',  // 지선버스            — 초록
  '3':  '#F99D1C',  // 순환버스            — 노랑
  '4':  '#5BB025',  // 마을버스            — 연초록
  '5':  '#E60026',  // 직행좌석(빨간버스)  — 빨강 ★
  '6':  '#E60026',  // 광역버스(서울)      — 빨강
  '7':  '#53B332',  // 일반버스            — 초록 ★
  '8':  '#53B332',  // 경기버스(서울코드)  — 초록
  '9':  '#0052A4',  // 공항버스            — 남색
  '10': '#F99D1C',  // 투어버스            — 노랑
  // ── 경기·인천 버스 ──────────────────────────────────
  '11': '#E60026',  // 경기 직행좌석       — 빨강
  '12': '#0075C8',  // 경기 좌석버스       — 파랑
  '13': '#53B332',  // 경기 일반버스       — 초록
  '14': '#E60026',  // 경기 광역버스       — 빨강
  '15': '#5BB025',  // 따복버스(경기 마을) — 연초록
  '16': '#F99D1C',  // 경기 순환버스       — 노랑
  '21': '#E60026',  // 농어촌 직행좌석     — 빨강
  '22': '#0075C8',  // 농어촌 좌석         — 파랑
  '23': '#53B332',  // 농어촌 일반         — 초록
  '30': '#5BB025',  // 경기 마을버스       — 연초록
  // ── 고속·시외버스 ────────────────────────────────────
  '41': '#0052A4',  // 고속버스            — 남색
  '42': '#0052A4',  // 시외좌석            — 남색
  '43': '#0052A4',  // 시외일반            — 남색
};

// trafficType별 색상 및 스타일 결정
function getPolylineStyle(subpath) {
  const trafficType = subpath.trafficType;
  let strokeColor = '#666666';  // 기본색
  let strokeWeight = 4;
  let strokeStyle = 'solid';

  // ODsay lane: 배열 또는 단일 객체 모두 처리
  const lane0 = normalizeLane(subpath.lane);

  if (trafficType === 1) {
    // 지하철: RouteSelectView가 주입한 subwayCode/name 우선,
    // 없으면 공식 가이드 구조(lane = 단일 객체)에서 직접 추출
    const code = subpath.subwayCode      // RouteSelectView 주입
      ?? subpath.subwaycode              // 직접 주입(소문자)
      ?? getSubwayCode(lane0);           // raw lane 폴백
    const name = subpath.name            // RouteSelectView 주입
      || (lane0 ? lane0.name : '')       // raw lane 폴백
      || '';
    strokeColor = resolveSubwayColor(code, name);
    strokeWeight = 5;
    console.log(`🚇 지하철: code=${code}, name=${name} → ${strokeColor}`);

  } else if (trafficType === 2) {
    // ── 버스 색상 결정 단계 ──────────────────────────────
    // 1단계: 버스 종류 (ODsay lane[0].type → BUS_COLORS)  ← 가장 정확한 근거
    // 2단계: 버스 번호 (busNo → BUS_NUMBER_COLORS)         ← type 없을 때 보조
    // 3단계: fallback #1B2A5E

    // 버스 번호 후보 수집 (주입값 → raw lane → simplified_paths.lanes 순)
    const injectedNos = Array.isArray(subpath.busNumbers) ? subpath.busNumbers : [];
    const laneArr     = Array.isArray(subpath.lane)
      ? subpath.lane
      : (subpath.lane && typeof subpath.lane === 'object' ? [subpath.lane] : []);
    const rawLaneNos  = laneArr.map(l => String(l.busNo || l.name || '').trim()).filter(Boolean);
    const simplNos    = Array.isArray(subpath.lanes) ? subpath.lanes.map(String) : [];

    // 앞자리 숫자 추출 ('5005(거점.평일운행)' → '5005')
    const allRaw = [...new Set([...injectedNos, ...rawLaneNos, ...simplNos])];
    const busNos = [...new Set(allRaw.flatMap(no => {
      const stripped = no.replace(/번$/, '').trim();
      const leading  = no.match(/^(\d+)/);
      return [no, stripped, ...(leading ? [leading[1]] : [])];
    }))].filter(Boolean);

    // ── 색상 결정 단계 ──────────────────────────────────────
    // 1단계: 버스 번호 명시 (BUS_NUMBER_COLORS)
    //        ODsay type 오분류 보정용 — 최우선
    // 2단계: 버스 종류 (BUS_COLORS[lane[0].type])
    //        ODsay type이 정확할 때 사용
    // 3단계: fallback #1B2A5E

    // 1단계: 번호 명시 테이블 (ODsay 오분류 보정)
    let matchedByNo = null;
    for (const no of busNos) {
      if (BUS_NUMBER_COLORS[no]) { matchedByNo = BUS_NUMBER_COLORS[no]; break; }
    }

    if (matchedByNo) {
      strokeColor = matchedByNo;
      console.log(`🚌 [1단계-번호보정] no=${busNos[0]} → ${strokeColor}`);
    } else {
      // 2단계: 버스 종류 (ODsay lane[0].type)
      const busType = subpath.busType            // RouteSelectView 주입
        ?? (lane0 != null ? lane0.type : null);  // raw lane[0].type
      const typeColor = (busType != null) ? BUS_COLORS[String(busType)] : null;
      strokeColor = typeColor || '#1B2A5E';
      console.log(typeColor
        ? `🚌 [2단계-종류] type=${busType} → ${strokeColor}`
        : `🚌 [3단계-fallback] nos=[${busNos.join(',')}] → ${strokeColor}`);
    }
    strokeWeight = 4;

  } else if (trafficType === 3) {
    // 도보: 회색 점선
    strokeColor = '#9ca3af';
    strokeWeight = 2;
    strokeStyle = 'shortdot';
    console.log(`🚶 도보 색상: ${strokeColor} (점선)`);
  }

  return { strokeColor, strokeWeight, strokeStyle };
}

// 폴리라인 전체 제거
function clearPolylines() {
  if (window.currentPolylines) {
    window.currentPolylines.forEach(polyline => {
      polyline.setMap(null);
    });
    window.currentPolylines = [];
  }
  console.log('✓ 기존 폴리라인 제거 완료');
}

// 정류장 목록에서 좌표 배열 추출 (passStopList.stations)
// ODsay가 배열({[]}) 또는 객체({0:{}, 1:{}}) 형태로 반환하는 경우 모두 처리
function extractCoordinatesFromStations(stations) {
  if (!stations) return [];

  // 객체(숫자 키) 형태이면 배열로 변환
  const list = Array.isArray(stations) ? stations : Object.values(stations);
  if (list.length === 0) return [];

  try {
    const coordinates = [];
    list.forEach(station => {
      const lat = parseFloat(station.y);
      const lng = parseFloat(station.x);
      if (!isNaN(lat) && !isNaN(lng)) {
        coordinates.push(new kakao.maps.LatLng(lat, lng));
      }
    });
    return coordinates;
  } catch (e) {
    console.error('정류장 좌표 추출 오류:', e);
    return [];
  }
}

// 시작점과 끝점으로 간단한 경로 생성 (정류장 목록이 없을 때)
function createSimplePath(startX, startY, endX, endY) {
  const coordinates = [];

  if (startX && startY) {
    coordinates.push(new kakao.maps.LatLng(parseFloat(startY), parseFloat(startX)));
  }

  if (endX && endY) {
    coordinates.push(new kakao.maps.LatLng(parseFloat(endY), parseFloat(endX)));
  }

  return coordinates;
}

// 경로 그리기
/**
 * ODsay loadLane API 데이터로 카카오버스 기준 정밀 폴리라인 그리기
 *
 * - loadLane의 graphPos를 실제 도로 좌표로 사용
 * - loadLane의 lane[i].type으로 지하철 호선 색상 결정
 * - 버스 색상은 routeData.subPath와 인덱스 매핑으로 결정
 * - 도보(trafficType=3) 구간은 점선 처리
 * - 실패 시 drawRoute() 폴백
 *
 * 서울시 공식 버스 색상 기준 (news.seoul.go.kr/traffic/archives/1706):
 *   간선=Blue, 지선·마을=Green, 순환=Yellow, 광역·직행좌석=Red
 */
function drawRouteWithLoadLane(laneData, routeData) {
  if (!laneData || !laneData.result || !laneData.result.lane) {
    console.warn('loadLane 데이터 없음, drawRoute 폴백');
    drawRoute(routeData);
    return;
  }

  clearPolylines();
  const bounds = new kakao.maps.LatLngBounds();

  // 도보가 아닌 subPath (지하철·버스)만 추출 → loadLane lane과 순서 매핑
  const transitSubpaths = (routeData?.subPath || []).filter(
    sp => sp.trafficType === 1 || sp.trafficType === 2
  );

  // 도보 구간은 routeData.subPath에서 직접 처리
  (routeData?.subPath || []).forEach(sp => {
    if (sp.trafficType !== 3) return;
    const pts = extractCoordinatesFromStations(sp.passStopList?.stations)
      .concat(createSimplePath(sp.startX, sp.startY, sp.endX, sp.endY));
    const path = pts.slice(0, 2);  // 도보는 start→end 직선만
    if (path.length < 2) return;

    path.forEach(p => bounds.extend(p));
    const pl = new kakao.maps.Polyline({
      path,
      strokeWeight: 2,
      strokeColor: '#9ca3af',
      strokeOpacity: 0.7,
      strokeStyle: 'shortdot',
    });
    pl.setMap(map);
    window.currentPolylines.push(pl);
  });

  // loadLane의 각 lane → 정밀 좌표 + 색상
  laneData.result.lane.forEach((lane, laneIdx) => {
    // ── 색상 결정 ─────────────────────────────────────────────────────
    // 핵심: lane.type 숫자로 지하철/버스를 판단하면 안 됨
    //       (버스 type 코드가 지하철 호선 코드와 충돌 가능)
    // 올바른 판단: transitSubpath.trafficType (1=지하철, 2=버스) 기준
    let strokeColor = '#666666';
    let strokeWeight = 4;

    const matchedSp = transitSubpaths[laneIdx];

    if (matchedSp?.trafficType === 1) {
      // 지하철: lane.type = 호선 코드 → SUBWAY_CODE_COLORS
      strokeColor = SUBWAY_CODE_COLORS[lane.type]
        || resolveSubwayColor(matchedSp.subwayCode, matchedSp.name);
      strokeWeight = 5;
      console.log(`🚇 loadLane[${laneIdx}] 지하철: laneType=${lane.type} → ${strokeColor}`);

    } else if (matchedSp?.trafficType === 2) {
      // 버스: transitSubpath 기반 getPolylineStyle (BUS_NUMBER_COLORS → BUS_COLORS[type])
      const style = getPolylineStyle(matchedSp);
      strokeColor = style.strokeColor;
      strokeWeight = style.strokeWeight;
      console.log(`🚌 loadLane[${laneIdx}] 버스: → ${strokeColor}`);

    } else {
      // 매핑 실패 fallback
      console.warn(`⚠️ loadLane[${laneIdx}] 매칭 실패 (laneType=${lane.type})`);
    }

    // graphPos → 정밀 좌표 배열
    (lane.section || []).forEach(section => {
      const path = (section.graphPos || [])
        .map(p => new kakao.maps.LatLng(parseFloat(p.y), parseFloat(p.x)))
        .filter(p => !isNaN(p.getLat()) && !isNaN(p.getLng()));

      if (path.length < 2) return;
      path.forEach(p => bounds.extend(p));

      const pl = new kakao.maps.Polyline({
        path,
        strokeWeight,
        strokeColor,
        strokeOpacity: 0.9,
        strokeStyle: 'solid',
      });
      pl.setMap(map);
      window.currentPolylines.push(pl);
    });
  });

  // 지도 범위 조정 (boundary 우선, 없으면 bounds)
  try {
    const b = laneData.result.boundary;
    if (b && b.top && b.bottom && b.left && b.right) {
      const sw = new kakao.maps.LatLng(b.bottom, b.left);
      const ne = new kakao.maps.LatLng(b.top, b.right);
      map.setBounds(new kakao.maps.LatLngBounds(sw, ne), 80, 80, 80, 80);
    } else {
      map.setBounds(bounds, 100, 100, 100, 100);
    }
    console.log('✓ loadLane 경로 표시 완료');
  } catch(e) {
    console.error('bounds 조정 오류:', e);
  }
}

function drawRoute(routeData) {
  if (!routeData || !routeData.subPath) {
    console.warn('경로 데이터 없음');
    return;
  }

  console.log('경로 그리기 시작, subPath:', routeData.subPath.length);

  // 기존 폴리라인 제거
  clearPolylines();

  // 경로 그리기
  const bounds = new kakao.maps.LatLngBounds();
  let totalPolylines = 0;
  let lastEndPoint = null;  // 직전 서브패스의 끝점

  routeData.subPath.forEach((subpath, index) => {
    let polylinePoints = [];
    const trafficType = subpath.trafficType;
    let currentEndPoint = null;

    // trafficType별로 다르게 처리
    if (trafficType === 3) {
      // 도보: 직전 끝점에서 시작해야 함
      const startPoint = lastEndPoint ||
        createSimplePath(subpath.startX, subpath.startY, subpath.endX, subpath.endY)[0];

      if (subpath.startX && subpath.startY && subpath.endX && subpath.endY) {
        const endPoint = new kakao.maps.LatLng(parseFloat(subpath.endY), parseFloat(subpath.endX));
        polylinePoints = [startPoint, endPoint];
        currentEndPoint = endPoint;
      } else if (startPoint) {
        polylinePoints = [startPoint];
      }
    } else if (trafficType === 1 || trafficType === 2) {
      // 지하철/버스: stations(배열·객체 모두 처리) → startX/Y fallback
      polylinePoints = extractCoordinatesFromStations(subpath.passStopList?.stations);
      if (polylinePoints.length === 0) {
        polylinePoints = createSimplePath(
          subpath.startX, subpath.startY,
          subpath.endX,   subpath.endY
        );
      }
      currentEndPoint = polylinePoints[polylinePoints.length - 1] || null;
    }

    if (polylinePoints.length === 0) {
      // 좌표를 전혀 얻지 못해도 start/end 를 bounds 에 포함해 지도 범위 보정
      const sx = parseFloat(subpath.startX), sy = parseFloat(subpath.startY);
      const ex = parseFloat(subpath.endX),   ey = parseFloat(subpath.endY);
      if (!isNaN(sy) && !isNaN(sx)) bounds.extend(new kakao.maps.LatLng(sy, sx));
      if (!isNaN(ey) && !isNaN(ex)) bounds.extend(new kakao.maps.LatLng(ey, ex));
      console.debug(`subPath[${index}] 좌표 없음, bounds만 보정 (trafficType=${trafficType})`);
      return;
    }

    // 경로 포인트를 bounds에 추가
    polylinePoints.forEach(point => {
      bounds.extend(point);
    });

    // 색상 및 스타일 결정
    const style = getPolylineStyle(subpath);

    // Polyline 생성
    const polyline = new kakao.maps.Polyline({
      path: polylinePoints,
      strokeWeight: style.strokeWeight,
      strokeColor: style.strokeColor,
      strokeOpacity: 0.85,
      strokeStyle: style.strokeStyle,
    });

    polyline.setMap(map);
    window.currentPolylines.push(polyline);
    totalPolylines++;

    // 다음 서브패스를 위해 현재 끝점 저장
    lastEndPoint = currentEndPoint;

    console.log(`✓ 폴리라인[${index}]: trafficType=${trafficType}, 색상=${style.strokeColor}, 좌표=${polylinePoints.length}개`);
  });

  // 지도 범위 조정
  if (totalPolylines > 0) {
    // 캠퍼스 마커도 범위에 포함
    if (CAMPUS_DATA) {
      for (const code in CAMPUS_DATA) {
        const campus = CAMPUS_DATA[code];
        if (campus.lat && campus.lng) {
          bounds.extend(new kakao.maps.LatLng(campus.lat, campus.lng));
        }
      }
    }

    try {
      map.setBounds(bounds, 100, 100, 100, 100);
      console.log(`✓ 지도 범위 조정 완료 (${totalPolylines}개 폴리라인)`);
    } catch (e) {
      console.error('지도 범위 조정 오류:', e);
    }
  } else {
    console.warn('그릴 폴리라인 없음 - 경로 데이터가 없습니다');
  }
}

// Kakao Maps SDK 로드 대기
function waitForKakaoMaps(callback, maxAttempts = 100) {
  let attempts = 0;

  const check = () => {
    attempts++;

    if (typeof window.kakao !== 'undefined' &&
        window.kakao.maps &&
        typeof window.kakao.maps.LatLng === 'function') {
      console.log('✓ Kakao Maps SDK 로드 완료');
      callback();
    } else if (attempts < maxAttempts) {
      setTimeout(check, 100);
    } else {
      console.error('✗ Kakao Maps SDK 로드 실패');
    }
  };

  check();
}

// 페이지 로드 시 지도 초기화
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM 로드 완료, Kakao SDK 확인...');
    waitForKakaoMaps(initializeMap);
  });
} else {
  console.log('DOM 이미 로드됨, Kakao SDK 확인...');
  waitForKakaoMaps(initializeMap);
}

// 셔틀 조합 경로 그리기 (대중교통 + 셔틀)
function drawShuttleComboRoute(route) {
  if (!route) {
    console.warn('셔틀 조합 경로 데이터 없음');
    return;
  }

  console.log('셔틀 조합 경로 그리기:', route);

  // 데이터 검증
  if (!route.transit_segment || !route.transit_segment.subPath) {
    console.error('대중교통 구간 데이터 없음:', route);
    return;
  }

  if (!route.direction || !route.transfer_lat || !route.transfer_lng) {
    console.error('필수 경로 정보 부족:', route);
    return;
  }

  // 기존 폴리라인 제거
  clearPolylines();

  const bounds = new kakao.maps.LatLngBounds();
  let totalPolylines = 0;
  let lastEndPoint = null;

  // 방향에 따라 순서 결정
  if (route.direction === 'seoul_to_yongin') {
    // 서울→용인: 대중교통 먼저, 그 다음 셔틀
    console.log('방향: 서울→용인 (대중교통 → 셔틀)');

    // 1. 대중교통 구간 그리기
    let transitPolylines = 0;
    route.transit_segment.subPath.forEach((subpath, index) => {
      let polylinePoints = [];
      const trafficType = subpath.trafficType;

      if (trafficType === 1 || trafficType === 2) {
        const stations = subpath.passStopList?.stations;
        polylinePoints = extractCoordinatesFromStations(stations);
        if (polylinePoints.length === 0) {
          polylinePoints = createSimplePath(
            subpath.startX, subpath.startY,
            subpath.endX, subpath.endY
          );
        }
        lastEndPoint = polylinePoints[polylinePoints.length - 1] || null;
      } else if (trafficType === 3) {
        polylinePoints = createSimplePath(
          subpath.startX, subpath.startY,
          subpath.endX, subpath.endY
        );
        lastEndPoint = polylinePoints[polylinePoints.length - 1] || null;
      }

      if (polylinePoints.length > 0) {
        polylinePoints.forEach(point => bounds.extend(point));
        const style = getPolylineStyle(subpath);
        const polyline = new kakao.maps.Polyline({
          path: polylinePoints,
          strokeWeight: style.strokeWeight,
          strokeColor: style.strokeColor,
          strokeOpacity: 0.85,
          strokeStyle: style.strokeStyle,
        });
        polyline.setMap(map);
        window.currentPolylines.push(polyline);
        totalPolylines++;
        transitPolylines++;
        console.log(`✓ 대중교통 폴리라인[${index}]: trafficType=${trafficType}, color=${style.strokeColor}`);
      } else {
        console.warn(`⚠️ subPath[${index}] 좌표 없음 (trafficType=${trafficType}, startX=${subpath.startX})`);
      }
    });

    // 대중교통 폴리라인을 하나도 그리지 못한 경우: 출발지→환승거점 직선 fallback
    if (transitPolylines === 0 && route.origin_lat && route.origin_lng) {
      const originPt = new kakao.maps.LatLng(route.origin_lat, route.origin_lng);
      const xferPt   = new kakao.maps.LatLng(route.transfer_lat, route.transfer_lng);
      bounds.extend(originPt);
      const fallback = new kakao.maps.Polyline({
        path: [originPt, xferPt],
        strokeWeight: 4,
        strokeColor: '#666666',
        strokeOpacity: 0.6,
        strokeStyle: 'dashed',
      });
      fallback.setMap(map);
      window.currentPolylines.push(fallback);
      totalPolylines++;
      console.warn('⚠️ 대중교통 구간 fallback: 출발지→환승거점 직선');
    }

    // 2. 환승 거점 마커 추가
    const transferPoint = new kakao.maps.LatLng(route.transfer_lat, route.transfer_lng);
    bounds.extend(transferPoint);

    const transferMarker = new kakao.maps.Marker({
      position: transferPoint,
      title: route.transfer_point,
    });
    transferMarker.setMap(map);

    // 환승 거점 정보 윈도우
    const transferInfo = `
      <div style="padding:8px;font-size:12px;text-align:center;">
        <strong>${route.transfer_point}</strong><br/>
        <span style="color:#F59E0B;font-size:11px;">대기 ${route.wait_minutes}분</span>
      </div>
    `;
    const transferWindow = new kakao.maps.InfoWindow({
      content: transferInfo,
    });
    transferWindow.open(map, transferMarker);

    // 3. 셔틀 구간 그리기 (환승지점 → 도착 캠퍼스)
    // 실제 도로 경로 좌표 사용 (Kakao Navi API 추출)
    let shuttleCoords = [];

    if (typeof SHUTTLE_GIHEUNG_TO_YONGIN !== 'undefined' && SHUTTLE_GIHEUNG_TO_YONGIN.length > 0) {
      // 실제 도로 경로 사용
      shuttleCoords = SHUTTLE_GIHEUNG_TO_YONGIN.map(coord =>
        new kakao.maps.LatLng(coord.lat, coord.lng)
      );
      console.log(`✓ 셔틀 구간: 실제 도로 경로 (${shuttleCoords.length}개 포인트)`);
    } else {
      // 폴백: 직선 경로
      shuttleCoords = [
        new kakao.maps.LatLng(route.transfer_lat, route.transfer_lng),
        new kakao.maps.LatLng(route.destination_lat, route.destination_lng),
      ];
      console.warn('⚠️ 셔틀 구간: 직선 경로 (상수 로드 실패)');
    }

    // bounds에 모든 포인트 추가
    shuttleCoords.forEach(coord => bounds.extend(coord));

    const shuttlePolyline = new kakao.maps.Polyline({
      path: shuttleCoords,
      strokeWeight: 5,
      strokeColor: '#1B2A5E',
      strokeOpacity: 0.9,
      strokeStyle: 'solid',
    });
    shuttlePolyline.setMap(map);
    window.currentPolylines.push(shuttlePolyline);
    totalPolylines++;
    console.log('✓ 셔틀 폴리라인: #1B2A5E (실제 도로 경로)');

  } else if (route.direction === 'yongin_to_seoul') {
    // 용인→서울: 셔틀 먼저, 그 다음 대중교통
    console.log('방향: 용인→서울 (셔틀 → 대중교통)');

    // 1. 셔틀 구간 그리기 (출발 캠퍼스 → 환승지점)
    // 실제 도로 경로 좌표 사용 (Kakao Navi API 추출, 역방향)
    let shuttleCoords = [];

    if (typeof SHUTTLE_YONGIN_TO_GIHEUNG !== 'undefined' && SHUTTLE_YONGIN_TO_GIHEUNG.length > 0) {
      // 실제 도로 경로 사용 (역방향)
      shuttleCoords = SHUTTLE_YONGIN_TO_GIHEUNG.map(coord =>
        new kakao.maps.LatLng(coord.lat, coord.lng)
      );
      console.log(`✓ 셔틀 구간: 실제 도로 경로 역방향 (${shuttleCoords.length}개 포인트)`);
    } else {
      // 폴백: 직선 경로
      shuttleCoords = [
        new kakao.maps.LatLng(route.origin_lat, route.origin_lng),
        new kakao.maps.LatLng(route.transfer_lat, route.transfer_lng),
      ];
      console.warn('⚠️ 셔틀 구간: 직선 경로 (상수 로드 실패)');
    }

    // bounds에 모든 포인트 추가
    shuttleCoords.forEach(coord => bounds.extend(coord));

    const shuttlePolyline = new kakao.maps.Polyline({
      path: shuttleCoords,
      strokeWeight: 5,
      strokeColor: '#1B2A5E',
      strokeOpacity: 0.9,
      strokeStyle: 'solid',
    });
    shuttlePolyline.setMap(map);
    window.currentPolylines.push(shuttlePolyline);
    totalPolylines++;
    console.log('✓ 셔틀 폴리라인: #1B2A5E (실제 도로 경로 역방향)');

    // 2. 환승 거점 마커 추가
    const transferPoint = new kakao.maps.LatLng(route.transfer_lat, route.transfer_lng);

    const transferMarker = new kakao.maps.Marker({
      position: transferPoint,
      title: route.transfer_point,
    });
    transferMarker.setMap(map);

    // 환승 거점 정보 윈도우
    const transferInfo = `
      <div style="padding:8px;font-size:12px;text-align:center;">
        <strong>${route.transfer_point}</strong><br/>
        <span style="color:#F59E0B;font-size:11px;">환승 준비</span>
      </div>
    `;
    const transferWindow = new kakao.maps.InfoWindow({
      content: transferInfo,
    });
    transferWindow.open(map, transferMarker);

    // 3. 대중교통 구간 그리기
    let transitPolylines2 = 0;
    route.transit_segment.subPath.forEach((subpath, index) => {
      let polylinePoints = [];
      const trafficType = subpath.trafficType;

      if (trafficType === 1 || trafficType === 2) {
        const stations = subpath.passStopList?.stations;
        polylinePoints = extractCoordinatesFromStations(stations);
        if (polylinePoints.length === 0) {
          polylinePoints = createSimplePath(
            subpath.startX, subpath.startY,
            subpath.endX, subpath.endY
          );
        }
      } else if (trafficType === 3) {
        polylinePoints = createSimplePath(
          subpath.startX, subpath.startY,
          subpath.endX, subpath.endY
        );
      }

      if (polylinePoints.length > 0) {
        polylinePoints.forEach(point => bounds.extend(point));
        const style = getPolylineStyle(subpath);
        const polyline = new kakao.maps.Polyline({
          path: polylinePoints,
          strokeWeight: style.strokeWeight,
          strokeColor: style.strokeColor,
          strokeOpacity: 0.85,
          strokeStyle: style.strokeStyle,
        });
        polyline.setMap(map);
        window.currentPolylines.push(polyline);
        totalPolylines++;
        transitPolylines2++;
        console.log(`✓ 대중교통 폴리라인[${index}]: trafficType=${trafficType}, color=${style.strokeColor}`);
      } else {
        console.warn(`⚠️ subPath[${index}] 좌표 없음 (trafficType=${trafficType}, startX=${subpath.startX})`);
      }
    });

    // 대중교통 폴리라인을 하나도 그리지 못한 경우: 환승거점→도착지 직선 fallback
    if (transitPolylines2 === 0 && route.destination_lat && route.destination_lng) {
      const xferPt  = new kakao.maps.LatLng(route.transfer_lat, route.transfer_lng);
      const destPt  = new kakao.maps.LatLng(route.destination_lat, route.destination_lng);
      bounds.extend(destPt);
      const fallback = new kakao.maps.Polyline({
        path: [xferPt, destPt],
        strokeWeight: 4,
        strokeColor: '#666666',
        strokeOpacity: 0.6,
        strokeStyle: 'dashed',
      });
      fallback.setMap(map);
      window.currentPolylines.push(fallback);
      totalPolylines++;
      console.warn('⚠️ 대중교통 구간 fallback: 환승거점→도착지 직선');
    }

    bounds.extend(new kakao.maps.LatLng(route.destination_lat, route.destination_lng));
  }

  // 캠퍼스 마커 포함
  if (CAMPUS_DATA) {
    for (const code in CAMPUS_DATA) {
      const campus = CAMPUS_DATA[code];
      if (campus.lat && campus.lng) {
        bounds.extend(new kakao.maps.LatLng(campus.lat, campus.lng));
      }
    }
  }

  // 지도 범위 조정
  try {
    map.setBounds(bounds, 100, 100, 100, 100);
    console.log(`✓ 셔틀 조합 경로 지도 범위 조정 완료 (${totalPolylines}개 폴리라인)`);
  } catch (e) {
    console.error('지도 범위 조정 오류:', e);
  }
}

// 조합 경로 그리기 (대중교통 + 셔틀) - 하위호환성 유지
function drawCombinedRoute(route) {
  return drawShuttleComboRoute(route);
}

// window에 함수 노출
window.drawRoute = drawRoute;
window.drawRouteWithLoadLane = drawRouteWithLoadLane;
window.drawShuttleComboRoute = drawShuttleComboRoute;
window.drawCombinedRoute = drawCombinedRoute;
window.clearPolylines = clearPolylines;
window.addCampusMarkers = addCampusMarkers;
window.updateCampusCoordinates = updateCampusCoordinates;
