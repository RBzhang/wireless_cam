# wireless-cam

GNU Radio 3.10.12.0 project transmitting images over wireless via Phase Modulation (PM).

## Flow graphs

- **`pm_tx.grc`** — GNU Radio Companion source. Edit this in GRC, then regenerate `pm_tx.py`.
- **`pm_tx.py`** — PM transmitter + receiver. Reads `1920x1080.jpg`, modulates phase, demodulates, saves `received.png`. Launches a Qt GUI with a gain slider and live received-image preview.

## Custom blocks

| Block file | Type | What it does |
|---|---|---|
| `_image_source_impl.py` | source | Loads image (PIL, grayscale), outputs `np.uint8` bytes |
| `_image_sink_impl.py` | sink | Accumulates bytes, reconstructs grayscale image, saves PNG + optional Qt preview |

Thin wrappers (`pm_tx_epy_block_0.py`, `pm_tx_image_byte_source_0.py`) re-export these for GRC embedding.

## Run

```bash
python3 pm_tx.py       # PM image tx/rx (Qt GUI)
```

## Dependencies

- `gnuradio` 3.10.12.0 (system install: `/usr/bin/gnuradio-companion`)
- `python3`, `numpy`, `Pillow`, `PyQt5`

## Key conventions

- Image pipeline: JPEG → grayscale bytes → float [0,1] → multiply by `max_phase` (π/3) → PM → demod → `* 3/π` → uchar → PNG
- Hardcoded absolute paths in `.grc`/`.py` — update `image_path`/`output_path` when moving files.
- `image_byte_sink` `display=True` opens a live preview window.
- No package manager, no tests, no CI, not a git repo.
