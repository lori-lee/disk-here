#!/bin/env python
#coding:utf8
import os
import sys
import uuid
import subprocess as sp
from PyQt4 import QtGui as gui

if __name__ == '__main__':
    app = gui.QApplication(sys.argv);
    msgBox = gui.QMessageBox(None);
    msgBox.setText(str(uuid.getnode()));
    msgBox.show();
    sys.exit(app.exec_());
