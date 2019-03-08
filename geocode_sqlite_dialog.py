# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Geocode Sqlite
                                 A QGIS plugin
 This plugin helps geocoding an sqlite table using OSM Nominatim
                              -------------------
        begin                : 2018-11-12
        git sha              : $Format:%H$
        copyright            : (C) 2018 by Mátyás Gede
        email                : saman@map.elte.hu
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os
import requests
import qgis.utils

from PyQt5 import uic
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QAction, QMessageBox, QWidget
from PyQt5.QtCore import *
from PyQt5 import QtSql
from PyQt5.QtSql import *
from collections import deque
from datetime import *
from time import *

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'geocode_sqlite_dialog_base.ui'), resource_suffix='')


class GeocodeSqliteDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(GeocodeSqliteDialog, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        self.fwDBFile.setFilter("SQLite files (*.sqlite)")
        # event handlers
        self.pbOpenDb.clicked.connect(self.openDb) # Open DB button
        self.cbTable.currentIndexChanged.connect(self.getFieldList) # Get field list from table
        self.cbField.currentIndexChanged.connect(self.setGeomField) # Get field list from table
        self.pbStart.clicked.connect(self.startGcThread) # Start button
        self.pbClose.clicked.connect(self.close) # Close button
        self.pbHelp.clicked.connect(self.help) # Help button
        self.WT=None
    
    def close(self):
        """Close dialog"""
        if self.WT is not None:
            self.WT.stop()
        self.reject()
    
    def help(self):
        """Help 'dialog'"""
        QMessageBox.information(self,"Help",'Select the database file, the table and the field to geocode, '+
            'then press "Start".<br/>Depending on the number of records, processing may take several minutes.')
        
    def openDb(self):
        """Opens DB file and refreshs table list"""
        # connect to spatialite
        dbFile=self.fwDBFile.filePath()
        con=qgis.utils.spatialite_connect(dbFile)
        cur=con.cursor()
        r=cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        self.cbTable.clear()
        for l in r:
            self.cbTable.addItem(l[0])
        
    def getFieldList(self):
        """Lists fields of the chosen table"""
        self.cbField.clear()
        # connect to spatialite
        dbFile=self.fwDBFile.filePath()
        con=qgis.utils.spatialite_connect(dbFile)
        cur=con.cursor()
        r=cur.execute("SELECT * FROM "+self.cbTable.currentText()+" LIMIT 1")
        for f in cur.description:
            self.cbField.addItem(f[0])
    
    def setGeomField(self):
        """Set geometry field name based on name field"""
        self.leGeomField.setText(self.cbField.currentText()+"_geom");
    
    def startGcThread(self):
        """Starts geocoding thread"""
        
        # return to lat/lon boxes if number is not valid
        def numberError(le):
            QMessageBox.warning(self,"Error","Enter a valid number here")
            le.setFocus()
            le.selectAll()
            
        if self.pbStart.text()=="Start":
            dbFile=self.fwDBFile.filePath()
            tblName=self.cbTable.currentText()
            fldName=self.cbField.currentText()
            geomFld=self.leGeomField.text()
            noGeom=self.cbNoGeom.isChecked()
            # change button text to stop
            self.pbStart.setText("Stop");
            # clear log box
            self.teLog.clear()
            # create and start thread
            self.WT=WorkerThread(qgis.utils.iface.mainWindow(),dbFile,tblName,fldName,geomFld,noGeom)
            self.WT.jobFinished.connect(self.jobFinishedFromThread)
            self.WT.addMsg.connect(self.msgFromThread)
            self.WT.setTotal.connect(self.setTotal)
            self.WT.setProgress.connect(self.setProgress)
            self.WT.start()
        else:
            # change button text to start
            self.pbStart.setText("Start")
            # stop working thread
            self.WT.stop()
            self.teLog.append("Process stopped")
            
    def jobFinishedFromThread( self, success ):
        if success:
            self.progressBar.setValue(self.progressBar.maximum())
        # change button text to start
        self.pbStart.setText("Start")
        # stop working thread
        self.WT.stop()

    def msgFromThread( self, msg ):
        self.teLog.append(msg)        
    
    def setTotal( self, total ):
        self.progressBar.setMaximum(total)
        
    def setProgress( self, p ):
        self.progressBar.setValue(p)

class WorkerThread( QThread ):
    # signals
    addMsg=pyqtSignal(str)
    jobFinished=pyqtSignal(bool)
    setTotal=pyqtSignal(int)
    setProgress=pyqtSignal(int)
       
    def __init__( self, parentThread,dbFile,tblName,fldName,geomFld,noGeom):
        QThread.__init__( self, parentThread )
        self.dbFile=dbFile
        self.tblName=tblName
        self.fldName=fldName
        self.geomFld=geomFld
        self.noGeom=noGeom
    def run( self ):
        self.running = True
        success = self.doWork()
        self.jobFinished.emit(success)
    def stop( self ):
        self.running = False
        pass
    def doWork( self ):
        """Starts geocoding process"""
        dbFile=self.dbFile
        tblName=self.tblName
        fldName=self.fldName
        geomFld=self.geomFld
        
        # connect to spatialite
        con=qgis.utils.spatialite_connect(dbFile)
        cur=con.cursor()
        
        # create geometry field if not exists
        r=cur.execute("SELECT * FROM "+tblName+" LIMIT 1")
        haveIt=False
        for f in cur.description:
            if (f[0]==geomFld):
                haveIt=True
                break
        if (not haveIt):
            cur.execute("select AddGeometryColumn('"+tblName+"', '"+geomFld+"', 4326, 'POINT', 'XY');")
            cur.execute("select CreateSpatialIndex('"+tblName+"', '"+geomFld+"');")
            self.addMsg.emit("Geometry field '"+geomFld+"' added.");
        # query to get distinct names
        sql="select distinct "+fldName+" from "+tblName
        if (self.noGeom):
            sql=sql+" where "+geomFld+" is null"
        # sql=sql+" limit 10" # limit only during dev!!!
        names=[]
        for l in cur.execute(sql):
            names.append(l[0])
        self.addMsg.emit(str(len(names))+" names to geocode...")
        # iterate over names
        self.setTotal.emit(len(names))
        places={}
        for i in range(len(names)):
            # emergency exit
            if (not self.running):
                self.jobFinished.emit(False)
                return False
            # send geocoding request
            url="https://nominatim.openstreetmap.org/search?format=json&q="+names[i]
            # self.addMsg.emit(url);
            self.addMsg.emit("Sending request for "+names[i]+"...")
            req=requests.get(url)
            data=req.json()
            places[names[i]]=data;
            if req.status_code!=200:
                self.addMsg.emit('http status: '+str(r.status_code)+' '+r.reason)
            elif (len(data)>0):
                lon=str(data[0]['lon'])
                lat=str(data[0]['lat'])
                # update db with geometry
                sql="update "+tblName+" set "+geomFld+"=PointFromText('point("+lon+" "+lat+")',4326) where "+fldName+"='"+(names[i].replace("'","''"))+"'"
                # self.addMsg.emit(sql);
                cur.execute(sql)
                con.commit();
            else:
                self.addMsg.emit("No result!");
            self.setProgress.emit(i)
            sleep(1) # this is to not exceed nominatim usage limits
        con.commit();
        self.addMsg.emit("I think it's ready...")  
        self.jobFinished.emit(True)
        return True         
        
    def cleanUp(self):
        pass