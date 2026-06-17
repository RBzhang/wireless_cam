import os
import numpy as np
from gnuradio import gr
from PIL import Image
from PyQt5 import QtGui, QtCore, QtWidgets


class _ImageDisplay(QtCore.QObject):
    update_signal = QtCore.pyqtSignal(QtGui.QPixmap)

    def __init__(self, width, height):
        super().__init__()
        self.width = width
        self.height = height
        self._widget = QtWidgets.QWidget()
        self._widget.setWindowTitle("Received Image")
        self._label = QtWidgets.QLabel()
        self._label.setStyleSheet("background-color: black;")
        max_w = min(width, 960)
        max_h = min(height, 720)
        self._label.setFixedSize(max_w, max_h)
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self._label)
        self._widget.setLayout(layout)
        self._widget.show()
        self.update_signal.connect(self._set_pixmap)

    def _set_pixmap(self, pixmap):
        self._label.setPixmap(pixmap)

    def show_image(self, buffer):
        qimage = QtGui.QImage(buffer.tobytes(), self.width, self.height,
                              self.width, QtGui.QImage.Format_Grayscale8)
        if qimage.isNull():
            return
        pixmap = QtGui.QPixmap.fromImage(qimage)
        self.update_signal.emit(pixmap)

    def close(self):
        self._widget.close()


class image_byte_sink(gr.sync_block):
    def __init__(self, width=64, height=64, output_path='/tmp/received.png',
                 save_sequence=False, display=False):
        gr.sync_block.__init__(
            self,
            name='Image Byte Sink',
            in_sig=[np.uint8],
            out_sig=None
        )
        self.width = width
        self.height = height
        self.output_path = output_path
        self.save_sequence = save_sequence

        self.frame_size = width * height
        self.buffer = np.empty(self.frame_size, dtype=np.uint8)
        self.fill_pos = 0
        self.frame_count = 0

        base, ext = os.path.splitext(output_path)
        self._base = base
        self._ext = ext if ext else '.png'

        self._display = None
        if display:
            self._display = _ImageDisplay(width, height)

        self._acc_bytes = 0
        self._refresh_interval = max(1, self.frame_size // 200)

    def _refresh_display(self):
        if self._display is None:
            return
        full = np.zeros(self.frame_size, dtype=np.uint8)
        full[:self.fill_pos] = self.buffer[:self.fill_pos]
        self._display.show_image(full)

    def work(self, input_items, output_items):
        in0 = input_items[0]
        n_in = len(in0)
        consumed = 0

        while consumed < n_in:
            need = self.frame_size - self.fill_pos
            take = min(need, n_in - consumed)
            self.buffer[self.fill_pos:self.fill_pos + take] = in0[consumed:consumed + take]
            self.fill_pos += take
            consumed += take

            self._acc_bytes += take
            if self._acc_bytes >= self._refresh_interval or self.fill_pos >= self.frame_size:
                self._refresh_display()
                self._acc_bytes = 0

            if self.fill_pos >= self.frame_size:
                self._save_frame()
                self.fill_pos = 0
                self._acc_bytes = 0

        return consumed

    def _save_frame(self):
        img_array = self.buffer.reshape((self.height, self.width))
        img = Image.fromarray(img_array, mode='L')

        if self.save_sequence:
            path = f"{self._base}_{self.frame_count:04d}{self._ext}"
        else:
            path = f"{self._base}{self._ext}"

        img.save(path)
        print(f"[Image Byte Sink] 已保存第{self.frame_count}帧: {path} "
              f"({self.width}x{self.height})")
        self.frame_count += 1

    def stop(self):
        if self.fill_pos > 0:
            partial = np.zeros(self.frame_size, dtype=np.uint8)
            partial[:self.fill_pos] = self.buffer[:self.fill_pos]
            img_array = partial.reshape((self.height, self.width))
            img = Image.fromarray(img_array, mode='L')
            path = f"{self._base}_partial{self._ext}"
            img.save(path)
            print(f"[Image Byte Sink] 流结束,保存了不完整帧(已收{self.fill_pos}/"
                  f"{self.frame_size}像素): {path}")
        if self._display is not None:
            self._display.close()
        return True
