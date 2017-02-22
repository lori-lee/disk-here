#!/bin/env python
#-*- coding: utf-8 -*-

import Tkinter as GUI
import os as OS
import re as RE

class MenuList:
    menu = (
        {'name' : 'gui', 'label' : u'界面', 'status' : 1,
            'children' : (
                {'name' : 'test', 'label' : u'测试', 'status' : 1},
                {'name' : 'config', 'label' : u'配置', 'status' : 1,},
                {'name' : 'line_sep', 'label' : '', 'status' : 0,},
                {'name' : 'exit', 'label' : u'退出', 'status' : 1,},
            )
        },
        {'name' : 'help', 'label' : u'帮助', 'status' : 0,
            'children' : (
                {'name' : 'test', 'label' : u'测试', 'status' : 1},
                {'name' : 'config', 'label' : u'配置', 'status' : 1,},
                {'name' : 'line_sep', 'label' : '', 'status' : 0,},
                {'name' : 'exit', 'label' : u'退出', 'status' : 0,
                    'children' : (
                        {'name' : 'config', 'label' : u'配置', 'status' : 1,},
                        {'name' : 'line_sep', 'label' : '', 'status' : 0,},
                        {'name' : 'config', 'label' : u'配置', 'status' : 1,},
                    )
                },
            )
        },        
    )
#
class Command:
    def __init__(self, func, *argvs, **kwargvs):
        self.func = func
        self.argvs= argvs
        self.kwargvs = kwargvs
    #
    def __call__(self, *argvs, **kwargvs):
        argvs += self.argvs + argvs
        kw = dict(self.kwargvs)
        for k in kwargvs:
            kw[k] = kwargvs[k]
        if callable(self.func):
            return self.func(*argvs, **kw)
#
class AppMenu:
    def __init__(self, app):
        self.app = app
        self.rootMenu = GUI.Menu(app.getWindow())
        for menu in MenuList.menu:
            self.createMenu(self.rootMenu, menu, menu['status'])
        app.getWindow().config(menu = self.rootMenu)
    #
    def createMenu(self, parent, menu, status = 1):
        if menu.has_key('children'):
            m = GUI.Menu(parent, tearoff = 0)
            for child in menu['children']:
                self.createMenu(m, child, menu['status'])
            parent.add_cascade(
                label = menu['label'],
                menu = m
            )
        else:
            if 'line_sep' == menu['name']:
                parent.add_separator()
            else:
                parent.add_command(
                    label = menu['label'],
                    command = Command(self.app.getMenuClickHandle(), menu = dict(menu)),
                    state = GUI.NORMAL if menu['status'] and status else GUI.DISABLED
                )
        return self
    #
    def destroy(self):
        try:
            self.rootMenu.destroy()
        except Exception, e:
            pass
        return self
    #
class Application:
    def __init__(self):
        self.window = GUI.Tk()
        self.initVars()
        self.initGUI()
    #
    def initVars(self):
        configFile = self.getConfigFile()
        return self
    #
    def initGUI(self):
        self.screenSize = (600, 800)
        self.menu = AppMenu(self)
        #self.container = AppContainer(self)
        return self
    #
    def initMenu(self):
        if self.menu and self.menu.destroy:
            try:
                self.menu.destroy()
            except Exception, e:
                pass
        self.menu = AppMenu(self)
        return self
    #
    def menuClickHandle(self, *argvs, **kwargvs):
        print argvs, kwargvs
        return self
    #
    def getMenuClickHandle(self):
        return self.menuClickHandle
    #                    
    def run(self):
        self.window.mainloop()
        return self
    #
    def getWindow(self):
        return self.window
    #
    def getCWD(self):
        return OS.path.dirname(__file__)
    #
    def getDir(self, type, autoCreate = True):
        path = self.getCWD() + OS.path.sep + RE.sub(r'^\s*[\\/]+', '', type)
        if autoCreate and not OS.path.isdir(path):
            OS.mkdir(path)
        return path
    #
    def getConfigFile(self):
        return self.getDir('config') + OS.path.sep + 'app.ini'
    #
    def resize(self, width, height):
        self.window.geometry(str(width) + 'x' + str(height))
        return self

if __name__ == '__main__':
    app = Application()
    app.run()
