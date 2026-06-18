import numpy as np
from gnuradio import gr


class pilot_sync(gr.sync_block):
    def __init__(self, sync_len=60, pilot_len=1024):
        gr.sync_block.__init__(
            self,
            name='Pilot Sync & Phase Correction',
            in_sig=[np.float32],
            out_sig=[np.float32]
        )
        self.sync_len = sync_len
        self.pilot_len = pilot_len
        self.block_n = sync_len // 3
        self.expected_amp = np.pi / 3

        self.state = 'SEARCHING'
        self.buf = []
        self.pilot_samples = []
        self.phi_est = 0.0

    def _detect_sync(self, buf):
        a = np.unwrap(np.array(buf, dtype=np.float64))
        b0 = a[0 * self.block_n:1 * self.block_n]
        b1 = a[1 * self.block_n:2 * self.block_n]
        b2 = a[2 * self.block_n:3 * self.block_n]

        m0, v0 = np.mean(b0), np.var(b0)
        m1, v1 = np.mean(b1), np.var(b1)
        m2, v2 = np.mean(b2), np.var(b2)

        d01 = m0 - m1
        d21 = m2 - m1
        d02 = abs(m0 - m2)

        if (v0 < 0.01 and v1 < 0.01 and v2 < 0.01
                and d01 > 0.5 and d21 > 0.5
                and d02 < 0.3):
            return True, (m0, m1, m2, v0, v1, v2)
        return False, (m0, m1, m2, v0, v1, v2)

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
                              f"blocks=({stats[0]:.3f},{stats[1]:.3f},{stats[2]:.3f}) "
                              f"vars=({stats[3]:.4f},{stats[4]:.4f},{stats[5]:.4f})",
                              flush=True)
                        self.state = 'PILOT'
                        self.buf = []

            elif self.state == 'PILOT':
                out0[i] = 0.0
                self.pilot_samples.append(sample)
                if len(self.pilot_samples) >= self.pilot_len:
                    self.phi_est = np.mean(self.pilot_samples)
                    print(f"[Pilot Sync] Pilot done. "
                          f"\u03c6_est = {self.phi_est:.4f} rad")
                    self.state = 'ACTIVE'
                    self.pilot_samples = []

            else:
                corrected = sample - self.phi_est
                out0[i] = corrected

                self.buf.append(corrected)
                if len(self.buf) > self.sync_len:
                    self.buf.pop(0)

                if len(self.buf) == self.sync_len:
                    ok, stats = self._detect_sync(self.buf)
                    if ok:
                        print(f"[Pilot Sync] Resync detected! "
                              f"blocks=({stats[0]:.3f},{stats[1]:.3f},{stats[2]:.3f})",
                              flush=True)
                        self.state = 'PILOT'
                        self.buf = []
