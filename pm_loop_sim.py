#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: PM Loop Software Simulation
# Description: PM image transmitter, 900 MHz equivalent channel, and receiver
# GNU Radio version: 3.10.12.0

from gnuradio import analog
from gnuradio import blocks
from gnuradio import filter
from gnuradio.filter import firdes
from gnuradio import gr
from gnuradio.fft import window
import sys
import signal
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation
import math
import pm_loop_sim_image_byte_sink_0 as image_byte_sink_0  # embedded python block
import pm_loop_sim_image_byte_source_0 as image_byte_source_0  # embedded python block
import pm_loop_sim_pilot_sync_0 as pilot_sync_0  # embedded python block
import threading




class pm_loop_sim(gr.top_block):

    def __init__(self):
        gr.top_block.__init__(self, "PM Loop Software Simulation", catch_exceptions=True)
        self.flowgraph_started = threading.Event()

        ##################################################
        # Variables
        ##################################################
        self.sim_if = sim_if = 100e3
        self.samp_rate = samp_rate = 0.5e6
        self.rf_freq = rf_freq = 900e6
        self.noise_voltage = noise_voltage = 0.01
        self.max_phase = max_phase = math.pi/3
        self.freq_offset_hz = freq_offset_hz = 0
        self.frame_width = frame_width = 1920
        self.frame_height = frame_height = 1080
        self.channel_taps = channel_taps = [1.0+0.0j]

        ##################################################
        # Blocks
        ##################################################

        self.pilot_sync_0 = pilot_sync_0.pilot_sync(sync_len=416, pilot_len=1024, frame_size=frame_width*frame_height)
        self.image_byte_source_0 = image_byte_source_0.image_byte_source(image_path="/home/ray/Project/wireless-cam/scene1920x1080.jpg", repeat=False)
        self.image_byte_sink_0 = image_byte_sink_0.image_byte_sink(width=frame_width, height=frame_height, output_path="/home/ray/Project/wireless-cam/received_sim.png", save_sequence=False, display=False, skip_each_frame=0)
        self.fir_filter_channel = filter.fir_filter_ccc(1, channel_taps)
        self.fir_filter_channel.declare_sample_delay(0)
        self.blocks_uchar_to_float_0 = blocks.uchar_to_float()
        self.blocks_throttle_0 = blocks.throttle( gr.sizeof_gr_complex*1, samp_rate, True, 0 if "auto" == "auto" else max( int(float(0.1) * samp_rate) if "auto" == "time" else int(0.1), 1) )
        self.blocks_rotator_cc_tx = blocks.rotator_cc((2*math.pi*sim_if/samp_rate), False)
        self.blocks_rotator_cc_rx = blocks.rotator_cc((-2*math.pi*sim_if/samp_rate), False)
        self.blocks_rotator_cc_cfo = blocks.rotator_cc((2*math.pi*freq_offset_hz/samp_rate), False)
        self.blocks_null_sink_0 = blocks.null_sink(gr.sizeof_float*1)
        self.blocks_multiply_const_vxx_scale = blocks.multiply_const_ff((1.0/255.0))
        self.blocks_multiply_const_vxx_rx = blocks.multiply_const_ff((3/math.pi))
        self.blocks_multiply_const_vxx_phase = blocks.multiply_const_ff(max_phase)
        self.blocks_magphase_to_complex_0 = blocks.magphase_to_complex(1)
        self.blocks_float_to_uchar_0 = blocks.float_to_uchar(1, 255, 0)
        self.blocks_file_sink_tx_phase = blocks.file_sink(gr.sizeof_float*1, '/home/ray/Project/wireless-cam/phase_tx_sim.dat', False)
        self.blocks_file_sink_tx_phase.set_unbuffered(False)
        self.blocks_file_sink_rx_phase = blocks.file_sink(gr.sizeof_float*1, '/home/ray/Project/wireless-cam/phase_rx_sim.dat', False)
        self.blocks_file_sink_rx_phase.set_unbuffered(False)
        self.blocks_complex_to_magphase_0 = blocks.complex_to_magphase(1)
        self.blocks_add_xx_0 = blocks.add_vcc(1)
        self.analog_rail_ff_0 = analog.rail_ff(0, 1)
        self.analog_noise_source_x_0 = analog.noise_source_c(analog.GR_GAUSSIAN, noise_voltage, 42)
        self.analog_const_source_x_0 = analog.sig_source_f(0, analog.GR_CONST_WAVE, 0, 0, 1)


        ##################################################
        # Connections
        ##################################################
        self.connect((self.analog_const_source_x_0, 0), (self.blocks_magphase_to_complex_0, 0))
        self.connect((self.analog_noise_source_x_0, 0), (self.blocks_add_xx_0, 1))
        self.connect((self.analog_rail_ff_0, 0), (self.blocks_float_to_uchar_0, 0))
        self.connect((self.blocks_add_xx_0, 0), (self.blocks_rotator_cc_rx, 0))
        self.connect((self.blocks_complex_to_magphase_0, 1), (self.blocks_file_sink_rx_phase, 0))
        self.connect((self.blocks_complex_to_magphase_0, 0), (self.blocks_null_sink_0, 0))
        self.connect((self.blocks_complex_to_magphase_0, 1), (self.pilot_sync_0, 0))
        self.connect((self.blocks_float_to_uchar_0, 0), (self.image_byte_sink_0, 0))
        self.connect((self.blocks_magphase_to_complex_0, 0), (self.blocks_throttle_0, 0))
        self.connect((self.blocks_multiply_const_vxx_phase, 0), (self.blocks_file_sink_tx_phase, 0))
        self.connect((self.blocks_multiply_const_vxx_phase, 0), (self.blocks_magphase_to_complex_0, 1))
        self.connect((self.blocks_multiply_const_vxx_rx, 0), (self.analog_rail_ff_0, 0))
        self.connect((self.blocks_multiply_const_vxx_scale, 0), (self.blocks_multiply_const_vxx_phase, 0))
        self.connect((self.blocks_rotator_cc_cfo, 0), (self.blocks_add_xx_0, 0))
        self.connect((self.blocks_rotator_cc_rx, 0), (self.blocks_complex_to_magphase_0, 0))
        self.connect((self.blocks_rotator_cc_tx, 0), (self.fir_filter_channel, 0))
        self.connect((self.blocks_throttle_0, 0), (self.blocks_rotator_cc_tx, 0))
        self.connect((self.blocks_uchar_to_float_0, 0), (self.blocks_multiply_const_vxx_scale, 0))
        self.connect((self.fir_filter_channel, 0), (self.blocks_rotator_cc_cfo, 0))
        self.connect((self.image_byte_source_0, 0), (self.blocks_uchar_to_float_0, 0))
        self.connect((self.pilot_sync_0, 0), (self.blocks_multiply_const_vxx_rx, 0))


    def get_sim_if(self):
        return self.sim_if

    def set_sim_if(self, sim_if):
        self.sim_if = sim_if
        self.blocks_rotator_cc_tx.set_phase_inc((2*math.pi*self.sim_if/self.samp_rate))
        self.blocks_rotator_cc_rx.set_phase_inc((-2*math.pi*self.sim_if/self.samp_rate))

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.blocks_throttle_0.set_sample_rate(self.samp_rate)
        self.blocks_rotator_cc_tx.set_phase_inc((2*math.pi*self.sim_if/self.samp_rate))
        self.blocks_rotator_cc_cfo.set_phase_inc((2*math.pi*self.freq_offset_hz/self.samp_rate))
        self.blocks_rotator_cc_rx.set_phase_inc((-2*math.pi*self.sim_if/self.samp_rate))

    def get_rf_freq(self):
        return self.rf_freq

    def set_rf_freq(self, rf_freq):
        self.rf_freq = rf_freq

    def get_noise_voltage(self):
        return self.noise_voltage

    def set_noise_voltage(self, noise_voltage):
        self.noise_voltage = noise_voltage
        self.analog_noise_source_x_0.set_amplitude(self.noise_voltage)

    def get_max_phase(self):
        return self.max_phase

    def set_max_phase(self, max_phase):
        self.max_phase = max_phase
        self.blocks_multiply_const_vxx_phase.set_k(self.max_phase)

    def get_freq_offset_hz(self):
        return self.freq_offset_hz

    def set_freq_offset_hz(self, freq_offset_hz):
        self.freq_offset_hz = freq_offset_hz
        self.blocks_rotator_cc_cfo.set_phase_inc((2*math.pi*self.freq_offset_hz/self.samp_rate))

    def get_frame_width(self):
        return self.frame_width

    def set_frame_width(self, frame_width):
        self.frame_width = frame_width
        self.pilot_sync_0.frame_size = self.frame_width*self.frame_height
        self.image_byte_sink_0.width = self.frame_width

    def get_frame_height(self):
        return self.frame_height

    def set_frame_height(self, frame_height):
        self.frame_height = frame_height
        self.pilot_sync_0.frame_size = self.frame_width*self.frame_height
        self.image_byte_sink_0.height = self.frame_height

    def get_channel_taps(self):
        return self.channel_taps

    def set_channel_taps(self, channel_taps):
        self.channel_taps = channel_taps
        self.fir_filter_channel.set_taps(self.channel_taps)




def main(top_block_cls=pm_loop_sim, options=None):
    tb = top_block_cls()

    def sig_handler(sig=None, frame=None):
        tb.stop()
        tb.wait()

        sys.exit(0)

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    tb.start()
    tb.flowgraph_started.set()

    tb.wait()


if __name__ == '__main__':
    main()
