import sys
import numpy as np
import matplotlib.pyplot as plt

data_rx = np.fromfile("phase_rx", dtype=np.float32)
data_tx = np.fromfile("phase_tx", dtype=np.float32)
plt.figure()
plt.plot(data_rx[0:5000],"r.")
plt.figure()
plt.plot(data_tx[0:5000],"b.")
plt.grid(True)
plt.show()
