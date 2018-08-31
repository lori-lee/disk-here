#!/bin/env python
#coding:utf8
import sys
import os
import uuid
from PyQt4 import QtGui as gui
from PyQt4 import QtCore as core
from PyQt4 import Qt as qt
import cv2 as cv
import time as tm
import ctypes as ct
import math as m
from colormath.color_objects import sRGBColor as rgbcolor, LabColor as labcolor
from colormath.color_conversions import convert_color as converter
from colormath.color_diff import delta_e_cie2000 as deltaE2000

class Utils(object):
    #
    s_windll  = None;
    s_user32  = None;
    s_gdi32   = None;
    s_screendc= None;
    s_getPixel= None;
    #
    s_screenImage = None;
    #
    s_targetWidget= None;
    s_widgetRect  = None;
    #
    @staticmethod
    def encrypt(date):
        mac = Utils.getMac();
        smac= mac >> 24;
        lmac= mac & ((1 << 24) - 1);
        crypt = (smac | lmac) ^ date;
    #
    def decrypt(cipher):
        mac = Utils.getMac();
        smac= mac >> 24;
        lmac= mac & ((1 << 24) - 1);
        return cipher ^ (smac | lmac);
    #
    @staticmethod
    def isRegistered():
        cwd = os.getcwd();
        file= '%s/data.dat';
        if os.path.isfile(file):
            pass
        else:
            return False;
    @staticmethod
    def  getMac():
        return '%X' % uuid.getnode();
    #
    @staticmethod
    def colorDeltaE(rgbA, rgbB):
        colorA = rgbcolor(float(rgbA[0]) / 255, float(rgbA[1]) / 255, float(rgbA[2]) / 255);
        colorB = rgbcolor(float(rgbB[0]) / 255, float(rgbB[1]) / 255, float(rgbB[2]) / 255);
        colorLabA = converter(colorA, labcolor);
        colorLabB = converter(colorB, labcolor);
        deltaE = deltaE2000(colorLabA, colorLabB);
        #print m.sqrt(pow(colorLabA.lab_l - colorLabB.lab_l, 2) + pow(colorLabA.lab_a - colorLabB.lab_a, 2) + pow(colorLabA.lab_b - colorLabB.lab_b, 2));
        return deltaE;
    #
    @staticmethod
    #https://stackoverflow.com/questions/9018016/how-to-compare-two-colors-for-similarity-difference
    #https://www.compuphase.com/cmetric.htm
    #https://enwikipedia.org/wiki/Color_difference
    #Lab & LUV color space
    def colorDistance(rgbA, rgbB):
        rmean = 0.5 * (rgbA[0] + rgbB[0]);
        dr    = rgbA[0] - rgbB[0];
        dg    = rgbA[1] - rgbB[1];
        db    = rgbA[2] - rgbB[2];
        dr2   = pow(dr, 2);
        dg2   = pow(dg, 2);
        db2   = pow(db, 2);
        return m.sqrt(2 * dr2 + 4 * dg2 + 3 * db2 + (rmean * (dr2 - db2) / 256));
    #
    @staticmethod
    def getCrossPoints(x, y, r, dx, dy):
        l = m.sqrt(pow(dx, 2) + pow(dy, 2));
        dx *= r;
        dy *= r;
        dx /= l;
        dy /= l;
        return ((int(x - dx), int(y - dy)), (int(x + dx), int(y + dy)));
    #
    @staticmethod
    def getWidgetRectImage():
        widget = Utils.s_targetWidget;
        rect   = Utils.s_widgetRect;
        if isinstance(widget, gui.QWidget) and isinstance(rect, core.QRect):
            pixMap = gui.QPixmap.grabWidget(widget, rect);
            Utils.s_screenImage = pixMap.toImage();
        return Utils.s_screenImage;
    #
    @staticmethod
    def setScreenWidget(widget):
        Utils.s_targetWidget = widget;
        Utils.getWidgetRectImage();
    #
    @staticmethod
    def setWidgetArea(rect):
        Utils.s_widgetRect = rect;
        Utils.getWidgetRectImage();
    #
    @staticmethod
    def getPixel2(x, y):
        if not Utils.s_screenImage:
            #Utils.s_screenImage = gui.QPixmap.grabWindow(gui.QApplication.desktop().winId()).toImage();
            Utils.getWidgetRectImage();
        abgr = Utils.s_screenImage.pixel(x, y);
        return (gui.qRed(abgr), gui.qGreen(abgr), gui.qBlue(abgr), gui.qAlpha(abgr));
    #
    @staticmethod
    def getPixel(x, y):
        if not Utils.s_windll:
            Utils.s_windll = ct.windll;
        if not Utils.s_user32:
            Utils.s_user32 = Utils.s_windll.user32;
        if not Utils.s_gdi32:
            Utils.s_gdi32 = Utils.s_windll.gdi32;
        if not Utils.s_screendc:
            getWinDC = Utils.s_user32.GetWindowDC;
            Utils.s_screendc = getWinDC(None);
        if not Utils.s_getPixel:
            Utils.s_getPixel = Utils.s_gdi32.GetPixel;
        abgr = Utils.s_getPixel(Utils.s_screendc, x, y);
        return (abgr & 0xFF, (abgr >> 8) & 0xFF, (abgr >> 16) & 0xFF, (abgr >> 24) & 0xFF);
    #
    @staticmethod
    def getMeanPixel(x, y, r):
        xc = x;
        yc = y;
        maxX = x + r;
        minX = x - r;
        maxY = y + r;
        minY = y - r;
        R2   = r * r;
        rgb  = [0, 0, 0];
        n    = 0;
        while x <= maxX:
            y = minY;
            while y <= maxY:
                r2 = pow(x - xc, 2) + pow(y - yc, 2);
                if r2 < R2:
                    n += 1;
                    r, g, b, a = Utils.getPixel2(x, y);
                    rgb[0] += r;
                    rgb[1] += g;
                    rgb[2] += b;
                    #rgb[3] += w * a;
                y += 1;
            x += 1;
        if not n:
            r, g, b, a = Utils.getPixel2(x, y);
            rgb[0] = r;
            rgb[1] = g;
            rgb[2] = b;
        else:
            rgb[0] /= n;
            rgb[1] /= n;
            rgb[2] /= n;
            #rgb[3] /= n;
        return rgb;
