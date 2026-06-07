# MJU Navigate — 프로젝트 시작 프롬프트
> Claude Code / Cursor 등 AI 코딩 도구에 붙여넣어 사용한다.

---

## 1단계 · 문서 읽기 (필수)

작업을 시작하기 전에 아래 문서들을 **반드시 순서대로** 읽자.

1. `@docs/PRD.md`   — 프로젝트 요구사항 및 기능 우선순위
2. `@docs/README.md` — 프로젝트 비전, 스택, 폴더 구조
3. `@docs/TCD.md`   — 기술 컨텍스트 (Django 철학, API 연동 방식)
4. `@docs/DP.md`    — 디자인 원칙 (Pantone 2768 C / 300 C 컬러 시스템)
5. `@docs/CBP.md`   — 코딩 표준 및 TDD 워크플로우
6. `@docs/DD.md`    — 데이터베이스 스키마 및 Django 모델 설계

이전에 구현한 작업들을 메모리에 기억시키고 업무를 시작하자.
분석이 완벽하게 끝나면 아래 작업을 시작해.

---

## 2단계 · 프로젝트 개요

- **프로젝트명**: MJU Navigate (명지대학교 캠퍼스 통학 길찾기)
- **목적**: 서울캠퍼스 ↔ 용인캠퍼스 맞춤 통학 경로 안내 + 셔틀버스 시간표 + 학사일정 + 주변 음식점 + 회원 기능
- **Django 버전**: 5.2.x LTS
- **Python 버전**: 3.12+

---

## 3단계 · Django 앱 목록

아래 **5개 앱**을 생성하고 `settings.py`에 등록한다.

```
accounts        # 회원가입·로그인·프로필 (django-allauth 기반)
navigation      # 길찾기·셔틀버스 시간표 (ODsay API + Kakao Maps)
academic        # 학사일정 캘린더 (관리자 직접 등록)
restaurants     # 주변 음식점 (Kakao Local API)
admin_dashboard # 관리자 커스텀 대시보드 (Django Admin 확장)
```

> ⚠️ notices, posts, polls, surveys, django-mptt 는 이 프로젝트 범위 밖이다. 추가하지 않는다.

---

## 4단계 · requirements.txt

Django 5.2.x LTS와 호환성이 검증된 패키지만 추가한다.

### `requirements/base.txt`
```
django>=5.2,<5.3

# 인증
django-allauth>=0.63.0

# 환경변수 (API 키 보안 관리)
django-environ>=0.11.0

# HTMX 서버 사이드 인터랙션
django-htmx>=1.17.0

# 폼 스타일링 (Tailwind 팩)
django-crispy-forms>=2.3.0
crispy-tailwind>=1.0.0

# 이미지 처리
Pillow>=10.0.0

# 외부 API 호출 (ODsay, Kakao)
requests>=2.31.0

# PostgreSQL 드라이버 (Supabase 운영 환경)
psycopg2-binary>=2.9.0

# 정적 파일 서빙
whitenoise>=6.6.0

# 운영 WSGI 서버
gunicorn>=21.0.0
```

### `requirements/development.txt`
```
-r base.txt

# 테스트
pytest-django>=4.8.0
factory-boy>=3.3.0
responses>=0.25.0      # 외부 API 모킹
freezegun>=1.4.0       # 시간 고정 (셔틀 시각 테스트)

# 디버깅
django-debug-toolbar>=4.3.0
```

### `requirements/production.txt`
```
-r base.txt
sentry-sdk>=1.40.0
```

---

## 5단계 · 프로젝트 구조 설정

아래 순서대로 진행한다.

### 5-1. 가상환경 및 프로젝트 생성

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements/development.txt
django-admin startproject config .
```

### 5-2. 5개 앱 생성

```bash
python manage.py startapp accounts
python manage.py startapp navigation
python manage.py startapp academic
python manage.py startapp restaurants
python manage.py startapp admin_dashboard
```

각 앱을 `apps/` 폴더로 이동하고 `apps.py`의 `name`을 `apps.accounts` 형식으로 수정한다.

### 5-3. settings 분리 구조

```
config/
└── settings/
    ├── __init__.py
    ├── base.py        # 공통 설정
    ├── development.py # 로컬 개발 (DEBUG=True, SQLite)
    └── production.py  # 운영 (DEBUG=False, Supabase PostgreSQL)
