import PySide6.QtWidgets as qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT
import numpy as np


class GraphSection(qt.QGroupBox):
    """Separate class for graph visualization section - I-V-T graph"""
    def __init__(self):
        super().__init__("I-V-T Graph Visualization")
        self.init_ui()
    
    def init_ui(self):
        layout = qt.QVBoxLayout()
        
        # Create a matplotlib figure with 3 subplots for I-V-T graphs
        self.figure = Figure(figsize=(12, 8), dpi=100)
        self.figure.suptitle("Memristor I-V-T Analysis", fontsize=14, fontweight='bold')
        
        # Create three subplots
        self.ax_iv = self.figure.add_subplot(2, 2, 1)  # I-V Characteristic
        self.ax_it = self.figure.add_subplot(2, 2, 2)  # I-T Characteristic
        self.ax_vt = self.figure.add_subplot(2, 2, 3)  # V-T Characteristic
        self.ax_rt = self.figure.add_subplot(2, 2, 4)  # Resistance-Time
        
        # Set labels and titles
        self.ax_iv.set_xlabel('Voltage (V)')
        self.ax_iv.set_ylabel('Current (A)')
        self.ax_iv.set_title('I-V Characteristic')
        self.ax_iv.grid(True, alpha=0.3)
        
        self.ax_it.set_xlabel('Time (s)')
        self.ax_it.set_ylabel('Current (A)')
        self.ax_it.set_title('I-T Characteristic')
        self.ax_it.grid(True, alpha=0.3)
        
        self.ax_vt.set_xlabel('Time (s)')
        self.ax_vt.set_ylabel('Voltage (V)')
        self.ax_vt.set_title('V-T Characteristic')
        self.ax_vt.grid(True, alpha=0.3)
        
        self.ax_rt.set_xlabel('Time (s)')
        self.ax_rt.set_ylabel('Resistance (Ω)')
        self.ax_rt.set_title('Resistance-Time')
        self.ax_rt.grid(True, alpha=0.3)
        
        self.figure.tight_layout()
        
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

        # toolbar
        toolbar = NavigationToolbar2QT(self.canvas,self)
        layout.addWidget(toolbar(
        
        self.setLayout(layout)
    
    def plot_data(self, voltage=None, current=None, time=None):
        """
        Plot I-V-T data on the graph
        
        Parameters:
        voltage: array of voltage values
        current: array of current values
        time: array of time values
        """
        # Clear previous plots
        self.ax_iv.clear()
        self.ax_it.clear()
        self.ax_vt.clear()
        self.ax_rt.clear()
        
        # Plot I-V characteristic
        if voltage is not None and current is not None:
            self.ax_iv.plot(voltage, current, 'b-', linewidth=2, marker='o', markersize=4)
            self.ax_iv.set_xlabel('Voltage (V)')
            self.ax_iv.set_ylabel('Current (A)')
            self.ax_iv.set_title('I-V Characteristic')
            self.ax_iv.grid(True, alpha=0.3)
        
        # Plot I-T characteristic
        if time is not None and current is not None:
            self.ax_it.plot(time, current, 'g-', linewidth=2, marker='s', markersize=4)
            self.ax_it.set_xlabel('Time (s)')
            self.ax_it.set_ylabel('Current (A)')
            self.ax_it.set_title('I-T Characteristic')
            self.ax_it.grid(True, alpha=0.3)
        
        # Plot V-T characteristic
        if time is not None and voltage is not None:
            self.ax_vt.plot(time, voltage, 'r-', linewidth=2, marker='^', markersize=4)
            self.ax_vt.set_xlabel('Time (s)')
            self.ax_vt.set_ylabel('Voltage (V)')
            self.ax_vt.set_title('V-T Characteristic')
            self.ax_vt.grid(True, alpha=0.3)
        
        # Plot Resistance-Time (R = V/I)
        if voltage is not None and current is not None and time is not None:
            # Avoid division by zero
            resistance = np.divide(voltage, current, where=current != 0, 
            out=np.zeros_like(voltage))
            self.ax_rt.plot(time, resistance, 'm-', linewidth=2, marker='d', markersize=4)
            self.ax_rt.set_xlabel('Time (s)')
            self.ax_rt.set_ylabel('Resistance (Ω)')
            self.ax_rt.set_title('Resistance-Time')
            self.ax_rt.grid(True, alpha=0.3)
        
        self.figure.tight_layout()
        self.canvas.draw()
    
    def clear_plots(self):
        """Clear all plots"""
        self.ax_iv.clear()
        self.ax_it.clear()
        self.ax_vt.clear()
        self.ax_rt.clear()
        self.canvas.draw()