#
class CameraWorker(core.QObject):
    #
    def __init__(self):
        super(CameraWorker, self).__init__();
        self.mutex = core.QMutex();
        self.currentFrame = None;
        self.__reset();
    #
    def __reset(self):
        self.videoCap = None;
        self.isRunning= False;
        self.isStoped = False;
        return self;
    #
    def start(self):
        self.mutex.lock();
        if not self.isRunning:
            self.__reset();
            self.isRunning = True;
            self.mutex.unlock();
            self.videoCap = cv.VideoCapture(0);
            self.__run();
        else:
            self.mutex.unlock();
        return self;
    #
    def stop(self):
        self.mutex.lock();
        if self.isRunning:
            self.isRunning = False;
            self.isStoped  = True;
            self.mutex.unlock();
            self.videoCap.release();
        else:
            self.isStoped = True;
            self.mutex.unlock();
        return self;
    #
    def suspend(self):
        self.mutex.lock();
        self.isRunning = False;
        self.mutex.unlock();
        return self;
    #
    def resume(self):
        self.mutex.lock();
        if not self.isStoped:
            self.isRunning = True;
        self.mutex.unlock();
        return self;
    #
    def __run(self):
        while not self.isStoped:
            if not self.isRunning:
                continue;
            ret, self.currentFrame = self.videoCap.read();
            if ret:
                self.emit(core.SIGNAL('repaintCamera()'));
                self.suspend();
    #
    def getCurrentFrame(self):
        return self.currentFrame
