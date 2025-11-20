"""データベースの設計図"""
from django.db import models
from django.utils import timezone

class Staff(models.Model):
    """スタッフ情報（最適化の制約条件に使います）"""
    name = models.CharField("名前", max_length=50)
    is_veteran = models.BooleanField("ベテランフラグ", default=False, help_text="シフトに最低1人は必要な場合にチェック")# 例えば経験者 消すかも、
    max_hours_per_week = models.IntegerField("週の最大勤務時間", default=28)# 1週間で最大何時間働けるか 多分消す
    #パントリー情報入れる可能性あり
    
    def __str__(self):
        return self.name

class ShiftRequest(models.Model):
    """スタッフからのシフト希望"""
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE)
    date = models.DateField("日付")
    start_time = models.IntegerField("開始時間(時)", choices=[(i, f"{i}:00") for i in range(9, 24)])
    end_time = models.IntegerField(
        "終了時間(時)",
        choices=[(i, f"{i}:00") for i in range(9, 24)],
        null=True,  # データベース的に空っぽOK
        blank=True  # フォーム入力時に空っぽOK
        )
    availability = models.BooleanField("出勤可否", default=True)

    def __str__(self):
        return f"{self.staff.name} - {self.date} ({self.start_time}:00-{self.end_time}:00)"

class WorkSchedule(models.Model):
    """AIが計算した確定シフト"""
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE)
    date = models.DateField("日付")
    start_time = models.IntegerField("開始時間(時)")
    end_time = models.IntegerField("終了時間(時)")

    def __str__(self):
        return f"{self.staff.name} : {self.date}"