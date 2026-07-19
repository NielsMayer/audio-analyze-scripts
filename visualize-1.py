import sys
import json
from pathlib import Path
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def main():
    # 1. Handle Command Line Arguments
    if len(sys.argv) < 2:
        print("Usage: python generate_audio_dashboard.py <mediafilename.ext>")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    
    # Extract the base name (e.g., "audio" from "audio.webm")
    base_name = input_path.stem
    dir_name = input_path.parent

    # Construct the expected JSON filenames based on the base name
    spec_path = dir_name / f"{base_name}.spectrogram.json"
    wave_path = dir_name / f"{base_name}.waveform.json"
    lufs_path = dir_name / f"{base_name}.loudness.json"
    meta_path = dir_name / f"{base_name}.metadata.json"

    # 2. Verify all required files exist before attempting to load
    required_files = [spec_path, wave_path, lufs_path, meta_path]
    missing_files = [f for f in required_files if not f.exists()]
    
    if missing_files:
        print("Error: The following required JSON files are missing:")
        for missing in missing_files:
            print(f"  - {missing}")
        sys.exit(1)

    # 3. Load the Data
    print(f"Loading data for {input_path.name}...")
    with open(spec_path) as f: spec_data = json.load(f)
    with open(wave_path) as f: wave_data = json.load(f)
    with open(lufs_path) as f: lufs_data = json.load(f)
    with open(meta_path) as f: meta_data = json.load(f)

    # 4. Extract Data for Plotly
    times = spec_data['timesSeconds']
    freqs = spec_data['frequenciesHz']
    
    # Transpose spectrogram magnitudes for Plotly Heatmap
    magnitudes = [frame['magnitudes'] for frame in spec_data['spectrogram']]
    Z = np.array(magnitudes).T 

    wave_times = [w['time'] for w in wave_data['waveform']]
    max_amp = [w['maxAmplitude'] for w in wave_data['waveform']]
    min_amp = [w['minAmplitude'] for w in wave_data['waveform']]
    rms = [w['rms'] for w in wave_data['waveform']]

    low_energy = [w['bandEnergy']['low'] for w in wave_data['waveform']]
    mid_energy = [w['bandEnergy']['mid'] for w in wave_data['waveform']]
    high_energy = [w['bandEnergy']['high'] for w in wave_data['waveform']]

    # Calculate LUFS x-axis based on duration provided in metadata
    duration = meta_data['file']['durationSeconds']
    lufs_values = lufs_data['momentaryLUFS']['values']
    lufs_times = np.linspace(0, duration, len(lufs_values))

    # 5. Build the Dashboard
    print("Generating visual dashboard...")
    fig = make_subplots(
        rows=4, cols=1, 
        shared_xaxes=True,
        vertical_spacing=0.05,
        subplot_titles=(
            "Spectral Heatmap (dB)", 
            "Amplitude Envelope & RMS", 
            "Band Energy Dynamics", 
            "Loudness (Momentary LUFS)"
        ),
        row_heights=[0.4, 0.2, 0.2, 0.2]
    )

    # Spectrogram
    fig.add_trace(go.Heatmap(
        z=Z, x=times, y=freqs, 
        colorscale='Inferno',
        zmin=-120, zmax=0,
        showscale=False,
        name="Spectrogram"
    ), row=1, col=1)

    # Waveform Min/Max Envelope
    fig.add_trace(go.Scatter(
        x=wave_times + wave_times[::-1],
        y=max_amp + min_amp[::-1],
        fill='toself',
        fillcolor='rgba(0, 255, 204, 0.2)',
        line=dict(color='rgba(255,255,255,0)'),
        hoverinfo="skip",
        name="Amplitude Envelope"
    ), row=2, col=1)

    # Waveform RMS
    fig.add_trace(go.Scatter(
        x=wave_times, y=rms,
        mode='lines',
        line=dict(color='#00ffcc', width=1.5),
        name="RMS"
    ), row=2, col=1)

    # Band Energies
    fig.add_trace(go.Scatter(
        x=wave_times, y=low_energy, mode='lines', line=dict(width=0),
        stackgroup='one', fillcolor='rgba(255, 51, 102, 0.6)', name="Low Energy"
    ), row=3, col=1)

    fig.add_trace(go.Scatter(
        x=wave_times, y=mid_energy, mode='lines', line=dict(width=0),
        stackgroup='one', fillcolor='rgba(255, 153, 51, 0.6)', name="Mid Energy"
    ), row=3, col=1)

    fig.add_trace(go.Scatter(
        x=wave_times, y=high_energy, mode='lines', line=dict(width=0),
        stackgroup='one', fillcolor='rgba(51, 204, 255, 0.6)', name="High Energy"
    ), row=3, col=1)

    # LUFS
    fig.add_trace(go.Scatter(
        x=lufs_times, y=lufs_values,
        mode='lines', line=dict(color='#ff00ff', width=2),
        name="Momentary LUFS"
    ), row=4, col=1)

    # Dashboard Styling
    fig.update_layout(
        title=f"Audio Analysis Dashboard: {input_path.name}",
        template="plotly_dark",
        plot_bgcolor='rgba(15, 15, 20, 1)',
        paper_bgcolor='rgba(10, 10, 15, 1)',
        hovermode="x unified",
        showlegend=True,
        height=1000
    )

    fig.update_yaxes(type="log", title_text="Frequency (Hz)", row=1, col=1, range=[np.log10(20), np.log10(24000)])
    fig.update_yaxes(title_text="Amplitude", row=2, col=1)
    fig.update_yaxes(title_text="Energy %", row=3, col=1, range=[0, 1])
    fig.update_yaxes(title_text="LUFS", row=4, col=1)
    fig.update_xaxes(title_text="Time (Seconds)", row=4, col=1)

    # 6. Export Output
    output_filename = dir_name / f"{base_name}_dashboard.html"
    fig.write_html(str(output_filename))
    print(f"Success! Dashboard saved to: {output_filename}")

if __name__ == "__main__":
    main()
