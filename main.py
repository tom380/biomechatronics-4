import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIntValidator, QDoubleValidator, QIcon
from PyQt5.QtCore import pyqtSlot, QIODevice, pyqtSignal
from PyQt5.QtSerialPort import QSerialPort, QSerialPortInfo
import pyqtgraph as pg
import numpy as np
import json

from plot_decoder import PlotDecoder


class ComboBox(QComboBox):
    """Extend QComboBox widget to handle click event"""

    popupAboutToBeShown = pyqtSignal()

    def showPopup(self):
        """Fire event first, then call parent popup method"""
        self.popupAboutToBeShown.emit()
        super().showPopup()


class MainWindow(QMainWindow):
    """Class for running the application window"""

    LINECOLORS = ['y', 'm', 'r', 'g', 'c', 'w', 'b']

    def __init__(self, *args, **kwargs):
        """Constructor"""

        super().__init__(*args, **kwargs)  # Run parent constructor

        # Initialize serial
        self.serial = QSerialPort(
            None,
            baudRate=QSerialPort.Baud115200,
            readyRead=self.on_serial_receive
        )
        self.decoder = PlotDecoder()

        # Prepare data structure
        self.channels = 0  # Wait for serial data, resize on the fly
        self.data = None  # Received data, each row is a channel
        self.time = None  # Timestamps of each data column
        self.data_points = 0  # Number of points recorded
        self.data_size = 200  # Number of points in history
        self.time_offset = None  # Time offset in microseconds
        self.overlay = False  # When true, all plots should be combined in one plot
        self.autoscale = True  # Automatic y-scaling when true
        self.y_scale = [-10.0, 10.0]  # Y-scale values when not automatic
        self.render_frames = 1  # Render every nth serial frame (increase to ease performance)

        self.last_update = 0  # Keep track of how long ago the graphs were last updated

        self.build_ui_elements()  # Put actual GUI together

        self.setWindowTitle('uScope')
        self.show()

        self.set_channels(self.channels)

        # Load previous settings
        self.load_settings()

    def build_ui_elements(self):
        """Create and connect the Qt Widgets to build the full GUI"""

        layout_main = QVBoxLayout()  # Main vertical layout
        layout_top = QHBoxLayout()  # Layout for top buttons
        layout_bottom = QVBoxLayout()  # Layout for channels

        # Port control
        layout_settings = QFormLayout()
        self.input_port = ComboBox()
        self.input_port.popupAboutToBeShown.connect(self.find_devices)
        self.find_devices()  # Call it once already so an initial value is chosen
        layout_settings.addRow(QLabel('Serial port:'), self.input_port)
        self.button_port = QPushButton('Connect')
        self.button_port.setCheckable(True)
        self.button_port.toggled.connect(self.on_connect_toggle)

        # Data size
        self.input_size = QLineEdit()
        self.input_size.setValidator(QIntValidator(5, 1000000))
        self.input_size.setText(str(self.data_size))
        layout_settings.addRow(QLabel('Samples:'), self.input_size)

        # Overlay
        self.input_overlay = QCheckBox()
        self.input_overlay.setChecked(self.overlay)
        layout_settings.addRow(QLabel('Overlay channels:'), self.input_overlay)

        # Y-Scale
        layout_scaling = QHBoxLayout()
        self.input_autoscale = QCheckBox()
        self.input_autoscale.setChecked(self.autoscale)
        self.input_autoscale.toggled.connect(self.on_autoscale_toggle)
        layout_scaling.addWidget(self.input_autoscale)
        layout_scaling.addWidget(QLabel('Autoscale'))
        layout_scaling.addStretch(0)
        layout_scaling.addWidget(QLabel('Manual scale:'))
        self.input_scale = {
            'min': QLineEdit(),
            'max': QLineEdit()
        }
        for key, input_scale in self.input_scale.items():
            input_scale.setValidator(QDoubleValidator(-1.0e6, 1.0e6, 4))
            val = self.y_scale[0] if key == 'min' else self.y_scale[1]
            input_scale.setText(str(val))
            input_scale.setDisabled(self.autoscale)
            layout_scaling.addWidget(input_scale)

        layout_settings.addRow(QLabel('Y-scale:'), layout_scaling)

        # Update rate
        self.input_render = QLineEdit()
        self.input_render.setToolTip('Increase this value to slow down the graph rendering. If set to 1, the graph is '
                                     'updated on each frame.\nWhen set to e.g. 5 the graph will only be re-rendered '
                                     'every fifth frame. Use this if the application starts to lag.')
        self.input_render.setText(str(self.render_frames))
        layout_settings.addRow(QLabel('Frame updates:'), self.input_render)

        # Attach top layout
        layout_top.addLayout(layout_settings)
        layout_top.addWidget(self.button_port)

        layout_main.addLayout(layout_top)

        # Plots
        self.layout_plots = pg.GraphicsLayoutWidget()
        layout_bottom.addWidget(self.layout_plots)

        self.plots = []  # Start with empty plots
        self.curves = []

        layout_main.addLayout(layout_bottom)

        # Buttons
        layout_buttons = QHBoxLayout()
        menu_save = QMenu()
        menu_save.addAction('Numpy')
        menu_save.addAction('CSV')
        self.button_save = QPushButton(
            'Save'
        )
        menu_save.triggered.connect(self.on_save)
        self.button_save.setMenu(menu_save)
        layout_buttons.addWidget(self.button_save)
        layout_main.addLayout(layout_buttons)

        # Main window widget
        widget = QWidget()
        widget.setLayout(layout_main)
        self.setCentralWidget(widget)

    @pyqtSlot(bool)
    def on_connect_toggle(self, checked):
        """When the serial `connect` button is pressed"""

        self.button_port.setText('Disconnect' if checked else 'Connect')

        self.serial.close()

        if checked:
            port = self.input_port.currentData()
            self.serial.setPortName(port)
            if self.serial.open(QIODevice.ReadOnly):  # If serial opened successfully
                self.input_port.setDisabled(True)
                self.input_size.setDisabled(True)
                self.input_overlay.setDisabled(True)
                self.input_autoscale.setDisabled(True)
                self.input_render.setDisabled(True)
                self.start_recording()
            else:
                self.button_port.setChecked(False)  # Undo toggle
                QMessageBox.warning(self, 'Serial connection', 'Could not connect to device', QMessageBox.Ok)
        else:
            self.input_port.setDisabled(False)
            self.input_size.setDisabled(False)
            self.input_overlay.setDisabled(False)
            self.input_autoscale.setDisabled(False)
            self.input_render.setDisabled(False)

    @pyqtSlot(bool)
    def on_autoscale_toggle(self, checked):
        """Callback for the autoscale checkbox"""

        # Enable/disable manual scales
        for key, input_scale in self.input_scale.items():
            input_scale.setDisabled(checked)

    @pyqtSlot()
    def on_serial_receive(self):
        """"
        Callback for serial data, already triggered by data

        It's important all available bytes are consumed, because this call-back cannot keep up with incoming streams
        at real-time!
        """

        new_bytes = self.serial.readAll()

        for byte in new_bytes:
            if self.decoder.receive_byte(byte):
                self.update_data(self.decoder.channel_size, self.decoder.time, self.decoder.data)

    @pyqtSlot(QAction)
    def on_save(self, action):
        self.save_data(action.text())

    def save_data(self, file_format):
        """Save data, file_format is either `csv` or `numpy`"""

        file_format = file_format.lower()

        if np.size(self.data, 0) < 3:
            QMessageBox.information(self, 'Saving data', 'No data recorded yet', QMessageBox.Ok)
            return

        if file_format == 'numpy':
            ext = 'Numpy Data (*.npz)'
        else:
            ext = 'Comma Separated Values (*.csv)'

        options = QFileDialog.Options()
        filename, _ = QFileDialog.getSaveFileName(
            self, 'QFileDialog.getSaveFileName()', '', ext, options=options)

        if filename:
            if file_format == 'numpy':
                np.savez(filename, data=self.data, time=self.time)
            else:
                data = np.vstack((self.time, self.data))
                header = 'time [s]'
                for i in range(self.channels):
                    header += ', Channel {}'.format(i)

                np.savetxt(filename, data.transpose(), delimiter=';', header=header)

    def load_settings(self):
        """Load settings from file"""
        try:
            with open('settings.json', 'r') as file:
                settings = json.load(file)
                if 'port' in settings and settings['port']:
                    self.input_port.setCurrentIndex(
                        self.input_port.findData(settings['port'])
                    )
                if 'size' in settings and settings['size'] > 10:
                    self.input_size.setText(str(settings['size']))
                if 'overlay' in settings:
                    self.input_overlay.setChecked(settings['overlay'])
                if 'autoscale' in settings:
                    self.input_autoscale.setChecked(settings['autoscale'])
                if 'y_scale_max' in settings:
                    self.input_scale['max'].setText(str(settings['y_scale_max']))
                if 'y_scale_min' in settings:
                    self.input_scale['min'].setText(str(settings['y_scale_min']))
                if 'render_frames' in settings:
                    self.input_render.setText(str(settings['render_frames']))
        except FileNotFoundError:
            return  # Do nothing
        except json.decoder.JSONDecodeError:
            return  # Do nothing

    def save_settings(self):
        """Save current settings to file"""
        settings = {
            'port': self.serial.portName(),
            'size': self.data_size,
            'overlay': self.overlay,
            'autoscale': self.autoscale,
            'y_scale_min': self.y_scale[0],
            'y_scale_max': self.y_scale[1],
            'render_frames': self.render_frames
        }
        with open('settings.json', 'w') as file:
            file.write(json.dumps(settings))

    def closeEvent(self, event):
        """When main window is closed"""
        self.serial.close()
        self.save_settings()
        super().closeEvent(event)  # Call original method too

    def find_devices(self):
        """Set found serial devices into dropdown"""
        ports = QSerialPortInfo.availablePorts()

        self.input_port.clear()

        for port in ports:

            label = port.portName()
            if port.description:
                label += ' - ' + port.description()

            self.input_port.addItem(label, port.portName())

    def start_recording(self):
        """Called when recording should start (e.g. when `Connect` was hit)"""
        self.channels = 0  # Force an update on the next data point
        self.data_points = 0
        self.data_size = int(self.input_size.text())
        self.overlay = self.input_overlay.isChecked()
        self.autoscale = self.input_autoscale.isChecked()
        self.y_scale = [
            float(self.input_scale['min'].text()),
            float(self.input_scale['max'].text())
        ]
        self.render_frames = int(self.input_render.text())

        self.serial.clear()  # Get rid of data in buffer

    def update_data(self, channels, time, new_data):
        """Called when new row was received"""

        if self.channels != channels:
            self.set_channels(channels)

        col = np.array(new_data, dtype=float)
        self.data = np.roll(self.data, -1, axis=1)  # Rotate backwards
        self.data[:, -1] = col[:, 0]  # Set new column at the end

        self.time = np.roll(self.time, -1)  # Rotate backwards

        if self.time_offset is None:
            self.time_offset = time

        self.time[0, -1] = (time - self.time_offset) / 1000000

        self.data_points += 1

        if self.last_update + 1 >= self.render_frames:
            self.update_plots()
            self.last_update = 0
        else:
            self.last_update += 1

    def update_plots(self):
        """With data already updated, update plots"""

        if self.data_points < self.data_size:
            data_x = self.time[:, -self.data_points:]
            data_y = self.data[:, -self.data_points:]
        else:
            data_x = self.time
            data_y = self.data

        for i, curve in enumerate(self.curves):
            curve.setData(x=data_x[0, :], y=data_y[i, :])

    def set_channels(self, channels):
        """
        Resize number of channels

        Also functions as a reset between recordings, also sets new plot windows and curves
        """

        self.channels = channels
        self.data = np.zeros((channels, self.data_size))
        self.time = np.zeros((1, self.data_size))
        self.time_offset = None
        self.data_points = 0

        self.last_update = 0

        self.create_plots()

    def create_plots(self):
        """Create the desired plots and curves"""

        # Clear old
        for plot in self.plots:
            plot.clear()
            self.layout_plots.removeItem(plot)

        self.plots = []
        self.curves = []

        if self.overlay:
            new_plot = self.layout_plots.addPlot(row=0, col=0, title='Channels')

            for i in range(self.channels):
                new_curve = new_plot.plot()
                self.curves.append(new_curve)

            self.plots.append(new_plot)

        else:
            for i in range(self.channels):
                new_plot = self.layout_plots.addPlot(row=i, col=0, title='Ch{}'.format(i))
                new_plot.showGrid(False, True)

                new_curve = new_plot.plot()

                self.plots.append(new_plot)
                self.curves.append(new_curve)

        # Set style
        for plot in self.plots:
            plot.showGrid(False, True)
            if not self.autoscale:
                plot.setYRange(self.y_scale[0], self.y_scale[1])  # Autoscaling is by default

        for i, curve in enumerate(self.curves):
            c = self.LINECOLORS[i % len(self.LINECOLORS)]  # Set automatic colors
            pen = pg.mkPen(c, width=2)
            curve.setPen(pen)


# Run window when file was called as executable
if __name__ == '__main__':

    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setWindowIcon(QIcon('images/logo.ico'))
    window = MainWindow()
    sys.exit(app.exec())
