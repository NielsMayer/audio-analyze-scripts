# audio-analyze — Standalone CLI Audio/Video Analysis Suite

Unix command-line scripts that replicate the analysis pipeline from
[@counterpoint-studio/audio-file-mcp-app](https://github.com/counterpoint-studio/audio-file-mcp-app)
without any UI or MCP server overhead.

Pass any audio or video file to `audio-analyze` and it outputs four JSON files:

```
$ audio-analyze mytrack.wav
Analyzing: mytrack.wav
Outputs will be written to: mytrack.*.json
  ✓ metadata
  ✓ loudness
  ✓ waveform
  ✓ spectrogram
Done.

$ ls mytrack.*.json
mytrack.metadata.json    mytrack.loudness.json
mytrack.waveform.json    mytrack.spectrogram.json
```

## What each script produces

| Script | Output file | Contents |
|--------|-------------|----------|
| `audio-analyze-metadata` | `<file>.metadata.json` | Codecs, sample rate, channels, duration, bit rate, tags, chapters, video streams |
| `audio-analyze-loudness` | `<file>.loudness.json` | EBU R128: Integrated LUFS, LRA, True Peak, Sample Peak, RMS; plus momentary & short-term LUFS arrays |
| `audio-analyze-waveform` | `<file>.waveform.json` | Per-block amplitude envelope (min/max), RMS, spectral centroid, low/mid/high band-energy ratios |
| `audio-analyze-spectrogram` | `<file>.spectrogram.json` | Log-frequency spectrogram (dB magnitude), time/frequency axes, configurable resolution |

## Requirements

- **ffmpeg** and **ffprobe** (for demuxing, decoding, EBU R128)
- **python3** with **numpy** and **scipy**
- **jq** (for JSON merging in loudness script)

Install on macOS:
```bash
brew install ffmpeg jq python3
pip3 install numpy scipy
```

Install on Ubuntu/Debian:
```bash
sudo apt-get install ffmpeg jq python3 python3-pip
pip3 install numpy scipy
```

## Installation

```bash
git clone <repo>
cd audio-analyze-scripts
chmod +x audio-analyze*
# Optional: add to PATH
sudo ln -s "$PWD/audio-analyze" /usr/local/bin/audio-analyze
sudo ln -s "$PWD/audio-analyze-metadata" /usr/local/bin/audio-analyze-metadata
sudo ln -s "$PWD/audio-analyze-loudness" /usr/local/bin/audio-analyze-loudness
sudo ln -s "$PWD/audio-analyze-waveform" /usr/local/bin/audio-analyze-waveform
sudo ln -s "$PWD/audio-analyze-spectrogram" /usr/local/bin/audio-analyze-spectrogram
```

## Usage

### Master script (runs all analyses)
```bash
audio-analyze /path/to/mediafile.mp3
```

### Individual scripts (pipe JSON to stdout)
```bash
audio-analyze-metadata song.flac > song.metadata.json
audio-analyze-loudness song.flac > song.loudness.json
audio-analyze-waveform song.flac > song.waveform.json
audio-analyze-spectrogram song.flac > song.spectrogram.json
```

### Environment variables for tuning

| Variable | Default | Description |
|----------|---------|-------------|
| `WAVEFORM_POINTS` | `2000` | Number of waveform data points |
| `SPECTROGRAM_BINS` | `256` | Frequency resolution (log bins) |
| `SPECTROGRAM_FRAMES` | `512` | Max time frames in spectrogram |
| `SPECTROGRAM_FFT` | `2048` | FFT window size |
| `SPECTROGRAM_HOP` | `512` | FFT hop size |

Example:
```bash
WAVEFORM_POINTS=4000 SPECTROGRAM_BINS=512 audio-analyze podcast.mp3
```

## Output schema examples

### metadata.json
```json
{
  "file": { "path": "...", "sizeBytes": 16400000, "durationSeconds": 270.0, ... },
  "audio": [{ "codecName": "flac", "sampleRate": 48000, "channels": 2, ... }],
  "video": [...],
  "subtitles": [...],
  "formatTags": { "TITLE": "My Song", "ARTIST": "Artist Name" }
}
```

### loudness.json
```json
{
  "file": "...",
  "global": {
    "integratedLUFS": -19.0,
    "loudnessRangeLU": 8.5,
    "truePeakDBTP": -4.1,
    "samplePeakDB": -4.1,
    "rmsDB": -21.5,
    "rmsLinear": 0.084
  },
  "momentaryLUFS": { "values": [...], "mean": -18.2, "max": -12.0, "min": -25.0 },
  "shortTermLUFS": { "values": [...], "mean": -19.1, "max": -15.0, "min": -22.0 }
}
```

### waveform.json
```json
{
  "durationSeconds": 270.0,
  "points": 2000,
  "waveform": [
    { "time": 0.0, "minAmplitude": -0.05, "maxAmplitude": 0.06,
      "rms": 0.01, "spectralCentroidHz": 850.0,
      "bandEnergy": { "low": 0.3, "mid": 0.5, "high": 0.2 } },
    ...
  ]
}
```

### spectrogram.json
```json
{
  "sampleRate": 48000,
  "durationSeconds": 270.0,
  "fftSize": 2048,
  "frequencyBins": 256,
  "timeFrames": 512,
  "frequenciesHz": [20.0, 21.2, 22.5, ...],
  "timesSeconds": [0.0, 0.01, 0.02, ...],
  "spectrogram": [
    { "time": 0.0, "magnitudes": [-80.2, -75.1, ...] },
    ...
  ]
}
```

## License

ISC (same as the original audio-file-mcp-app)
