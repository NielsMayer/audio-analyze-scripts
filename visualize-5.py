import sys
import json
from pathlib import Path
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def main():
    if len(sys.argv) < 2:
        print("Usage: python generate_bands.py <mediafilename.ext>")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    base_name = input_path.stem
    dir_name = input_path.parent
    wave_path = dir_name / f"{base_name}.waveform.json"
    
    if not wave_path.exists():
        print(f"Error: {wave_path} not found.")
        sys.exit(1)

    with open(wave_path) as f:
        data = json.load(f)['waveform']

    # We map "Band Energy" to horizontal rectangles
    # Threshold determines the sensitivity of the 'banded' look
    threshold = 0.2 
    
    fig = go.Figure()

    # Define our layers (bottom to top)
    layers = [
        {"key": "low", "color": "#ff3366", "name": "Low"},
        {"key": "mid", "color": "#ff6699", "name": "Mid"},
        {"key": "high", "color": "#ff9933", "name": "High"}
    ]

    for i, layer in enumerate(layers):
        # Find active segments: where energy > threshold
        start = None
        for entry in data:
            val = entry['bandEnergy'][layer['key']]
            t = entry['time']
            
            if val > threshold and start is None:
                start = t
            elif val <= threshold and start is not None:
                # Add a horizontal bar
                fig.add_shape(type="rect", x0=start, y0=i, x1=t, y1=i+0.8,
                              fillcolor=layer['color'], line_width=0, opacity=0.9)
                start = None
        
        # Add a dummy trace for the legend
        fig.add_trace(go.Scatter(x=[None], y=[None], mode='markers',
                                 marker=dict(size=10, color=layer['color']),
                                 name=layer['name']))

    fig.update_layout(
        template="plotly_dark",
        title=f"Feature Extents: {base_name}",
        yaxis=dict(tickvals=[0.4, 1.4, 2.4], ticktext=["Low", "Mid", "High"]),
        xaxis_title="Time (s)",
        height=400,
        margin=dict(l=50, r=50, t=50, b=50)
    )

    output = dir_name / f"{base_name}_bands.html"
    fig.write_html(str(output))
    print(f"Generated banded visualization: {output}")

if __name__ == "__main__":
    main()