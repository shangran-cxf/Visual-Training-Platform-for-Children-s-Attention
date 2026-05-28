"""导出训练数据到 CSV，方便查看视觉模型稳定性得分"""

import csv
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from database.db import get_db_connection


def main():
    conn = get_db_connection()

    sessions = conn.execute("""
        SELECT
            ss.session_id,
            c.name AS child_name,
            ss.game_type,
            ss.attention_type,
            ss.overall_score,
            ss.performance_level,
            ss.head_stable_score,
            ss.face_stable_score,
            ss.blink_stable_score,
            ss.accuracy_score,
            ss.precision_score,
            ss.speed_score,
            ss.impulse_score,
            ss.memory_score,
            ss.no_fatigue_score,
            ss.rt_score,
            ss.order_score,
            ss.stable_act_score,
            (SELECT COUNT(*) FROM vision_raw_data v WHERE v.session_id = ss.session_id) AS vision_data_count,
            ss.created_at
        FROM session_summaries ss
        JOIN children c ON ss.child_id = c.id
        ORDER BY ss.created_at DESC
    """).fetchall()

    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "time_utils", os.path.join(os.path.dirname(__file__), "..", "backend", "utils", "time_utils.py")
    )
    tu = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tu)
    to_beijing_string = tu.to_beijing_string

    output_dir = os.path.join(os.path.dirname(__file__), "..", "database")
    from datetime import datetime as dt

    ts = dt.now().strftime("%Y%m%d_%H%M%S")
    csv_path = os.path.join(output_dir, f"training_export_{ts}.csv")

    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "session_id",
                "孩子姓名",
                "游戏类型",
                "注意力类型",
                "总分",
                "表现等级",
                "头部稳定度",
                "面部稳定度",
                "眨眼稳定度",
                "正确率",
                "精确率",
                "速度",
                "冲动控制",
                "记忆力",
                "抗疲劳",
                "反应时",
                "顺序",
                "动作稳定",
                "视觉数据条数",
                "创建时间",
            ]
        )
        for row in sessions:
            row_list = list(row)
            row_list[-1] = to_beijing_string(row_list[-1], "%Y/%m/%d %H:%M")
            writer.writerow(row_list)

    print(f"导出完成: {csv_path}")
    print(f"共 {len(sessions)} 条记录")

    # 汇总统计
    zero_vision = sum(1 for s in sessions if (s[18] or 0) == 0)
    all_half = 0
    for s in sessions:
        h, f, b = s[6], s[7], s[8]
        if h == 0.5 and f == 0.5 and b == 0.5:
            all_half += 1

    print(f"无视觉数据的会话: {zero_vision}")
    print(f"三个稳定度均为 0.5 的会话: {all_half}")

    # 输出稳定度的值分布
    for col_name, idx in [("头部稳定度", 6), ("面部稳定度", 7), ("眨眼稳定度", 8)]:
        vals = [s[idx] for s in sessions if s[idx] is not None]
        if vals:
            print(
                f"{col_name}: min={min(vals):.4f}, max={max(vals):.4f}, "
                f"zeros={sum(1 for v in vals if v == 0)}, "
                f"halfs={sum(1 for v in vals if v == 0.5)}, "
                f"ones={sum(1 for v in vals if v == 1.0)}"
            )

    conn.close()


if __name__ == "__main__":
    main()
