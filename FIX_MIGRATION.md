# 마이그레이션 오류 해결 가이드

## 문제
`no such table: donation_pool` 오류가 발생했습니다. 이는 일부 앱의 마이그레이션이 생성되지 않았기 때문입니다.

## 해결 방법

### 방법 1: 명령 프롬프트(cmd) 사용 (권장)

PowerShell 대신 명령 프롬프트(cmd)를 사용하세요:

1. Windows 키 + R을 누르고 `cmd` 입력 후 Enter
2. 다음 명령어로 프로젝트 디렉터리로 이동:
   ```
   cd /d "C:\Users\shvlt\OneDrive\바탕 화면\moodgarden\myproject"
   ```
3. 마이그레이션 생성:
   ```
   python manage.py makemigrations
   ```
4. 마이그레이션 적용:
   ```
   python manage.py migrate
   ```

### 방법 2: Python 스크립트 실행

다음 Python 스크립트를 실행하세요:

```python
# create_migrations.py
import os
import sys
import django

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.core.management import call_command

# 마이그레이션 생성
call_command('makemigrations')
call_command('migrate')
```

실행:
```
cd myproject
python create_migrations.py
```

### 방법 3: 각 앱별로 개별 생성

```
python manage.py makemigrations donation
python manage.py makemigrations community
python manage.py makemigrations growth
python manage.py makemigrations notification
python manage.py migrate
```

## 확인

마이그레이션이 성공적으로 생성되었는지 확인:

```
python manage.py showmigrations
```

모든 앱에 `[X]` 표시가 있어야 합니다.

## 추가 확인사항

마이그레이션 후에도 오류가 발생하면:

1. 데이터베이스 파일 삭제 후 재생성 (개발 환경에서만):
   ```
   del db.sqlite3
   python manage.py migrate
   ```

2. 관리자 계정 재생성:
   ```
   python manage.py createsuperuser
   ```


