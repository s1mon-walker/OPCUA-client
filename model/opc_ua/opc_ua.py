import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import time

from opcua import Client


class SubscriptionHandler(object):
    """Callbackhandler of the OPC-UA datachange event"""
    def __init__(self, callback=None):
        # refrence to external callback function
        self.callback = callback

    def datachange_notification(self, node, val, data):
        if self.callback is not None:
            self.callback(node.nodeid.Identifier.split()[-1], val)
            # print('change event ' + node.nodeid.Identifier.split()[-1])
        else:
            print('change event ' + node.nodeid.Identifier.split()[-1])


class Opc_Ua:
    """communication to PLC via the OPC-UA protocol
    requirements: pip install opcua."""

    def __init__(self, ip='192.168.0.31', callback_error=None):
        self.ip = ip
        self.url = 'opc.tcp://' + self.ip + ':4840'
        self.callback_error = callback_error

        self._client = Client(self.url)
        self._subscription_handler = None
        self._handler_ext_callback = None
        self._subscription = None
        self._handles = []
        self._connected = False

        # Value variable declaration
        self.__m1_enable = False
        self.__m2_enable = False
        self.m1_w = 0.0
        self.m2_w = 0.0
        self.__m1_i_lim = 0.0
        self.__m2_i_lim = 0.0
        self.__m1_reg_n = False
        self.__m2_reg_n = False
        self.__m1_reg_m = False
        self.__m2_reg_m = False
        self.__re_mode = False
        self.change_event = False
        self.reg_mode_update = False
        self.w_update = False
        self.__re_n_active = False
        self.__re_m_active = False
        self.__awu_n_active = False
        self.__awu_m_active = False
        self.__m1_i_lim = 0.0
        self.__m2_i_lim = 0.0
        self.__cw = True
        self.__m_cw = False
        self.__rpm = 0.0
        self.__torque = 0.0
        self.revolutions = 0.0
        self.logger_values = []
        self.__lin_active = False
        self.__w_n = 0.0
        self.__w_m = 0.0
        self.__logger_running = False
        self.__logger_time = 0.0
        self.__re_n_p = 0.0
        self.__re_n_i = 0.0
        self.__re_n_d = 0.0
        self.__re_m_p = 0.0
        self.__re_m_i = 0.0
        self.__re_m_d = 0.0
        self.re_update = True

        # Node variable declaration
        self.M1_ENABLE_N = None
        self.M2_ENABLE_N = None
        self.M1_W_N = None
        self.M2_W_N = None
        self.M_CW_N = None
        self.M1_REG_N_N = None
        self.M1_REG_M_N = None
        self.M2_REG_N_N = None
        self.M2_REG_M_N = None
        self.M1_I_LIM_N = None
        self.M2_I_LIM_N = None
        self.M1_I_N = None
        self.M2_I_N = None
        self.CW_N = None
        self.CCW_N = None
        self.Y_ROT_N = None
        self.RE_MODE_N = None
        self.REG_N_ACTIVE_N = None
        self.REG_M_ACTIVE_N = None
        self.AWU_N_ACTIVE_N = None
        self.AWU_M_ACTIVE_N = None
        self.RPM_N = None
        self.REVOLUTIONS_N = None
        self.Y_VISUOVERWRITE_N = None
        self.LIN_RPM_ACTIVE_N = None
        self.LIN_ROT_ARR_X_1_CW_N = None  # Lin Array Motor 1 CW X (Input)
        self.LIN_ROT_ARR_Y_1_CW_N = None  # Lin Array Motor 1 CW Y (Output)
        self.LIN_ROT_ARR_X_1_CCW_N = None  # Lin Array Motor 1 CW X (Input)
        self.LIN_ROT_ARR_Y_1_CCW_N = None  # Lin Array Motor 1 CW Y (Output)
        self.LIN_ROT_ARR_X_2_CW_N = None  # Lin Array Motor 1 CW X (Input)
        self.LIN_ROT_ARR_Y_2_CW_N = None  # Lin Array Motor 1 CW Y (Output)
        self.LIN_ROT_ARR_X_2_CCW_N = None  # Lin Array Motor 1 CW X (Input)
        self.LIN_ROT_ARR_Y_2_CCW_N = None  # Lin Array Motor 1 CW Y (Output)
        self.W_M_N = None
        self.W_N_N = None
        self.TORQUE_N = None
        self.LOGGER_NODES = []
        self.LOGGER_RUNNING_N = None
        self.LOGGER_TIME_N = None
        self.RE_N_P_N = None
        self.RE_N_I_N = None
        self.RE_N_D_N = None
        self.RE_M_P_N = None
        self.RE_M_I_N = None
        self.RE_M_D_N = None
        self.RESET_N = None
        self.SHUTDOWN_N = None

    def get_all_nodes(self):
        """Method gets all Nodes based on given Address"""
        base_addr = 'ns=4;s=|var|CODESYS Control for Raspberry Pi SL.app.'
        self.M1_ENABLE_N = self._client.get_node(base_addr + 'HAL.bAntrieb1_Visu_Enable')
        self.M2_ENABLE_N = self._client.get_node(base_addr + 'HAL.bAntrieb2_Visu_Enable')
        self.M_CW_N = self._client.get_node(base_addr + 'GVL_VISU_Hilfsvariablen.DrehrichtungVorgabe')
        self.M1_REG_N_N = self._client.get_node(base_addr + 'GVL_VISU_Hilfsvariablen.Reg_M1_Drehzahl')
        self.M1_REG_M_N = self._client.get_node(base_addr + 'GVL_VISU_Hilfsvariablen.Reg_M1_Drehmoment')
        self.M2_REG_N_N = self._client.get_node(base_addr + 'GVL_VISU_Hilfsvariablen.Reg_M2_Drehzahl')
        self.M2_REG_M_N = self._client.get_node(base_addr + 'GVL_VISU_Hilfsvariablen.Reg_M2_Drehmoment')
        self.M1_I_LIM_N = self._client.get_node(base_addr + 'GVL_VISU_Hilfsvariablen.Strom_M1_Limit')
        self.M2_I_LIM_N = self._client.get_node(base_addr + 'GVL_VISU_Hilfsvariablen.Strom_M2_Limit')
        self.M1_I_N = self._client.get_node(base_addr + 'HAL.fpga.rAdc1Strom')
        self.M2_I_N = self._client.get_node(base_addr + 'HAL.fpga.rAdc2Strom')
        self.REVOLUTIONS_N = self._client.get_node(base_addr + 'HAL.fpga.rDrehzahl')
        self.CW_N = self._client.get_node(base_addr + 'HAL.fpga.bEncoderCw')
        self.CCW_N = self._client.get_node(base_addr + 'HAL.fpga.bEncoderCcw')
        self.LIN_RPM_ACTIVE_N = self._client.get_node(base_addr + 'DC_MOTOR.bLinDrehzahlAktiv')
        self.Y_ROT_N = self._client.get_node(base_addr + 'DC_MOTOR.rY_Visu_Drehzahl')
        self.RE_MODE_N = self._client.get_node(base_addr + 'DC_MOTOR.bSelectRotMode')
        self.REG_N_ACTIVE_N = self._client.get_node(base_addr + 'DC_MOTOR.bRE_DrehzahlAktiv')
        self.REG_M_ACTIVE_N = self._client.get_node(base_addr + 'DC_MOTOR.bRE_DrehmomentAktiv')
        self.AWU_N_ACTIVE_N = self._client.get_node(base_addr + 'DC_MOTOR.bAWU_RE_Drehzahl_Aktiv')
        self.AWU_M_ACTIVE_N = self._client.get_node(base_addr + 'DC_MOTOR.bAWU_RE_Drehmoment_Aktiv')
        self.Y_VISUOVERWRITE_N = self._client.get_node(base_addr + 'DC_MOTOR.bY_VisuOverwrite')
        self.LIN_ROT_ARR_X_1_CW_N = self._client.get_node(base_addr + 'PersistentVars.arXLin1CW')
        self.LIN_ROT_ARR_Y_1_CW_N = self._client.get_node(base_addr + 'PersistentVars.arYLin1CW')
        self.LIN_ROT_ARR_X_1_CCW_N = self._client.get_node(base_addr + 'PersistentVars.arXLin1CCW')
        self.LIN_ROT_ARR_Y_1_CCW_N = self._client.get_node(base_addr + 'PersistentVars.arYLin1CCW')
        self.LIN_ROT_ARR_X_2_CW_N = self._client.get_node(base_addr + 'PersistentVars.arXLin2CW')
        self.LIN_ROT_ARR_Y_2_CW_N = self._client.get_node(base_addr + 'PersistentVars.arYLin2CW')
        self.LIN_ROT_ARR_X_2_CCW_N = self._client.get_node(base_addr + 'PersistentVars.arXLin2CCW')
        self.LIN_ROT_ARR_Y_2_CCW_N = self._client.get_node(base_addr + 'PersistentVars.arYLin2CCW')

        self.RE_N_P_N = self._client.get_node(base_addr + 'PersistentVars.Regler_Drehzahl_Kp')
        self.RE_N_I_N = self._client.get_node(base_addr + 'PersistentVars.Regler_Drehzahl_Ti')
        self.RE_N_D_N = self._client.get_node(base_addr + 'PersistentVars.Regler_Drehzahl_Td')
        self.RE_M_P_N = self._client.get_node(base_addr + 'PersistentVars.Regler_Drehmoment_Kp')
        self.RE_M_I_N = self._client.get_node(base_addr + 'PersistentVars.Regler_Drehmoment_Ti')
        self.RE_M_D_N = self._client.get_node(base_addr + 'PersistentVars.Regler_Drehmoment_Td')

        self.W_M_N = self._client.get_node(base_addr + 'MAIN.rW_Drehmoment_Visu_Value')
        self.W_N_N = self._client.get_node(base_addr + 'MAIN.rW_Drehzal_Visu_Value')
        self.RPM_N = self._client.get_node(base_addr + 'HAL.fpga.rRPM')
        self.TORQUE_N = self._client.get_node(base_addr + 'MAIN.rMoment_Ruoss')
        self.RESET_N = self._client.get_node(base_addr + 'MAIN.bReset')
        self.SHUTDOWN_N = self._client.get_node(base_addr + 'HAL.Shutdown')

        self.LOGGER_RUNNING_N = self._client.get_node(base_addr + 'DC_MOTOR.bLoggerRunning')
        self.LOGGER_TIME_N = self._client.get_node(base_addr + 'DC_MOTOR.rLoggerTime_Drehzahl')
        for i in range(11):
            # generate list of addresses to the logger arrays
            node = 'arTime' if i == 0 else 'arSignal_' + str(i)
            self.LOGGER_NODES.append(self._client.get_node(base_addr + 'DC_MOTOR.logger_drehzahl_0.' + node))

    def connect(self, ip=None):
        """Connecting to PLC"""
        try:
            if ip is None:
                self.url = 'opc.tcp://' + self.ip + ':4840'
            else:
                self.url = 'opc.tcp://' + ip + ':4840'
            self._client = Client(self.url)

            # print('connect')
            self._client.connect()
            self._connected = True

            self.get_all_nodes()
            self.read()
            print('[OPCUA] got all data')

        except Exception as e:
            self.callback_error('Error OPC UA connect:', e)

    def read(self):
        """Reading data"""
        try:
            self.__m1_enable = self.M1_ENABLE_N.get_value()
            self.__m2_enable = self.M1_ENABLE_N.get_value()
            self.__cw = self.CW_N.get_value()
            self.__w_n = self.W_N_N.get_value()
            self.__w_m = self.W_M_N.get_value()
            self.__m1_reg_n = self.M1_REG_N_N.get_value()
            self.__m1_reg_m = self.M1_REG_M_N.get_value()
            self.__m2_reg_n = self.M2_REG_N_N.get_value()
            self.__m2_reg_m = self.M2_REG_M_N.get_value()

        except Exception as e:
            self.callback_error('Error OPC UA read:', e)

    # Get and set methods for Motor 1 enable
    def get_m1_enable(self):
        return self.__m1_enable

    def set_m1_enable(self, value):
        self.__m1_enable = bool(value)
        self.M1_ENABLE_N.set_value(value, self.M1_ENABLE_N.get_data_type_as_variant_type())
    m1_enable = property(get_m1_enable, set_m1_enable)

    # Get and set methods for Motor 2 enable
    def get_m2_enable(self):
        return self.__m2_enable

    def set_m2_enable(self, value):
        self.__m2_enable = bool(value)
        self.M2_ENABLE_N.set_value(value, self.M2_ENABLE_N.get_data_type_as_variant_type())
    m2_enable = property(get_m2_enable, set_m2_enable)

    # Reset method
    def reset(self):
        self.RESET_N.set_value(not self.RESET_N.get_value())

    # Shutdown method
    def shutdown(self):
        self.SHUTDOWN_N.set_value(True, self.SHUTDOWN_N.get_data_type_as_variant_type())

    # Get and set methods for w revolutions
    def get_w_n(self):
        return self.__w_n

    def set_w_n(self, value):
        self.__w_n = float(value)
        self.W_N_N.set_value(value, self.W_N_N.get_data_type_as_variant_type())
    w_n = property(get_w_n, set_w_n)

    # Get and set methods for w torque
    def get_w_m(self):
        return self.__w_m

    def set_w_m(self, value):
        self.__w_m = float(value)
        self.W_M_N.set_value(value, self.W_M_N.get_data_type_as_variant_type())
    w_m = property(get_w_m, set_w_m)

    # Get and set methods for Motor 1 in revolution control
    def get_m1_reg_n(self):
        self.__m1_reg_n = self.M1_REG_N_N.get_value()
        return self.__m1_reg_n

    def set_m1_reg_n(self, value):
        self.__m1_reg_n = bool(value)
        self.M1_REG_N_N.set_value(value, self.M1_REG_N_N.get_data_type_as_variant_type())
    m1_reg_n = property(get_m1_reg_n, set_m1_reg_n)

    # Get and set methods for Motor 1 in torque control
    def get_m1_reg_m(self):
        self.__m1_reg_m = self.M1_REG_M_N.get_value()
        return self.__m1_reg_m

    def set_m1_reg_m(self, value):
        self.__m1_reg_m = bool(value)
        self.M1_REG_M_N.set_value(value, self.M1_REG_M_N.get_data_type_as_variant_type())
    m1_reg_m = property(get_m1_reg_m, set_m1_reg_m)

    # Get and set methods for Motor 2 in revolution control
    def get_m2_reg_n(self):
        self.__m2_reg_n = self.M2_REG_N_N.get_value()
        return self.__m2_reg_n

    def set_m2_reg_n(self, value):
        self.__m2_reg_n = bool(value)
        self.M2_REG_N_N.set_value(value, self.M2_REG_N_N.get_data_type_as_variant_type())
    m2_reg_n = property(get_m2_reg_n, set_m2_reg_n)

    # Get and set methods for Motor 2 in torque control
    def get_m2_reg_m(self):
        self.__m2_reg_m = self.M2_REG_M_N.get_value()
        return self.__m2_reg_m

    def set_m2_reg_m(self, value):
        self.__m2_reg_m = bool(value)
        self.M2_REG_M_N.set_value(value, self.M2_REG_M_N.get_data_type_as_variant_type())
    m2_reg_m = property(get_m2_reg_m, set_m2_reg_m)

    # Get and set methods for RotMode
    def get_re_mode(self):
        self.__re_mode = self.RE_MODE_N.get_value()
        return self.__re_mode

    def set_re_mode(self, value):
        self.__re_mode = bool(value)
        self.RE_MODE_N.set_value(value, self.RE_MODE_N.get_data_type_as_variant_type())
    re_mode = property(get_re_mode, set_re_mode)

    # Get and set methods for RE revolutions active
    def get_re_n_active(self):
        self.__re_n_active = self.REG_N_ACTIVE_N.get_value()
        return self.__re_n_active

    def set_re_n_active(self, value):
        self.__re_n_active = bool(value)
        self.REG_N_ACTIVE_N.set_value(value, self.REG_N_ACTIVE_N.get_data_type_as_variant_type())
    re_n_active = property(get_re_n_active, set_re_n_active)

    # Get and set methods for RE torque active
    def get_re_m_active(self):
        self.__re_m_active = self.REG_M_ACTIVE_N.get_value()
        return self.__re_m_active

    def set_re_m_active(self, value):
        self.__re_m_active = bool(value)
        self.REG_M_ACTIVE_N.set_value(value, self.REG_M_ACTIVE_N.get_data_type_as_variant_type())
    re_m_active = property(get_re_m_active, set_re_m_active)

    # Get and set methods for Motor 1 I lim
    def get_m1_i_lim(self):
        return self.__m1_i_lim

    def set_m1_i_lim(self, value):
        self.__m1_i_lim = float(value)
        self.M1_I_LIM_N.set_value(value, self.M1_I_LIM_N.get_data_type_as_variant_type())
    m1_i_lim = property(get_m1_i_lim, set_m1_i_lim)

    # Get and set methods for Motor 2 I lim
    def get_m2_i_lim(self):
        return self.__m2_i_lim

    def set_m2_i_lim(self, value):
        self.__m2_i_lim = float(value)
        self.M2_I_LIM_N.set_value(value, self.M2_I_LIM_N.get_data_type_as_variant_type())
    m2_i_lim = property(get_m2_i_lim, set_m2_i_lim)

    # Get method for I Motor 1
    def get_i_m1(self):
        return self.M1_I_N.get_value()
    m1_i = property(get_i_m1)

    # Get method for I Motor 2
    def get_i_m2(self):
        return self.M2_I_N.get_value()
    m2_i = property(get_i_m2)

    # Get method for RPM
    def get_rpm(self):
        self.__rpm = self.RPM_N.get_value()
        return self.__rpm
    rpm = property(get_rpm)

    # Get method for Torque
    def get_torque(self):
        self.__torque = self.TORQUE_N.get_value()
        return self.__torque
    torque = property(get_torque)

    # Get and set methods for Motor Clockwise selection
    def get_m_cw(self):
        return self.__m_cw

    def set_m_cw(self, value):
        self.__m_cw = bool(value)
        self.M_CW_N.set_value(value, self.M_CW_N.get_data_type_as_variant_type())
    m_cw = property(get_m_cw, set_m_cw)

    # Get and set methods for linearisation active
    def get_lin_active(self):
        return self.__lin_active

    def set_lin_acttive(self, value):
        self.__lin_active = bool(value)
        self.LIN_RPM_ACTIVE_N.set_value(value, self.LIN_RPM_ACTIVE_N.get_data_type_as_variant_type())
    lin_active = property(get_lin_active, set_lin_acttive)

    # Get and set methods for linearisation array
    def get_lin_array(self, motor=1, cw=True):
        """returns 2x11 list of linearisation values based on motor and cw selection"""
        value_x = []
        value_y = []
        if motor == 1 and cw:
            value_x = self.LIN_ROT_ARR_X_1_CW_N.get_value()
            value_y = self.LIN_ROT_ARR_Y_1_CW_N.get_value()
        if motor == 1 and not cw:
            value_x = self.LIN_ROT_ARR_X_1_CCW_N.get_value()
            value_y = self.LIN_ROT_ARR_Y_1_CCW_N.get_value()
        if motor == 2 and cw:
            value_x = self.LIN_ROT_ARR_X_2_CW_N.get_value()
            value_y = self.LIN_ROT_ARR_Y_2_CW_N.get_value()
        if motor == 2 and not cw:
            value_x = self.LIN_ROT_ARR_X_2_CCW_N.get_value()
            value_y = self.LIN_ROT_ARR_Y_2_CCW_N.get_value()
        return [value_x, value_y]

    def set_lin_array(self, values=[[], []], motor=1, cw=True):
        """sets linerarisation arrays on PLC to the input values (2x11 list)"""
        if motor == 1 and cw:
            self.LIN_ROT_ARR_X_1_CW_N.set_value(values[0], self.LIN_ROT_ARR_X_1_CW_N.get_data_type_as_variant_type())
            self.LIN_ROT_ARR_Y_1_CW_N.set_value(values[1], self.LIN_ROT_ARR_Y_1_CW_N.get_data_type_as_variant_type())
        if motor == 1 and not cw:
            self.LIN_ROT_ARR_X_1_CCW_N.set_value(values[0], self.LIN_ROT_ARR_X_1_CCW_N.get_data_type_as_variant_type())
            self.LIN_ROT_ARR_Y_1_CCW_N.set_value(values[1], self.LIN_ROT_ARR_Y_1_CCW_N.get_data_type_as_variant_type())
        if motor == 2 and cw:
            self.LIN_ROT_ARR_X_2_CW_N.set_value(values[0], self.LIN_ROT_ARR_X_2_CW_N.get_data_type_as_variant_type())
            self.LIN_ROT_ARR_Y_2_CW_N.set_value(values[1], self.LIN_ROT_ARR_Y_2_CW_N.get_data_type_as_variant_type())
        if motor == 2 and not cw:
            self.LIN_ROT_ARR_X_2_CCW_N.set_value(values[0], self.LIN_ROT_ARR_X_2_CCW_N.get_data_type_as_variant_type())
            self.LIN_ROT_ARR_Y_2_CCW_N.set_value(values[1], self.LIN_ROT_ARR_Y_2_CCW_N.get_data_type_as_variant_type())
        print('[LINEARISE] Arrys geschrieben')

    # Get and set methods for RE RPM P
    def get_re_n_p(self):
        self.__re_n_p = self.RE_N_P_N.get_value()
        return self.__re_n_p

    def set_re_n_p(self, value):
        self.__re_n_p = float(value)
        self.RE_N_P_N.set_value(value, self.RE_N_P_N.get_data_type_as_variant_type())
    re_n_p = property(get_re_n_p, set_re_n_p)

    # Get and set methods for RE RPM I
    def get_re_n_i(self):
        self.__re_n_i = self.RE_N_I_N.get_value()
        return self.__re_n_i

    def set_re_n_i(self, value):
        self.__re_n_i = float(value)
        self.RE_N_I_N.set_value(value, self.RE_N_I_N.get_data_type_as_variant_type())
    re_n_i = property(get_re_n_i, set_re_n_i)

    # Get and set methods for RE RPM D
    def get_re_n_d(self):
        self.__re_n_d = self.RE_N_D_N.get_value()
        return self.__re_n_d

    def set_re_n_d(self, value):
        self.__re_n_d = float(value)
        self.RE_N_D_N.set_value(value, self.RE_N_D_N.get_data_type_as_variant_type())
    re_n_d = property(get_re_n_d, set_re_n_d)

    # Get and set methods for RE torque P
    def get_re_m_p(self):
        self.__re_m_p = self.RE_M_P_N.get_value()
        return self.__re_m_p

    def set_re_m_p(self, value):
        self.__re_m_p = float(value)
        self.RE_M_P_N.set_value(value, self.RE_M_P_N.get_data_type_as_variant_type())
    re_m_p = property(get_re_m_p, set_re_m_p)

    # Get and set methods for RE torque I
    def get_re_m_i(self):
        self.__re_m_i = self.RE_M_I_N.get_value()
        return self.__re_m_i

    def set_re_m_i(self, value):
        self.__re_m_i = float(value)
        self.RE_M_I_N.set_value(value, self.RE_M_I_N.get_data_type_as_variant_type())
    re_m_i = property(get_re_m_i, set_re_m_i)

    # Get and set methods for RE torque D
    def get_re_m_d(self):
        self.__re_m_d = self.RE_M_D_N.get_value()
        return self.__re_m_d

    def set_re_m_d(self, value):
        self.__re_m_d = float(value)
        self.RE_M_D_N.set_value(value, self.RE_M_D_N.get_data_type_as_variant_type())
    re_m_d = property(get_re_m_d, set_re_m_d)

    # Get and set methods for RE AWU RPM active
    def get_awu_n_active(self):
        return self.__awu_n_active

    def set_awu_n_active(self, value):
        self.__awu_n_active = bool(value)
        self.AWU_N_ACTIVE_N.set_value(value, self.AWU_N_ACTIVE_N.get_data_type_as_variant_type())
    awu_n_active = property(get_awu_n_active, set_awu_n_active)

    # Get and set methods for RE AWU torque active
    def get_awu_m_active(self):
        return self.__awu_m_active

    def set_awu_m_active(self, value):
        self.__awu_m_active = bool(value)
        self.AWU_M_ACTIVE_N.set_value(value, self.AWU_M_ACTIVE_N.get_data_type_as_variant_type())
    awu_m_active = property(get_awu_m_active, set_awu_m_active)

    # Get and set methods for logger running
    def get_logger_running(self):
        self.__logger_running = self.LOGGER_RUNNING_N.get_value()
        return self.__logger_running

    def set_logger_running(self, value):
        self.__logger_running = bool(value)
        if not value: time.sleep(0.05)  # wait one SPS cycle to reset logger_running
        self.LOGGER_RUNNING_N.set_value(value, self.LOGGER_RUNNING_N.get_data_type_as_variant_type())
    logger_running = property(get_logger_running, set_logger_running)

    # Get and set methods for logger time
    def get_logger_time(self):
        return self.__logger_time

    def set_logger_time(self, value):
        if not self.__logger_running:
            self.__logger_time = float(value)
            self.LOGGER_TIME_N.set_value(value, self.LOGGER_TIME_N.get_data_type_as_variant_type())
    logger_time = property(get_logger_time, set_logger_time)

    def disconnect(self):
        """disconnect from PLC"""
        try:
            print('[OPCUA] disconnecting...')
            self._client.disconnect()
            self._connected = False
        except Exception as e:
            self.callback_error('Error OPC UA disconnect:', e)

    def subscribe_datachange_event(self, callback=None, inhibit_time=500):
        """activating the OPC-UA node in server eventhandler at change of values"""
        self._subscription_handler = SubscriptionHandler(self.callback_datachange)
        self._handler_ext_callback = callback
        self._subscription = self._client.create_subscription(inhibit_time, self._subscription_handler)
        self._handles.append(self._subscription.subscribe_data_change(self.M1_ENABLE_N))
        self._handles.append(self._subscription.subscribe_data_change(self.M2_ENABLE_N))
        self._handles.append(self._subscription.subscribe_data_change(self.W_M_N))
        self._handles.append(self._subscription.subscribe_data_change(self.W_N_N))
        self._handles.append(self._subscription.subscribe_data_change(self.M_CW_N))
        self._handles.append(self._subscription.subscribe_data_change(self.M1_REG_N_N))
        self._handles.append(self._subscription.subscribe_data_change(self.M1_REG_M_N))
        self._handles.append(self._subscription.subscribe_data_change(self.M2_REG_N_N))
        self._handles.append(self._subscription.subscribe_data_change(self.M2_REG_M_N))
        self._handles.append(self._subscription.subscribe_data_change(self.RE_MODE_N))
        self._handles.append(self._subscription.subscribe_data_change(self.REG_N_ACTIVE_N))
        self._handles.append(self._subscription.subscribe_data_change(self.REG_M_ACTIVE_N))
        self._handles.append(self._subscription.subscribe_data_change(self.AWU_N_ACTIVE_N))
        self._handles.append(self._subscription.subscribe_data_change(self.AWU_M_ACTIVE_N))
        self._handles.append(self._subscription.subscribe_data_change(self.M1_I_LIM_N))
        self._handles.append(self._subscription.subscribe_data_change(self.M2_I_LIM_N))
        self._handles.append(self._subscription.subscribe_data_change(self.RE_N_P_N))
        self._handles.append(self._subscription.subscribe_data_change(self.RE_N_I_N))
        self._handles.append(self._subscription.subscribe_data_change(self.RE_N_D_N))
        self._handles.append(self._subscription.subscribe_data_change(self.RE_M_P_N))
        self._handles.append(self._subscription.subscribe_data_change(self.RE_M_I_N))
        self._handles.append(self._subscription.subscribe_data_change(self.RE_M_D_N))
        self._handles.append(self._subscription.subscribe_data_change(self.LOGGER_TIME_N))
        self._handles.append(self._subscription.subscribe_data_change(self.LIN_RPM_ACTIVE_N))

    def unsubscribe_datachange_event(self):
        """deleting all handles from server eventhandler"""
        for handle in self._handles:
            self._subscription.unsubscribe(handle)

    def callback_datachange(self, identifier, val):
        """callbackfunction after datachange"""
        print(identifier, ' = ', val)
        self.change_event = True
        # Change events of control setpoint W
        if identifier.find('rW_Drehzal_Visu_Value') >= 0:
            self.__w_n = val
            self.w_update = True
        elif identifier.find('rW_Drehmoment_Visu_Value') >= 0:
            self.__w_m = val
            self.w_update = True
        # Change events of Motor enable
        elif identifier.find('bAntrieb1_Visu_Enable') >= 0:
            self.__m1_enable = val
        elif identifier.find('bAntrieb2_Visu_Enable') >= 0:
            self.__m2_enable = val
        # Change events of rotation direction
        elif identifier.find('DrehrichtungVorgabe') >= 0:
            self.__m_cw = val
        # Change events of RE Mode
        elif identifier.find('Reg_M1_Drehzahl') >= 0:
            self.__m1_reg_n = val
            self.reg_mode_update = True
        elif identifier.find('Reg_M1_Drehmoment') >= 0:
            self.__m1_reg_m = val
            self.reg_mode_update = True
        elif identifier.find('Reg_M2_Drehzahl') >= 0:
            self.__m2_reg_n = val
            self.reg_mode_update = True
        elif identifier.find('Reg_M2_Drehmoment') >= 0:
            self.__m2_reg_m = val
            self.reg_mode_update = True
        elif identifier.find('bSelectRotMode') >= 0:
            self.__re_mode = val
            self.reg_mode_update = True
        elif identifier.find('bRE_DrehzahlAktiv') >= 0:
            self.__re_n_active = val
            self.reg_mode_update = True
        elif identifier.find('bRE_DrehmomentAktiv') >= 0:
            self.__re_m_active = val
            self.reg_mode_update = True
        elif identifier.find('bAWU_RE_Drehzahl_Aktiv') >= 0:
            self.__awu_n_active = val
            self.reg_mode_update = True
        elif identifier.find('bAWU_RE_Drehmoment_Aktiv') >= 0:
            self.__awu_m_active = val
            self.reg_mode_update = True
        # Change events of current Limit
        elif identifier.find('Strom_M1_Limit') >= 0:
            self.__m1_i_lim = val
        elif identifier.find('Strom_M2_Limit') >= 0:
            self.__m2_i_lim = val
        # Change events of RE parameters
        elif identifier.find('Regler_Drehzahl_Kp') >= 0:
            self.__re_n_p = val
            self.re_update = True
        elif identifier.find('Regler_Drehzahl_Ti') >= 0:
            self.__re_n_i = val
            self.re_update = True
        elif identifier.find('Regler_Drehzahl_Td') >= 0:
            self.__re_n_d = val
            self.re_update = True
        elif identifier.find('Regler_Drehmoment_Kp') >= 0:
            self.__re_m_p = val
            self.re_update = True
        elif identifier.find('Regler_Drehmoment_Ti') >= 0:
            self.__re_m_i = val
            self.re_update = True
        elif identifier.find('Regler_Drehmoment_Td') >= 0:
            self.__re_m_d = val
            self.re_update = True
        # Change events of logger time
        elif identifier.find('rLoggerTime_Drehzahl') >= 0:
            self.__logger_time = val
        # Change events of linearisation active
        elif identifier.find('bLinDrehzahlAktiv') >= 0:
            self.__lin_active = val
        else:
            print('callback_datachange unbekannter Variablencallback')

        if self._handler_ext_callback is not None:
            self._handler_ext_callback(identifier, val)

    def callback_error(self, *args):
        """errorhandler"""
        self._connected = False
        try:
            self._client.disconnect()
        except Exception as e:
            pass

        if self.callback_error is not None:
            self.callback_error(*args)
        else:
            print('call_callback_error', args)
            sys.exit()

    def is_connected(self):
        return self._connected

    def linearise(self, path='', input_min_value=0, input_max_value=100, steps=11, wait_time=3.0, motor=1, cw=True, min_time=3):
        """automatically drives the motor to generate linearisation values"""
        self.reset()  # reset emergancy stop
        self.Y_VISUOVERWRITE_N.set_value(True)  # enable overwrite directly to HAL
        self.LIN_RPM_ACTIVE_N.set_value(False)  # disable linearisation

        # Arrays for input and output values
        input_values = np.linspace(input_min_value, input_max_value, steps, True)
        output_values = np.zeros(steps, np.float)

        # choose the motor
        if motor == 1:
            MOTOR_ENABLE = self.M1_ENABLE_N
            self.RE_MODE_N.set_value(True)
        else:
            MOTOR_ENABLE = self.M2_ENABLE_N
            self.RE_MODE_N.set_value(False)

        # choose direction
        self.M_CW_N.set_value(cw)

        # Set RPM to 0
        self.Y_ROT_N.set_value(int(input_min_value), self.Y_ROT_N.get_data_type_as_variant_type())
        MOTOR_ENABLE.set_value(True)

        print('Messung starten: dauer {} s'.format(steps*wait_time))

        for i in range(steps):
            # set drive speed
            self.Y_ROT_N.set_value(int(input_values[i]), self.Y_ROT_N.get_data_type_as_variant_type())

            # wait for system to stabilize
            values_queue = [self.REVOLUTIONS_N.get_value()] * 50
            new_queue = [0] * 10
            time_step = time.time()
            if wait_time <= 0:
                while True:
                    # loop that detects when system is stable and input can be incremented
                    time.sleep(0.05)
                    new_value = self.REVOLUTIONS_N.get_value()
                    new_queue.append(new_value)
                    if time.time() - time_step > min_time:
                        if abs(np.mean(new_queue) - np.mean(values_queue)) < 0.01:
                            time_step = time.time()
                            break
                    values_queue.pop(0)
                    values_queue.append(new_queue.pop(0))
            else:
                time.sleep(wait_time)

            # save corresponding revolutions
            output_values[i] = self.REVOLUTIONS_N.get_value()

            print('Messung {}/{} abgeschlossen {} sekunden verbleibend'.format(i+1, steps, (steps-i-1)*wait_time))

        # Set RPM back to 0 and deactivate motor
        self.Y_ROT_N.set_value(0, self.Y_ROT_N.get_data_type_as_variant_type())
        MOTOR_ENABLE.set_value(False)

        normalized_values = np.divide(output_values, output_values[-1]) * 100

        file_name = 'linearisation_m' + str(motor)
        file_name += '_cw.txt' if cw else '_ccw.txt'
        file = open(path + file_name, 'w')

        for i in range(len(input_values)):
            line = '{:.6f}\t{:.6f}\t{:.6f}\n'.format(input_values[i], output_values[i], normalized_values[i])
            file.write(line)

        file.close()
        print('Datei gespeichert')

        self.Y_VISUOVERWRITE_N.set_value(False)
        self.LIN_RPM_ACTIVE_N.set_value(True)

        if motor == 1 and cw:
            self.LIN_ROT_ARR_X_1_CW_N.set_value(normalized_values.tolist(), self.LIN_ROT_ARR_X_1_CW_N.get_data_type_as_variant_type())
            self.LIN_ROT_ARR_Y_1_CW_N.set_value(input_values.tolist(), self.LIN_ROT_ARR_Y_1_CW_N.get_data_type_as_variant_type())
        if motor == 1 and not cw:
            self.LIN_ROT_ARR_X_1_CCW_N.set_value(normalized_values.tolist(), self.LIN_ROT_ARR_X_1_CCW_N.get_data_type_as_variant_type())
            self.LIN_ROT_ARR_Y_1_CCW_N.set_value(input_values.tolist(), self.LIN_ROT_ARR_Y_1_CCW_N.get_data_type_as_variant_type())
        if motor == 2 and cw:
            self.LIN_ROT_ARR_X_2_CW_N.set_value(normalized_values.tolist(), self.LIN_ROT_ARR_X_2_CW_N.get_data_type_as_variant_type())
            self.LIN_ROT_ARR_Y_2_CW_N.set_value(input_values.tolist(), self.LIN_ROT_ARR_Y_2_CW_N.get_data_type_as_variant_type())
        if motor == 2 and not cw:
            self.LIN_ROT_ARR_X_2_CCW_N.set_value(normalized_values.tolist(), self.LIN_ROT_ARR_X_2_CCW_N.get_data_type_as_variant_type())
            self.LIN_ROT_ARR_Y_2_CCW_N.set_value(input_values.tolist(), self.LIN_ROT_ARR_Y_2_CCW_N.get_data_type_as_variant_type())
        print('[LINEARISE] Arrys geschrieben')
        Opc_Ua.plot_linearity(input_values, normalized_values)

    def linearity_validation(self, input_min_value=0, input_max_value=100, steps=11, wait_time=3.0, motor=1, cw=True):
        """automaticly drives the motor to validate the linearisation values"""
        self.reset()  # reset emergancy stop
        self.Y_VISUOVERWRITE_N.set_value(True)  # enable overwrite directly to HAL
        self.LIN_RPM_ACTIVE_N.set_value(True)  # activate the linearisation

        # Arrays for Input and Output Values
        input_values = np.linspace(input_min_value, input_max_value, steps, True)
        output_values = np.zeros(steps, np.float)

        if motor == 1:
            MOTOR_ENABLE = self.M1_ENABLE_N
            self.RE_MODE_N.set_value(True)
        else:
            MOTOR_ENABLE = self.M2_ENABLE_N
            self.RE_MODE_N.set_value(False)

        self.M_CW_N.set_value(cw)

        # Set RPM to 0
        self.Y_ROT_N.set_value(int(input_min_value), self.Y_ROT_N.get_data_type_as_variant_type())
        MOTOR_ENABLE.set_value(True)

        print('Verifikation starten: dauer {} s'.format(steps*wait_time))

        for i in range(steps):

            # set drive speed
            self.Y_ROT_N.set_value(int(input_values[i]), self.Y_ROT_N.get_data_type_as_variant_type())

            # wait for system to stabilize
            values_queue = [self.REVOLUTIONS_N.get_value()] * 50  # queue of 50 old values
            new_queue = [0] * 10  # queue of 10 new values
            time_step = time.time()  # time of last input step
            if wait_time <= 0:  # if defined waittime smaller than 0 -> try auto detecting stable state
                while True:
                    # loop that detects when system is stable and input can be incremented
                    time.sleep(0.05)  # wait one SPS cycle
                    new_value = self.REVOLUTIONS_N.get_value()  # get newest value
                    new_queue.append(new_value)  # append newest value to list
                    if time.time() - time_step > 2:  # if minimum waittime is reachend
                        if abs(np.mean(new_queue) - np.mean(values_queue)) < 0.01:
                            time_step = time.time()  # set new steptime
                            break  # break waiting loop to set new step
                    values_queue.pop(0)  # remove oldest value from old values queue
                    values_queue.append(new_queue.pop(0))  # move oldest value from new queue to old queue
            else:
                time.sleep(wait_time)  # just wait time secified by function parameters

            # save corresponding revolutions
            output_values[i] = self.REVOLUTIONS_N.get_value()

            print('Messung {}/{} abgeschlossen {} sekunden verbleibend'.format(i+1, steps, (steps-i-1)*wait_time))

        # Set RPM back to 0 and deactivate motor
        self.Y_ROT_N.set_value(0, self.Y_ROT_N.get_data_type_as_variant_type())
        MOTOR_ENABLE.set_value(False)

        normalized_values = np.divide(output_values, output_values[-1]) * 100

        self.Y_VISUOVERWRITE_N.set_value(False)

        Opc_Ua.plot_linearity(input_values, normalized_values)

    @staticmethod
    def plot_linearity(input, output):
        """plots the given input and output values"""
        x = np.arange(0, len(input))
        plt.plot(x, input)
        plt.plot(x, output)
        plt.grid()
        plt.show()

    def read_logger(self, file_name='logger_data.txt'):
        """reads the logger data via OPCUA from the PLC"""
        self.logger_values = []
        # read data from PLC logger
        for node in self.LOGGER_NODES:
            self.logger_values.append(node.get_value())

        # process logger data
        for n in range(len(self.LOGGER_NODES)):
            for i in range(0, len(self.logger_values[n])):
                self.logger_values[n][i] = self.logger_values[n][i]*1.0 + 0.0

        # save logger data to csv
        # file_name = "logger_data.txt"
        with open(file_name, 'w') as file:
            for i in range(0, len(self.logger_values[0])):
                line = ''
                for n in range(len(self.logger_values)):
                    line += '{:.3f}\t'.format(self.logger_values[n][i])
                file.write(line + '\n')

        # plot logger data
        fig = plt.figure(figsize=(15.0, 10.0), dpi=300, facecolor="white")
        ax = fig.add_subplot(1, 1, 1)
        ax.plot(self.logger_values[0], self.logger_values[1], '-', linewidth=2, label="w_geRampt")
        ax.plot(self.logger_values[0], self.logger_values[2], '-', linewidth=2, label="w")
        ax.plot(self.logger_values[0], self.logger_values[3], '-', linewidth=2, label="x")
        ax.plot(self.logger_values[0], self.logger_values[4], '-', linewidth=2, label="y_RE")
        ax.plot(self.logger_values[0], self.logger_values[5], '-', linewidth=2, label="y")
        ax.plot(self.logger_values[0], self.logger_values[6], '-', linewidth=2, label="y_lin")
        ax.plot(self.logger_values[0], self.logger_values[7], '-', linewidth=2, label="pwm")
        ax.plot(self.logger_values[0], self.logger_values[8], '-', linewidth=2, label="w_M")
        ax.plot(self.logger_values[0], self.logger_values[9], '-', linewidth=2, label="x_M")
        ax.plot(self.logger_values[0], self.logger_values[10], '-', linewidth=2, label="y_M")

        ax.legend(loc='upper right', fancybox=True, title='')
        plt.grid(True)
        plt.show()
        fig.savefig('logger_data.png', dpi=96)

    def auto_re(self, fast=True):
        """This method needs a time vector and samples of system with oscillating input and output"""
        time = self.logger_values[0]
        sig_y = self.logger_values[5]
        sig_x = self.logger_values[3]

        t_sum = Opc_Ua.calc_t_sum(time, sig_y, sig_x)

        delta_y = max(sig_y) - min(sig_y)
        delta_x = max(sig_x) - min(sig_x)
        k_ps = delta_x / delta_y

        if fast:
            k_pr = 2 / k_ps
            t_i = 0.8 * t_sum
            t_d = 0.194 * t_sum
        else:
            k_pr = 1 / k_ps
            t_i = 0.66 * t_sum
            t_d = 0.167 * t_sum

        print('K_ps = {:.3f} T_sum = {:.3f}'.format(k_ps, t_sum))
        return k_pr, t_i, t_d

    @staticmethod
    def calc_t_sum(time, sig_y, sig_x, smooth=9):
        time = np.asarray(time)
        sig_y = np.asarray(sig_y)
        sig_x_unfilterd = np.asarray(sig_x)

        if smooth > 1:
            sig_x = pd.Series(sig_x_unfilterd).rolling(smooth, center=True).mean()
            sig_x = sig_x[int(np.ceil(smooth/2)):-int(np.ceil(smooth/2))]
            sig_x = np.asarray(sig_x)
        else:
            sig_x = sig_x_unfilterd

        sig_y = sig_y - min(sig_y)
        sig_x = sig_x - min(sig_x)

        threshold = 0.1 * max(sig_y)

        # starting at a point where the signal y is in low state
        index_start = 0
        i = 0
        while i < len(sig_y):
            if sig_y[i] < threshold / 2:
                index_start = i
                break
            else:
                i += 1

        # finding the step in signal y
        index_step = 0
        i = index_start
        while i < len(sig_y):
            if sig_y[i] > threshold:
                index_step = i
                break
            else:
                i += 1

        # set endpoint to static high section of signal x
        index_end = 0
        i = index_step
        while i < len(sig_x):
            if sig_x[i] > (0.99 * max(sig_x)):
                index_end = i
                break
            else:
                i += 1

        # trim all signals to just the significant parts
        time = time[index_step:index_end]
        sig_y = sig_y[index_step:index_end]
        sig_x = sig_x[index_step:index_end]

        # searching for index of t_sum by trying
        index_t_sum = 0
        i = 0
        while i < len(sig_x):
            before_t = sig_x[:i]
            after_t = sig_x[i:]
            sum_bevore_t = sum(before_t)
            sum_after_t = max(sig_x) * len(after_t) - sum(after_t)

            if sum_bevore_t > sum_after_t:
                index_t_sum = i
                break
            else:
                i += 1

        t_sum = time[index_t_sum] - time[0]

        # plot the result
        plt.plot(time, sig_y)
        plt.plot(time, sig_x)
        plt.vlines(t_sum + time[0], min(sig_x), max(sig_x))
        plt.hlines([min(sig_x), max(sig_x)], time[0], time[-1])
        plt.fill_between(time[:index_t_sum], sig_x[:index_t_sum])
        plt.fill_between(time[index_t_sum:], max(sig_x), sig_x[index_t_sum:])
        plt.show()

        return t_sum


if __name__ == '__main__':
    import time

    opc_ua = Opc_Ua('192.168.2.114')
    opc_ua.connect()
    opc_ua.read()
    print(f'rRadius = {opc_ua.rRadius:1.01f} | rBogenmass = {opc_ua.rBogenmass:0.03f}')
    opc_ua.write(rRadius=99.9)
    print(f'rRadius = {opc_ua.rRadius:1.01f} | rBogenmass = {opc_ua.rBogenmass:0.03f}')
    opc_ua.subscribe_datachange_event()
    time.sleep(2.25)
    opc_ua.unsubscribe_datachange_event()
    time.sleep(1.25)
    opc_ua.disconnect()
