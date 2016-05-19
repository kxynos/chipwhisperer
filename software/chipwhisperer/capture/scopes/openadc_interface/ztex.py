# Authors: Colin O'Flynn
#
# Find this and more at newae.com - this file is part of the chipwhisperer
# project, http://www.assembla.com/spaces/chipwhisperer
#
#    This file is part of chipwhisperer.
#
#    chipwhisperer is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    chipwhisperer is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with chipwhisperer.  If not, see <http://www.gnu.org/licenses/>.
#=================================================

import sys

import chipwhisperer.capture.scopes._qt as openadc_qt
from chipwhisperer.capture.scopes.cwhardware.ChipWhispererFWLoader import CWCRev2_Loader
from chipwhisperer.capture.scopes.cwhardware.ChipWhispererFWLoader import FWLoaderConfig
from chipwhisperer.capture.scopes.cwhardware.ChipWhispererFWLoaderGUI import FWLoaderConfigGUI
from chipwhisperer.common.utils.pluginmanager import Plugin
from chipwhisperer.common.utils.parameter import Parameterized, Parameter

try:
    import usb
except ImportError:
    usb = None


class OpenADCInterface_ZTEX(Parameterized, Plugin):
    _name = "OpenADC-ZTEX"

    def __init__(self, parentParam, oadcInstance):
        self.params = Parameter(name=self.getName(), type='group')
        self.ser = None
        self._toolActs = []

        if (openadc_qt is None) or (usb is None):
            missingInfo = ""
            if openadc_qt is None:
                missingInfo += "openadc.qt "
            if usb is None:
                missingInfo += " usb"
            raise ImportError("Needed imports for ChipWhisperer missing: %s" % missingInfo)
        else:
            self.scope = oadcInstance
            self.cwFirmwareConfig = FWLoaderConfig(CWCRev2_Loader())

    def __del__(self):
        if self.ser != None:
            self.ser.close()

    def con(self):
        if self.ser == None:

            # Download firmware if required
            self.cwFirmwareConfig.loadRequired()

            try:
                dev = usb.core.find(idVendor=0x221A, idProduct=0x0100)
            except IOError, e:
                exctype, value = sys.exc_info()[:2]
                raise IOError("FX2 Port " +  str(exctype) + str(value))

            if dev is None:
                raise IOError("FX2 Port. Could not open USB Device")

            dev.set_configuration()

            self.dev = dev
            self.writeEP = 0x06
            self.readEP = 0x82
            self.interface = 0
            self.ser = self

        try:
            self.scope.con(self.ser)
            print("OpenADC Found, Connecting")
        except IOError,e:
            exctype, value = sys.exc_info()[:2]
            raise IOError("OpenADC Error (FX2 Port): " + (str(exctype) + str(value)) + " - Did you download firmware/FPGA data to ChipWhisperer?")

    def dis(self):
        if self.ser != None:
            self.ser.close()
            self.ser = None

    def read(self, N=0, debug=False):
        try:
            # self.interface removed from call for latest API compatability
            data = self.dev.read(self.readEP, N, timeout=100)
        except IOError:
            return []

        data = bytearray(data)
        if debug:
            print "RX: ",
            for b in data:
                print "%02x "%b,
            print ""
        return data

    def write(self, data, debug=False):
        data = bytearray(data)
        if debug:
            print "TX: ",
            for b in data:
                print "%02x "%b,
            print ""
        # self.interface removed from call for latest API compatability
        self.dev.write(self.writeEP, data, timeout=500)

    def getTextName(self):
        try:
            return self.ser.name
        except:
            return "None?"

    def setupGuiActions(self, mainWindow):
        if not hasattr(self, 'fwLoaderConfigGUI'):
            self.fwLoaderConfigGUI = FWLoaderConfigGUI(mainWindow, self.cwFirmwareConfig)
        return [['CW Firmware Preferences','Configure ChipWhisperer FW Paths', self.fwLoaderConfigGUI.show],  # Can' use Config/Setup... name with MacOS
               ['Download CW Firmware','Download Firmware+FPGA To Hardware', self.cwFirmwareConfig.loadRequired]]
