from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from .models import CommunityMeeting, MeetingParticipant, MeetingSubmission, SubmissionMedia
from account.models import User

# Create your views here.

def community_list(request):
    """커뮤니티 모임 목록"""
    meetings = []
    user_participations = {}
    search_query = request.GET.get('search', '')
    
    try:
        meetings = CommunityMeeting.objects.all().annotate(
            participant_count=Count('participants')
        ).order_by('-created_at')
        
        # 필터링
        if search_query:
            meetings = meetings.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(location_name__icontains=search_query)
            )
        
        # 참여 여부 확인
        if request.user.is_authenticated:
            user_participations = {
                p.meeting_id.meeting_id: True
                for p in MeetingParticipant.objects.filter(user_id=request.user)
            }
    except Exception:
        pass
    
    context = {
        'meetings': meetings,
        'user_participations': user_participations,
        'search_query': search_query,
    }
    return render(request, 'community.html', context)


@login_required
def meeting_detail(request, meeting_id):
    """모임 상세 페이지"""
    meeting = get_object_or_404(CommunityMeeting, meeting_id=meeting_id)
    
    # 참여자 목록
    participants = MeetingParticipant.objects.filter(meeting_id=meeting)
    participant_count = participants.count()
    
    # 참여 여부
    is_participant = False
    is_host = meeting.host_id == request.user
    if request.user.is_authenticated:
        is_participant = MeetingParticipant.objects.filter(
            meeting_id=meeting,
            user_id=request.user
        ).exists()
    
    # 인증 제출 상태 (호스트만)
    submission = None
    if is_host:
        submission = MeetingSubmission.objects.filter(
            meeting_id=meeting,
            host_id=request.user
        ).order_by('-created_at').first()
    
    context = {
        'meeting': meeting,
        'participants': participants,
        'participant_count': participant_count,
        'is_participant': is_participant,
        'is_host': is_host,
        'submission': submission,
    }
    return render(request, 'community/meeting_detail.html', context)


@login_required
def meeting_create(request):
    """모임 생성"""
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        location_name = request.POST.get('location_name')
        meeting_date = request.POST.get('meeting_date')
        capacity = request.POST.get('capacity', 10)
        
        if not all([title, description, location_name, meeting_date]):
            messages.error(request, '모든 필드를 입력해주세요.')
            return render(request, 'community/meeting_create.html')
        
        try:
            # Parse meeting_date (input type=datetime-local -> e.g. '2025-11-26T10:00')
            dt = None
            if meeting_date:
                dt = parse_datetime(meeting_date)
                if dt is None:
                    # fallback: try replacing 'T' with space
                    try:
                        dt = parse_datetime(meeting_date.replace(' ', 'T'))
                    except Exception:
                        dt = None
                # Make timezone-aware if settings use tz and dt is naive
                if dt is not None and timezone.is_naive(dt):
                    dt = timezone.make_aware(dt)

            if dt is None:
                raise ValueError('Invalid meeting_date format')

            meeting = CommunityMeeting.objects.create(
                host_id=request.user,
                title=title,
                description=description,
                location_name=location_name,
                meeting_date=dt,
                capacity=int(capacity)
            )
            messages.success(request, '모임이 생성되었습니다.')
            return redirect('meeting_detail', meeting_id=meeting.meeting_id)
        except Exception as e:
            messages.error(request, f'모임 생성 중 오류가 발생했습니다: {str(e)}')
            return render(request, 'community/meeting_create.html')
    
    return render(request, 'community/meeting_create.html')


@login_required
def meeting_join(request, meeting_id):
    """모임 참여"""
    meeting = get_object_or_404(CommunityMeeting, meeting_id=meeting_id)
    
    # 이미 참여했는지 확인
    if MeetingParticipant.objects.filter(meeting_id=meeting, user_id=request.user).exists():
        messages.warning(request, '이미 참여한 모임입니다.')
        return redirect('meeting_detail', meeting_id=meeting_id)
    
    # 호스트는 참여 불가
    if meeting.host_id == request.user:
        messages.warning(request, '호스트는 참여할 수 없습니다.')
        return redirect('meeting_detail', meeting_id=meeting_id)
    
    # 정원 확인
    participant_count = MeetingParticipant.objects.filter(meeting_id=meeting).count()
    if participant_count >= meeting.capacity:
        messages.error(request, '모임 정원이 가득 찼습니다.')
        return redirect('meeting_detail', meeting_id=meeting_id)
    
    # 모임 날짜 확인 (ensure timezone-aware comparison)
    try:
        meeting_dt = meeting.meeting_date
        if timezone.is_naive(meeting_dt):
            meeting_dt = timezone.make_aware(meeting_dt)
        if meeting_dt < timezone.now():
            messages.error(request, '이미 지난 모임입니다.')
            return redirect('meeting_detail', meeting_id=meeting_id)
    except Exception:
        messages.error(request, '모임 일시를 확인할 수 없습니다.')
        return redirect('meeting_detail', meeting_id=meeting_id)
    
    try:
        MeetingParticipant.objects.create(
            meeting_id=meeting,
            user_id=request.user
        )
        messages.success(request, '모임에 참여했습니다.')
    except Exception as e:
        messages.error(request, f'참여 중 오류가 발생했습니다: {str(e)}')
    
    return redirect('meeting_detail', meeting_id=meeting_id)


