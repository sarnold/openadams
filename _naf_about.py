from PyQt4 import QtGui

class cAbout(QtGui.QDialog):
    def __init__(self, parent, text):
        super(cAbout, self).__init__(parent)
        self.setSizeGripEnabled(False)
        self.setWindowTitle(self.tr("About"))
        self.aboutText = QtGui.QLabel(self, openExternalLinks=True)
        self.aboutText.setText(text)
        self.aboutText.setFrameStyle(QtGui.QFrame.Panel | QtGui.QFrame.Sunken)
        self.aboutText.setStyleSheet('border-style: inset; border-width:2px; border-color:#909090;' \
                                     'background: qradialgradient(cx:0, cy:0, radius: 1,fx:0.5, fy:0.5, stop:0 white, stop:1 #CCCCCC)')

        self.buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Close)
        self.buttonBox.rejected.connect(self.reject)
        hbox = QtGui.QHBoxLayout()
        lbl = QtGui.QLabel()
        lbl.setPixmap(QtGui.QPixmap(':/icons/appicon48x48.png'))
        lbl.setStyleSheet('border-style: solid; border-width:1px; border-radius: 6px; border-color:#909090; background-color:white;')
        hbox.addWidget(lbl)
        hbox.addWidget(self.aboutText)
        layout = QtGui.QVBoxLayout()
        layout.addLayout(hbox)
        layout.addWidget(self.buttonBox)
        self.setLayout(layout)