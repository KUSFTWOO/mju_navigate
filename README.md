# MJU Navigate — 명지대 캠퍼스 통학 길찾기

> 명지대학교 서울캠퍼스 ↔ 용인캠퍼스 맞춤형 통학 경로 안내 서비스

---

## 비전

명지대 학생과 교직원이 두 캠퍼스를 오갈 때 **단 하나의 앱**으로 최적 경로를 찾을 수 있어야 한다.
일반 내비게이션이 모르는 **학교 셔틀버스 정보**를 대중교통과 결합해 진짜 빠른 경로를 제공하고,
캠퍼스 생활에 필요한 정보(학사일정, 주변 음식점)를 한 곳에서 해결한다.

---

## 핵심 기능

| 기능 | 설명 |
|---|---|
| 🗺️ 캠퍼스 길찾기 | 서울↔용인 대중교통 + 셔틀버스 조합 경로 안내 |
| 🚌 셔틀버스 안내 | 명지대역·기흥역 셔틀 시간표, 다음 출발 시각 |
| 📅 학사일정 | 서울캠·용인캠 캘린더 조회 |
| 🍜 주변 음식점 | 캠퍼스 반경 500m 음식점 지도·목록 |
| 👤 회원 기능 | 이메일 가입, 로그인, 프로필 관리 |
| ⚙️ 관리자 대시보드 | 셔틀 시간표·학사일정·회원 관리 |

---

## 기술 스택

```
Frontend      Django Templates + HTMX + Tailwind CSS
Backend       Django 5.x (Python 3.12+)
Database      Supabase (PostgreSQL)
Auth          django-allauth
Maps          Kakao Maps JavaScript SDK
Transit       ODsay API (한국 대중교통 전문)
Restaurants   Kakao Local API
Deployment    Railway / Render
```

### 왜 이 스택인가?

- **Django**: Python 기반으로 AI 코딩 도구와 궁합이 좋고, 관리자 대시보드가 내장되어 있다.
- **HTMX**: React 없이 동적 UI를 구현한다. 상태 관리 복잡도가 없고, Django 템플릿과 자연스럽게 통합된다.
- **Tailwind CSS**: 유틸리티 클래스로 빠른 스타일링. 디자인 일관성을 유지하기 쉽다.
- **Supabase**: PostgreSQL 기반 관리형 DB. 무료 티어가 충분하고, 나중에 Realtime 기능 확장이 가능하다.
- **ODsay API**: 국내 대중교통 전용 API. 경기광역버스, 에버라인, 수인분당선, 서울 지하철을 모두 커버한다.

---

## 프로젝트 구조

```
mju-navigate/
├── config/                  # Django 프로젝트 설정
│   ├── settings/
│   │   ├── base.py          # 공통 설정
│   │   ├── development.py   # 개발 환경
│   │   └── production.py    # 운영 환경
│   ├── urls.py
│   └── wsgi.py
│
├── apps/
│   ├── navigation/          # 길찾기 앱
│   │   ├── models.py        # ShuttleRoute, ShuttleSchedule
│   │   ├── views.py
│   │   ├── services.py      # ODsay API 호출 로직
│   │   ├── urls.py
│   │   └── templates/
│   │
│   ├── academic/            # 학사일정 앱
│   │   ├── models.py        # AcademicEvent
│   │   ├── views.py
│   │   └── templates/
│   │
│   ├── restaurants/         # 음식점 앱
│   │   ├── views.py         # Kakao Local API 호출
│   │   └── templates/
│   │
│   └── accounts/            # 회원 앱 (django-allauth)
│       ├── models.py        # UserProfile
│       ├── views.py
│       └── templates/
│
├── static/
│   ├── css/                 # Tailwind 빌드 결과
│   └── js/                  # HTMX, Kakao Maps 초기화
│
├── templates/
│   ├── base.html            # 전체 레이아웃
│   ├── components/          # 재사용 컴포넌트 (HTMX partial)
│   └── partials/            # HTMX 응답용 조각 템플릿
│
├── requirements/
│   ├── base.txt
│   ├── development.txt
│   └── production.txt
│
├── .env.example             # 환경변수 예시
├── manage.py
└── README.md
```

---

## 환경 변수

```env
# Django
DJANGO_SECRET_KEY=
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# Database (Supabase)
DATABASE_URL=postgresql://user:password@host:5432/dbname

# Kakao API
KAKAO_API_KEY=          # REST API 키
KAKAO_JS_KEY=           # JavaScript 키 (지도 렌더링)

# ODsay API
ODSAY_API_KEY=

# Email (학사일정 알림, 회원가입 인증)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
```

---

## 로컬 개발 시작

```bash
# 1. 저장소 클론
git clone https://github.com/your-org/mju-navigate.git
cd mju-navigate

# 2. 가상환경 생성 및 패키지 설치
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements/development.txt

# 3. 환경 변수 설정
cp .env.example .env
# .env 파일에 실제 값 입력

# 4. DB 마이그레이션
python manage.py migrate

# 5. 관리자 계정 생성
python manage.py createsuperuser

# 6. 개발 서버 실행
python manage.py runserver
```

Tailwind CSS 빌드 (별도 터미널):
```bash
npx tailwindcss -i ./static/css/input.css -o ./static/css/output.css --watch
```

---

## 현재 상태 (2026-06-07)

| 항목 | 상태 |
|---|---|
| 프로젝트 기획·설계 | ✅ 완료 |
| 기술 스택 확정 | ✅ 완료 |
| 문서 작성 (PRD, README 등) | ✅ 완료 |
| 프로젝트 초기 셋업 | 🔲 예정 |
| 회원 기능 구현 | 🔲 예정 |
| 관리자 대시보드 | 🔲 예정 |
| 길찾기 기능 | 🔲 예정 |
| 학사일정 | 🔲 예정 |
| 음식점 목록 | 🔲 예정 |
| 배포 | 🔲 예정 |

---

## 라이선스

MIT License — 명지대학교 학생/교직원 비상업적 사용 자유
