# 마이그레이션 적용 가이드

## ✅ 완료된 작업

모든 앱의 초기 마이그레이션 파일이 생성되었습니다:
- ✅ `community/migrations/0001_initial.py`
- ✅ `growth/migrations/0001_initial.py`
- ✅ `donation/migrations/0001_initial.py`
- ✅ `notification/migrations/0001_initial.py`

## 다음 단계: 마이그레이션 적용

프로젝트 디렉터리(`myproject`)에서 다음 명령어를 실행하세요:

### 방법 1: 명령 프롬프트(cmd) 사용 (권장)

1. Windows 키 + R → `cmd` 입력 후 Enter
2. 다음 명령어 실행:

```cmd
cd /d "C:\Users\shvlt\OneDrive\바탕 화면\moodgarden\myproject"
python manage.py migrate
```

### 방법 2: Python 스크립트 사용

```bash
cd myproject
python create_migrations.py
```

(이 스크립트는 makemigrations와 migrate를 모두 실행합니다)

### 방법 3: PowerShell에서 직접 실행

```powershell
cd "C:\Users\shvlt\OneDrive\바탕 화면\moodgarden\myproject"
python manage.py migrate
```

## 마이그레이션 확인

마이그레이션이 성공적으로 적용되었는지 확인:

```bash
python manage.py showmigrations
```

모든 앱에 `[X]` 표시가 있어야 합니다:
```
account
 [X] 0001_initial
 [X] 0002_alter_user_options_user_created_at_alter_user_table
community
 [X] 0001_initial
donation
 [X] 0001_initial
growth
 [X] 0001_initial
notification
 [X] 0001_initial
```

## 문제 해결

만약 마이그레이션 중 오류가 발생하면:

1. **데이터베이스 초기화** (개발 환경에서만, 기존 데이터 삭제됨):
   ```bash
   del db.sqlite3
   python manage.py migrate
   python manage.py createsuperuser
   ```

2. **특정 앱만 마이그레이션**:
   ```bash
   python manage.py migrate community
   python manage.py migrate growth
   python manage.py migrate donation
   python manage.py migrate notification
   ```

## 생성될 테이블

마이그레이션 후 다음 테이블들이 생성됩니다:

- `community_meeting`
- `meeting_participant`
- `meeting_submission`
- `submission_media`
- `pet_item`
- `user_pet`
- `user_inventory`
- `points_history`
- `donation_pool`
- `donation_history`
- `notification`

마이그레이션 적용 후 서버를 다시 시작하면 정상 작동합니다!