#
class ImageLabel(gui.QLabel):
    def __init__(self, parent):
        super(ImageLabel, self).__init__(parent);
        self.parentWindow = parent;
        self.paintPreCallback = None;
        self.paintPostCallback= None;
    #
    def setPaintPreCallback(self, callback):
        if callable(callback):
            self.paintPreCallback = callback;
        return self;
    #
    def setPaintPostCallback(self, callback):
        if callable(callback):
            self.paintPostCallback = callback;
        return self;
    #
    def paintEvent(self, event):
        if callable(self.paintPreCallback):
            self.paintPreCallback(event);
        super(ImageLabel, self).paintEvent(event);
        if callable(self.paintPostCallback):
            self.paintPostCallback(event);
#
class ColorLabel(gui.QLabel):
    #
    def __init__(self, width, height, rgb, parent):
        super(ColorLabel, self).__init__(parent);
        self.parentWindow = parent;
        self.width  = width;
        self.height = height;
        self.rgb = gui.QColor(rgb);
        self.fillBackground();
    #
    def getColor(self):
        return self.rgb;
    #
    def setColor(self, rgb):
        self.rgb = gui.QColor(rgb);
        self.fillBackground();
    #
    def fillBackground(self):
        pixMap = gui.QPixmap(self.width, self.height);
        pixMap.fill(self.rgb);
        self.setPixmap(pixMap);
    #
    def mouseReleaseEvent(self, mouseEvent):
        self.rgb = gui.QColorDialog.getColor(self.rgb, self.parentWindow);
        self.fillBackground();
#
class OutputLabel(ColorLabel):
    #
    def mouseReleaseEvent(self, mouseEvent):
        pass
