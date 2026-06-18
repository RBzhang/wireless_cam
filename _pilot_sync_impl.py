import numpy as np
from gnuradio import gr


class pilot_sync(gr.sync_block):
    def __init__(self, sync_len=64, pilot_len=1024, diff_thresh=0.3,
                 min_matching_diffs=30):
        gr.sync_block.__init__(
            self,
            name='Pilot Sync & Phase Correction',
            in_sig=[np.float32],
            out_sig=[np.float32]
        )
        self.sync_len = sync_len
        self.pilot_len = pilot_len
        self.diff_thresh = diff_thresh
        self.min_matching_diffs = min_matching_diffs
        self.expected_diff = np.pi / 3

        self.state = 'SEARCHING'
        self.buf = []
        self.pilot_samples = []
        self.phi_est = 0.0

    def _sync_match(self, buf):
        n_diffs = len(buf) - 1
        count = 0
        for j in range(n_diffs):
            d = abs(buf[j+1] - buf[j])
            if abs(d - self.expected_diff) < self.diff_thresh:
                count += 1
        return count >= self.min_matching_diffs

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
                    if self._sync_match(self.buf):
                        print(f"[Pilot Sync] Sync detected!",
                              flush=True)
                        self.state = 'PILOT'
                        self.buf = []

            elif self.state == 'PILOT':
                out0[i] = 0.0
                self.pilot_samples.append(sample)
                if len(self.pilot_samples) >= self.pilot_len:
                    self.phi_est = np.mean(self.pilot_samples)
                    print(f"[Pilot Sync] Pilot done. "
                          f"φ_est = {self.phi_est:.4f} rad")
                    self.state = 'ACTIVE'
                    self.pilot_samples = []

            else:
                corrected = sample - self.phi_est
                out0[i] = corrected

                self.buf.append(corrected)
                if len(self.buf) > self.sync_len:
                    self.buf.pop(0)

                if len(self.buf) == self.sync_len:
                    if self._sync_match(self.buf):
                        print(f"[Pilot Sync] Resync detected!",
                              flush=True)
                        self.state = 'PILOT'
                        self.buf = []

        return n
