"""
@Project : Mood Garden (Community & Donation Platform)
@File    : donation/models.py
@Author  : Minsu Kim (Backend & Infra)
@Date    : 2025-12-01 ~ 2025-12-03
@Description : 기부 풀 및 기부 이력 관리 모델
"""

from django.db import models
from account.models import User


class DonationPool(models.Model):
    """
    기부 풀(캠페인) 모델
    
    사용자가 얻은 포인트를 특정 목표를 위해 기부하는 캠페인입니다.
    목표 포인트에 도달하면 완료 상태로 변경되고, 기부자 명단이 저장됩니다.
    
    Attributes:
        pool_id (AutoField): 기부 풀 ID (PK)
        title (CharField): 캠페인 제목
        sponsor (CharField, optional): 후원사 이름
        description (TextField, optional): 캠페인 상세 설명
        start_date (DateField, optional): 기부 시작일
        end_date (DateField, optional): 기부 종료일
        current_points (IntegerField): 현재까지 모인 포인트
        goal_points (IntegerField): 캠페인 목표 포인트
        status (CharField): 진행 상태 ('open' 또는 'completed')
        created_at (DateTimeField): 캠페인 생성 시간
        completed_at (DateTimeField, optional): 캠페인 완료 시간
    """
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
        """
        캠페인 진행률 계산
        
        Returns:
            int: 진행률 (0~100)
        """
        if self.goal_points == 0:
            return 0
        return min(100, int((self.current_points / self.goal_points) * 100))


class DonationHistory(models.Model):
    """
    기부 명예의 전당 모델
    
    DonationPool이 완료될 때, 각 참여 사용자의 기여 포인트를 스냅샷으로 저장합니다.
    사용자가 기부 완료 기념 배지나 랭킹을 볼 수 있게 합니다.
    
    Attributes:
        donation_id (AutoField): 기부 기록 ID (PK)
        pool_id (ForeignKey): 완료된 기부 풀
        user_id (ForeignKey): 기여한 사용자
        contributed_points (IntegerField): 해당 풀에 대한 최종 기여 포인트
        created_at (DateTimeField): 기록 생성 시간
    """
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
    기부 거래 기록 모델
    
    사용자가 포인트를 어느 기부 풀에 기부했는지 추적합니다.
    펫 상점에서 포인트를 소비할 때마다, 동일 금액이 현재 진행 중인 DonationPool에 
    기부된 것으로 기록되는 비즈니스 규칙을 구현합니다.
    
    Attributes:
        transaction_id (AutoField): 거래 기록 ID (PK)
        pool_id (ForeignKey): 기부한 기부 풀
        user_id (ForeignKey): 기부 사용자
        amount (PositiveIntegerField): 기부한 포인트 양
        created_at (DateTimeField): 거래 발생 시간
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