#
class Window(gui.QMainWindow):
    MODE_STD     = 0x1;
    MODE_WORKING = 0x2;
	#
    def __init__(self):
        super(Window, self).__init__(None);
        self.btnMinH = 40;
        self.toolBarMinH = 50;
        self.radiusMark  = 5;
        self.defaultColor= 0xFF0000;
        self.defaultResultColor = 0xCCCCCC;
        self.radiusInputWidth = 35;
        self.currentMode = Window.MODE_STD;
        #
        self.sameColorDelta = 8;
        #
        self.circleMarked = [];
        self.circleMarkedRecyle = [];
        self.cwd = os.getcwd();
        self.setWindowTitle(u'版权所有@Copyright - leejqy@163.com');
        self.createActions();
        self.createButtons();
        self.createInputs();
        self.initMenus();
        self.initToolBars();
        self.initImgWidget();
        self.run();
    #
    def initStdMode(self):
        pass
    #
    def initWorkingMode(self):
        pass
    #
    def getFullPath(self, relativePath):
        return self.cwd + os.path.sep + relativePath;
    #
    def cameraHandle(self):
        if self.currentMode == Window.MODE_STD:
            self.clearMarksHandle();
        self.btnCapture.setEnabled(True);
        self.cameraThread.start();
        return self;
    #
    def toggleModeHandle(self):
        if self.currentMode == Window.MODE_WORKING:
            self.currentMode = Window.MODE_STD;
            self.btnToggleMode.setEnabled(False);
            self.secondaryToolBar.setEnabled(True);
            self.btnClearMarks.setEnabled(True);
            self.actionUndo.setEnabled(True);
            self.actionRedo.setEnabled(True);
            self.actionZoomIn.setEnabled(True);
            self.actionZoomOut.setEnabled(True);
            self.clearMarksHandle();
            self.outputLabel.setColor(self.defaultResultColor);
    #
    def captureHandle(self):
        self.cameraWorker.stop();
        self.cameraThread.exit();
        imageLabel = self.getImageLabel();
        Utils.setScreenWidget(imageLabel);
        rect = imageLabel.geometry();
        rect.setY(0);
        Utils.setWidgetArea(rect);
        if self.currentMode == Window.MODE_WORKING:
            self.btnCapture.setEnabled(False);
            self.checkMarkedPoint();
            self.btnCapture.setEnabled(True);
            pass
        return self;
    #
    def checkMarkedPoint(self):
        ok = True;
        #print '===================================';
        if len(self.circleMarked) > 0:
            i = 1;
            for circle in self.circleMarked:
                stdRgb = circle['rgb'];
                rgb = Utils.getMeanPixel(circle['x'], circle['y'], circle['r']);
                #d   = Utils.colorDistance(rgb, stdRgb);
                deltaE = Utils.colorDeltaE(rgb, stdRgb);
                if deltaE > self.sameColorDelta:
                    circle['bad'] = True;
                    ok = False;
                #print i, '[', deltaE, ']:', circle['x'], circle['y'], circle['r'], circle['rgb'], 'vs:', rgb;
                i += 1;
            if ok:
                self.outputLabel.setColor(gui.QColor(0x00FF00));
            else:
                self.outputLabel.setColor(gui.QColor(0xFF0000));
            self.getImageLabel().update();
    #
    def clearMarksHandle(self):
        self.circleMarked = [];
        self.circleMarkedRecyle = [];
        self.actionRedo.setEnabled(False);
        self.actionUndo.setEnabled(False);
        self.actionDone.setEnabled(False);
        self.btnClearMarks.setEnabled(False);
        self.getImageLabel().update();
        return self;
    #
    def radiusMarkChanged(self):
        try:
            sender   = self.sender();
            inputTxt = sender.text();
            val = int(str(inputTxt));
            self.radiusMark = val;
        except:
            msgBox = gui.QMessageBox(self);
            msgBox.setWindowTitle(u'出错了');
            msgBox.setText(u'输入的半径包含非法字符!');
            msgBox.setButtonText(gui.QMessageBox.Ok, u'确认');
            msgBox.show();
    def mouseClickHandle(self, mouseEvent):
        if self.cameraWorker.isStoped and self.currentMode == Window.MODE_STD:
            #imageLabel = self.getImageLabel();
            #window     = self.geometry();
            #contentRect= imageLabel.geometry();
            #x = window.x() + contentRect.x();
            #y = window.y() + contentRect.y();
            wx = window.x();
            wy = window.y();
            gx= mouseEvent.globalX();
            gy= mouseEvent.globalY();
            x = mouseEvent.x();
            y = mouseEvent.y();
            r, g, b, a = Utils.getPixel(gx, gy);
            self.circleMarked.append({
                'wx': wx, 'wy': wy,
                'gx': gx, 'gy': gy,
                'x': x, 'y': y,
                'r': self.radiusMark,
                'c': self.colorLabel.getColor(),
                'red': r, 'green': g, 'blue': b, 'alpha': a
            });
            self.getImageLabel().update();
            self.btnClearMarks.setEnabled(True);
            self.actionUndo.setEnabled(True);
            self.actionDone.setEnabled(True);
    #
    def mouseMoveHandle(self, mouseEvent):
        if self.cameraWorker.isStoped:
            imageLabel = self.getImageLabel();
            window     = self.geometry();
            contentRect= imageLabel.geometry();
            x = window.x() + contentRect.x();
            y = window.y() + contentRect.y();
            pen = gui.QPen();
            pen.setWidth(1);
            pen.setStyle(core.Qt.DashDotLine);
            color = gui.QColor(self.colorLabel.getColor());
            color.setAlpha(0.5);
            painter = gui.QPainter(self.imageLabel);
            pen.setColor(color);
            painter.setPen(pen);
            painter.drawEllipse(x, y, self.radiusMark, self.radiusMark);
    #
    def paintEventPostCallback(self, event):
        length = len(self.circleMarked);
        pen = gui.QPen();
        pen.setStyle(core.Qt.SolidLine);
        color = gui.QColor(self.colorLabel.getColor());
        painter = gui.QPainter(self.imageLabel);
        for circle in self.circleMarked:
            pen.setColor(circle['c']);
            pen.setWidth(1);
            painter.setPen(pen);
            painter.drawEllipse(core.QPoint(circle['x'], circle['y']), circle['r'], circle['r']);
            if circle.has_key('bad') and circle['bad']:
                pointsA = Utils.getCrossPoints(circle['x'], circle['y'], circle['r'], 1, 1);
                pointsB = Utils.getCrossPoints(circle['x'], circle['y'], circle['r'], 1, -1);
                pen.setWidth(5);
                painter.setPen(pen);
                painter.drawLine(pointsA[0][0], pointsA[0][1], pointsA[1][0], pointsA[1][1]);
                painter.drawLine(pointsB[0][0], pointsB[0][1], pointsB[1][0], pointsB[1][1]);
                circle['bad'] = False;
    #
    def markHandle(self):
        pass
    #
    def undoHandle(self):
        if len(self.circleMarked) > 0:
            self.circleMarkedRecyle.append(self.circleMarked.pop());
            self.actionRedo.setEnabled(True);
            self.getImageLabel().update();
        if not len(self.circleMarked):
            self.actionUndo.setEnabled(False);
            self.actionDone.setEnabled(False);
    #    
    def redoHandle(self):
        if len(self.circleMarkedRecyle) > 0:
            self.circleMarked.append(self.circleMarkedRecyle.pop());
            self.actionUndo.setEnabled(True);
            self.actionDone.setEnabled(True);
            self.getImageLabel().update();
        if not len(self.circleMarkedRecyle):
            self.actionRedo.setEnabled(False);
        self.btnClearMarks.setEnabled(True);
    #
    def doneHandle(self):
        if len(self.circleMarked) > 0:
            self.actionDone.setEnabled(False);
            self.currentMode = Window.MODE_WORKING;
            for circle in self.circleMarked:
                rgb = Utils.getMeanPixel(circle['x'], circle['y'], circle['r']);
                circle['rgb'] = rgb;
            self.secondaryToolBar.setEnabled(False);
            self.btnClearMarks.setEnabled(False);
            self.actionUndo.setEnabled(False);
            self.actionRedo.setEnabled(False);
            self.actionZoomIn.setEnabled(False);
            self.actionZoomOut.setEnabled(False);
            self.btnToggleMode.setEnabled(True);
    #
    def zoomInHandle(self):
        pass
    #
    def zoomOutHandle(self):
        pass
    #
    def aboutAuthorHandle(self):
        title = u' ';
        body  = u'''
作者：李<br>
邮箱：<strong style="color:red;">leejqy@163.com</strong><br>
''';
        gui.QMessageBox.about(self, title, body);
    #
    def aboutHelpHandle(self):
        title = u'软件使用方法';
        body  = u'''
软件使用方法:<br><br>
I.&nbsp;&nbsp;&nbsp;打开软件，此时为标记模式；<br>
II.&nbsp;&nbsp;打开摄像头，若图像符合期望，则点击“截图”按钮；<br>
III.&nbsp;截图后可以对需要检测的点进行标记，每次的标记半径和标记颜色可以单独设置；<br>
IV.&nbsp;标记完成后，点击工具栏中的“保存”图标，此时软件进入比对模式；<br>
V.&nbsp;&nbsp;比对模式下，单击“截图”按钮，软件将自动与标记模式进行比对，<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;i.  如果标记的位置存在差别，则提示红色的NG;<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;ii. 否则提示绿色的OK。<br>
VI.&nbsp;点击“继续”按钮进入下一个产品检测循环。
''';
        gui.QMessageBox.about(self, title, body);
    #
    def createActions(self):
        self.actionCapture = gui.QAction(
            gui.QIcon(self.getFullPath('images/capture.png')),
            'CA&PTURE', self, shortcut = 'Ctrl+P',
            triggered = self.captureHandle
        );
        #
        self.actionMark = gui.QAction(
            gui.QIcon(self.getFullPath('images/mark.png')),
            '&MARK', self, shortcut = 'Ctrl+M',
            triggered = self.markHandle
        );
        #
        self.actionUndo = gui.QAction(
            gui.QIcon(self.getFullPath('images/undo.png')),
            u'撤销', self, shortcut = 'Ctrl+U',
            triggered = self.undoHandle, enabled = False
        );
        #
        self.actionRedo = gui.QAction(
            gui.QIcon(self.getFullPath('images/redo.png')),
            u'重做', self, shortcut = 'Ctrl+R',
            triggered = self.redoHandle, enabled = False
        );
        #
        self.actionDone = gui.QAction(
            gui.QIcon(self.getFullPath('images/done.png')),
            u'标记完成，开始工作模式', self, shortcut = 'Ctrl+D',
            triggered = self.doneHandle, enabled = False
        );
        #
        self.actionZoomIn = gui.QAction(
            gui.QIcon(self.getFullPath('images/zoomin.png')),
            u'放大', self, shortcut = 'Ctrl+I',
            triggered = self.zoomInHandle
        );
        #
        self.actionZoomOut = gui.QAction(
            gui.QIcon(self.getFullPath('images/zoomout.png')),
            u'缩小', self, shortcut = 'Ctrl+O',
            triggered = self.zoomOutHandle
        );
        #
        self.actionAboutAuthor = gui.QAction(
            gui.QIcon(self.getFullPath('images/author.png')),
            u'关于作者', self, shortcut = 'Ctrl+U',
            triggered = self.aboutAuthorHandle
        );
        #
        self.actionAboutHelp = gui.QAction(
            gui.QIcon(self.getFullPath('images/help.png')),
            u'帮助', self, shortcut = 'Ctrl+H',
            triggered = self.aboutHelpHandle
        );
        return self;
    #
    def getImageLabel(self):
        return self.imageLabel;
    #
    def createButtons(self):
        btnStyle = gui.QStyleOptionButton();
        btnStyle.features |= gui.QStyleOptionButton.DefaultButton;
        #
        self.btnCamera = gui.QPushButton(self);
        self.btnCamera.initStyleOption(btnStyle);
        self.btnCamera.setMinimumHeight(self.btnMinH);
        self.btnCamera.setText(u'打开摄像头');
        self.btnCamera.clicked.connect(self.cameraHandle);
        #
        self.btnCapture = gui.QPushButton(self);
        self.btnCapture.initStyleOption(btnStyle);
        self.btnCapture.setMinimumHeight(self.btnMinH);
        self.btnCapture.setText(u'截图');
        self.btnCapture.clicked.connect(self.captureHandle);
        self.btnCapture.setEnabled(False);
        #
        self.cameraWorker = CameraWorker();
        self.cameraThread = core.QThread(self);
        self.cameraWorker.moveToThread(self.cameraThread);
        self.cameraThread.started.connect(self.cameraWorker.start);
        self.cameraWorker.connect(self.cameraWorker, core.SIGNAL('repaintCamera()'), self.repaintCameraArea);
        #
        self.btnClearMarks = gui.QPushButton(self);
        self.btnClearMarks.initStyleOption(btnStyle);
        self.btnClearMarks.setMinimumHeight(self.btnMinH);
        self.btnClearMarks.setText(u'清除所有标记');
        self.btnClearMarks.clicked.connect(self.clearMarksHandle);
        self.btnClearMarks.setEnabled(False);
        #
        self.btnToggleMode = gui.QPushButton(self);
        self.btnToggleMode.initStyleOption(btnStyle);
        self.btnToggleMode.setMinimumHeight(self.btnMinH);
        self.btnToggleMode.setText(u'切换到标记模式');
        self.btnToggleMode.clicked.connect(self.toggleModeHandle);
        self.btnToggleMode.setEnabled(False);
        return self;
    #
    def createInputs(self):
        self.radiusInput = gui.QLineEdit(self);
        self.radiusInput.setFixedWidth(self.radiusInputWidth);
        self.radiusInput.setText(str(self.radiusMark));
        self.radiusInput.editingFinished.connect(self.radiusMarkChanged);
        return self;
    #
    def repaintCameraArea(self):
        frame = self.cameraWorker.getCurrentFrame();
        if frame is not None:
            qImageLabel = self.getImageLabel();
            frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB);
            height, width, bytes = frame.shape;
            qImage = gui.QImage(frame.data, width, height, gui.QImage.Format_RGB888);
            qImageLabel.setPixmap(gui.QPixmap.fromImage(qImage.mirrored(True, False)));
            #qImageLabel.repaint();
            qImageLabel.update();
            self.cameraWorker.resume();
        return self;
    #
    def initMenus(self):
        menuBar = self.menuBar();
        self.aboutMenu = gui.QMenu(u'关于');
        self.aboutMenu.addAction(self.actionAboutAuthor);
        self.aboutMenu.addAction(self.actionAboutHelp);
        menuBar.addMenu(self.aboutMenu);
        return self;
    #
    def initToolBars(self):
        self.masterToolBar = gui.QToolBar(self);
        self.masterToolBar.setMinimumHeight(self.toolBarMinH);
        self.addToolBar(self.masterToolBar);
        self.masterToolBar.addWidget(self.btnCamera);
        self.masterToolBar.addWidget(self.btnCapture);
        self.masterToolBar.addSeparator();
        self.masterToolBar.addWidget(self.btnClearMarks);
        self.masterToolBar.addAction(self.actionUndo);
        self.masterToolBar.addAction(self.actionRedo);
        self.masterToolBar.addAction(self.actionDone);
        self.masterToolBar.addAction(self.actionZoomIn);
        self.masterToolBar.addAction(self.actionZoomOut);
        self.masterToolBar.addWidget(self.btnToggleMode);
        #
        self.secondaryToolBar = gui.QToolBar(self);
        label = gui.QLabel(u'标记半径: ');
        self.secondaryToolBar.addWidget(label);
        self.secondaryToolBar.addWidget(self.radiusInput);
        label = gui.QLabel(u' 标记颜色: ');
        self.secondaryToolBar.addWidget(label);
        self.colorLabel = ColorLabel(50, 20, self.defaultColor, self);
        self.secondaryToolBar.addWidget(self.colorLabel);
        label = gui.QLabel(u'  ');
        self.secondaryToolBar.addWidget(label);
        self.addToolBar(self.secondaryToolBar);
        #
        self.outputToolBar = gui.QToolBar(self);
        self.outputLabel   = OutputLabel(40, 40, self.defaultResultColor, self);
        self.outputToolBar.addWidget(self.outputLabel);
        self.addToolBar(self.outputToolBar);
        return self;
    #
    def initImgWidget(self):
        self.imageLabel = ImageLabel(self);
        self.imageLabel.setPaintPostCallback(self.paintEventPostCallback);
        self.setCentralWidget(self.imageLabel);
        self.imageLabel.setEnabled(True);
        self.imageLabel.setFrameStyle(gui.QFrame.Box);
        self.imageLabel.setGeometry(0, 0, 800, 800);
        self.imageLabel.setVisible(True);
        self.imageLabel.setScaledContents(True);
        self.imageLabel.setAlignment(core.Qt.AlignCenter);
        self.imageLabel.mouseReleaseEvent = self.mouseClickHandle;
        self.imageLabel.mouseMoveEvent = self.mouseMoveHandle;
        self.imageLabel.show();
        return self;
    #
    def run(self):
        self.setGeometry(100, 100, 1000, 1000);
        self.update();
        self.show();
        return self;
    #
    def closeEvent(self, closeEvent):
        self.cameraWorker.stop();
        self.cameraThread.exit();
        super(Window, self).close();
#
if __name__ == '__main__':
    if Utils.isRegistered():
        app = gui.QApplication(sys.argv);
        window = Window();
        window.run();
        sys.exit(app.exec_());