```

`manage.py`와 `config/wsgi.py`의 기본 settings 모듈을 `config.settings.development`로 지정한다.

### 5-4. URL 라우팅

```python
# config/urls.py
urlpatterns = [
    path('admin/',          admin.site.urls),
    path('accounts/',       include('apps.accounts.urls',      namespace='accounts')),
    path('navigation/',     include('apps.navigation.urls',    namespace='navigation')),
    path('academic/',       include('apps.academic.urls',      namespace='academic')),
    path('restaurants/',    include('apps.restaurants.urls',   namespace='restaurants')),
    path('dashboard/',      include('apps.admin_dashboard.urls', namespace='admin_dashboard')),
    path('',                include('apps.navigation.urls')),   # 메인 → 길찾기
]
```

---

## 6단계 · 데이터베이스 설정

### 개발 환경 — SQLite WAL 최적화 (Rails 8 수준)

```python
# config/settings/development.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        'OPTIONS': {
            'timeout': 20,          # busy_timeout 20초 → "Database is locked" 방지
            'init_command': (
                "PRAGMA journal_mode=WAL;"        # 읽기·쓰기 동시성 극대화
                "PRAGMA busy_timeout=20000;"      # 20초 대기
                "PRAGMA foreign_keys=ON;"         # FK 무결성 강제
                "PRAGMA synchronous=NORMAL;"      # 성능·안전성 균형
                "PRAGMA cache_size=-32000;"       # 32MB 페이지 캐시
                "PRAGMA temp_store=MEMORY;"       # 임시 테이블 메모리 사용
                "PRAGMA mmap_size=134217728;"     # 128MB 메모리 맵 I/O
            ),
        },
    }
}
```

### 운영 환경 — Supabase PostgreSQL

```python
# config/settings/production.py
import environ
env = environ.Env()
environ.Env.read_env(BASE_DIR / '.env')

DATABASES = {
    'default': env.db('DATABASE_URL')
    # 예: postgresql://user:pass@db.xxxx.supabase.co:5432/postgres
}
```

> ⚠️ Prisma는 이 프로젝트와 무관하다. Django ORM만 사용한다. Prisma 관련 파일을 생성하지 않는다.

---

## 7단계 · 환경변수 파일

`.env.example`을 아래 내용으로 생성한다 (`.env`는 `.gitignore`에 추가):

```env
# Django
DJANGO_SECRET_KEY=your-very-long-random-secret-key
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# Database (운영: Supabase PostgreSQL)
DATABASE_URL=postgresql://user:password@host:5432/postgres

# Kakao API (https://developers.kakao.com)
KAKAO_API_KEY=          # REST API 키 (서버 사이드 - 음식점 검색)
KAKAO_JS_KEY=           # JavaScript 키 (클라이언트 - 지도 렌더링)

# ODsay API (https://lab.odsay.com)
ODSAY_API_KEY=          # 대중교통 경로탐색

# Email (회원가입 인증 메일)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
DEFAULT_FROM_EMAIL=noreply@mju-navigate.kr
```

---

## 8단계 · 베이스 템플릿 (`templates/base.html`)

아래 요소를 반드시 포함한다:

```html
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{% block title %}MJU Navigate{% endblock %}</title>

  <!-- Tailwind CSS CDN -->
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {
      theme: {
        extend: {
          colors: {
            brand: {
              50:  '#eef0f8',
              100: '#d4d8ef',
              500: '#1B2A5E',   /* Pantone 2768 C — 서울캠 · 메인 브랜드 */
              600: '#152249',
              700: '#0f1a37',
            },
            campus: {
              seoul:        '#1B2A5E',   /* Pantone 2768 C */
              'seoul-bg':   '#eef0f8',
              yongin:       '#0057A8',   /* Pantone 300 C */
              'yongin-bg':  '#E0EFFF',
            },
            shuttle: {
              DEFAULT: '#16a34a',
              light:   '#dcfce7',
            },
          }
        }
      }
    }
  </script>

  <!-- CSRF → HTMX 자동 삽입 -->
  <meta name="csrf-token" content="{{ csrf_token }}">

  <!-- HTMX -->
  <script src="https://unpkg.com/htmx.org@2.0.0" defer></script>
  <!-- Alpine.js (탭·드롭다운 등 최소 UI 상태) -->
  <script src="https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js" defer></script>
  <!-- Kakao Maps SDK (지도 렌더링, JS 키 필요) -->
  <script type="text/javascript"
    src="//dapi.kakao.com/v2/maps/sdk.js?appkey={{ KAKAO_JS_KEY }}&libraries=services"></script>
