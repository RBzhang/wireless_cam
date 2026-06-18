import sys
import numpy as np
import matplotlib.pyplot as plt

data_rx = np.fromfile("phase_rx.dat", dtype=np.float32)
data_tx = np.fromfile("phase_tx.dat", dtype=np.float32)
plt.figure()
plt.plot(data_rx[10000:30000],"r.-")
plt.figure()
plt.plot(data_tx[10000:30000],"b.-")
plt.grid(True)
plt.show()
