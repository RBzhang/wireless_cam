# wireless-cam

GNU Radio 3.10.12.0 project for transmitting grayscale images over a
wireless PM link using USRP hardware.

## Primary flow graph

- **`pm_loop_usrp.grc`** - GNU Radio Companion source. Make persistent
  flow-graph changes here, then regenerate `pm_loop_usrp.py`.
- **`pm_loop_usrp.py`** - Generated Qt application containing the PM
  transmitter and receiver. The current image source is
  `scene1920x1080.jpg`; received frames are saved to `received.png`.
- **`pm_tx.grc` / `pm_tx.py`** - Older PM flow graph. Do not assume changes
  made here affect `pm_loop_usrp`.
- **`b210test.grc` / `b210test.py`** - Separate USRP B210 test flow graph.

Run the primary application with:

```bash
python3 pm_loop_usrp.py
```

## Custom blocks

| Block file | Type | Responsibility |
|---|---|---|
| `_image_source_impl.py` | source | Loads an image with Pillow, converts it to grayscale, prepends a 416-sample Barker-13 sync word and a 1024-sample zero pilot, then emits `np.uint8` samples. Repeat mode must preserve `self.pos` across GNU Radio `work()` calls. |
| `_pilot_sync_impl.py` | variable-rate block | Searches the received phase stream for the Barker sync word using vectorized normalized correlation after removing constant phase and linear trend. It consumes sync/pilot samples without output, estimates pilot phase, and outputs exactly `frame_size` corrected image-phase samples. |
| `_image_sink_impl.py` | sink | Accumulates `width * height` bytes, saves a grayscale PNG, and optionally updates a Qt preview. The primary flow uses `skip_each_frame=0` because the synchronizer removes the preamble. |

The generated wrapper modules named `pm_loop_usrp_*` and `pm_tx_*` re-export
these implementations for GRC embedded Python blocks.

## Current framing and synchronization

- Sync word: Barker-13 chips
  `[+ + + + + - - + + - + - +]`.
- Samples per chip: 32.
- Total sync length: 416 samples.
- Pilot length: 1024 zero-valued image samples.
- Image phase range: `0` to `pi/3`.
- Receiver sync thresholds in `_pilot_sync_impl.py`:
  correlation `> 0.94`, amplitude `> 0.4`, residual noise `< 0.35`.
- Synchronization does not use stream tags. This is intentional so separate
  transmitter and receiver processes work over the RF link.
- Before converting corrected values to `uint8`, the primary flow rails the
  normalized signal to `[0, 1]` to prevent values above 255 from wrapping to
  black.

At the current sample rate of 500 kS/s, a 1920x1080 frame plus preamble lasts
about 4.15 seconds. A receiver started in the middle of a frame may wait up to
one complete frame period for the next sync word, then another frame period to
save a complete image.

## Signal path

```text
JPEG/PNG
  -> grayscale uint8
  -> /255
  -> * (pi/3)
  -> complex PM
  -> USRP TX/RX
  -> complex phase
  -> Barker sync + pilot phase correction
  -> * (3/pi)
  -> rail [0,1]
  -> *255 and uint8
  -> received.png
```

`phase_tx.dat` and `phase_rx.dat` are optional float32 phase captures used for
offline diagnosis. They can be large and may be truncated when a new run opens
the file sinks.

## Dependencies

- GNU Radio 3.10.12.0
- UHD and compatible USRP hardware
- Python 3
- NumPy
- Pillow
- PyQt5

## Validation

There is no automated test suite or CI. Before committing DSP changes:

```bash
python3 -m py_compile \
  _image_source_impl.py \
  _pilot_sync_impl.py \
  _image_sink_impl.py \
  pm_loop_usrp.py

PYTHONPATH="$PWD" grcc -o /tmp pm_loop_usrp.grc
```

For image quality, compare the configured source image with `received.png`
after converting both to grayscale. The last verified
`scene1920x1080.jpg`/`received.png` result was approximately 38.736 dB PSNR.

## Repository conventions

- Absolute image/output paths currently exist in the GRC and generated Python
  files. Update both or regenerate Python after changing the GRC.
- Keep `.grc` and generated `.py` changes consistent in the same commit.
- Do not reintroduce `frame_start` stream tags for RF synchronization.
- Do not add a software throttle in a hardware-timed USRP path.
- The worktree may contain local images, phase captures, and unrelated
  diagnostics. Stage only files belonging to the requested change.
