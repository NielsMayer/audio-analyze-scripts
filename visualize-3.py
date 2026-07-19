import sys
import json
from pathlib import Path
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def build_extents(times, energies, threshold, label):
    """
    Converts continuous energy data into discrete horizontal line segments (extents)
    by inserting None gaps when the energy falls below the threshold.
    """
    x_vals = []
    y_vals = []
    is_active = False
    
    for t, e in zip(times, energies):
        if e >= threshold:
            if not is_active:
                x_vals.append(t)      # Start of extent
                y_vals.append(label)
                is_active = True
        else:
            if is_active:
                x_vals.append(t)      # End of extent
                y_vals.append(label)
                x_vals.append(None)   # Break the line
                y_vals.append(None)
                is_active = False
                
    if is_active:
        x_vals.append(times[-1])
        y_vals.append(label)
        
    return x_vals, y_vals

def main():
    # 1. Handle Command Line Arguments
    if len(sys.argv) < 2:
        print("Usage: python generate_extents_dashboard.py <mediafilename.ext>")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    base_name = input_path.stem
    dir_name = input_path.parent

    # We drop the empty spectrogram.json entirely for this approach
    wave_path = dir_name / f"{base_name}.waveform.json"
    lufs_path = dir_name / f"{base_name}.loudness.json"
    meta_path = dir_name / f"{base_name}.metadata.json"

    required_files = [wave_path, lufs_path, meta_path]
    missing_files = [f for f in required_files if not f.exists()]
    
    if missing_files:
        print("Error: The following required JSON files are missing:")
        for missing in missing_files:
            print(f"  - {missing}")
        sys.exit(1)

    # 2. Load the Data
    print(f"Loading data for {input_path.name}...")
    with open(wave_path) as f: wave_data = json.load(f)
    with open(lufs_path) as f: lufs_data = json.load(f)
    with open(meta_path) as f: meta_data = json.load(f)

    # 3. Extract Data
    wave_times = [w['time'] for w in wave_data['waveform']]
    max_amp = [w['maxAmplitude'] for w in wave_data['waveform']]
    min_amp = [w['minAmplitude'] for w in wave_data['waveform']]
    rms = [w['rms'] for w in wave_data['waveform']]

    low_energy = [w['bandEnergy']['low'] for w in wave_data['waveform']]
    mid_energy = [w['bandEnergy']['mid'] for w in wave_data['waveform']]
    high_energy = [w['bandEnergy']['high'] for w in wave_data['waveform']]

    # Calculate LUFS x-axis
    duration = meta_data['file']['durationSeconds']
    lufs_values = lufs_data['momentaryLUFS']['values']
    lufs_times = np.linspace(0, duration, len(lufs_values))

    # 4. Generate Horizontal Extents (Threshold set to 40% dominance)
    threshold = 0.40 
    x_low, y_low = build_extents(wave_times, low_energy, threshold, "Low")
    x_mid, y_mid = build_extents(wave_times, mid_energy, threshold, "Mid")
    x_high, y_high = build_extents(wave_times, high_energy, threshold, "High")

    # 5. Build the Dashboard
    print("Generating visual dashboard...")
    fig = make_subplots(
        rows=4, cols=1, 
        shared_xaxes=True,
        vertical_spacing=0.06,
        subplot_titles=(
            "Band Activation Extents (>40% Energy)", 
            "Band Energy Dynamics", 
            "Amplitude Envelope & RMS", 
            "Loudness (Momentary LUFS)"
        ),
        row_heights=[0.25, 0.25, 0.25, 0.25]
    )

    # Row 1: The new Horizontal Extents
    fig.add_trace(go.Scatter(x=x_low, y=y_low, mode='lines', line=dict(color='#ff3366', width=16), name="Low Active"), row=1, col=1)
    fig.add_trace(go.Scatter(x=x_mid, y=y_mid, mode='lines', line=dict(color='#ff9933', width=16), name="Mid Active"), row=1, col=1)
    fig.add_trace(go.Scatter(x=x_high, y=y_high, mode='lines', line=dict(color='#33ccff', width=16), name="High Active"), row=1, col=1)

    # Row 2: Retain the stacked area chart for raw comparison
    fig.add_trace(go.Scatter(x=wave_times, y=low_energy, mode='lines', line=dict(width=0), stackgroup='one', fillcolor='rgba(255, 51, 102, 0.6)', showlegend=False), row=2, col=1)
    fig.add_trace(go.Scatter(x=wave_times, y=mid_energy, mode='lines', line=dict(width=0), stackgroup='one', fillcolor='rgba(255, 153, 51, 0.6)', showlegend=False), row=2, col=1)
    fig.add_trace(go.Scatter(x=wave_times, y=high_energy, mode='lines', line=dict(width=0), stackgroup='one', fillcolor='rgba(51, 204, 255, 0.6)', showlegend=False), row=2, col=1)

    # Row 3: Waveform Envelope & RMS
    fig.add_trace(go.Scatter(x=wave_times + wave_times[::-1], y=max_amp + min_amp[::-1], fill='toself', fillcolor='rgba(0, 255, 204, 0.2)', line=dict(color='rgba(255,255,255,0)'), hoverinfo="skip", showlegend=False), row=3, col=1)
    fig.add_trace(go.Scatter(x=wave_times, y=rms, mode='lines', line=dict(color='#00ffcc', width=1.5), name="RMS"), row=3, col=1)

    # Row 4: LUFS
    fig.add_trace(go.Scatter(x=lufs_times, y=lufs_values, mode='lines', line=dict(color='#ff00ff', width=2), name="LUFS"), row=4, col=1)

    # Dashboard Styling
    fig.update_layout(
        title=f"TrainsPODder Analysis: {input_path.name}",
        template="plotly_dark",
        plot_bgcolor='rgba(15, 15, 20, 1)',
        paper_bgcolor='rgba(10, 10, 15, 1)',
        hovermode="x unified",
        height=1000,
        margin=dict(l=60, r=40, t=80, b=40)
    )

    fig.update_yaxes(title_text="Active Band", row=1, col=1)
    fig.update_yaxes(title_text="Energy %", row=2, col=1, range=[0, 1])
    fig.update_yaxes(title_text="Amplitude", row=3, col=1, range=[-1.1, 1.1])
    fig.update_yaxes(title_text="LUFS", row=4, col=1)
    fig.update_xaxes(title_text="Time (Seconds)", row=4, col=1)

    # 6. Export
    output_filename = dir_name / f"{base_name}_extents_dashboard.html"
    fig.write_html(str(output_filename))
    print(f"Success! Dashboard saved to: {output_filename}")

if __name__ == "__main__":
    main()