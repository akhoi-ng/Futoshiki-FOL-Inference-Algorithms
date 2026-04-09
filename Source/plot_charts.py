#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
plot_charts.py — Trích xuất dữ liệu từ file CSV và vẽ biểu đồ cho Báo cáo Đồ án.
Tạo ra 3 biểu đồ: Thời gian (Time), Bộ nhớ (Memory), và Số lượng Node mở rộng.
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Cấu hình giao diện biểu đồ cho đẹp (chuẩn báo cáo)
sns.set_theme(style="whitegrid")
plt.rcParams.update({'font.size': 12})

def load_data(csv_path):
    if not os.path.exists(csv_path):
        print(f"[Lỗi] Không tìm thấy file {csv_path}. Hãy chạy benchmark trước!")
        return None
    
    # Đọc dữ liệu
    df = pd.read_csv(csv_path)
    
    # Chỉ lấy những lần giải thành công (ok hoặc ok(fc+bt))
    df = df[df['status'].str.startswith('ok')]
    
    # Chuyển đổi kiểu dữ liệu cho chắc chắn
    df['time_s'] = pd.to_numeric(df['time_s'], errors='coerce')
    df['mem_peak_kb'] = pd.to_numeric(df['mem_peak_kb'], errors='coerce')
    df['nodes'] = pd.to_numeric(df['nodes'], errors='coerce')
    
    # Sắp xếp theo tên input để trục X hiển thị đúng thứ tự
    df = df.sort_values(by=['input', 'algo'])
    return df

def plot_metric(df, metric_col, ylabel, title, output_filename, use_log_scale=False):
    plt.figure(figsize=(12, 6))
    
    # Vẽ biểu đồ cột (Bar chart)
    ax = sns.barplot(
        data=df, 
        x='input', 
        y=metric_col, 
        hue='algo', 
        palette='tab10'
    )
    
    plt.title(title, fontsize=16, fontweight='bold', pad=15)
    plt.xlabel('Test Cases (Kích thước tăng dần)', fontsize=14)
    plt.ylabel(ylabel, fontsize=14)
    plt.xticks(rotation=45) # Xoay nhãn trục X cho dễ đọc
    
    # Dùng thang đo Logarit nếu dữ liệu chênh lệch nhau quá lớn (ví dụ: A* sinh hàng ngàn node, FC sinh 10 node)
    if use_log_scale:
        plt.yscale('log')
        plt.ylabel(f"{ylabel} (Log Scale)")
    
    plt.legend(title='Algorithms', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    
    # Lưu file
    plt.savefig(output_filename, dpi=300) # dpi=300 để ảnh nét căng khi đưa vào file Word/PDF
    print(f"Đã lưu biểu đồ: {output_filename}")
    plt.close()

def main():
    # Giả sử bạn đã gộp chung kết quả time và memory vào file này
    csv_file = 'Results/benchmark.csv' 
    output_dir = 'Results/Charts'
    
    os.makedirs(output_dir, exist_ok=True)
    
    df = load_data(csv_file)
    if df is None or df.empty:
        print("[Lỗi] Dữ liệu trống hoặc không hợp lệ.")
        return

    print("Bắt đầu vẽ biểu đồ...")

    # 1. Biểu đồ Thời gian (Running Time)
    plot_metric(
        df=df, 
        metric_col='time_s', 
        ylabel='Thời gian (Giây)', 
        title='So sánh Thời gian thực thi (Running Time) giữa các thuật toán', 
        output_filename=f"{output_dir}/chart_time.png",
        use_log_scale=True # Dùng log scale vì có test case 0.01s và test case 300s
    )

    # 2. Biểu đồ Bộ nhớ (Memory Usage)
    plot_metric(
        df=df, 
        metric_col='mem_peak_kb', 
        ylabel='Peak Memory (KB)', 
        title='So sánh Mức tiêu thụ Bộ nhớ (Memory Usage) giữa các thuật toán', 
        output_filename=f"{output_dir}/chart_memory.png",
        use_log_scale=False # Bộ nhớ thường không chênh tới mức hàng vạn lần, ko cần log scale
    )

    # 3. Biểu đồ Số Node / Inferences (Expansions)
    # Gom chung Inferences (của FC/BC) và Nodes (của A*/BT) vào 1 biểu đồ để so sánh khối lượng công việc
    df['work_done'] = df['nodes'].fillna(0) + df['inferences'].fillna(0)
    plot_metric(
        df=df, 
        metric_col='work_done', 
        ylabel='Số trạng thái/Suy diễn (Nodes/Inferences)', 
        title='So sánh Không gian Tìm kiếm (Nodes Expanded / Inferences) của các thuật toán', 
        output_filename=f"{output_dir}/chart_nodes.png",
        use_log_scale=True # Rất cần log scale vì A* sinh cực kỳ nhiều node
    )

    print("Hoàn tất! Các file ảnh đã được lưu trong thư mục Results/Charts/")

if __name__ == "__main__":
    main()