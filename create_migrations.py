#!/usr/bin/env python
"""
마이그레이션 생성 스크립트
한글 경로 문제로 인해 직접 실행이 어려울 때 사용
"""
import os
import sys
import django

# 프로젝트 디렉터리 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from django.core.management import call_command

if __name__ == '__main__':
    print("마이그레이션 생성 중...")
    try:
        call_command('makemigrations')
        print("마이그레이션 생성 완료!")
    except Exception as e:
        print(f"마이그레이션 생성 중 오류: {e}")
        sys.exit(1)
    
    print("\n마이그레이션 적용 중...")
    try:
        call_command('migrate')
        print("마이그레이션 적용 완료!")
    except Exception as e:
        print(f"마이그레이션 적용 중 오류: {e}")
        sys.exit(1)
    
    print("\n모든 작업이 완료되었습니다!")


