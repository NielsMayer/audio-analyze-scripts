import sys
import json
from pathlib import Path
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def get_active_regions(times, energies, threshold=0.25):
    """Identify contiguous timeline blocks where band energy exceeds a threshold."""
    regions = []
    start_t = None
    in_region = False
    
    for t, e in zip(times, energies):
        if e >= threshold and not in_region:
            start_t = t
            in_region = True
        elif e < threshold and in_region:
            regions.append({"start": start_t, "end": t})
            in_region = False
            
    if in_region:
        regions.append({"start": start_t, "end": times[-1]})
    return regions

def main():
    if len(sys.argv) < 2:
        print("Usage: python generate_lanes.py <mediafilename.ext>")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    base_name = input_path.stem
    dir_name = input_path.parent

    # Resolve necessary files, dropping the empty spectrogram.json
    wave_path = dir_name / f"{base_name}.waveform.json"
    lufs_path = dir_name / f"{base_name}.loudness.json"
    meta_path = dir_name / f"{base_name}.metadata.json"

    for path in [wave_path, lufs_path, meta_path]:
        if not path.exists():
            print(f"Error: Required file {path} is missing.")
            sys.exit(1)

    with open(wave_path) as f: wave_data = json.load(f)
    with open(lufs_path) as f: lufs_data = json.load(f)
    with open(meta_path) as f: meta_data = json.load(f)

    # 1. Extract Waveform Data
    wave_times = [w['time'] for w in wave_data['waveform']]
    max_amp = [w['maxAmplitude'] for w in wave_data['waveform']]
    min_amp = [w['minAmplitude'] for w in wave_data['waveform']]
    
    # 2. Extract Band Energies
    low_energy = [w['bandEnergy']['low'] for w in wave_data['waveform']]
    mid_energy = [w['bandEnergy']['mid'] for w in wave_data['waveform']]
    high_energy = [w['bandEnergy']['high'] for w in wave_data['waveform']]

    # Generate contiguous active regions
    low_regions = get_active_regions(wave_times, low_energy)
    mid_regions = get_active_regions(wave_times, mid_energy)
    high_regions = get_active_regions(wave_times, high_energy)

    # 3. Extract LUFS
    duration = meta_data['file']['durationSeconds']
    lufs_values = lufs_data['momentaryLUFS']['values']
    lufs_times = np.linspace(0, duration, len(lufs_values))

    # Build the 3-row dashboard
    fig = make_subplots(
        rows=3, cols=1, 
        shared_xaxes=True,
        vertical_spacing=0.08,
        subplot_titles=("Waveform Envelope", "Band Activation Extents", "Loudness (Momentary LUFS)"),
        row_heights=[0.3, 0.4, 0.3]
    )

    # Row 1: Waveform
    fig.add_trace(go.Scatter(
        x=wave_times + wave_times[::-1],
        y=max_amp + min_amp[::-1],
        fill='toself', fillcolor='rgba(150, 150, 150, 0.8)',
        line=dict(color='rgba(255,255,255,0)'),
        hoverinfo="skip", name="Waveform"
    ), row=1, col=1)

    # Row 2: Band Extents
    colors = {"Low": "#ff3366", "Mid": "#ff6699", "High": "#ff9933"} # Reddish-pink to orange palette
    y_positions = {"Low": 1, "Mid": 2, "High": 3}

    def draw_lanes(regions, band_name):
        for r in regions:
            fig.add_shape(
                type="rect",
                x0=r["start"], y0=y_positions[band_name] - 0.25,
                x1=r["end"], y1=y_positions[band_name] + 0.25,
                fillcolor=colors[band_name],
                line=dict(width=0),
                opacity=0.8,
                row=2, col=1
            )

    draw_lanes(low_regions, "Low")
    draw_lanes(mid_regions, "Mid")
    draw_lanes(high_regions, "High")

    # Add invisible scatter markers to populate the legend neatly
    for band in ["Low", "Mid", "High"]:
        fig.add_trace(go.Scatter(
            x=[None], y=[y_positions[band]], mode="markers", 
            marker=dict(color=colors[band], symbol="square", size=10),
            name=f"{band} Active"
        ), row=2, col=1)

    # Row 3: LUFS
    fig.add_trace(go.Scatter(
        x=lufs_times, y=lufs_values,
        mode='lines', line=dict(color='#cc33ff', width=2),
        name="LUFS"
    ), row=3, col=1)

    # Styling
    fig.update_layout(
        title=f"TrainsPODder Analysis: {input_path.name}",
        template="plotly_dark",
        plot_bgcolor='#111111', paper_bgcolor='#111111',
        hovermode="x unified", height=800,
        margin=dict(l=60, r=40, t=80, b=40)
    )

    fig.update_yaxes(title_text="Amplitude", row=1, col=1, range=[-1.1, 1.1])
    fig.update_yaxes(
        tickmode="array", tickvals=[1, 2, 3], ticktext=["Low", "Mid", "High"],
        range=[0.5, 3.5], showgrid=False, row=2, col=1
    )
    fig.update_yaxes(title_text="LUFS", row=3, col=1)
    fig.update_xaxes(title_text="Time (Seconds)", row=3, col=1)

    output_filename = dir_name / f"{base_name}_lanes.html"
    fig.write_html(str(output_filename))
    print(f"Generated annotation lanes dashboard: {output_filename}")

if __name__ == "__main__":
    main()