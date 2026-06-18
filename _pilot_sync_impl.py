import numpy as np
from gnuradio import gr

BARKER_13 = np.array(
    [1, 1, 1, 1, 1, -1, -1, 1, 1, -1, 1, -1, 1],
    dtype=np.float64
)


class pilot_sync(gr.basic_block):
    def __init__(self, sync_len=416, pilot_len=1024, frame_size=4000):
        gr.basic_block.__init__(
            self,
            name='Pilot Sync & Phase Correction',
            in_sig=[np.float32],
            out_sig=[np.float32]
        )
        self.sync_len = sync_len
        self.pilot_len = pilot_len
        self.frame_size = frame_size
        self.expected_amp = np.pi / 3
        if self.sync_len % len(BARKER_13) != 0:
            raise ValueError("sync_len must be a multiple of 13")

        chip_samples = self.sync_len // len(BARKER_13)
        template = np.repeat(BARKER_13, chip_samples)
        self._trend_index = (
            np.arange(self.sync_len, dtype=np.float64)
            - (self.sync_len - 1) / 2
        )
        self._trend_energy = np.dot(self._trend_index, self._trend_index)
        self._sync_template = template - np.mean(template)
        template_slope = (
            np.dot(self._sync_template, self._trend_index)
            / self._trend_energy
        )
        self._sync_template -= template_slope * self._trend_index
        self._sync_template_energy = np.dot(
            self._sync_template, self._sync_template)
        self._sync_template_norm = np.sqrt(self._sync_template_energy)

        self.state = 'SEARCHING'
        self.buf = []
        self.pilot_samples = []
        self.phi_est = 0.0
        self._active_count = 0

    def _find_sync(self, samples):
        if len(samples) < self.sync_len:
            return None

        a = np.unwrap(np.asarray(samples, dtype=np.float64))
        count = len(a) - self.sync_len + 1
        cumulative = np.concatenate(([0.0], np.cumsum(a)))
        cumulative_sq = np.concatenate(([0.0], np.cumsum(a * a)))
        window_sum = cumulative[self.sync_len:] - cumulative[:-self.sync_len]
        window_sq = (
            cumulative_sq[self.sync_len:] - cumulative_sq[:-self.sync_len]
        )

        trend_projection = np.correlate(
            a, self._trend_index, mode='valid')
        sync_projection = np.correlate(
            a, self._sync_template, mode='valid')

        detrended_energy = (
            window_sq
            - window_sum * window_sum / self.sync_len
            - trend_projection * trend_projection / self._trend_energy
        )
        detrended_energy = np.maximum(detrended_energy, 1e-12)
        correlation = sync_projection / (
            np.sqrt(detrended_energy) * self._sync_template_norm)
        amplitude = sync_projection / self._sync_template_energy
        residual_energy = (
            detrended_energy
            - sync_projection * sync_projection / self._sync_template_energy
        )
        noise = np.sqrt(
            np.maximum(residual_energy, 0.0) / self.sync_len)

        matches = np.flatnonzero(
            (correlation > 0.94)
            & (amplitude > 0.4)
            & (noise < 0.35)
        )
        if len(matches) == 0:
            return None

        start = int(matches[np.argmax(correlation[matches])])
        end = start + self.sync_len - 1
        stats = (
            float(correlation[start]),
            float(amplitude[start]),
            float(noise[start])
        )
        return end, stats

    def forecast(self, noutput_items, ninputs):
        return [1] * ninputs

    def general_work(self, input_items, output_items):
        in0 = input_items[0]
        out0 = output_items[0]
        consumed = 0
        produced = 0

        while consumed < len(in0):
            if self.state == 'SEARCHING':
                buffered = len(self.buf)
                samples = np.concatenate((
                    np.asarray(self.buf, dtype=np.float32),
                    in0[consumed:]
                ))
                match = self._find_sync(samples)
                if match is None:
                    keep = min(self.sync_len - 1, len(samples))
                    self.buf = samples[-keep:].tolist()
                    consumed = len(in0)
                    continue

                end, stats = match
                consumed += max(0, end + 1 - buffered)
                print(f"[Pilot Sync] Sync detected! "
                      f"corr={stats[0]:.3f} "
                      f"amp={stats[1]:.3f} "
                      f"noise={stats[2]:.3f}",
                      flush=True)
                self.state = 'PILOT'
                self.buf = []

            elif self.state == 'PILOT':
                sample = float(in0[consumed])
                self.pilot_samples.append(sample)
                consumed += 1
                if len(self.pilot_samples) >= self.pilot_len:
                    self.phi_est = np.mean(self.pilot_samples)
                    print(f"[Pilot Sync] Pilot done. "
                          f"\u03c6_est = {self.phi_est:.4f} rad",
                              flush=True)
                    self.state = 'ACTIVE'
                    self.pilot_samples = []

            else:
                if produced >= len(out0):
                    break
                sample = float(in0[consumed])
                out0[produced] = sample - self.phi_est
                produced += 1
                consumed += 1
                self._active_count += 1
                if self.frame_size > 0 and self._active_count >= self.frame_size:
                    print(f"[Pilot Sync] Frame done, "
                          f"re-searching...", flush=True)
                    self.state = 'SEARCHING'
                    self.buf = []
                    self._active_count = 0

        self.consume(0, consumed)
        return produced
