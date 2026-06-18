import numpy as np
from gnuradio import gr


class pilot_sync(gr.sync_block):
    def __init__(self, sync_len=60, pilot_len=1024, frame_size=4000):
        gr.sync_block.__init__(
            self,
            name='Pilot Sync & Phase Correction',
            in_sig=[np.float32],
            out_sig=[np.float32]
        )
        self.sync_len = sync_len
        self.pilot_len = pilot_len
        self.frame_size = frame_size
        self.expected_amp = np.pi / 3

        self.state = 'SEARCHING'
        self.buf = []
        self.pilot_samples = []
        self.phi_est = 0.0
        self._active_count = 0

    def _detect_sync(self, buf):
        a = np.unwrap(np.array(buf, dtype=np.float64))
        amp = np.ptp(a)
        if amp < 0.5:
            return False, (amp, 0, 0)
        edge = np.mean(a[0:10]) + np.mean(a[50:60])
        center = np.mean(a[25:35]) * 2
        diff = abs(edge - center)
        if diff > 0.5:
            return True, (amp, diff, 0)
        return False, (amp, diff, 0)

    def work(self, input_items, output_items):
        in0 = input_items[0]
        out0 = output_items[0]
        n = len(in0)

        for i in range(n):
            sample = float(in0[i])

            if self.state == 'SEARCHING':
                out0[i] = 0.0
                self.buf.append(sample)
                if len(self.buf) > self.sync_len:
                    self.buf.pop(0)

                if len(self.buf) == self.sync_len:
                    ok, stats = self._detect_sync(self.buf)
                    if ok:
                        print(f"[Pilot Sync] Sync detected! "
                              f"amp={stats[0]:.3f} diff={stats[1]:.3f}",
                              flush=True)
                        self.state = 'PILOT'
                        self.buf = []

            elif self.state == 'PILOT':
                out0[i] = 0.0
                self.pilot_samples.append(sample)
                if len(self.pilot_samples) >= self.pilot_len:
                    self.phi_est = np.mean(self.pilot_samples)
                    print(f"[Pilot Sync] Pilot done. "
                          f"\u03c6_est = {self.phi_est:.4f} rad",
                          flush=True)
                    self.state = 'ACTIVE'
                    self.pilot_samples = []

            else:
                corrected = sample - self.phi_est
                out0[i] = corrected
                self._active_count += 1
                if self.frame_size > 0 and self._active_count >= self.frame_size:
                    print(f"[Pilot Sync] Frame done, "
                          f"re-searching...", flush=True)
                    self.state = 'SEARCHING'
                    self.buf = []
                    self._active_count = 0

        return n
