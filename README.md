# wireless-cam

GNU Radio 3.10.12.0 project for transmitting grayscale images over a wireless
Phase Modulation (PM) link using USRP hardware.

## Flow Graphs (by priority)

### 1. `pm_rx_usrp` — Primary Receiver

The main receive-only flow graph. It simultaneously transmits a constant complex
carrier and receives a PM-modulated image signal from a remote transmitter.

| Parameter | Value |
|---|---|
| Center frequency | 400 MHz |
| Sample rate | 200 kS/s |
| Digital IF | 10 kHz |
| Frame size | 500 × 500 |
| Sync thresholds | corr > 0.90, amp > 0.4, noise < 0.35 |
| Auto phase scale | Enabled |

**RX signal chain:**

```
USRP Source (400 MHz, RX2)
  → Rotator (-IF) [digital downconversion]
  → Complex to MagPhase
       Mag  → Null Sink
       Phase → pilot_sync [Barker-13 detection + phase correction]
           → * (3/π) [undo PM scaling]
           → Rail [0, 1]
           → Float to UChar (*255)
           → image_byte_sink → received.png
```

**TX signal chain (carrier reference):**

```
Constant Source (1+0j) → Rotator (+IF) → USRP Sink (400 MHz, TX/RX)
```

**Run:**

```bash
python3 pm_rx_usrp.py
```

**Generated wrappers:** `pm_rx_usrp_epy_block_0.py`, `pm_rx_usrp_pilot_sync_0.py`

---

### 2. `pm_loop_usrp` — Primary Transmitter + Receiver

The original combined TX/RX flow graph running both sides in a single process.
Intended for loopback testing with a single USRP.

| Parameter | Value |
|---|---|
| Center frequency | 900 MHz |
| Sample rate | 500 kS/s |
| Digital IF | 100 kHz |
| Frame size | 1920 × 1080 |
| Image source | `scene1920x1080.jpg` |
| Modulation depth | π/3 |

**Run:**

```bash
python3 pm_loop_usrp.py
```

**Generated wrappers:** `pm_loop_usrp_epy_block_0.py`,
`pm_loop_usrp_image_byte_source_0.py`, `pm_loop_usrp_pilot_sync_0.py`

---

### 3. `pm_loop_sim` — Simulated Loopback

Simulation-only variant of `pm_loop_usrp`. No USRP hardware required. Useful for
algorithm development and debugging without RF.

**Run:**

```bash
python3 pm_loop_sim.py
```

---

### 4. `PM_400M_test` — Hardware Loopback Test

Minimal RF sanity check: transmits a constant carrier at 400 MHz and monitors
the received IQ and phase on the same USRP.

| Parameter | Value |
|---|---|
| Center frequency | 400 MHz |
| Sample rate | 100 kS/s |
| Digital IF | 10 kHz |
| Image / sync | None |

**Run:**

```bash
python3 PM.py
```

---

### 5. `pm_tx` — Legacy Transmitter

Older PM transmit-only flow graph. Changes here are independent of
`pm_loop_usrp` and `pm_rx_usrp`.

---

### 6. `b210test` — B210 Hardware Test

Separate flow graph for testing USRP B210 hardware separately from the image
transmission chain.

---

## Custom Blocks

| Block | Type | File | Description |
|---|---|---|---|
| Image Source | source | `_image_source_impl.py` | Loads image via Pillow, converts to grayscale, prepends 416-sample Barker-13 sync word, emits `uint8` samples in repeat mode |
| Pilot Sync | variable-rate | `_pilot_sync_impl.py` | Detects Barker-13 sync via vectorized normalized correlation, removes constant phase + linear trend, outputs `frame_size` corrected phase samples |
| Image Sink | sink | `_image_sink_impl.py` | Accumulates `width × height` bytes, saves grayscale PNG, optionally displays in Qt window |

Generated wrapper modules (`*_epy_block_0.py`, `*_pilot_sync_0.py`,
`*_image_byte_source_0.py`) re-export these implementations for GRC embedded
Python blocks.

## Framing and Synchronization

- **Sync word:** Barker-13 `[+ + + + + − − + + − + − +]`
- **Samples per chip:** 32
- **Total preamble:** 416 samples
- **Image phase range:** 0 to π/3
- **Default thresholds:** correlation > 0.94, amplitude > 0.4, residual noise < 0.35
- **No stream tags** — synchronization works over RF between separate Tx and Rx processes

At 500 kS/s, a 1920×1080 frame plus preamble lasts ~4.15 seconds. A receiver
started mid-frame waits up to one frame period for the next sync word, then
another frame period to accumulate a complete image.

## Signal Path

```
JPEG/PNG
  → grayscale uint8
  → /255
  → × (π/3)
  → complex PM
  → USRP TX → RF → USRP RX
  → complex phase
  → Barker sync + zero-code phase correction
  → × (3/π)
  → rail [0, 1]
  → ×255 → uint8
  → received.png
```

## Dependencies

- GNU Radio 3.10.12.0
- UHD with compatible USRP hardware
- Python 3
- NumPy
- Pillow
- PyQt5

## Validation

Compile-check all custom blocks and primary flow graphs:

```bash
python3 -m py_compile \
  _image_source_impl.py \
  _pilot_sync_impl.py \
  _image_sink_impl.py \
  pm_rx_usrp.py \
  pm_loop_usrp.py

PYTHONPATH="$PWD" grcc -o /tmp pm_rx_usrp.grc
PYTHONPATH="$PWD" grcc -o /tmp pm_loop_usrp.grc
```

For image quality, compare the source image with `received.png` after converting
both to grayscale. The last verified `scene1920x1080.jpg` → `received.png`
result was approximately 38.736 dB PSNR.

## File Overview

| File | Role |
|---|---|
| `pm_rx_usrp.grc` / `.py` | **Primary receiver** flow graph |
| `pm_loop_usrp.grc` / `.py` | Combined TX/RX flow graph |
| `pm_loop_sim.grc` / `.py` | Simulation-only flow graph |
| `PM_400M_test.grc` / `PM.py` | Hardware loopback test |
| `pm_tx.grc` / `.py` | Legacy TX-only flow graph |
| `b210test.grc` / `.py` | USRP B210 hardware test |
| `_image_source_impl.py` | Image source custom block |
| `_pilot_sync_impl.py` | Barker-13 sync custom block |
| `_image_sink_impl.py` | Image sink custom block |
| `phase_tx.dat` / `phase_rx.dat` | Optional float32 phase captures |
| `plot_float.py` | Utility for plotting float32 binary data |

## Conventions

- Make persistent changes in `.grc` files, then regenerate `.py` via `grcc`.
- Keep `.grc` and generated `.py` changes in the same commit.
- Do not use stream tags for RF synchronization.
- Do not add a software throttle in a hardware-timed USRP path.
- Absolute paths in GRC/Python files must be updated in both.
