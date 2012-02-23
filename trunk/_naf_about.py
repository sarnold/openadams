from PyQt4 import QtGui

class cAbout(QtGui.QDialog):
    def __init__(self, parent, text):
        super(cAbout, self).__init__(parent)
        self.setSizeGripEnabled(False)
        self.setWindowTitle(self.tr("About"))
        self.aboutText = QtGui.QLabel(self, openExternalLinks=True)
        self.aboutText.setText(text)
        self.aboutText.setFrameStyle(QtGui.QFrame.Panel | QtGui.QFrame.Sunken)
        self.buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Close)
        self.buttonBox.rejected.connect(self.reject)
        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.aboutText)
        layout.addWidget(self.buttonBox)
        self.setLayout(layout)