from PyQt6.QtCore import QObject, pyqtSignal
from realtime_processor.plot import Plot

class PlotWorker(QObject):
    plot_drawn = pyqtSignal(object)

    def __init__(self, xst_data, dat_path, subband, rcu_mode):
        super().__init__()
        self.xst_data = xst_data
        self.dat_path = dat_path
        self.subband = subband
        self.rcu_mode = rcu_mode
        
    def run(self):
        plot_instance = Plot()
        sky_fig = plot_instance.plot_matrix(self.xst_data, self.dat_path, self.subband, self.rcu_mode, vmin=None, vmax=None)
        self.plot_drawn.emit(sky_fig)