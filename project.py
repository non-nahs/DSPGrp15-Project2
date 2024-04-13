from PySide6.QtWidgets import QApplication
import sys
from interface import MainWindow  # Make sure the class name and file are correctly referenced

def main():
    """ Main function to execute the application. """
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()