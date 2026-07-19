import sys
import json
from pathlib import Path
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def main():
    if len(sys.argv) < 2:
        print("Usage: python generate_audio_dashboard.py <mediafilename.ext>")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    base_name = input_path.stem
    dir_name = input_path.parent

    # We drop the spectrogram JSON requirement for this visualization
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

    print(f"Loading data for {input_path.name}...")
    with open(wave_path) as f: wave_data = json.load(f)
    with open(lufs_path) as f: lufs_data = json.load(f)
    with open(meta_path) as f: meta_data = json.load(f)

    # --- Extract Data ---
    wave_times = [w['time'] for w in wave_data['waveform']]
    max_amp = [w['maxAmplitude'] for w in wave_data['waveform']]
    min_amp = [w['minAmplitude'] for w in wave_data['waveform']]
    rms = [w['rms'] for w in wave_data['waveform']]
    centroid = [w['spectralCentroidHz'] for w in wave_data['waveform']]

    # Band Energies (0.0 to 1.0 representation)
    low_energy = [w['bandEnergy']['low'] for w in wave_data['waveform']]
    mid_energy = [w['bandEnergy']['mid'] for w in wave_data['waveform']]
    high_energy = [w['bandEnergy']['high'] for w in wave_data['waveform']]

    # Stack into a matrix for a crisp "Activation" Heatmap [Row 0=Low, Row 1=Mid, Row 2=High]
    band_matrix = np.array([low_energy, mid_energy, high_energy])

    # Calculate LUFS x-axis
    duration = meta_data['file']['durationSeconds']
    lufs_values = lufs_data['momentaryLUFS']['values']
    lufs_times = np.linspace(0, duration, len(lufs_values))

    # --- Build Dashboard ---
    print("Generating visual dashboard...")
    fig = make_subplots(
        rows=4, cols=1, 
        shared_xaxes=True,
        vertical_spacing=0.06,
        subplot_titles=(
            "Frequency Band Activity Matrix", 
            "Spectral Centroid (Brightness)",
            "Amplitude Envelope & RMS", 
            "Loudness (Momentary LUFS)"
        ),
        row_heights=[0.25, 0.25, 0.25, 0.25]
    )

    # 1. Band Activity Matrix (Heatmap)
    fig.add_trace(go.Heatmap(
        z=band_matrix,
        x=wave_times,
        y=["Low", "Mid", "High"],
        colorscale='Turbo', # 'Turbo' or 'Magma' look great for UI elements
        zmin=0, zmax=1,
        showscale=False,
        name="Band Activity"
    ), row=1, col=1)

    # 2. Spectral Centroid
    fig.add_trace(go.Scatter(
        x=wave_times, y=centroid,
        mode='lines',
        line=dict(color='#ff9933', width=1.5),
        name="Centroid (Hz)",
        fill='tozeroy',
        fillcolor='rgba(255, 153, 51, 0.1)'
    ), row=2, col=1)

    # 3. Waveform Min/Max & RMS
    fig.add_trace(go.Scatter(
        x=wave_times + wave_times[::-1],
        y=max_amp + min_amp[::-1],
        fill='toself',
        fillcolor='rgba(0, 255, 204, 0.2)',
        line=dict(color='rgba(255,255,255,0)'),
        hoverinfo="skip",
        name="Envelope"
    ), row=3, col=1)

    fig.add_trace(go.Scatter(
        x=wave_times, y=rms,
        mode='lines',
        line=dict(color='#00ffcc', width=1.5),
        name="RMS"
    ), row=3, col=1)

    # 4. LUFS
    fig.add_trace(go.Scatter(
        x=lufs_times, y=lufs_values,
        mode='lines', line=dict(color='#ff00ff', width=2),
        name="Momentary LUFS"
    ), row=4, col=1)

    # --- Styling ---
    fig.update_layout(
        title=f"TrainsPODder Analysis: {input_path.name}",
        template="plotly_dark",
        plot_bgcolor='rgba(15, 15, 20, 1)',
        paper_bgcolor='rgba(10, 10, 15, 1)',
        hovermode="x unified",
        showlegend=False, # Legend hidden to keep the UI clean; hover provides info
        height=900,
        margin=dict(l=60, r=40, t=80, b=40)
    )

    # Axes tuning
    fig.update_yaxes(title_text="Band", row=1, col=1)
    fig.update_yaxes(title_text="Hz", type="log", row=2, col=1, range=[np.log10(100), np.log10(10000)])
    fig.update_yaxes(title_text="Amplitude", row=3, col=1, range=[-1.1, 1.1])
    fig.update_yaxes(title_text="LUFS", row=4, col=1)
    fig.update_xaxes(title_text="Time (Seconds)", row=4, col=1)

    # --- Export ---
    output_filename = dir_name / f"{base_name}_dashboard.html"
    fig.write_html(str(output_filename))
    print(f"Success! Dashboard saved to: {output_filename}")

if __name__ == "__main__":
    main()