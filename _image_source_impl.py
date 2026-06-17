import numpy as np
from gnuradio import gr
from PIL import Image


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
        self.data = np.frombuffer(img.tobytes(), dtype=np.uint8)
        self.pos = 0
        print(f"[Image Byte Source] 已加载: {image_path}, "
              f"尺寸: {self.width}x{self.height}, 总像素: {len(self.data)}")

    def work(self, input_items, output_items):
        out = output_items[0]
        n = len(out)

        if len(self.data) == 0:
            return -1

        remaining = len(self.data) - self.pos
        if remaining <= 0:
            if self.repeat:
                self.pos = 0
                remaining = len(self.data)
            else:
                return -1

        n_copy = min(n, remaining)
        out[:n_copy] = self.data[self.pos:self.pos + n_copy]
        self.pos += n_copy

        if n_copy < n:
            if self.repeat:
                out[n_copy:n] = self.data[0:n - n_copy]
                self.pos = n - n_copy
            else:
                return n_copy if n_copy > 0 else -1

        return n
