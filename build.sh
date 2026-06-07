#!/usr/bin/env bash
# Render 빌드 스크립트
# Web Service > Settings > Build Command: ./build.sh
set -o errexit   # 명령 실패 시 즉시 종료

pip install --upgrade pip
pip install -r requirements.txt

# static 파일 수집
python manage.py collectstatic --no-input

# DB 마이그레이션
python manage.py migrate

# 초기 데이터 로드 (이미 존재해도 오류 없이 건너뜀)
python manage.py loaddata apps/academic/fixtures/sample_events.json || true
python manage.py loaddata apps/navigation/fixtures/shuttle_data_2026_spring.json || true
