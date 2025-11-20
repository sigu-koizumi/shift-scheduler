from ortools.sat.python import cp_model
from .models import WorkSchedule, Staff, ShiftRequest
import pandas as pd

def solve_shift_schedule(target_date):
    """
    指定された日付のシフトを最適化し、WorkScheduleに保存する関数
    """
    # -------------------------------------------------------
    # 1. データの準備
    # -------------------------------------------------------
    # その日のシフト希望を全部取ってくる
    requests = ShiftRequest.objects.filter(date=target_date)
    
    # スタッフのリスト
    staffs = Staff.objects.all()
    staff_ids = [s.id for s in staffs]

    # 営業時間（今回は簡易的に9時〜23時とする）
    hours = list(range(9, 23))

    # モデルの作成（ここからがOR-Toolsの世界）
    model = cp_model.CpModel()

    # -------------------------------------------------------
    # 2. 変数の定義 (Decision Variables)
    # -------------------------------------------------------
    # shifts[(staff_id, hour)] : その時間にその人が働くなら1、働かないなら0
    shifts = {}
    for s in staffs:
        for h in hours:
            shifts[(s.id, h)] = model.NewBoolVar(f'shift_{s.id}_{h}')

    # -------------------------------------------------------
    # 3. 制約条件 (Constraints)
    # -------------------------------------------------------
    
    # (A) 希望が出ていない時間には入れない & 不可の日には入れない
    for s in staffs:
        # そのスタッフのその日の希望を取得
        req = requests.filter(staff=s).first()
        
        for h in hours:
            if req:
                # 退勤時間が None なら「23時（閉店）」とみなす
                req_end = req.end_time if req.end_time is not None else 23
                # 希望があり、かつ「出勤可」で、かつ希望時間内ならOK
                if req.availability and (req.start_time <= h < req_end):
                    pass # 働いてもいい（何もしない＝0でも1でもいい）
                else:
                    # 希望時間外なら絶対に働けない（0に固定）
                    model.Add(shifts[(s.id, h)] == 0)
            else:
                # 希望自体が出ていない人は働けない
                model.Add(shifts[(s.id, h)] == 0)

    # (B) 店の必要人数（簡易版）： 12時〜13時（ランチ）は必ず2人以上必要
    #     それ以外の時間は1人以上必要
    for h in hours:
        if h in [12, 13]:
            model.Add(sum(shifts[(s.id, h)] for s in staffs) >= 2)
        else:
            model.Add(sum(shifts[(s.id, h)] for s in staffs) >= 1)

    # (C) 連続勤務時間の制限（労働基準法など）：とりあえず「1日8時間以内」
    for s in staffs:
        model.Add(sum(shifts[(s.id, h)] for h in hours) <= 8)

    # -------------------------------------------------------
    # 4. 目的関数 (Objective)
    # -------------------------------------------------------
    # 今回は「なるべく多くの希望を叶える（総労働時間を最大化）」とする
    total_working_hours = sum(shifts[(s.id, h)] for s in staffs for h in hours)
    model.Maximize(total_working_hours)

    # -------------------------------------------------------
    # 5. 解く (Solve)
    # -------------------------------------------------------
    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        print("最適解が見つかりました！")
        
        # 既存の確定シフトを消す（上書きのため）
        WorkSchedule.objects.filter(date=target_date).delete()

        # 結果を保存
        for s in staffs:
            # その人が働く時間をリストアップ
            working_hours = [h for h in hours if solver.Value(shifts[(s.id, h)]) == 1]
            
            if working_hours:
                # 連続していれば開始と終了になる（簡易実装）
                start = min(working_hours)
                end = max(working_hours) + 1 # 17時勤務なら終了は18時
                
                WorkSchedule.objects.create(
                    staff=s,
                    date=target_date,
                    start_time=start,
                    end_time=end
                )
        return True
    else:
        print("解が見つかりませんでした...")
        return False