import sys
from feuze.ui import main_window
from PySide2.QtWidgets import QApplication
from PySide2.QtGui import QPalette, QColor
from PySide2.QtCore import Qt

if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = main_window.MainWindow()
    window.show()

    app.setStyle("Fusion")

    # Now use a palette to switch to dark colors:
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.WindowText,QColor(180, 180, 180))
    palette.setColor(QPalette.Base, QColor(65, 65, 65))
    palette.setColor(QPalette.AlternateBase, QColor(60, 60, 60))
    palette.setColor(QPalette.ToolTipBase, Qt.black)
    palette.setColor(QPalette.ToolTipText,QColor(180, 180, 180))
    palette.setColor(QPalette.Text, QColor(180, 180, 180))
    palette.setColor(QPalette.Button, QColor(45, 45, 45))
    palette.setColor(QPalette.ButtonText, QColor(180, 180, 180))
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(180, 145, 50))
    palette.setColor(QPalette.HighlightedText, Qt.black)
    app.setPalette(palette)

    sys.exit(app.exec_())