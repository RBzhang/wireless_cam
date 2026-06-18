#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: pm_tx
# GNU Radio version: 3.10.12.0

from PyQt5 import Qt
from gnuradio import qtgui
from PyQt5 import QtCore
from gnuradio import analog
from gnuradio import blocks
from gnuradio import gr
from gnuradio.filter import firdes
from gnuradio.fft import window
import sys
import signal
from PyQt5 import Qt
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation
import math
import pm_tx_epy_block_0 as epy_block_0  # embedded python block
import pm_tx_image_byte_source_0 as image_byte_source_0  # embedded python block
import pm_tx_pilot_sync_0 as pilot_sync_0  # embedded python block
import threading



class pm_tx(gr.top_block, Qt.QWidget):

    def __init__(self):
        gr.top_block.__init__(self, "pm_tx", catch_exceptions=True)
        Qt.QWidget.__init__(self)
        self.setWindowTitle("pm_tx")
        qtgui.util.check_set_qss()
        try:
            self.setWindowIcon(Qt.QIcon.fromTheme('gnuradio-grc'))
        except BaseException as exc:
            print(f"Qt GUI: Could not set Icon: {str(exc)}", file=sys.stderr)
        self.top_scroll_layout = Qt.QVBoxLayout()
        self.setLayout(self.top_scroll_layout)
        self.top_scroll = Qt.QScrollArea()
        self.top_scroll.setFrameStyle(Qt.QFrame.NoFrame)
        self.top_scroll_layout.addWidget(self.top_scroll)
        self.top_scroll.setWidgetResizable(True)
        self.top_widget = Qt.QWidget()
        self.top_scroll.setWidget(self.top_widget)
        self.top_layout = Qt.QVBoxLayout(self.top_widget)
        self.top_grid_layout = Qt.QGridLayout()
        self.top_layout.addLayout(self.top_grid_layout)

        self.settings = Qt.QSettings("gnuradio/flowgraphs", "pm_tx")

        try:
            geometry = self.settings.value("geometry")
            if geometry:
                self.restoreGeometry(geometry)
        except BaseException as exc:
            print(f"Qt GUI: Could not restore geometry: {str(exc)}", file=sys.stderr)
        self.flowgraph_started = threading.Event()

        ##################################################
        # Variables
        ##################################################
        self.samp_rate = samp_rate = 1e6
        self.noise = noise = 0.01
        self.max_phase = max_phase = math.pi/3

        ##################################################
        # Blocks
        ##################################################

        self._noise_range = qtgui.Range(0, 1, 0.01, 0.01, 200)
        self._noise_win = qtgui.RangeWidget(self._noise_range, self.set_noise, "'noise'", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_layout.addWidget(self._noise_win)
        self.pilot_sync_0 = pilot_sync_0.pilot_sync(sync_len=60, pilot_len=1024)
        self.image_byte_source_0 = image_byte_source_0.image_byte_source(image_path="/home/ray/Project/wireless-cam/scene1920x1080.jpg", repeat=True)
        self.epy_block_0 = epy_block_0.image_byte_sink(width=1920, height=1080, output_path="/home/ray/Project/wireless-cam/received.png", save_sequence=False, display=True, skip_each_frame=1084)
        self.blocks_uchar_to_float_0 = blocks.uchar_to_float()
        self.blocks_throttle2_0 = blocks.throttle( gr.sizeof_char*1, samp_rate, True, 0 if "auto" == "auto" else max( int(float(0.1) * samp_rate) if "auto" == "time" else int(0.1), 1) )
        self.blocks_phase_shift_0 = blocks.phase_shift(math.pi/3, True)
        self.blocks_null_sink_0 = blocks.null_sink(gr.sizeof_float*1)
        self.blocks_multiply_const_vxx_scale = blocks.multiply_const_ff((1.0/255.0))
        self.blocks_multiply_const_vxx_1 = blocks.multiply_const_ff((3/math.pi))
        self.blocks_multiply_const_vxx_0 = blocks.multiply_const_ff(max_phase)
        self.blocks_magphase_to_complex_0 = blocks.magphase_to_complex(1)
        self.blocks_float_to_uchar_0 = blocks.float_to_uchar(1, 255, 0)
        self.blocks_complex_to_magphase_0 = blocks.complex_to_magphase(1)
        self.blocks_add_xx_0 = blocks.add_vcc(1)
        self.analog_noise_source_x_0 = analog.noise_source_c(analog.GR_GAUSSIAN, noise, 0)
        self.analog_const_source_x_0 = analog.sig_source_f(0, analog.GR_CONST_WAVE, 0, 0, 1)


        ##################################################
        # Connections
        ##################################################
        self.connect((self.analog_const_source_x_0, 0), (self.blocks_magphase_to_complex_0, 0))
        self.connect((self.analog_noise_source_x_0, 0), (self.blocks_add_xx_0, 1))
        self.connect((self.blocks_add_xx_0, 0), (self.blocks_complex_to_magphase_0, 0))
        self.connect((self.blocks_complex_to_magphase_0, 0), (self.blocks_null_sink_0, 0))
        self.connect((self.blocks_complex_to_magphase_0, 1), (self.pilot_sync_0, 0))
        self.connect((self.blocks_float_to_uchar_0, 0), (self.epy_block_0, 0))
        self.connect((self.blocks_magphase_to_complex_0, 0), (self.blocks_phase_shift_0, 0))
        self.connect((self.blocks_multiply_const_vxx_0, 0), (self.blocks_magphase_to_complex_0, 1))
        self.connect((self.blocks_multiply_const_vxx_1, 0), (self.blocks_float_to_uchar_0, 0))
        self.connect((self.blocks_multiply_const_vxx_scale, 0), (self.blocks_multiply_const_vxx_0, 0))
        self.connect((self.blocks_phase_shift_0, 0), (self.blocks_add_xx_0, 0))
        self.connect((self.blocks_throttle2_0, 0), (self.blocks_uchar_to_float_0, 0))
        self.connect((self.blocks_uchar_to_float_0, 0), (self.blocks_multiply_const_vxx_scale, 0))
        self.connect((self.image_byte_source_0, 0), (self.blocks_throttle2_0, 0))
        self.connect((self.pilot_sync_0, 0), (self.blocks_multiply_const_vxx_1, 0))


    def closeEvent(self, event):
        self.settings = Qt.QSettings("gnuradio/flowgraphs", "pm_tx")
        self.settings.setValue("geometry", self.saveGeometry())
        self.stop()
        self.wait()

        event.accept()

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.blocks_throttle2_0.set_sample_rate(self.samp_rate)

    def get_noise(self):
        return self.noise

    def set_noise(self, noise):
        self.noise = noise
        self.analog_noise_source_x_0.set_amplitude(self.noise)

    def get_max_phase(self):
        return self.max_phase

    def set_max_phase(self, max_phase):
        self.max_phase = max_phase
        self.blocks_multiply_const_vxx_0.set_k(self.max_phase)




def main(top_block_cls=pm_tx, options=None):

    qapp = Qt.QApplication(sys.argv)

    tb = top_block_cls()

    tb.start()
    tb.flowgraph_started.set()

    tb.show()

    def sig_handler(sig=None, frame=None):
        tb.stop()
        tb.wait()

        Qt.QApplication.quit()

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    timer = Qt.QTimer()
    timer.start(500)
    timer.timeout.connect(lambda: None)

    qapp.exec_()

if __name__ == '__main__':
    main()
