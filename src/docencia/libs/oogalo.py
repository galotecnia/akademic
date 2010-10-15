#!/usr/bin/python
# -*- encoding: utf-8 -*-
"""
    Akademic: Herramienta para el control del alumnado en centros escolares.

    Copyright (C) 2010  Galotecnia Redes Sistemas y Servicios S.L.L. <info@galotecnia.com>

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as
    published by the Free Software Foundation, either version 3 of the
    License, or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

# Fuentes de ayuda:
#
# http://codesnippets.services.openoffice.org/index.xml
# http://wiki.services.openoffice.org/wiki/PrinttoWriter.py
# http://api.openoffice.org/

dummy = True
dummy = False
if dummy:
    # FIXME:
    # Cuando en django se hace un manage.py syncdb (por ejemplo)
    # esto explota por cargar modulos de pyuno.... :-(
    # Ponner dummy = True es una forma facil de saltarse el problema
    class Writer:
        def __init__(self):
            pass
        def _url(self, url):
            return ""
        def loadFile(self, inputfn):
            pass
        def appendFile(self, inputfn):
            pass
        def properties(self, proyecto, cliente):
            pass
        def _append(self, style, text):
            pass
        def changeParam(self, key, value):
            pass
        def appendH1(self, text):
            pass
        def appendH2(self, text):
            pass
        def appendH3(self, text):
            pass
        def appendP(self, text):
            pass
        def rebuildIndexes(self):
            pass
        def saveFile(self, outputfn, filtername):
            pass
        def saveODT(self, outputfn):
            return ""
        def savePDF(self, outputfn):
            return ""
        def close(self):
            pass
        def end(self):
            pass
        def searchAndReplacePageBreak(self, str_from):
            pass
        def searchAndReplaceUserField(self, str_from, field_to):
            pass
        def searchAndReplace(self, str_from, str_to):
            pass
else:       

    import sys, os, time
    import uno, unohelper
    from com.sun.star.beans import PropertyValue
    from com.sun.star.style.BreakType import PAGE_BEFORE, PAGE_AFTER
    from com.sun.star.uno import Exception as UnoException, RuntimeException
    from com.sun.star.connection import NoConnectException
    from com.sun.star.lang import IllegalArgumentException
    from com.sun.star.io import IOException
    from com.sun.star.text.ControlCharacter import PARAGRAPH_BREAK
    import xml.dom.minidom

    class Writer:
        def __init__(self, host="localhost", port=2002):
            ### Do the OpenOffice component dance
            context = uno.getComponentContext()
            resolver = context.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", context)

            ### Test for an existing connection
            connection = "socket,host=%s,port=%s;urp;StarOffice.ComponentContext" % (host, port)
            try:
                self.unocontext = resolver.resolve("uno:%s" % connection)
            except NoConnectException, e:
                sys.stderr.write("OpenOffice process not found or not listening (" + e.Message + ")\n")
                raise UnoException("OpenOffice processs not found", None)
            except IllegalArgumentException, e:
                sys.stderr.write("The url is invalid ( " + e.Message + ")\n")
                raise UnoException("OpenOffice url is invalid", None)
            except RuntimeException, e:
                sys.stderr.write("An unknown error occured: " + e.Message + "\n")
                raise UnoException("OpenOffice unknown error", None)

            ### And some more OpenOffice magic
            self.unosvcmgr = self.unocontext.ServiceManager
            self.desktop = self.unosvcmgr.createInstanceWithContext("com.sun.star.frame.Desktop", self.unocontext)
            self.dispatcher = self.unosvcmgr.createInstanceWithContext("com.sun.star.frame.DispatchHelper", self.unocontext)
            self.cwd = unohelper.systemPathToFileUrl( os.getcwd() )
#            self.doc = self.desktop.getCurrentComponent()
#            self.cursor = self.doc.Text.createTextCursor()
            self.cursor = None
            self.clipboard = None

        def _url(self, url):
            return unohelper.absolutize(self.cwd, unohelper.systemPathToFileUrl(url))

        def copyAll(self):
            self.cursor.gotoStart( False ) # Go to start of frame (not holding down shift key)
            self.cursor.gotoEnd( True ) # Go to end of frame (while holding down the shift key to select all) 
            #self.executeSlot (".uno:SelectAll")
            #self.executeSlot (".uno.Copy")
            self.doc.CurrentController.select(self.cursor)
            self.clipboard = self.doc.CurrentController.getTransferable()

        def pasteEnd(self):
            self.cursor.gotoEnd( False )
            self.executeSlot (".uno.Paste")
            self.doc.CurrentController.insertTransferable(self.clipboard)

        def _loadUrl(self, inputurl):
            inputprops = ( PropertyValue( "Hidden" , 0 , True, 0 ), )
            self.doc = self.desktop.loadComponentFromURL( inputurl , "_blank", 0, inputprops )
            if not self.doc:
                raise UnoException("File could not be loaded by OpenOffice", None)
            self.text = self.doc.Text
            self.cursor = self.text.createTextCursor()
            self.cursor.gotoEnd(False)

        def blank(self):
            self._loadUrl("private:factory/swriter")
            
        def loadFile(self, inputfn):
            self._loadUrl(self._url(inputfn))

        def appendFile(self, inputfn, pagebreak = False):
            try:
                inputurl = self._url(inputfn)
                self.cursor.gotoEnd(False)
                if pagebreak:
                    self.cursor.BreakType = PAGE_AFTER
                self.cursor.insertDocumentFromURL(inputurl, ())
                self.cursor.gotoEnd(False)
            except IOException, e:
                sys.stderr.write("Error during opening ( " + e.Message + ")\n")
            except IllegalArgumentException, e:
                sys.stderr.write("The url is invalid ( " + e.Message + ")\n")
            except UnoException, e:
                sys.stderr.write( "Error ("+repr(e.__class__)+") during conversion:" + e.Message + "\n" )

        def properties(self, proyecto, cliente):
            info = self.doc.getDocumentInfo()
            #print info.getUserFieldName(0), info.getUserFieldValue(0) # proyecto
            #print info.getUserFieldName(1), info.getUserFieldValue(1) # cliente
            #print info.getUserFieldName(2), info.getUserFieldValue(2) # proveedor
            #print info.getUserFieldName(3), info.getUserFieldValue(3) # info 4
            info.setUserFieldValue(0, proyecto)
            info.setUserFieldValue(1, cliente)

        def _append(self, style, text):
            self.cursor.gotoEnd(False)
            self.text.insertControlCharacter(self.cursor, PARAGRAPH_BREAK, False)
            self.cursor.ParaStyleName = style
            self.text.insertString(self.cursor, text, False)

        def changeParam(self, key, value):
            field = self.doc.getTextFieldMasters().getByName("com.sun.star.text.FieldMaster.User." + key)
            if type(value) is unicode:
                field.Content = value.encode("latin-1")
            else:
                field.Content = value

        def appendH1(self, text):
            self._append("Heading 1", text)

        def appendH2(self, text):
            self._append("Heading 2", text)

        def appendH3(self, text):
            self._append("Heading 3", text)

        def appendP(self, text):
            self._append("Standard", text)

        def appendPageBreak(self):
            self.cursor.gotoEnd(False)
            self.cursor.gotoPreviousParagraph(False)
            self.cursor.BreakType = PAGE_AFTER

        def rebuildIndexes(self):
            x = self.doc.getDocumentIndexes()
            for xi in range(x.getCount()):
                print "Actualizando TOC #", xi
                x.getByIndex(xi).update()

        def saveFile(self, outputfn, filtername):
            outputprops = (
                    PropertyValue( "FilterName" , 0, filtername, 0 ),
                    PropertyValue( "Overwrite" , 0, True , 0 ),
                   )
            outputurl = self._url(outputfn)
            self.rebuildIndexes()
            self.doc.storeToURL(outputurl, outputprops)

        def saveODT(self, outputfn):
            return self.saveFile(outputfn, "writer8")

        def savePDF(self, outputfn):
            return self.saveFile(outputfn, "writer_pdf_Export")

        def close(self):
            if self.doc is not None:
                self.doc.dispose()
                self.doc = None

        def end(self):
            self.close()
        
        def searchAndReplacePageBreak(self, str_from):
            # FIXME: El PAGEBREAK genera un retorno de salto adicional
            # (un nuevo parrafo supongo)
            s = self.doc.createSearchDescriptor()
            s.setSearchString(str_from)
            cursor1 = self.doc.findFirst(s)
            while cursor1:
                cursor1.collapseToStart() # ?????
                cursor1.goRight(len(str_from), True) 
                if str_from == cursor1.getString():
                    #self.text.insertString(cursor1, "", True) 
                    self.text.insertControlCharacter(cursor1, PARAGRAPH_BREAK, True)
                    # MOVE TO JUST BEFORE THE NEW PARAGRAPH BREAK
                    cursor1.collapseToEnd() # ?????
                    cursor1.gotoPreviousParagraph(False)
                    # SET THE BREAK TYPE OF THE oCursor1 PARAGRAPH TO BE A PAGE BREAK
                    cursor1.BreakType = PAGE_AFTER 
                cursor1 = self.doc.findNext(cursor1.getEnd(), s)

        def searchAndReplaceUserField(self, str_from, field_to):
            field = self.doc.getTextFieldMasters().getByName("com.sun.star.text.FieldMaster.User." + field_to)
            s = self.doc.createSearchDescriptor()
            s.setSearchString(str_from)
            cursor1 = self.doc.findFirst(s)
            while cursor1:
                cursor1.collapseToStart() # ?????
                cursor1.goRight(len(str_from), True) 
                if str_from == cursor1.getString():
                    x = self.doc.createInstance("com.sun.star.text.TextField.User")
                    x.attachTextFieldMaster(field)
                    self.text.insertTextContent(cursor1, x, True) 
                cursor1 = self.doc.findNext(cursor1.getEnd(), s)

        def searchAndReplacePage(self, page, str_from, str_to):
            return self.searchAndReplace(str_from, str_to)
        #def searchAndReplacePage(self, page, str_from, str_to):
        #    s = self.doc.createSearchDescriptor()
        #    s.setSearchString(str_from)
        #    oVC  = self.doc.CurrentController.ViewCursor
        #    cursor1 = self.doc.findFirst(s)
        #    while cursor1:
        #        oVC.gotoRange(cursor1, False)
        #        if oVC.Page == page: cursor1.String = str_to
        #        cursor1 = self.doc.findNext(cursor1.getEnd(), s)

        def searchAndReplace(self, str_from, str_to):
            s = self.doc.createReplaceDescriptor()
            s.setSearchString(str_from)
            s.setReplaceString(str_to)
            self.doc.replaceAll(s)

        def searchAndReplaceDict(self, d):
            for key, val in d.items():
                self.searchAndReplace(key, val)

        # A wrapper function to wrap around OpenOffice's
        # Dispatch API.
        # islot is a Slot ID ( aka Command Name )
        # For all Slot IDs see
        # http://framework.openoffice.org/servlets/ProjectDocumentList?folderID=72&expandFolder=72&folderID=71
        def executeSlot(self, islot ):
            dispatchHelper = self.unosvcmgr.createInstanceWithContext(
                        "com.sun.star.frame.DispatchHelper", self.unocontext)
            frame = self.doc.getCurrentController().getFrame()
            dispatchHelper.executeDispatch( frame, islot, "", 0, () )

        # http://wiki.services.openoffice.org/wiki/Documentation/DevGuide/Text/Named_Table_Cells_in_Rows,_Columns_and_the_Table_Cursor
        def getTables(self):
            l = self.doc.getTextTables()
            return [l.getByIndex(i).getName() for i in range(l.getCount())]

        def tableAddRows(self, table_name, num_rows):
            l = self.doc.getTextTables() # lista de tablas
            t = l.getByName(table_name) # tabla factura
            r = t.getRows() # objeto "filas"
            r.insertByIndex(r.getCount(), num_rows) # mete 'num_rows' filas nuevas por el final

        def tableWriteContent(self, table_name, x, y, content):
            "Para no liarnos, la celda (x,y)=(1,1) es la primera izqda, la (2,1) es la de abajo"
            l = self.doc.getTextTables() # lista de tablas
            t = l.getByName(table_name) # tabla factura
            cell = t.getCellByPosition(y-1, x-1) # celda
            cell.setString(content) # sobreescribir la celda

        def tableGetRowCount(self, table_name):
            l = self.doc.getTextTables() # lista de tablas
            t = l.getByName(table_name) # tabla factura
            r = t.getRows() # objeto "filas"
            return r.Count

        def tableWriteRow(self, table_name, x, *args):
            "Para no liarnos, la fila x=1 es la primera, x=2 la segunda"
            l = self.doc.getTextTables() # lista de tablas
            t = l.getByName(table_name) # tabla factura
            for y in range(len(args)):
                cell = t.getCellByPosition(y, x-1) # celda
                cell.setString(args[y]) # sobreescribir la celda

        def tableAddRow(self, table_name, *args):
            self.tableAddRows(table_name, 1)
            c = self.tableGetRowCount(table_name)
            self.tableWriteRow(table_name, c, *args)
        
        def tableWriteInRow(self, table_name, x, *args):
            l = self.doc.getTextTables()
            t = l.getByName(table_name)
            for y in range(len(args)):
                cell = t.getCellByPosition(y, x-1)
                cell.setString(args[y])
        
        def tableDeleteRow(self, table_name, x):
            l = self.doc.getTextTables()
            t = l.getByName(table_name)
            r = t.getRows()
            r.removeByIndex(x-1,1)

    def prueba_plantilla_incidencias():
        writer = Writer('ltsp', 2002)
        writer.blank()
        writer.appendFile("../../media/plantillas-odt/incidencias.odt")
        writer.copyAll()
        for i in range(1,10+1):
            writer.pasteEnd()
            writer.searchAndReplacePage(None, "$$nombre$$", "Alberto Morales")
            writer.searchAndReplacePage(None, "$$curso$$", "%d de ESO" % i)
            if i > 1: writer.appendPageBreak()
        # Escribir en la celda 1,1 de todas las tablas
        for tablename in writer.getTables():
            writer.tableWriteContent(tablename, 1, 1, "tabla %s" % t)
        writer.savePDF("out.pdf")
        writer.end()

    def prueba_antigua():
        writer = Writer()
        #writer.loadFile("plantilla-fax.ott")
        writer.blank()
        writer.appendFile("plantilla-fax.ott")
        writer.properties("Sistema de gestion para estudio de arquitectos", "Moron arquitectos S.L")
        #writer.changeParam("FechaUltimaRevision", "hoy")
        #writer.appendFile("sample.html")
        #writer.appendH1("Anexos")
        #writer.appendH2("Anexo 1: Transacciones económicas")
        #writer.appendP("En este anexo vamso a tratar de lorem ipsum dolor sit ametlorem ipsum dolor sit ametlorem ipsum dolor sit ametlorem ipsum dolor sit amet lorem ipsum dolor sit amet ipsum")
        #writer.appendP("Y esto es otro pararafo. En este anexo vamso a tratar de lorem ipsum dolor sit anexo vamso a tratar de lorem ipsum dolor sit anexo vamso a tratar de lorem ipsum dolor sit anexo vamso a tratar de lorem ipsum dolor sit anexo vamso a tratar de lorem ipsum dolor sit anexo vamso a tratar de lorem ipsum dolor sit aaaaaaanexo vamso a tratar de lorem ipsum dolor sit amet ipsum")
        #writer.appendP("Aqui va un campo user tal que asi 'USER' y eso")
        #writer.appendH2("Anexo 2: Transacciones económicas")
        #writer.appendP("En super este anexo vamso a tratar de lorem ipsum dolor sit ametlorem ipsum dolor sit ametlorem ipsum dolor sit ametlorem ipsum dolor sit amet lorem ipsum dolor sit amet ipsum")
        #writer.appendP("Y supersuper  esto es otro pararafo. En este anexo vamso a tratar de lorem ipsum dolor sit anexo vamso a tratar de lorem ipsum dolor sit aqui va un pagebr...PAGEBREAK ...salio?vamso a tratar de lorem ipsum dolor sit anexo vamso a tratar de lorem ipsum dolor sit anexo vamso a tratar de lorem ipsum dolor sit anexo vamso a tratar de lorem ipsum dolor sit aaaaaaanexo vamso a tratar de lorem ipsum dolor sit amet ipsum")
        #writer.searchAndReplace("esto", "((esto otro))")
        #writer.searchAndReplacePageBreak("PAGEBREAK")
        #writer.searchAndReplaceUserField("USER", "ClienteNombre")

        writer.loadFile("plantilla-fax.ott")
        writer.copyAll()
        for i in range (0, 2):
            generaboletin
            writer.appendPageBreak()
            writer.pasteEnd()
        writer.searchAndReplacePage(2, "a", "A")
        writer.savePDF("out.pdf")
        print "- Tienes la salida en out.pdf"
        #writer.saveODT("out.odt")
        #print "- Tienes la salida en out.odt"
        writer.end()

    if __name__ == '__main__':
        #prueba_antigua()
        prueba_plantilla_incidencias()
