from django.shortcuts import render, redirect
from django.contrib import messages
import datetime

# 自作のファイルからクラスや関数を読み込む
from .forms import ShiftRequestForm
from .models import ShiftRequest, WorkSchedule, Staff
from .solver import solve_shift_schedule  # AIエンジン
#カレンダー実装用
import calendar # 追加
from django.db import transaction # 追加
import jpholiday  # ★追加：日本の祝日判定ライブラリ

# -------------------------------------------------------
# 1. バイト生用：シフト希望入力画面（あなたが貼ってくれたコード）
# -------------------------------------------------------



def input_schedule(request):
    """カレンダーによる一括シフト希望入力"""
    
    today = datetime.date.today()
    year = today.year
    month = today.month

    if request.method == 'POST':
        selected_dates = request.POST.getlist('dates')
        
        # ★変更：平日用と休日用の2つの時間を取得
        weekday_time = request.POST.get('weekday_start_time')
        holiday_time = request.POST.get('weekend_start_time')
        
        if selected_dates:
            with transaction.atomic():
                for date_str in selected_dates:
                    date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
                    
                    # ★判定ロジック：土日(5,6) または 祝日なら「休日時間」を使う
                    if date.weekday() >= 5 or jpholiday.is_holiday(date):
                        start_time = holiday_time
                    else:
                        start_time = weekday_time
                    
                    # start_timeが入っている場合のみ登録（念のため）
                    if start_time:
                        ShiftRequest.objects.update_or_create(
                            staff=Staff.objects.first(), # ※仮：あとでログインユーザーに変更
                            date=date,
                            defaults={
                                'start_time': int(start_time),
                                'end_time': None, # 退勤はおまかせ
                                'availability': True
                            }
                        )
            messages.success(request, f'{len(selected_dates)}件のシフト希望を提出しました！')
            return redirect('input_schedule')

    # カレンダー作成
    cal = calendar.Calendar(firstweekday=6)
    month_days = cal.monthdatescalendar(year, month)

    return render(request, 'scheduler/input_schedule.html', {
        'month_days': month_days,
        'year': year,
        'month': month,
        # hoursはもう使わないので削除してOK
    })

# -------------------------------------------------------
# 2. 店長用：AI実行ダッシュボード（今回追加する部分）
# -------------------------------------------------------
def admin_dashboard(request):
    """店長用ダッシュボード：シフト作成と確認"""
    
    # URLに ?date=2025-11-25 のように日付があればそれを使い、なければ「今日」にする
    target_date_str = request.GET.get('date', datetime.date.today().strftime('%Y-%m-%d'))
    try:
        target_date = datetime.datetime.strptime(target_date_str, '%Y-%m-%d').date()
    except ValueError:
        # 日付の形式がおかしい場合は今日にする
        target_date = datetime.date.today()

    if request.method == 'POST':
        if 'date' in request.POST:
            target_date_str = request.POST.get('date')
            try:
                target_date = datetime.datetime.strptime(target_date_str, '%Y-%m-%d').date()
            except ValueError:
                pass
            
        # 「AIで作成」ボタンが押されたら実行
        if 'create_shift' in request.POST:
            # ここで solver.py のAIが動く！
            is_success = solve_shift_schedule(target_date)
            
            if is_success:
                messages.success(request, f'{target_date} のシフトをAIが作成しました！')
            else:
                messages.error(request, f'{target_date} のシフト作成に失敗しました（解なし）。条件を緩めてください。')
            
            return redirect(f'/admin-dashboard/?date={target_date}')

    # その日の「確定シフト」をDBから取得して表示
    schedules = WorkSchedule.objects.filter(date=target_date).order_by('start_time')
    
    return render(request, 'scheduler/admin_dashboard.html', {
        'target_date': target_date,
        'schedules': schedules,
    })