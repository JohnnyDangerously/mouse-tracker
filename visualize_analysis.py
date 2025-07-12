
import matplotlib.pyplot as plt
import numpy as np
from analyze_mouse_data import analyze_mouse_csv
import os

def create_visualizations(analyzer, smooth_events, jittery_events):
    """Create visualizations of the mouse movement analysis"""
    
    # Create figure with subplots
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('Mouse Movement Analysis Results', fontsize=16)
    
    # 1. Event distribution pie chart
    labels = ['Smooth Events', 'Jittery Events']
    sizes = [len(smooth_events), len(jittery_events)]
    colors = ['lightgreen', 'lightcoral']
    
    ax1.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
    ax1.set_title('Event Type Distribution')
    
    # 2. Duration comparison
    if smooth_events and jittery_events:
        smooth_durations = [e['duration'] for e in smooth_events]
        jittery_durations = [e['duration'] for e in jittery_events]
        
        ax2.hist([smooth_durations, jittery_durations], bins=15, alpha=0.7, 
                label=['Smooth', 'Jittery'], color=['green', 'red'])
        ax2.set_xlabel('Duration (seconds)')
        ax2.set_ylabel('Frequency')
        ax2.set_title('Event Duration Distribution')
        ax2.legend()
    
    # 3. Path efficiency comparison
    if smooth_events and jittery_events:
        smooth_efficiency = [e['path_efficiency'] for e in smooth_events]
        jittery_efficiency = [e['path_efficiency'] for e in jittery_events]
        
        ax3.hist([smooth_efficiency, jittery_efficiency], bins=15, alpha=0.7,
                label=['Smooth', 'Jittery'], color=['green', 'red'])
        ax3.set_xlabel('Path Efficiency')
        ax3.set_ylabel('Frequency')
        ax3.set_title('Path Efficiency Distribution')
        ax3.legend()
    
    # 4. Jitter score vs efficiency scatter plot
    all_events = smooth_events + jittery_events
    jitter_scores = [e['jitter_score'] for e in all_events]
    efficiencies = [e['path_efficiency'] for e in all_events]
    colors = ['green'] * len(smooth_events) + ['red'] * len(jittery_events)
    
    ax4.scatter(jitter_scores, efficiencies, c=colors, alpha=0.6)
    ax4.set_xlabel('Jitter Score')
    ax4.set_ylabel('Path Efficiency')
    ax4.set_title('Jitter vs Efficiency')
    
    # Add legend for scatter plot
    import matplotlib.patches as mpatches
    green_patch = mpatches.Patch(color='green', label='Smooth')
    red_patch = mpatches.Patch(color='red', label='Jittery')
    ax4.legend(handles=[green_patch, red_patch])
    
    plt.tight_layout()
    plt.savefig('mouse_analysis_visualization.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    print("Visualization saved as 'mouse_analysis_visualization.png'")

def main():
    """Main function to run analysis and create visualizations"""
    default_csv = os.path.expanduser("~/Documents/MouseLogs/mouse_log.csv")
    
    if os.path.exists(default_csv):
        print("Running mouse movement analysis...")
        analyzer, smooth, jittery = analyze_mouse_csv(default_csv)
        
        if analyzer and analyzer.aiming_events:
            create_visualizations(analyzer, smooth, jittery)
        else:
            print("No events to visualize.")
    else:
        print(f"No mouse log file found at {default_csv}")
        print("Please run the mouse tracker first to collect data.")

if __name__ == "__main__":
    main()
