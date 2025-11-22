# 마이그레이션 가이드

## 다음 단계

### 1. 마이그레이션 생성 및 적용

프로젝트 디렉터리(`myproject`)에서 다음 명령어를 실행하세요:

```bash
python manage.py makemigrations
python manage.py migrate
```

### 2. 관리자 계정 생성

```bash
python manage.py createsuperuser
```

### 3. 초기 데이터 생성 (선택사항)

관리자 페이지에서 다음을 수동으로 생성할 수 있습니다:
- PetItem (상점 아이템)
- DonationPool (기부 풀)

또는 Django shell을 사용하여 생성할 수 있습니다:

```bash
python manage.py shell
```

```python
from growth.models import PetItem
from donation.models import DonationPool

# 예시 아이템 생성
PetItem.objects.create(
    item_name="사과 간식",
    item_type="snack",
    required_level=1,
    cost=50
)

PetItem.objects.create(
    item_name="꽃 장식",
    item_type="decoration",
    required_level=3,
    cost=200
)

# 기부 풀 생성
DonationPool.objects.create(
    title="유기동물 보호소 간식 기부",
    goal_points=10000,
    status="open"
)
```

## 주요 기능

### 완료된 기능
- ✅ 사용자 인증 (회원가입, 로그인, 로그아웃)
- ✅ 커뮤니티 모임 (생성, 목록, 상세, 참여/취소)
- ✅ 인증 제출 시스템
- ✅ AI 인증 시뮬레이션
- ✅ 포인트 지급 시스템
- ✅ 동물 키우기 (레벨, XP, 아이템 구매)
- ✅ 기부 시스템
- ✅ 알림 시스템
- ✅ 관리자 검증 기능

### 템플릿 파일
모든 템플릿 파일이 생성되었으며, 기본 CSS 스타일링이 포함되어 있습니다.

### MEDIA 설정
이미지 업로드를 위한 MEDIA 설정이 완료되었습니다.
- 업로드된 파일은 `myproject/media/` 디렉터리에 저장됩니다.

## 실행 방법

```bash
cd myproject
python manage.py runserver
```

브라우저에서 `http://127.0.0.1:8000` 접속

## 주의사항

1. **한글 경로 문제**: Windows에서 한글 경로가 포함된 경우 PowerShell에서 명령어 실행 시 문제가 발생할 수 있습니다. 
   - 해결 방법: 명령 프롬프트(cmd)를 사용하거나, 경로를 짧게 변경하세요.

2. **AI 인증**: 현재는 시뮬레이션으로 구현되어 있습니다. 실제 AI 모델을 연동하려면 `community/tasks.py`의 `simulate_ai_verification` 함수를 수정하세요.

3. **이미지 업로드**: 실제 프로덕션 환경에서는 S3나 다른 스토리지 서비스를 사용하는 것을 권장합니다.


