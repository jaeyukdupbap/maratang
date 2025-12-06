from django.db import models
from account.models import User

# Create your models here.


class DonationPool(models.Model):
    """기부 풀(캠페인) 모델"""
    STATUS_CHOICES = [
        ('open', '진행 중'),
        ('completed', '완료'),
    ]
    
    pool_id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=200, help_text="예: '유기동물 보호소 간식 기부'")
    sponsor = models.CharField(max_length=200, null=True, blank=True, help_text="후원사 이름")
    description = models.TextField(null=True, blank=True, help_text="캠페인 상세 설명")
    start_date = models.DateField(null=True, blank=True, help_text="기부 시작일")
    end_date = models.DateField(null=True, blank=True, help_text="기부 종료일")

    current_points = models.IntegerField(
        default=0,
        help_text="해당 캠페인에 누적된 전체 기부 포인트 합계"
    )
    goal_points = models.IntegerField(help_text="캠페인 목표 포인트")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')

    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'donation_pool'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def get_progress_percentage(self):
        """진행률 계산 (0-100)"""
        if self.goal_points == 0:
            return 0
        return min(100, int((self.current_points / self.goal_points) * 100))


class DonationHistory(models.Model):
    """기부 명예의 전당 모델 (Pool 완료 시 사용자별 기여 스냅샷)"""
    donation_id = models.AutoField(primary_key=True)
    pool_id = models.ForeignKey(
        DonationPool,
        on_delete=models.CASCADE,
        related_name='donation_history',
        db_column='pool_id',
    )
    user_id = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='donation_history',
        db_column='user_id',
    )
    contributed_points = models.IntegerField(help_text="해당 pool에 대한 최종 기여 포인트")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'donation_history'
        ordering = ['-contributed_points', '-created_at']
        unique_together = ['pool_id', 'user_id']  # 같은 pool에 대한 중복 기록 방지
    
    def __str__(self):
        return f"{self.user_id.username} - {self.contributed_points} points to {self.pool_id.title}"


class DonationTransaction(models.Model):
    """
    개별 기부 트랜잭션 로그
    - 비즈니스 규칙: 펫 상점에서 포인트를 소비할 때마다,
      동일 금액이 현재 진행 중인 DonationPool 에 기부된 것으로 기록
    """
    transaction_id = models.AutoField(primary_key=True)
    pool_id = models.ForeignKey(
        DonationPool,
        on_delete=models.CASCADE,
        related_name='transactions',
        db_column='pool_id',
    )
    user_id = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='donation_transactions',
        db_column='user_id',
    )
    amount = models.PositiveIntegerField(help_text="기부된 포인트 양 (User Point Consumption 기준)")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'donation_transaction'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user_id.username} - {self.amount}P to {self.pool_id.title}"