@login_required
def meeting_cancel(request, meeting_id):
    """모임 참여 취소"""
    meeting = get_object_or_404(CommunityMeeting, meeting_id=meeting_id)
    
    participant = MeetingParticipant.objects.filter(
        meeting_id=meeting,
        user_id=request.user
    ).first()
    
    if not participant:
        messages.warning(request, '참여하지 않은 모임입니다.')
        return redirect('meeting_detail', meeting_id=meeting_id)
    
    participant.delete()
    messages.success(request, '모임 참여를 취소했습니다.')
    return redirect('meeting_detail', meeting_id=meeting_id)


@login_required
def submission_create(request, meeting_id):
    """인증 제출 (모임 종료 후 호스트만)"""
    meeting = get_object_or_404(CommunityMeeting, meeting_id=meeting_id)
    
    # ... (호스트 확인 및 중복 제출 확인 로직은 그대로 유지) ...
    if meeting.host_id != request.user:
        messages.error(request, '호스트만 인증을 제출할 수 있습니다.')
        return redirect('meeting_detail', meeting_id=meeting_id)
    
    existing_submission = MeetingSubmission.objects.filter(
        meeting_id=meeting, host_id=request.user, status__in=['pending', 'ai_pass']
    ).first()
    
    if existing_submission:
        messages.warning(request, '이미 제출한 인증이 있습니다.')
        return redirect('meeting_detail', meeting_id=meeting_id)
    
    if request.method == 'POST':
        text_summary = request.POST.get('text_summary', '')
        scene_photo = request.FILES.get('scene_photo')
        
        # [수정] 대표 셀카 1장만 받거나, 여러 장 중 첫 번째를 대표로 사용하도록 유도
        # 여기서는 템플릿에서 'selfie_representative'라는 이름으로 파일 하나만 받는 것을 권장합니다.
        # 기존 로직(참여자별 셀카)을 유지하려면, tasks.py가 그 중 하나만 골라서 검사한다는 점을 인지해야 합니다.
        
        if not scene_photo:
            messages.error(request, '장소 사진을 업로드해주세요.')
            return render(request, 'community/submission_create.html', {'meeting': meeting})
        
        try:
            # 1. Submission 생성
            submission = MeetingSubmission.objects.create(
                meeting_id=meeting,
                host_id=request.user,
                text_summary=text_summary,
                status='pending'
            )
            
            # 2. 장소 사진 저장
            SubmissionMedia.objects.create(
                submission_id=submission,
                media_type='scene_photo',
                file=scene_photo
            )
            
            # 3. 셀카 저장 (여러 장 업로드 처리)
            # 템플릿에서 <input type="file" name="selfie_xxx"> 형태로 보낸다고 가정
            has_selfie = False
            for key, file in request.FILES.items():
                if key.startswith('selfie'):
                    SubmissionMedia.objects.create(
                        submission_id=submission,
                        # user_id는 파일명이나 key에서 파싱해야 하지만, 복잡하면 NULL로 둠
                        media_type='selfie',
                        file=file
                    )
                    has_selfie = True
            
            if not has_selfie:
                 messages.warning(request, '셀카가 없어 AI 검증 정확도가 낮을 수 있습니다.')

            # 4. AI 검증 호출 (try-except로 감싸서 메인 로직 보호)
            try:
                # tasks.py가 같은 폴더(community)에 있어야 함
                from .tasks import process_ai_verification
                process_ai_verification(submission.submission_id)
                messages.success(request, '인증 제출 완료! AI가 검증을 시작했습니다. (약 3~5초 소요)')
            except ImportError:
                messages.error(request, 'AI 검증 모듈을 찾을 수 없습니다. 관리자에게 문의하세요.')
            except Exception as ai_error:
                # AI가 실패해도 제출은 성공으로 처리하되, 경고 메시지 표시
                print(f"AI Error: {ai_error}")
                messages.warning(request, '제출은 완료되었으나 AI 검증 연결에 실패했습니다. 관리자가 수동으로 확인합니다.')

            return redirect('meeting_detail', meeting_id=meeting_id)
            
        except Exception as e:
            messages.error(request, f'제출 중 오류가 발생했습니다: {str(e)}')
            return render(request, 'community/submission_create.html', {'meeting': meeting})
    
    # GET 요청
    participants = MeetingParticipant.objects.filter(meeting_id=meeting)
    context = {
        'meeting': meeting,
        'participants': participants,
    }
    return render(request, 'community/submission_create.html', context)