</head>
<body class="bg-gray-50 text-gray-900">

  <!-- 상단 헤더 (Pantone 2768 C) -->
  <header class="bg-brand-500 text-white shadow-sm">
    <div class="max-w-5xl mx-auto px-4 py-3 flex items-center justify-between">
      <a href="{% url 'navigation:index' %}" class="font-bold text-lg">🏫 MJU Navigate</a>
      <nav class="hidden md:flex gap-6 text-sm">
        <a href="{% url 'navigation:index' %}"   class="hover:text-brand-100">길찾기</a>
        <a href="{% url 'academic:index' %}"     class="hover:text-brand-100">학사일정</a>
        <a href="{% url 'restaurants:index' %}"  class="hover:text-brand-100">음식점</a>
        {% if user.is_authenticated %}
          <a href="{% url 'accounts:profile' %}" class="hover:text-brand-100">프로필</a>
        {% else %}
          <a href="{% url 'account_login' %}"    class="hover:text-brand-100">로그인</a>
        {% endif %}
      </nav>
    </div>
  </header>

  <!-- 메인 콘텐츠 -->
  <main class="max-w-5xl mx-auto px-4 py-6">
    {% block content %}{% endblock %}
  </main>

  <!-- 모바일 하단 탭 바 -->
  <nav class="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 md:hidden z-50">
    <div class="flex">
      <a href="{% url 'navigation:index' %}"  class="flex-1 flex flex-col items-center py-2 text-xs text-brand-500">
        <span class="text-lg">🗺️</span>길찾기
      </a>
      <a href="{% url 'academic:index' %}"    class="flex-1 flex flex-col items-center py-2 text-xs text-gray-500">
        <span class="text-lg">📅</span>학사일정
      </a>
      <a href="{% url 'restaurants:index' %}" class="flex-1 flex flex-col items-center py-2 text-xs text-gray-500">
        <span class="text-lg">🍜</span>음식점
      </a>
      <a href="{% url 'accounts:profile' %}"  class="flex-1 flex flex-col items-center py-2 text-xs text-gray-500">
        <span class="text-lg">👤</span>프로필
      </a>
    </div>
  </nav>

  <!-- HTMX CSRF 자동 삽입 스크립트 -->
  <script>
    document.addEventListener('htmx:configRequest', (e) => {
      e.detail.headers['X-CSRFToken'] =
        document.querySelector('meta[name="csrf-token"]').content;
    });
  </script>

</body>
</html>
```

---

## 9단계 · 완료 후 로그 작성

작업이 끝나면 아래 두 파일을 반드시 작성한다. 날짜는 실제 오늘 날짜(YYYYMMDD)로 치환한다.

### `@logs/YYYYMMDD_tasks.md` — 업무 보고서

```markdown
# 업무 보고서 YYYYMMDD

## 완료 작업
- [ ] 항목1
- [ ] 항목2

## 생성된 파일 목록
- 파일 경로 및 설명

## 다음 단계 (Next Steps)
- 다음에 해야 할 작업
```

### `@logs/YYYYMMDD_logs.md` — 개발 일기

```markdown
# 개발 일기 YYYYMMDD

## 오늘의 결정 사항
- 왜 이 방식을 선택했는가

## 트러블슈팅
- 문제 / 원인 / 해결 방법

## 배운 점
- 인사이트, 주의사항
```

---

## 체크리스트 (작업 완료 기준)

- [ ] `venv` 생성 및 패키지 설치 완료
- [ ] 5개 Django 앱 생성 및 `INSTALLED_APPS` 등록
- [ ] `config/settings/` 3분할 구조 (base / development / production)
- [ ] SQLite WAL 최적화 설정 (`development.py`)
- [ ] Supabase PostgreSQL 연결 설정 (`production.py`)
- [ ] `.env.example` 생성 (6개 환경변수 그룹)
- [ ] `templates/base.html` 생성 (Pantone 2768 C 헤더, 모바일 탭 바)
- [ ] URL 라우팅 5개 앱 연결
- [ ] `python manage.py migrate` 성공
- [ ] `python manage.py runserver` 정상 실행
- [ ] 로그 파일 2개 작성 완료
