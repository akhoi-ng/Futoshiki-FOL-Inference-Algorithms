#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
plot_charts.py — Extract data from CSV and plot charts for the Project Report.
Generates 3 charts: Time, Memory, and Number of Expanded Nodes.
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Set up the chart theme (Report standard)
sns.set_theme(style="whitegrid")
plt.rcParams.update({'font.size': 12})

def load_data(csv_path):
    if not os.path.exists(csv_path):
        print(f"[Error] File {csv_path} not found. Please run the benchmark first!")
        return None
    
    # Read data
    df = pd.read_csv(csv_path)
    
    # Filter only successful runs (ok or ok(fc+bt))
    df = df[df['status'].str.startswith('ok')]
    
    # Ensure correct data types
    df['time_s'] = pd.to_numeric(df['time_s'], errors='coerce')
    df['mem_peak_kb'] = pd.to_numeric(df['mem_peak_kb'], errors='coerce')
    df['nodes'] = pd.to_numeric(df['nodes'], errors='coerce')
    
    # Sort by input name for consistent X-axis ordering
    df = df.sort_values(by=['input', 'algo'])
    return df

def plot_metric(df, metric_col, ylabel, title, output_filename, use_log_scale=False):
    plt.figure(figsize=(12, 6))
    
    # Draw bar chart
    ax = sns.barplot(
        data=df, 
        x='input', 
        y=metric_col, 
        hue='algo', 
        palette='tab10'
    )
    
    plt.title(title, fontsize=16, fontweight='bold', pad=15)
    plt.xlabel('Test Cases (Increasing Size)', fontsize=14)
    plt.ylabel(ylabel, fontsize=14)
    plt.xticks(rotation=45) # Rotate X-axis labels for readability
    
    # Use Logarithmic scale if data variance is too large
    if use_log_scale:
        plt.yscale('log')
        plt.ylabel(f"{ylabel} (Log Scale)")
    
    plt.legend(title='Algorithms', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    
    # Save file
    plt.savefig(output_filename, dpi=300) # dpi=300 for high-quality images in Word/PDF
    print(f"Saved chart: {output_filename}")
    plt.close()

def main():
    # Assuming time and memory results are merged in this file
    csv_file = 'Results/benchmark.csv' 
    output_dir = 'Results/Charts'
    
    os.makedirs(output_dir, exist_ok=True)
    
    df = load_data(csv_file)
    if df is None or df.empty:
        print("[Error] Data is empty or invalid.")
        return

    print("Starting to plot charts...")

    # 1. Running Time Chart
    plot_metric(
        df=df, 
        metric_col='time_s', 
        ylabel='Time (Seconds)', 
        title='Comparison of Running Time Among Algorithms', 
        output_filename=f"{output_dir}/chart_time.png",
        use_log_scale=True # Use log scale because time ranges from 0.01s to 300s
    )

    # 2. Memory Usage Chart
    plot_metric(
        df=df, 
        metric_col='mem_peak_kb', 
        ylabel='Peak Memory (KB)', 
        title='Comparison of Memory Usage Among Algorithms', 
        output_filename=f"{output_dir}/chart_memory.png",
        use_log_scale=False # Memory usually doesn't vary by thousands of times, no need for log scale
    )

    # 3. Nodes / Inferences (Expansions) Chart
    # Combine Inferences (from FC/BC) and Nodes (from A*/BT) into one chart to compare workload
    df['work_done'] = df['nodes'].fillna(0) + df['inferences'].fillna(0)
    plot_metric(
        df=df, 
        metric_col='work_done', 
        ylabel='Nodes / Inferences Expanded', 
        title='Comparison of Search Space (Nodes / Inferences) Among Algorithms', 
        output_filename=f"{output_dir}/chart_nodes.png",
        use_log_scale=True # Log scale needed because A* generates a huge number of nodes
    )

    print("Done! Chart images have been saved in the Results/Charts/ directory.")

if __name__ == "__main__":
    main()