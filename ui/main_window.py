from PyQt5.QtWidgets import QWidget, QMainWindow, QLabel, QCheckBox, \
    QLineEdit, QPushButton, QMenu, QAction, QMessageBox, QFileDialog, \
    QVBoxLayout, QHBoxLayout, QFormLayout, QFrame
from PyQt5.QtGui import QIntValidator, QDoubleValidator, QIcon, QCloseEvent
from PyQt5.QtCore import pyqtSlot, QThread
import hid
import pyqtgraph as pg
import numpy as np
import json
import os
import time
from typing import Optional, List, Tuple

from hid_worker.hid_worker import HIDWorker
from simulator.simulator import Simulator
from simulator.model import Model

try:
    import ctypes
    app_id = 'BioRobotics.uScope'  # Change application id to make the
    # taskbar icon displayed correctly
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
except ImportError:
    ctypes = None  # Very unimportant fix, continue if ctypes was not found


# class MainWindow(QMainWindow):
class MainWindow(QWidget):
    """Class for running the application window."""

    LINECOLORS = ['y', 'm', 'r', 'g', 'c', 'w', 'b']

    FRAME_TIME = 1.0 / 60.0  # Inverse of framerate

    def __init__(self, *args, **kwargs):
        """

        All class properties are created inside the constructor.
        As much as possible is moved to the separate init method.
        """

        super().__init__(*args, **kwargs)  # Run parent constructor

        # Initialize HID USB device (not connected yet)
        self.hid = hid.device()

        self.thread = QThread()
        self.worker = HIDWorker(self.hid)
        self.worker.moveToThread(self.thread)
        self.worker.update.connect(self.update_data)  # Link HID reports to local list
        self.thread.started.connect(self.worker.run)  # Start worker with thread

        # Prepare data structure
        self.channels = 0  # Wait for serial data, resize on the fly
        self.data: Optional[np.array] = None  # Received data, each row is a channel
        self.time: Optional[np.array] = None  # Timestamps of each data column
        self.data_points = 0  # Number of points recorded
        self.data_size = 200  # Number of points in history
        self.render_size = self.data_size  # Number of points shown in graph
        self.time_offset = None  # Client micros when starting recording

        self.overlay = False  # When true, all plots should be combined in one plot
        self.autoscale = True  # Automatic y-scaling when true
        self.y_scale = [-10.0, 10.0]  # Y-scale values when not automatic

        # The system time of the last frame update - Used to limit framerate
        self.last_update = 0.0

        # Make simulator
        self.simulator = Simulator()
        self.model = Model()

        # Create property stubs
        self.input_device_name = QLineEdit()
        self.button_port = QPushButton('Connect')
        self.input_size = QLineEdit()
        self.input_render_size = QLineEdit()
        self.input_render_all = QCheckBox()
        self.input_overlay = QCheckBox()
        self.input_autoscale = QCheckBox()
        self.input_scale = {
            'min': QLineEdit(),
            'max': QLineEdit()
        }
        self.layout_plots = pg.GraphicsLayoutWidget()
        self.button_save = QPushButton('Save')

        self.plots: List[pg.PlotItem] = []  # Start with empty plots
        self.curves: List[pg.PlotDataItem] = []

        self.build_ui_elements()  # Put actual GUI together

        self.setWindowTitle('uScope')
        icon_path = os.path.realpath('images/logo.ico')
        self.setWindowIcon(QIcon(icon_path))

        self.show()

        self.set_channels(self.channels)

        # Load previous settings
        self.load_settings()

    def build_ui_elements(self):
        """Create and connect the Qt Widgets to build the full GUI"""

        layout_main = QHBoxLayout(self)  # Main horizontal layout

        layout_right = QVBoxLayout()
        layout_left = QVBoxLayout()
        layout_right_buttons = QHBoxLayout()  # Layout for top buttons
        layout_right_plots = QVBoxLayout()  # Layout for channels

        layout_main.addLayout(layout_left)
        layout_main.addLayout(layout_right)

        # Frame
        layout_right.addWidget(self.simulator)

        # Port control
        layout_settings = QFormLayout()
        self.input_device_name.setText('mbed')
        self.input_device_name.setToolTip('Text to search for the HID device')
        layout_settings.addRow(QLabel('Device name:'), self.input_device_name)
        self.button_port.setCheckable(True)
        self.button_port.toggled.connect(self.on_connect_toggle)

        # Data size
        self.input_size.setValidator(QIntValidator(5, 1000000))
        self.input_size.setText(str(self.data_size))
        self.input_size.setToolTip('The number of samples that are kept in memory')
        layout_settings.addRow(QLabel('Keep samples:'), self.input_size)

        # Render size
        layout_samples = QHBoxLayout()
        self.input_render_all.setToolTip('Enable to render fewer samples')
        self.input_render_all.setChecked(True)
        self.input_render_all.toggled.connect(self.on_render_all_toggle)

        self.input_render_size.setValidator(QIntValidator(5, 1000000))
        self.input_render_size.setToolTip('The number of samples shown in the graph ('
                                          'equal to or lower than the number of '
                                          'samples in memory)')
        self.input_render_size.setDisabled(self.render_size == self.data_size)

        layout_samples.addWidget(self.input_render_all)
        layout_samples.addWidget(QLabel('Render all samples'))
        layout_samples.addStretch(0)
        layout_samples.addWidget(QLabel('Samples in graph:'))
        layout_samples.addWidget(self.input_render_size)

        layout_settings.addRow(QLabel('Render samples:'), layout_samples)

        # Overlay
        self.input_overlay.setChecked(self.overlay)
        layout_settings.addRow(QLabel('Overlay channels:'), self.input_overlay)

        # Y-Scale
        layout_scaling = QHBoxLayout()
        self.input_autoscale.setChecked(self.autoscale)
        self.input_autoscale.toggled.connect(self.on_autoscale_toggle)
        layout_scaling.addWidget(self.input_autoscale)
        layout_scaling.addWidget(QLabel('Autoscale'))
        layout_scaling.addStretch(0)
        layout_scaling.addWidget(QLabel('Manual scale:'))

        for key, input_scale in self.input_scale.items():
            input_scale.setValidator(QDoubleValidator(-1.0e6, 1.0e6, 4))
            val = self.y_scale[0] if key == 'min' else self.y_scale[1]
            input_scale.setText(str(val))
            input_scale.setDisabled(self.autoscale)
            layout_scaling.addWidget(input_scale)

        layout_settings.addRow(QLabel('Y-scale:'), layout_scaling)

        # Attach top layout
        layout_right_buttons.addLayout(layout_settings)
        layout_right_buttons.addWidget(self.button_port)

        layout_left.addLayout(layout_right_buttons)

        # Plots
        layout_right_plots.addWidget(self.layout_plots)

        layout_left.addLayout(layout_right_plots)

        # Buttons
        layout_buttons = QHBoxLayout()
        menu_save = QMenu()
        menu_save.addAction('Numpy')
        menu_save.addAction('CSV')

        menu_save.triggered.connect(self.on_save)
        self.button_save.setMenu(menu_save)
        layout_buttons.addWidget(self.button_save)
        layout_left.addLayout(layout_buttons)

    @pyqtSlot(bool)
    def on_connect_toggle(self, checked: bool):
        """When the `connect` button is pressed"""

        self.button_port.setText('Disconnect' if checked else 'Connect')

        self.worker.stop()
        self.thread.quit()
        self.thread.wait()
        self.hid.close()

        if checked:
            name = self.input_device_name.text()
            device_tuple = self.get_hid_device(name)

            if device_tuple is None:
                message = QMessageBox()
                QMessageBox.warning(message, 'Device not found',
                                    'No HID device with such a name could be found. '
                                    'Is the device connected?', QMessageBox.Ok)
                self.button_port.setChecked(False)  # Undo toggle
                return

            try:
                self.hid.open(*device_tuple)
                self.hid.set_nonblocking(True)
            except IOError as err:
                message = QMessageBox()
                QMessageBox.warning(message, 'Failed to connect',
                                    'The HID device could not be opened.<br>'
                                    + str(err), QMessageBox.Ok)

                self.button_port.setChecked(False)  # Undo toggle
                return

            self.input_device_name.setDisabled(True)
            self.input_size.setDisabled(True)
            self.input_overlay.setDisabled(True)
            self.input_autoscale.setDisabled(True)
            self.start_recording()
            self.thread.start()  # Start
        else:
            self.input_device_name.setDisabled(False)
            self.input_size.setDisabled(False)
            self.input_overlay.setDisabled(False)
            self.input_autoscale.setDisabled(False)

    @pyqtSlot(bool)
    def on_render_all_toggle(self, checked: bool):
        """Callback for the render-all checkbox"""

        # Enable/disable render size
        self.input_render_size.setDisabled(checked)

    @pyqtSlot(bool)
    def on_autoscale_toggle(self, checked: bool):
        """Callback for the autoscale checkbox"""

        # Enable/disable manual scales
        for key, input_scale in self.input_scale.items():
            input_scale.setDisabled(checked)

    @pyqtSlot(QAction)
    def on_save(self, action: QAction):
        self.save_data(action.text())

    @staticmethod
    def get_hid_device(name: str) -> Optional[Tuple[int, int]]:
        """Get the first HID device that matches the provided name."""

        for device_dict in hid.enumerate():
            if name in device_dict['manufacturer_string']:
                return device_dict['vendor_id'], device_dict['product_id']

        return None

    def save_data(self, file_format):
        """Save data, file_format is either `csv` or `numpy`"""

        file_format = file_format.lower()

        if np.size(self.data, 0) < 3:
            message = QMessageBox()
            QMessageBox.information(message, 'Saving data',
                                    'No data recorded yet', QMessageBox.Ok)
            return

        if file_format == 'numpy':
            ext = 'Numpy Data (*.npz)'
        else:
            ext = 'Comma Separated Values (*.csv)'

        options = QFileDialog.Options()
        filename, _ = QFileDialog.getSaveFileName(
            self, 'QFileDialog.getSaveFileName()', '', ext,
            options=options)

        if filename:
            if file_format == 'numpy':
                np.savez(filename, data=self.data, time=self.time)
            else:
                data = np.vstack((self.time, self.data))
                header = 'time [s]'
                for i in range(self.channels):
                    header += ', Channel {}'.format(i)

                np.savetxt(filename, data.transpose(), delimiter=';', header=header,
                           fmt='%f')

    def load_settings(self):
        """Load settings from file"""
        try:
            with open('settings.json', 'r') as file:
                settings = json.load(file)
                if 'device' in settings and settings['device']:
                    self.input_device_name.setText(settings['device'])
                if 'size' in settings and settings['size'] > 10:
                    self.input_size.setText(str(settings['size']))
                if 'size_render' in settings:
                    self.input_render_size.setText(str(settings['size_render']))
                if 'overlay' in settings:
                    self.input_overlay.setChecked(settings['overlay'])
                if 'autoscale' in settings:
                    self.input_autoscale.setChecked(settings['autoscale'])
                if 'y_scale_max' in settings:
                    self.input_scale['max'].setText(str(settings['y_scale_max']))
                if 'y_scale_min' in settings:
                    self.input_scale['min'].setText(str(settings['y_scale_min']))
        except FileNotFoundError:
            return  # Do nothing
        except json.decoder.JSONDecodeError:
            return  # Do nothing

    def save_settings(self):
        """Save current settings to file"""
        settings = {
            'device': self.input_device_name.text(),
            'size': self.data_size,
            'size_render': self.render_size,
            'overlay': self.overlay,
            'autoscale': self.autoscale,
            'y_scale_min': self.y_scale[0],
            'y_scale_max': self.y_scale[1]
        }
        with open('settings.json', 'w') as file:
            file.write(json.dumps(settings))

    def closeEvent(self, event: QCloseEvent):
        """When main window is closed"""
        self.save_settings()

        self.hid.close()
        self.worker.stop()
        self.thread.quit()
        self.thread.wait()

        super().closeEvent(event)  # Call original method too

    def start_recording(self):
        """Called when recording should start (e.g. when `Connect` was hit)"""
        self.channels = 0  # Force an update on the next data point
        self.data_points = 0
        self.data_size = int(self.input_size.text())
        self.render_size = int(self.input_render_size.text())
        self.overlay = self.input_overlay.isChecked()
        self.autoscale = self.input_autoscale.isChecked()
        self.y_scale = [
            float(self.input_scale['min'].text()),
            float(self.input_scale['max'].text())
        ]

        if self.input_render_all.isChecked():
            self.render_size = self.data_size
        if self.render_size is None or self.render_size > self.data_size:
            self.render_size = self.data_size

    @pyqtSlot(int, list)
    def update_data(self, micros: int, new_data: list):
        """Called when new row was received"""

        channels = len(new_data)

        # Perform model update
        if channels == 2:
            self.simulator.angle = self.model.update(new_data[0], new_data[1])

        if self.channels != channels:
            self.set_channels(channels)

        col = np.array(new_data, dtype=float)
        self.data = np.roll(self.data, -1, axis=1)  # Rotate backwards
        self.data[:, -1] = col  # Set new column at the end

        if self.time_offset is None:
            self.time_offset = micros

        self.time = np.roll(self.time, -1)  # Rotate backwards
        self.time[0, -1] = 1.0e-6 * (micros - self.time_offset)  # Save as seconds

        self.data_points += 1

        now = time.time()
        if now - self.last_update >= self.FRAME_TIME:  # Limit update rate
            self.update_plots()
            self.last_update = now

    def update_plots(self):
        """With data already updated, update plots"""

        if self.data_points < self.render_size:
            data_x = self.time[:, -self.data_points:]
            data_y = self.data[:, -self.data_points:]
        elif self.render_size < self.data_size:
            data_x = self.time[:, -self.render_size:]
            data_y = self.data[:, -self.render_size:]
        else:
            data_x = self.time
            data_y = self.data

        for i, curve in enumerate(self.curves):
            curve.setData(x=data_x[0, :], y=data_y[i, :])

    def set_channels(self, channels: int):
        """
        Resize number of channels

        Also functions as a reset between recordings, also sets new plot
        windows and curves
        """

        self.channels = channels
        self.data = np.zeros((channels, self.data_size))
        self.time = np.zeros((1, self.data_size))
        self.data_points = 0

        self.time_offset = None  # Mark offset to be reset on first read

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
            new_plot = self.layout_plots.addPlot(row=0, col=0,
                                                 title='Channels')

            for i in range(self.channels):
                new_curve = new_plot.plot()
                self.curves.append(new_curve)

            self.plots.append(new_plot)

        else:
            for i in range(self.channels):
                new_plot = self.layout_plots.addPlot(row=i, col=0,
                                                     title='Ch{}'.format(i))
                new_plot.showGrid(False, True)

                new_curve = new_plot.plot()

                self.plots.append(new_plot)
                self.curves.append(new_curve)

        # Set style
        for plot in self.plots:
            plot.showGrid(False, True)
            if not self.autoscale:
                # Autoscaling is by default
                plot.setYRange(self.y_scale[0], self.y_scale[1])

        for i, curve in enumerate(self.curves):
            # Set automatic colors
            c = self.LINECOLORS[i % len(self.LINECOLORS)]
            pen = pg.mkPen(c, width=2)
            curve.setPen(pen)
