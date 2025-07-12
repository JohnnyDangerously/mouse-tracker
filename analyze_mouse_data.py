
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from scipy import signal
from scipy.spatial.distance import euclidean

class MouseDataAnalyzer:
    def __init__(self, csv_file_path):
        """Initialize analyzer with CSV file path"""
        self.csv_file_path = csv_file_path
        self.data = None
        self.aiming_events = []
        
    def load_data(self):
        """Load mouse tracking data from CSV"""
        try:
            self.data = pd.read_csv(self.csv_file_path)
            print(f"Loaded {len(self.data)} events from {self.csv_file_path}")
            return True
        except Exception as e:
            print(f"Error loading data: {e}")
            return False
    
    def calculate_movement_metrics(self, event_data):
        """Calculate movement smoothness metrics for a sequence of events"""
        if len(event_data) < 3:
            return None
            
        # Extract coordinates
        x_coords = event_data['x'].values
        y_coords = event_data['y'].values
        timestamps = event_data['time'].values
        
        # Calculate velocities
        dt = np.diff(timestamps)
        dx = np.diff(x_coords)
        dy = np.diff(y_coords)
        
        # Avoid division by zero
        dt[dt == 0] = 0.001
        
        velocities = np.sqrt(dx**2 + dy**2) / dt
        
        # Calculate acceleration (jerk proxy)
        accelerations = np.diff(velocities) / dt[:-1]
        
        # Movement metrics
        total_distance = np.sum(np.sqrt(dx**2 + dy**2))
        straight_line_distance = euclidean([x_coords[0], y_coords[0]], [x_coords[-1], y_coords[-1]])
        
        # Smoothness metrics
        velocity_variance = np.var(velocities) if len(velocities) > 1 else 0
        acceleration_variance = np.var(accelerations) if len(accelerations) > 1 else 0
        path_efficiency = straight_line_distance / total_distance if total_distance > 0 else 0
        
        # Jitter metric (high frequency movement changes)
        if len(velocities) > 10:
            # Use high-pass filter to detect jitter
            b, a = signal.butter(3, 0.3, 'high')
            filtered_vel = signal.filtfilt(b, a, velocities)
            jitter_score = np.mean(np.abs(filtered_vel))
        else:
            jitter_score = velocity_variance
            
        return {
            'duration': timestamps[-1] - timestamps[0],
            'total_distance': total_distance,
            'straight_line_distance': straight_line_distance,
            'path_efficiency': path_efficiency,
            'avg_velocity': np.mean(velocities),
            'velocity_variance': velocity_variance,
            'acceleration_variance': acceleration_variance,
            'jitter_score': jitter_score,
            'num_points': len(event_data)
        }
    
    def identify_aiming_events(self, min_duration=0.1, min_distance=50):
        """Identify potential aiming events from mouse movement data"""
        if self.data is None:
            print("No data loaded. Call load_data() first.")
            return
            
        # Filter only movement events
        move_data = self.data[self.data['event'] == 'move'].copy()
        move_data = move_data.sort_values('time').reset_index(drop=True)
        
        if len(move_data) < 10:
            print("Not enough movement data to analyze.")
            return
            
        # Group consecutive movements into potential aiming sequences
        aiming_events = []
        current_sequence = []
        last_time = 0
        
        for idx, row in move_data.iterrows():
            # Start new sequence if gap > 0.5 seconds or first event
            if row['time'] - last_time > 0.5 or idx == 0:
                if len(current_sequence) > 0:
                    # Process previous sequence
                    seq_df = pd.DataFrame(current_sequence)
                    metrics = self.calculate_movement_metrics(seq_df)
                    
                    if (metrics and 
                        metrics['duration'] >= min_duration and 
                        metrics['total_distance'] >= min_distance):
                        
                        metrics['start_time'] = seq_df['time'].iloc[0]
                        metrics['end_time'] = seq_df['time'].iloc[-1]
                        metrics['start_pos'] = (seq_df['x'].iloc[0], seq_df['y'].iloc[0])
                        metrics['end_pos'] = (seq_df['x'].iloc[-1], seq_df['y'].iloc[-1])
                        aiming_events.append(metrics)
                
                current_sequence = [row.to_dict()]
            else:
                current_sequence.append(row.to_dict())
                
            last_time = row['time']
        
        # Process final sequence
        if len(current_sequence) > 0:
            seq_df = pd.DataFrame(current_sequence)
            metrics = self.calculate_movement_metrics(seq_df)
            
            if (metrics and 
                metrics['duration'] >= min_duration and 
                metrics['total_distance'] >= min_distance):
                
                metrics['start_time'] = seq_df['time'].iloc[0]
                metrics['end_time'] = seq_df['time'].iloc[-1]
                metrics['start_pos'] = (seq_df['x'].iloc[0], seq_df['y'].iloc[0])
                metrics['end_pos'] = (seq_df['x'].iloc[-1], seq_df['y'].iloc[-1])
                aiming_events.append(metrics)
        
        self.aiming_events = aiming_events
        print(f"Identified {len(aiming_events)} aiming events")
    
    def categorize_events(self):
        """Categorize aiming events as smooth or jittery"""
        if not self.aiming_events:
            print("No aiming events to categorize. Run identify_aiming_events() first.")
            return
        
        smooth_events = []
        jittery_events = []
        
        # Calculate thresholds based on data distribution
        jitter_scores = [event['jitter_score'] for event in self.aiming_events]
        velocity_variances = [event['velocity_variance'] for event in self.aiming_events]
        path_efficiencies = [event['path_efficiency'] for event in self.aiming_events]
        
        jitter_threshold = np.percentile(jitter_scores, 70)  # Top 30% are jittery
        velocity_var_threshold = np.percentile(velocity_variances, 70)
        efficiency_threshold = np.percentile(path_efficiencies, 30)  # Bottom 30% are inefficient
        
        for event in self.aiming_events:
            # Classify as jittery if high jitter OR high velocity variance OR low efficiency
            is_jittery = (event['jitter_score'] > jitter_threshold or 
                         event['velocity_variance'] > velocity_var_threshold or
                         event['path_efficiency'] < efficiency_threshold)
            
            if is_jittery:
                jittery_events.append(event)
            else:
                smooth_events.append(event)
        
        print(f"Categorized events:")
        print(f"  Smooth events: {len(smooth_events)}")
        print(f"  Jittery events: {len(jittery_events)}")
        
        return smooth_events, jittery_events
    
    def generate_report(self, output_file="mouse_analysis_report.txt"):
        """Generate a detailed analysis report"""
        if not self.aiming_events:
            print("No aiming events to report. Run analysis first.")
            return
            
        smooth_events, jittery_events = self.categorize_events()
        
        with open(output_file, 'w') as f:
            f.write("MOUSE MOVEMENT ANALYSIS REPORT\n")
            f.write("=" * 40 + "\n\n")
            
            f.write(f"Total aiming events identified: {len(self.aiming_events)}\n")
            f.write(f"Smooth events: {len(smooth_events)}\n")
            f.write(f"Jittery events: {len(jittery_events)}\n\n")
            
            # Summary statistics
            all_durations = [e['duration'] for e in self.aiming_events]
            all_distances = [e['total_distance'] for e in self.aiming_events]
            all_efficiencies = [e['path_efficiency'] for e in self.aiming_events]
            
            f.write("OVERALL STATISTICS:\n")
            f.write(f"Average duration: {np.mean(all_durations):.3f}s\n")
            f.write(f"Average distance: {np.mean(all_distances):.1f} pixels\n")
            f.write(f"Average path efficiency: {np.mean(all_efficiencies):.3f}\n\n")
            
            # Smooth events analysis
            if smooth_events:
                smooth_durations = [e['duration'] for e in smooth_events]
                smooth_distances = [e['total_distance'] for e in smooth_events]
                smooth_efficiencies = [e['path_efficiency'] for e in smooth_events]
                
                f.write("SMOOTH EVENTS:\n")
                f.write(f"Average duration: {np.mean(smooth_durations):.3f}s\n")
                f.write(f"Average distance: {np.mean(smooth_distances):.1f} pixels\n")
                f.write(f"Average efficiency: {np.mean(smooth_efficiencies):.3f}\n\n")
            
            # Jittery events analysis
            if jittery_events:
                jittery_durations = [e['duration'] for e in jittery_events]
                jittery_distances = [e['total_distance'] for e in jittery_events]
                jittery_efficiencies = [e['path_efficiency'] for e in jittery_events]
                
                f.write("JITTERY EVENTS:\n")
                f.write(f"Average duration: {np.mean(jittery_durations):.3f}s\n")
                f.write(f"Average distance: {np.mean(jittery_distances):.1f} pixels\n")
                f.write(f"Average efficiency: {np.mean(jittery_efficiencies):.3f}\n\n")
        
        print(f"Report saved to {output_file}")

def analyze_mouse_csv(csv_file_path):
    """Main function to analyze a mouse tracking CSV file"""
    print(f"Analyzing mouse data from: {csv_file_path}")
    
    analyzer = MouseDataAnalyzer(csv_file_path)
    
    if not analyzer.load_data():
        return
    
    # Identify aiming events
    analyzer.identify_aiming_events(min_duration=0.1, min_distance=30)
    
    if not analyzer.aiming_events:
        print("No aiming events found with current criteria.")
        return
    
    # Categorize events
    smooth_events, jittery_events = analyzer.categorize_events()
    
    # Generate report
    analyzer.generate_report()
    
    return analyzer, smooth_events, jittery_events

if __name__ == "__main__":
    # Default path from mouse tracker
    default_csv = os.path.expanduser("~/Documents/MouseLogs/mouse_log.csv")
    
    if os.path.exists(default_csv):
        analyzer, smooth, jittery = analyze_mouse_csv(default_csv)
        
        print("\nAnalysis complete!")
        print("Check 'mouse_analysis_report.txt' for detailed results.")
    else:
        print(f"No mouse log file found at {default_csv}")
        print("Please run the mouse tracker first to collect data.")
