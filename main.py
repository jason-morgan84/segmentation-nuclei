from PyQt6.QtWidgets import QApplication
import sys

import ui
import image
import settings

def myexcepthook(type, value, tb):
    import traceback
    tbtext = ''.join(traceback.format_exception(type, value, tb))
    print(tbtext)
    settings.export_settings("autosave.txt",images.opened_image.filename)
    print("Settings Autosaved")
    app.quit()

sys.excepthook = myexcepthook


#example ImageName
file = "example.tif"


images = image.ImageProcessing()
images.open_image(file)
app = QApplication(sys.argv)

window = ui.MainWindow(images)
window.move(100,100)
window.height = 1200
window.show()

window.draw_image()
app.exec()

