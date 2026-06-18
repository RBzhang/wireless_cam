import os
import numpy as np
from gnuradio import gr


class pilot_sync(gr.sync_block):
    def __init__(self, sync_len=16, pilot_len=1024, diff_thresh=0.3,
                 log_path='/tmp/pilot_sync_diffs.log'):
        gr.sync_block.__init__(
            self,
            name='Pilot Sync & Phase Correction',
            in_sig=[np.float32],
            out_sig=[np.float32]
        )
        self.sync_len = sync_len
        self.pilot_len = pilot_len
        self.diff_thresh = diff_thresh
        self.expected_diff = np.pi / 3

        self.state = 'SEARCHING'
        self.buf = []
        self.pilot_samples = []
        self.phi_est = 0.0

        self._log_file = open(log_path, 'w')
        self._log_file.write("sample_idx,diffs\n")
        self._log_file.flush()
        self._sample_idx = 0
        self.log_diffs_enabled = False

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
                    diffs = [abs(self.buf[j+1] - self.buf[j])
                             for j in range(self.sync_len - 1)]
                    if self.log_diffs_enabled:
                        self._log_file.write(f"{self._sample_idx},{','.join(f'{d:.6f}' for d in diffs)}\n")
                        self._log_file.flush()
                    if all(abs(d - self.expected_diff) < self.diff_thresh
                           for d in diffs):
                        print(f"[Pilot Sync] Sync detected! "
                              f"first={self.buf[0]:.4f} last={self.buf[-1]:.4f}",
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
                    diffs = [abs(self.buf[j+1] - self.buf[j])
                             for j in range(self.sync_len - 1)]
                    if self.log_diffs_enabled:
                        self._log_file.write(f"{self._sample_idx},{','.join(f'{d:.6f}' for d in diffs)}\n")
                        self._log_file.flush()
                    if all(abs(d - self.expected_diff) < self.diff_thresh
                           for d in diffs):
                        print(f"[Pilot Sync] Resync detected! "
                              f"re-estimating φ...", flush=True)
                        self.state = 'PILOT'
                        self.buf = []

            self._sample_idx += 1

        return n

    def stop(self):
        self._log_file.close()
        return True
