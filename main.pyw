# =========================================================
# ===== SA WS20 - Die geregelte Motorengruppe         =====
# ===== OPCUA Python Client                           =====
# ===== Simon Walker, Philipp Eberle, Husein Mazlagic =====
# =========================================================
# -*- coding: utf-8 -*-
import sys
import time

from PyQt5 import QtWebEngineWidgets, QtCore, QtWidgets
from PyQt5.QtCore import QSize, QTimer, Qt, QThread, pyqtSignal
from PyQt5.QtGui import QIcon, QIntValidator, QDoubleValidator
from PyQt5.QtWidgets import QMainWindow, QApplication, QTableWidgetItem, QInputDialog, QFileDialog

from model.config import config
from ui.main_ui import Ui_MainWindow
from model.opc_ua import opc_ua


# 4k Display mit hoher DPI-Auflösung
# if hasattr(Qt, 'AA_EnableHighDpiScaling'):
#     QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
# if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
#     QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)


class Main(QMainWindow):

    def __init__(self, parent=None):
        # Instance of the base class
        QMainWindow.__init__(self, parent)

        # Instance of the visual description from QT Creator
        self.ui = Ui_MainWindow()
        # making the visualisation structure
        self.ui.setupUi(self)
        self.setWindowTitle('SA Geregelte Motorengruppe')
        self.setMinimumSize(QSize(100, 50))
        self.move(-5, 0)

        # Creating the always running threads
        self.ui_update = BasicThread(self, self.continuous_ui_update)
        self.ui_update.start()
        self.variable_subscription = BasicThread(self, opc_ua.subscribe_datachange_event)

        # Connecting the events from the PyQt framework to the eventhandler
        # Connecting the buttons
        self.ui.btn_start_logger.clicked.connect(self.on_start_logger)
        self.ui.btn_read_logger.clicked.connect(self.on_read_logger)
        self.ui.btn_connect.clicked.connect(self.on_connect)
        self.ui.btn_write_lin.clicked.connect(self.on_write_lin)
        self.ui.btn_plot.clicked.connect(self.on_plot_lin)
        self.ui.btn_snap_file.clicked.connect(self.on_create_new_file)
        self.ui.btn_snap.clicked.connect(self.on_value_snapshot)

        # Connecting the checkboxes
        self.ui.checkBox_enable_m1.clicked.connect(self.on_check_m1_enable)
        self.ui.checkBox_enable_m2.clicked.connect(self.on_check_m2_enable)
        self.ui.checkBox_re_m1_active.clicked.connect(self.on_check_re_m1_active)
        self.ui.checkBox_re_m2_active.clicked.connect(self.on_check_re_m2_active)
        self.ui.checkBox_awu_m1_active.clicked.connect(self.on_check_awu_m1_active)
        self.ui.checkBox_awu_m2_active.clicked.connect(self.on_check_awu_m2_active)
        self.ui.checkBox_lin_active.clicked.connect(self.on_check_lin_active)

        # Connecting the radiobuttons
        self.ui.radio_m1_n.clicked.connect(self.on_radio_m1_n)
        self.ui.radio_m1_m.clicked.connect(self.on_radio_m1_m)
        self.ui.radio_m2_n.clicked.connect(self.on_radio_m2_n)
        self.ui.radio_m2_m.clicked.connect(self.on_radio_m2_m)
        self.ui.radio_cw.clicked.connect(self.on_radio_cw)
        self.ui.radio_ccw.clicked.connect(self.on_radio_ccw)

        # Connecting the spinboxes
        self.ui.SpinBox_I_m1.valueChanged.connect(self.on_m1_i_lim_changed)
        self.ui.SpinBox_I_m2.valueChanged.connect(self.on_m2_i_lim_changed)
        self.ui.spinBox_len_logger.valueChanged.connect(self.on_logger_time_changed)

        # Connecting the comboboxes
        self.ui.comboBox_motor.currentIndexChanged.connect(self.on_show_lin)
        self.ui.comboBox_cw.currentIndexChanged.connect(self.on_show_lin)

        # Connecting the lineedits
        self.int_validator_0_1600 = QIntValidator(0, 1600)
        self.ui.lineEdit_w_m1.setValidator(self.int_validator_0_1600)
        self.ui.lineEdit_w_m2.setValidator(self.int_validator_0_1600)
        self.ui.lineEdit_w_m1.editingFinished.connect(self.on_w_m1_changed)
        self.ui.lineEdit_w_m2.editingFinished.connect(self.on_w_m2_changed)
        self.ui.lineEdit_x_m1.setReadOnly(True)
        self.ui.lineEdit_x_m2.setReadOnly(True)
        self.ui.lineEdit_m1_p.setValidator(QDoubleValidator())
        self.ui.lineEdit_m1_i.setValidator(QDoubleValidator())
        self.ui.lineEdit_m1_d.setValidator(QDoubleValidator())
        self.ui.lineEdit_m2_p.setValidator(QDoubleValidator())
        self.ui.lineEdit_m2_i.setValidator(QDoubleValidator())
        self.ui.lineEdit_m2_d.setValidator(QDoubleValidator())
        self.ui.lineEdit_m1_p.editingFinished.connect(self.on_m1_p_changed)
        self.ui.lineEdit_m1_i.editingFinished.connect(self.on_m1_i_changed)
        self.ui.lineEdit_m1_d.editingFinished.connect(self.on_m1_d_changed)
        self.ui.lineEdit_m2_p.editingFinished.connect(self.on_m2_p_changed)
        self.ui.lineEdit_m2_i.editingFinished.connect(self.on_m2_i_changed)
        self.ui.lineEdit_m2_d.editingFinished.connect(self.on_m2_d_changed)

        # Connecting the actions
        self.ui.actionNot_Aus_Quittieren.triggered.connect(self.on_reset)
        self.ui.actionVerbinden.triggered.connect(self.on_connect)
        self.ui.actionPLC_IP.triggered.connect(self.on_configure_plc_ip)
        self.ui.actionPLC_Herunterfahren.triggered.connect(self.on_shutdown)
        self.ui.actionMotor_1.triggered.connect(self.on_linearise_m1)
        self.ui.actionMotor_2.triggered.connect(self.on_linearise_m2)
        self.ui.actionLinearisierungskennline_validieren.triggered.connect(self.on_validate_lin)
        self.ui.actionKonfiguration_speichern.triggered.connect(self.on_write_config)
        self.ui.actionKonfiguration_laden.triggered.connect(self.on_read_config)
        self.ui.actionAuto_Regler.triggered.connect(self.on_auto_re)
        self.ui.actionSchliessen.triggered.connect(self.close)

        # Making the webview widgets
        base_url = 'http://' + config.plc_ip + ':8080/'
        self.web_view = QtWebEngineWidgets.QWebEngineView(self)
        self.web_view.setObjectName('web_view')
        self.web_view.setFixedHeight(450)
        self.web_view.setUrl(QtCore.QUrl(base_url + 'trace.htm'))
        self.ui.traceLayout.addWidget(self.web_view)

        self.web_view2 = QtWebEngineWidgets.QWebEngineView(self)
        self.web_view2.setObjectName('web_view2')
        self.web_view2.setFixedHeight(450)
        self.web_view2.setUrl(QtCore.QUrl(base_url + 'trace2.htm'))
        self.ui.traceLayout.addWidget(self.web_view2)

        self.web_view3 = QtWebEngineWidgets.QWebEngineView(self)
        self.web_view3.setObjectName('web_view3')
        self.web_view3.setUrl(QtCore.QUrl(base_url + 'scheibe.htm'))
        self.ui.horizontalLayout_webview.addWidget(self.web_view3)
        self.web_view3.setMinimumHeight(300)

        # Connecting to PLC if autoconnect is checked
        self.ui.actionAutoVerbinden.setChecked(config.plc_autoconnect)
        if self.ui.actionAutoVerbinden.isChecked():
            self.on_connect()

        # Setting the Flag that an update of the RE Mode variables occurred
        opc_ua.reg_mode_update = True

    def continuous_ui_update(self):
        # This function runs in its own thread and keeps the visu updated with changes in the opc nodes
        while True:
            if opc_ua.is_connected():
                # Values to always get updated when connected
                self.ui.lineEdit_i1.setText('{:.2f} A'.format(opc_ua.m1_i))
                self.ui.lineEdit_i2.setText('{:.2f} A'.format(opc_ua.m2_i))

                if opc_ua.re_mode:
                    self.ui.lineEdit_x_m1.setText('{:.3f} U/min'.format(opc_ua.rpm))
                    self.ui.lineEdit_x_m2.setText('{:.3f} Nm'.format(opc_ua.torque))
                else:
                    self.ui.lineEdit_x_m1.setText('{:.3f} Nm'.format(opc_ua.torque))
                    self.ui.lineEdit_x_m2.setText('{:.3f} U/min'.format(opc_ua.rpm))

                # Values to only get updated after change event
                if opc_ua.change_event:
                    self.ui.checkBox_enable_m1.setChecked(opc_ua.m1_enable)
                    self.ui.checkBox_enable_m2.setChecked(opc_ua.m2_enable)
                    self.ui.checkBox_lin_active.setChecked(opc_ua.lin_active)
                    self.ui.SpinBox_I_m1.setValue(opc_ua.m1_i_lim)
                    self.ui.SpinBox_I_m2.setValue(opc_ua.m2_i_lim)
                    self.ui.spinBox_len_logger.setValue(opc_ua.logger_time)
                    self.ui.radio_cw.setChecked(opc_ua.m_cw)
                    self.ui.radio_ccw.setChecked(not opc_ua.m_cw)

                    # Values to only get updated when there was an update of RE mode variables
                    if opc_ua.reg_mode_update:
                        time.sleep(0.05)  # wait for PLC to apply changes
                        self.ui.radio_m1_n.setChecked(opc_ua.re_mode and opc_ua.m1_reg_n)
                        self.ui.radio_m1_m.setChecked(not opc_ua.re_mode and opc_ua.m1_reg_m)
                        self.ui.radio_m2_n.setChecked(not opc_ua.re_mode and opc_ua.m2_reg_n)
                        self.ui.radio_m2_m.setChecked(opc_ua.re_mode and opc_ua.m2_reg_m)
                        print('[MAIN] Reg Mode updated')
                        opc_ua.reg_mode_update = False

                    # Values that when updated depend on witch Motor is in revolution / torque mode
                    if opc_ua.re_mode:
                        self.ui.checkBox_re_m1_active.setChecked(opc_ua.re_n_active)
                        self.ui.checkBox_re_m2_active.setChecked(opc_ua.re_m_active)
                        self.ui.checkBox_awu_m1_active.setChecked(opc_ua.awu_n_active)
                        self.ui.checkBox_awu_m2_active.setChecked(opc_ua.awu_m_active)

                        if opc_ua.w_update:
                            self.ui.lineEdit_w_m1.setText('{:d}'.format(int(opc_ua.w_n)))
                            self.ui.lineEdit_w_m2.setText('{:d}'.format(int(opc_ua.w_m)))

                        self.ui.lineEdit_m1_p.setText('{:.3f}'.format(opc_ua.re_n_p))
                        self.ui.lineEdit_m1_i.setText('{:.3f}'.format(opc_ua.re_n_i))
                        self.ui.lineEdit_m1_d.setText('{:.3f}'.format(opc_ua.re_n_d))
                        self.ui.lineEdit_m2_p.setText('{:.3f}'.format(opc_ua.re_m_p))
                        self.ui.lineEdit_m2_i.setText('{:.3f}'.format(opc_ua.re_m_i))
                        self.ui.lineEdit_m2_d.setText('{:.3f}'.format(opc_ua.re_m_i))
                    else:

                        self.ui.checkBox_re_m1_active.setChecked(opc_ua.re_m_active)
                        self.ui.checkBox_re_m2_active.setChecked(opc_ua.re_n_active)
                        self.ui.checkBox_awu_m1_active.setChecked(opc_ua.awu_m_active)
                        self.ui.checkBox_awu_m2_active.setChecked(opc_ua.awu_n_active)

                        if opc_ua.w_update:
                            self.ui.lineEdit_w_m1.setText('{:d}'.format(int(opc_ua.w_m)))
                            self.ui.lineEdit_w_m2.setText('{:d}'.format(int(opc_ua.w_n)))

                        if opc_ua.re_update:
                            self.ui.lineEdit_m1_p.setText('{:.3f}'.format(opc_ua.re_m_p))
                            self.ui.lineEdit_m1_i.setText('{:.3f}'.format(opc_ua.re_m_i))
                            self.ui.lineEdit_m1_d.setText('{:.3f}'.format(opc_ua.re_m_d))
                            self.ui.lineEdit_m2_p.setText('{:.3f}'.format(opc_ua.re_n_p))
                            self.ui.lineEdit_m2_i.setText('{:.3f}'.format(opc_ua.re_n_i))
                            self.ui.lineEdit_m2_d.setText('{:.3f}'.format(opc_ua.re_n_d))

                    opc_ua.change_event = False
            # Wait one SPS cycle to next update
            time.sleep(0.05)

    def on_check_m1_enable(self):
        """Method handles clicks on the Motor 1 enable button"""
        if opc_ua.re_mode:
            if opc_ua.m1_reg_n and not opc_ua.m1_enable:
                opc_ua.m1_enable = True
                opc_ua.re_n_active = True
                opc_ua.awu_n_active = True
            elif opc_ua.m1_reg_n and opc_ua.m1_enable:
                opc_ua.m1_enable = False
                opc_ua.re_n_active = False
                opc_ua.awu_n_active = False
        else:
            if opc_ua.m1_reg_m and not opc_ua.m1_enable:
                opc_ua.m1_enable = True
                opc_ua.re_m_active = True
                opc_ua.awu_m_active = True
            elif opc_ua.m1_reg_m and opc_ua.m1_enable:
                opc_ua.m1_enable = False
                opc_ua.re_m_active = False
                opc_ua.awu_m_active = False
        self.ui.checkBox_enable_m1.setChecked(opc_ua.m1_enable)

    def on_check_m2_enable(self):
        """Method handles clicks on the Motor 2 enable button"""
        if not opc_ua.re_mode:
            if not opc_ua.m2_enable:
                opc_ua.m2_enable = True
                opc_ua.re_n_active = True
                opc_ua.awu_n_active = True
            else:
                opc_ua.m2_enable = False
                opc_ua.re_n_active = False
                opc_ua.awu_n_active = False
        else:
            if not opc_ua.m2_enable:
                opc_ua.m2_enable = True
                opc_ua.re_m_active = True
                opc_ua.awu_m_active = True
            else:
                opc_ua.m2_enable = False
                opc_ua.re_m_active = False
                opc_ua.awu_m_active = False
        self.ui.checkBox_enable_m2.setChecked(opc_ua.m2_enable)

    def on_reset(self):
        """Method to reset the emergency stop of the PLC"""
        opc_ua.reset()

    def on_shutdown(self):
        """Method to shutdown the PLC safely"""
        opc_ua.shutdown()

    def on_configure_plc_ip(self):
        """Method shows user dialog to enter new PLC IP"""
        text, ok = QInputDialog.getText(self, 'PLC IP Einstellen', 'Neue IP eingeben:')
        if ok and main.ip_check(text):
            config.plc_ip = text
            print('[IP CHECK] passed -> PLC IP changed')
            base_url = 'http://' + config.plc_ip + ':8080/'
            self.web_view.setUrl(QtCore.QUrl(base_url + 'trace.htm'))
            self.web_view2.setUrl(QtCore.QUrl(base_url + 'trace2.htm'))
            self.web_view3.setUrl(QtCore.QUrl(base_url + 'scheibe.htm'))

    @staticmethod
    def ip_check(ip:str):
        """Method checks if the user input fits the format of an IP"""
        try:
            values = ip.split('.')
            if not len(values) == 4:
                return False
            for value in values:
                if len(value) > 3:
                    return False
                if not 0 <= int(value) < 256:
                    return False
        except ValueError:
            return False
        return True

    def on_create_new_file(self):
        """Method creating a Text file to autosave values"""
        with open('snapshot.txt', 'w') as file:
            file.write('W_N\tW_M\tM1_I\tM2_I\tRPM\tM\n')

    def on_value_snapshot(self):
        """Method to add new row of live values to the Snapshot file"""
        with open('snapshot.txt', 'a') as file:
            line = '{:.3f}\t{:.3f}\t{:.3f}\t{:.3f}\t{:.3f}\t{:.5f}\n'.format(opc_ua.w_n, opc_ua.w_m, opc_ua.m1_i, opc_ua.m2_i, opc_ua.rpm, opc_ua.torque)
            file.write(line)

    def on_check_re_m1_active(self):
        """Method activates RE depending on RE mode (True = M1 N / M2 M, False = M1 M / M2 N)"""
        if opc_ua.re_mode:
            opc_ua.re_n_active = not opc_ua.re_n_active
        else:
            opc_ua.re_m_active = not opc_ua.re_m_active

    def on_check_re_m2_active(self):
        """Method activates RE depending on RE mode (True = M1 N / M2 M, False = M1 M / M2 N)"""
        if not opc_ua.re_mode:
            opc_ua.re_n_active = not opc_ua.re_n_active
        else:
            opc_ua.re_m_active = not opc_ua.re_m_active

    def on_check_awu_m1_active(self):
        """Method activates AWU depending on RE mode (True = M1 N / M2 M, False = M1 M / M2 N)"""
        if opc_ua.re_mode:
            opc_ua.awu_n_active = not opc_ua.awu_n_active
        else:
            opc_ua.awu_m_active = not opc_ua.awu_m_active

    def on_check_awu_m2_active(self):
        """Method activates AWU depending on RE mode (True = M1 N / M2 M, False = M1 M / M2 N)"""
        if not opc_ua.re_mode:
            opc_ua.awu_n_active = not opc_ua.awu_n_active
        else:
            opc_ua.awu_m_active = not opc_ua.awu_m_active

    def on_w_m1_changed(self):
        """Method writes controlvalue W depending on RE mode (True = M1 N / M2 M, False = M1 M / M2 N)"""
        if opc_ua.re_mode:
            opc_ua.w_n = main.get_value_as_float(self.ui.lineEdit_w_m1)
        else:
            opc_ua.w_m = main.get_value_as_float(self.ui.lineEdit_w_m1)

    def on_w_m2_changed(self):
        """Method writes controlvalue W depending on RE mode (True = M1 N / M2 M, False = M1 M / M2 N)"""
        if not opc_ua.re_mode:
            opc_ua.w_n = main.get_value_as_float(self.ui.lineEdit_w_m2)
        else:
            opc_ua.w_m = main.get_value_as_float(self.ui.lineEdit_w_m2)

    def on_m1_p_changed(self):
        """Sets RE parameter based on RE mode"""
        if opc_ua.re_mode:
            opc_ua.re_n_p = main.get_value_as_float(self.ui.lineEdit_m1_p)
        else:
            opc_ua.re_m_p = main.get_value_as_float(self.ui.lineEdit_m2_p)

    def on_m1_i_changed(self):
        """Sets RE parameter based on RE mode"""
        if opc_ua.re_mode:
            opc_ua.re_n_i = main.get_value_as_float(self.ui.lineEdit_m1_i)
        else:
            opc_ua.re_m_i = main.get_value_as_float(self.ui.lineEdit_m2_i)

    def on_m1_d_changed(self):
        """Sets RE parameter based on RE mode"""
        if opc_ua.re_mode:
            opc_ua.re_n_d = main.get_value_as_float(self.ui.lineEdit_m1_d)
        else:
            opc_ua.re_m_d = main.get_value_as_float(self.ui.lineEdit_m2_d)

    def on_m2_p_changed(self):
        """Sets RE parameter based on RE mode"""
        if not opc_ua.re_mode:
            opc_ua.re_n_p = main.get_value_as_float(self.ui.lineEdit_m1_p)
        else:
            opc_ua.re_m_p = main.get_value_as_float(self.ui.lineEdit_m2_p)

    def on_m2_i_changed(self):
        """Sets RE parameter based on RE mode"""
        if not opc_ua.re_mode:
            opc_ua.re_n_i = main.get_value_as_float(self.ui.lineEdit_m1_i)
        else:
            opc_ua.re_m_i = main.get_value_as_float(self.ui.lineEdit_m2_i)

    def on_m2_d_changed(self):
        """Sets RE parameter based on RE mode"""
        if not opc_ua.re_mode:
            opc_ua.re_n_d = main.get_value_as_float(self.ui.lineEdit_m1_d)
        else:
            opc_ua.re_m_d = main.get_value_as_float(self.ui.lineEdit_m2_d)

    def on_radio_m1_n(self):
        """Method sets RE mode and visu variables based on user input (Motor 1 N -> RE_mode = True)"""
        opc_ua.re_mode = True
        opc_ua.m1_reg_n = True
        opc_ua.m1_reg_m = False
        opc_ua.m2_reg_n = False
        opc_ua.m2_reg_m = True

    def on_radio_m1_m(self):
        """Method sets RE mode and visu variables based on user input (Motor 1 M -> RE_mode = False)"""
        opc_ua.re_mode = False
        opc_ua.m1_reg_n = False
        opc_ua.m1_reg_m = True
        opc_ua.m2_reg_n = True
        opc_ua.m2_reg_m = False

    def on_radio_m2_n(self):
        """Method sets RE mode and visu variables based on user input (Motor 2 N -> RE_mode = False)"""
        opc_ua.re_mode = False
        opc_ua.m1_reg_n = False
        opc_ua.m1_reg_m = True
        opc_ua.m2_reg_n = True
        opc_ua.m2_reg_m = False

    def on_radio_m2_m(self):
        """Method sets RE mode and visu variables based on user input (Motor 2 M -> RE_mode = True)"""
        opc_ua.re_mode = True
        opc_ua.m1_reg_n = True
        opc_ua.m1_reg_m = False
        opc_ua.m2_reg_m = True
        opc_ua.m2_reg_n = False

    def on_m1_i_lim_changed(self):
        """Method updates the current limit of Motor 1 on the PLC when changed in visu"""
        opc_ua.m1_i_lim = self.ui.SpinBox_I_m1.value()

    def on_m2_i_lim_changed(self):
        """Method updates the current limit of Motor 2 on the PLC when changed in visu"""
        opc_ua.m2_i_lim = self.ui.SpinBox_I_m2.value()

    def on_radio_cw(self):
        """Method sets CW = True and Radio CCW unchecked"""
        self.ui.radio_ccw.setChecked(False)
        opc_ua.m_cw = True

    def on_radio_ccw(self):
        """Method sets CW = False and Radio CW unchecked"""
        self.ui.radio_cw.setChecked(False)
        opc_ua.m_cw = False

    def on_connect(self):
        """Method tries to connect to PLC"""
        try:
            opc_ua.connect(config.plc_ip)
            try:
                self.on_show_lin()
            except ValueError:
                print('[MAIN] Linearisierungskennlinie corrupted')
            self.variable_subscription.start()
        except TypeError:
            print('[MAIN] IP error')

    def on_check_lin_active(self):
        """Method sets OPCUA Node for Lin active to state of Checkbox"""
        opc_ua.lin_active = self.ui.checkBox_lin_active.isChecked()

    def on_linearise_m1(self):
        """Method shows dialog, then automaticly generates linearisation for Motor 1"""
        self.ui.comboBox_motor.setCurrentIndex(0)
        index = 0 if self.ui.radio_cw.isChecked() else 1
        self.ui.comboBox_cw.setCurrentIndex(index)
        text, ok = QInputDialog.getText(self, 'Motor 1 Linearisieren', 'Zeit pro Messpunkt eingeben (0 = auto):')
        if ok:
            value = float(text)
            func = lambda: opc_ua.linearise(path='', wait_time=value, motor=1, cw=opc_ua.m_cw)
            linearise_thread = BasicThread(self, func)
            linearise_thread.start()

    def on_linearise_m2(self):
        """Method automaticly generates linearisation for Motor 2"""
        self.ui.comboBox_motor.setCurrentIndex(1)
        index = 0 if self.ui.radio_cw.isChecked() else 1
        self.ui.comboBox_cw.setCurrentIndex(index)
        text, ok = QInputDialog.getText(self, 'Motor 2 Linearisieren', 'Zeit pro Messpunkt eingeben (0 = auto):')
        if ok:
            value = float(text)
            func = lambda : opc_ua.linearise(path='', wait_time=value, motor=2, cw=opc_ua.m_cw)
            linearise_thread = BasicThread(self, func)
            linearise_thread.start()

    def on_validate_lin(self):
        """Method starts thread to automaticly check linearisation"""
        motor = self.ui.comboBox_motor.currentIndex() + 1
        cw = True if self.ui.comboBox_cw.currentText() == 'CW' else False
        func = lambda : opc_ua.linearity_validation(wait_time=0.0, motor=motor, cw=cw)
        validation_thread = BasicThread(self, func)
        validation_thread.start()

    def on_show_lin(self):
        """Method loads the configured linearisation data from the PLC"""
        motor = self.ui.comboBox_motor.currentIndex() + 1
        cw = True if self.ui.comboBox_cw.currentText() == 'CW' else False
        values = opc_ua.get_lin_array(motor, cw)

        for i in range(2):
            for j in range(11):
                if float(values[i][j]) == float(int(values[i][j])):
                    string = str(values[i][j])
                else:
                    string = '{:.2f}'.format(values[i][j])
                self.ui.tableWidget.setItem(i, j, QTableWidgetItem(string))

    def on_write_lin(self):
        """Method writes the Values from the table to the PLC"""
        values_x = []
        values_y = []
        for i in range(11):
            values_x.append(float(self.ui.tableWidget.item(0, i).text()))
            values_y.append(float(self.ui.tableWidget.item(1, i).text()))
        values = [values_x, values_y]

        motor = self.ui.comboBox_motor.currentIndex() + 1
        cw = True if self.ui.comboBox_cw.currentText() == 'CW' else False
        opc_ua.set_lin_array(values, motor, cw)

    def on_plot_lin(self):
        """Method plots the data from the table widget"""
        values_x = []
        values_y = []
        for i in range(11):
            values_x.append(float(self.ui.tableWidget.item(0, i).text()))
            values_y.append(float(self.ui.tableWidget.item(1, i).text()))
        opc_ua.plot_linearity(values_x, values_y)

    def on_start_logger(self):
        """Method starts the logger on the PLC and a thread to visualize the progress"""
        opc_ua.logger_running = True
        logger_thread = BasicThread(self, self.logger_running)
        logger_thread.start()

    def on_read_logger(self):
        """Method reads the logger data from the PLC"""
        fname, ok = QFileDialog.getSaveFileUrl()
        fname = fname.toString()
        fname = fname[8:]
        fname = fname + '.txt'
        if not ok:
            fname = 'logger_data.txt'
        opc_ua.read_logger(fname)

    def on_logger_time_changed(self):
        """Method changes the logger time based on user input if the logger is not running"""
        if not opc_ua.logger_running:
            opc_ua.logger_time = self.ui.spinBox_len_logger.value()

    def logger_running(self):
        """Method for visualizing the progress of the logger (needs to run in separate thread)"""
        initial_value = self.ui.spinBox_len_logger.value()
        self.ui.spinBox_len_logger.setReadOnly(True)
        self.ui.spinBox_len_logger.setValue(0)
        start_time = time.time()
        while time.time() - start_time <= initial_value:
            value = time.time() - start_time
            self.ui.spinBox_len_logger.setValue(int(value))
            time.sleep(0.1)
        self.ui.spinBox_len_logger.setValue(initial_value)
        self.ui.spinBox_len_logger.setReadOnly(False)

    def on_auto_re(self):
        items = ['normal', 'schnell']
        item, ok = QInputDialog.getItem(self, "Automatische Reglerauslegung nach T-Summen-Regel",
                                        "Wie soll sich der Regler verhalten?", items, 0, False)
        if ok and item == 'normal':
            fast = False
        elif ok and item == 'schnell':
            fast = True
        else:
            return -1

        k_pr, t_i, t_d = opc_ua.auto_re(fast)

        items = ['übernehmen', 'verwerfen']
        item, ok = QInputDialog.getItem(self, "Regelparameter übernehmen",
                                        "P = {:.3f}, I = {:.3f}, D = {:.3f}".format(k_pr, t_i, t_d),
                                        items, 0, False)

        if ok and item == 'übernehmen':
            opc_ua.re_n_p = k_pr
            opc_ua.re_n_i = t_i
            opc_ua.re_n_d = t_d

    @staticmethod
    def get_value_as_float(ui_line_edit):
        """returns value of QLineEdit as float"""
        if ui_line_edit.text() == '':
            value = 0.0
        else:
            value = float(ui_line_edit.text())
        return value

    def on_write_config(self, filename=None):
        """writes the live values from the OPCUA server to local config file"""
        print('[MAIN] writing config file')
        config.plc_autoconnect = self.ui.actionAutoVerbinden.isChecked()
        config.re_drehzahl_p = opc_ua.re_n_p
        config.re_drehzahl_i = opc_ua.re_n_i
        config.re_drehzahl_d = opc_ua.re_n_d
        config.re_moment_p = opc_ua.re_m_p
        config.re_moment_i = opc_ua.re_m_i
        config.re_moment_d = opc_ua.re_m_d
        config.lin_rot_arr_m1_cw = opc_ua.get_lin_array(1, True)
        config.lin_rot_arr_m1_ccw = opc_ua.get_lin_array(1, False)
        config.lin_rot_arr_m2_cw = opc_ua.get_lin_array(2, True)
        config.lin_rot_arr_m2_ccw = opc_ua.get_lin_array(2, False)
        config.write()

    def on_read_config(self, filename=None):
        """gets basic setting and PLC IP from config file"""
        print('[MAIN] reading config file')
        config.read()
        self.ui.actionAutoVerbinden.setChecked(config.plc_autoconnect)

    def keyPressEvent(self, event):
        """capturing of key press events"""
        super().keyPressEvent(event)
        if event.key() == Qt.Key_Q:
            self.variable_subscription.stop()
            self.ui_update.stop()
            self.close()


class BasicThread(QThread):
    """basic class to execute thread, distinct function is defined by passing function pointer to init"""
    signal_counter = pyqtSignal(int)  # define new Signal

    def __init__(self, parent=None, function=None):
        super().__init__(parent)
        self.function = function

    def run(self):
        """automaticly called by the thread"""
        self.function()
        print('[MAIN] terminateing thread')

    def start_thread(self):
        print('[MAIN] starting thread...')
        self.start(QThread.NormalPriority)

    def stop(self):
        print('[MAIN] stopping thread...')
        self.terminate()


def except_hook(cls, exception, traceback):
    """printing errors to python console instead of terminal"""
    print('Fehler auf Mainebene')
    sys.__excepthook__(cls, exception, traceback)


if __name__ == '__main__':
    sys.excepthook = except_hook
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon('assets/icon/abbts.ico'))
    # add_ons.style.set_style(app)
    main = Main()
    main.show()
    sys.exit(app.exec_())
