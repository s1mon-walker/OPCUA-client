#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from configparser import ConfigParser


class Config:
    """Konfigurationsklasse für den remanenten Datenzugriff von Parametern."""
    def __init__(self, file_path=None):
        if file_path is None:
            absolute_path = (os.path.dirname(os.path.abspath(__file__))).replace('\\', '/')
            self._file_path = absolute_path + '/config.ini'
        else:
            self._file_path = file_path

        self._config = ConfigParser()

        # [plc]
        self.plc_ip = '0.0.0.0'
        self.plc_autoconnect = False

        # [param]
        self.re_drehzahl_p = 0.0
        self.re_drehzahl_i = 0.0
        self.re_drehzahl_d = 0.0

        self.re_moment_p = 0.0
        self.re_moment_i = 0.0
        self.re_moment_d = 0.0

        # [lin]
        self.lin_rot_arr_m1_cw = []
        self.lin_rot_arr_m1_ccw = []
        self.lin_rot_arr_m2_cw = []
        self.lin_rot_arr_m2_ccw = []

        self.read()

    def read(self):
        """Lesen der Parameter aus der Konfigurationsdatei."""
        try:
            f = open(self._file_path, 'r')
            self._config.read_file(f)
            f.close()

            # [plc]
            self.plc_ip = self._config.get('plc', 'ip')
            self.plc_autoconnect = self._config.getboolean('plc', 'autoconnect')

            # [param]
            self.re_drehzahl_p = self._config.getfloat('param', 'RE_Drehzahl_P')
            self.re_drehzahl_i = self._config.getfloat('param', 'RE_Drehzahl_I')
            self.re_drehzahl_d = self._config.getfloat('param', 'RE_Drehzahl_D')

            self.re_moment_p = self._config.getfloat('param', 'RE_Drehmoment_P')
            self.re_moment_i = self._config.getfloat('param', 'RE_Drehmoment_I')
            self.re_moment_d = self._config.getfloat('param', 'RE_Drehmoment_D')

            # [lin]
            self.lin_rot_arr_m1_cw = self._config.get('lin', 'Linearisierung_M1_CW')
            self.lin_rot_arr_m1_ccw = self._config.get('lin', 'Linearisierung_M1_CCW')
            self.lin_rot_arr_m2_cw = self._config.get('lin', 'Linearisierung_M2_CW')
            self.lin_rot_arr_m2_ccw = self._config.get('lin', 'Linearisierung_M2_CCW')

        except Exception as e:
            print('Error _config read:', str(e))

        finally:
            f.close()

    def write(self):
        """Schreiben der Parameter in die Konfigurationsdatei."""
        try:
            f = open(self._file_path, 'w')

            # [plc]
            self._config.set('plc', 'ip', self.plc_ip)
            self._config.set('plc', 'autoconnect', Config.bool_to_string(self.plc_autoconnect))

            # [param]
            #self._config.add_section('param')
            self._config.set('param', 'RE_Drehzahl_P', '{:.3f}'.format(self.re_drehzahl_p))
            self._config.set('param', 'RE_Drehzahl_I', '{:.3f}'.format(self.re_drehzahl_i))
            self._config.set('param', 'RE_Drehzahl_D', '{:.3f}'.format(self.re_drehzahl_d))

            self._config.set('param', 'RE_Drehmoment_P', '{:.3f}'.format(self.re_moment_p))
            self._config.set('param', 'RE_Drehmoment_I', '{:.3f}'.format(self.re_moment_i))
            self._config.set('param', 'RE_Drehmoment_D', '{:.3f}'.format(self.re_moment_d))

            # [lin]
            self._config.set('lin', 'Linearisierung_M1_CW', str(self.lin_rot_arr_m1_cw))
            self._config.set('lin', 'Linearisierung_M1_CCW', str(self.lin_rot_arr_m1_ccw))
            self._config.set('lin', 'Linearisierung_M2_CW', str(self.lin_rot_arr_m2_cw))
            self._config.set('lin', 'Linearisierung_M2_CCW', str(self.lin_rot_arr_m2_ccw))

            self._config.write(f)

        # except Exception as e:
        #     print('Error _config write:', str(e))

        finally:
            f.close()

    @staticmethod
    def bool_to_string(value):
        """Hilfsmethode zur Speicherung von boolschen Datentypen. In Konfigurationsdateien
        sind die Werte True und False in true und false zu konvertieren."""
        if value:
            string = 'true'
        else:
            string = 'false'
        return string


if __name__ == '__main__':
    config = Config()
    config.read()

    print('[plc]')
    print('ip =', config.plc_ip)

    config.write()
