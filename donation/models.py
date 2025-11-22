from django.db import models
from account.models import User

# Create your models here.

class DonationPool(models.Model):
    """기부 풀 모델"""
    STATUS_CHOICES = [
        ('open', '진행 중'),
        ('completed', '완료'),
    ]
    
    pool_id = models.AutoField(primary_key=True)
    current_points = models.IntegerField(default=0, help_text="모든 PointsHistory의 points_change > 0 합계")
    goal_points = models.IntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    title = models.CharField(max_length=200, help_text="예: '유기동물 보호소 간식 기부'")
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
    """기부 명예의 전당 모델 (Pool 완료 시 PointsHistory 집계 스냅샷)"""
    donation_id = models.AutoField(primary_key=True)
    pool_id = models.ForeignKey(DonationPool, on_delete=models.CASCADE, related_name='donation_history', db_column='pool_id')
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='donation_history', db_column='user_id')
    contributed_points = models.IntegerField(help_text="해당 pool에 대한 기여분")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'donation_history'
        ordering = ['-contributed_points', '-created_at']
        unique_together = ['pool_id', 'user_id']  # 같은 pool에 대한 중복 기록 방지
    
    def __str__(self):
        return f"{self.user_id.username} - {self.contributed_points} points to {self.pool_id.title}"
