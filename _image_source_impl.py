import numpy as np
from gnuradio import gr
from PIL import Image

BARKER_13 = np.array(
    [1, 1, 1, 1, 1, -1, -1, 1, 1, -1, 1, -1, 1],
    dtype=np.int8
)
SYNC_CHIP_SAMPLES = 32
SYNC_CODE = np.where(
    np.repeat(BARKER_13, SYNC_CHIP_SAMPLES) > 0, 0xFF, 0x00
).astype(np.uint8)


class image_byte_source(gr.sync_block):
    def __init__(self, image_path='', repeat=True):
        gr.sync_block.__init__(
            self,
            name='Image Byte Source',
            in_sig=None,
            out_sig=[np.uint8]
        )
        self.repeat = repeat
        self.pos = 0
        self.data = np.array([], dtype=np.uint8)
        self.width = 0
        self.height = 0

        if image_path:
            self._load_image(image_path)

    def _load_image(self, image_path):
        img = Image.open(image_path).convert('L')
        self.width, self.height = img.size
        image_data = np.frombuffer(img.tobytes(), dtype=np.uint8)
        self.data = np.concatenate([SYNC_CODE, image_data])
        self.pos = 0
        total = len(self.data)
        print(f"[Image Byte Source] loaded: {image_path}, "
              f"size: {self.width}x{self.height}, "
              f"total bytes: {total}")

    def work(self, input_items, output_items):
        out = output_items[0]
        n = len(out)

        if len(self.data) == 0:
            return -1

        if self.repeat:
            idx = (self.pos + np.arange(n)) % len(self.data)
            out[:] = self.data[idx]
            self.pos = (self.pos + n) % len(self.data)
        else:
            remaining = len(self.data) - self.pos
            if remaining <= 0:
                return -1
            n_copy = min(n, remaining)
            out[:n_copy] = self.data[self.pos:self.pos + n_copy]
            self.pos += n_copy
            if n_copy < n:
                return n_copy

        return n
