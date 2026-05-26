from PyQt6 import QtWidgets, QtCore, QtGui
from PyQt6.QtCore import Qt
from PyQt6.QtGui import * 
from PyQt6.QtCore import *
from PyQt6.QtWidgets import QSlider, QGroupBox,QTabWidget,QWidget,QMainWindow
import skimage as ski
import numpy as np
import sys
from matplotlib.backends.backend_qt5agg import FigureCanvas
from matplotlib.figure import Figure
from matplotlib import pyplot as plt

import settings
import LUTs

class MainWindow(QMainWindow):
    def __init__(self, current_image):
        super().__init__()
        self.current_image = current_image
        self.setWindowTitle("Segmentation")
        #self.setStyleSheet("background-color: whitesmoke;")

        
        self.container = QWidget()
        self.wlayout = self.create_main_layout()
        self.container.setLayout(self.wlayout)

        # Set the central widget of the Window.
        self.setCentralWidget(self.container)
        self._createMenuBar()
  
    def create_main_layout(self):
        wlayout = QtWidgets.QHBoxLayout()
        left_layout=self.left_side()
        centre_layout=self.centre()
        right_layout=self.right_side()
        wlayout.addLayout(left_layout)
        wlayout.addLayout(centre_layout)
        wlayout.addLayout(right_layout)

        return wlayout

    def _createMenuBar(self):

        #def export_output_button(self):

        menuBar = self.menuBar()

        self.open_action = QAction("&Open Image", self)
        self.open_action.triggered.connect(self.open_image_window)
        self.export_action = QAction("&Export Output", self)
        self.export_action.triggered.connect(lambda: self.current_image.export_output(heading = True, echo = True))
        self.batch_action = QAction("&Batch Process", self)
        self.batch_action.triggered.connect(self.open_batch_window)
        self.export_image_action = QAction("Export &Images", self)
        self.export_image_action.triggered.connect(self.export_images)
        self.exit_action = QAction("E&xit", self) 
        self.exit_action.triggered.connect(self.exit_button)

        self.import_settings_action = QAction("&Import Settings", self) 
        self.import_settings_action.triggered.connect(self.import_settings)
        self.export_settings_action = QAction("&Export Settings", self) 
        self.export_settings_action.triggered.connect(self.export_settings)
        self.reset_settings_action = QAction("&Reset Settings", self) 
        self.reset_settings_action.triggered.connect(self.reset_settings)

        file_menu = menuBar.addMenu("&File")
        file_menu.addAction(self.open_action)
        file_menu.addAction(self.export_action)
        file_menu.addAction(self.batch_action)
        file_menu.addAction(self.export_image_action)
        file_menu.addAction(self.exit_action)

        settings_menu = menuBar.addMenu("&Settings")
        settings_menu.addAction(self.import_settings_action)
        settings_menu.addAction(self.export_settings_action)
        settings_menu.addAction(self.reset_settings_action)

    def clear_page(self, layout):

        for widget_no in range(0, layout.count()):
            if layout.itemAt(widget_no) != None:
                if "Layout" not in str(layout.itemAt(widget_no)):
                    layout.itemAt(widget_no).widget().deleteLater()
                else:
                    self.clear_page(layout.itemAt(widget_no))
        
    def export_images(self):
        self.ImageBoxLeft.figure.savefig("left.png", bbox_inches = 'tight')
        self.ImageBoxRight.figure.savefig("right.png", bbox_inches = 'tight')
        print("Images Exported")

    def open_image_window(self):

        class OpenImageSettingsWindow(QWidget):
            def __init__(self, parent, file_name):
                super().__init__()
                self.parent = parent
                self.file_name = file_name
                self.layout = QtWidgets.QVBoxLayout()

                self.channel_input_layout = QtWidgets.QHBoxLayout()
                self.channel_input_label = QtWidgets.QLabel("No. channels:")                           
                self.channel_input = QtWidgets.QLineEdit("4")
                self.channel_input.textChanged.connect(lambda: self.ChangeText())
                self.channel_input_layout.addWidget(self.channel_input_label)
                self.channel_input_layout.addWidget(self.channel_input)

                self.analyses_input_layout = QtWidgets.QHBoxLayout()
                self.analyses_input_label = QtWidgets.QLabel("No. analyses:")    
                self.analyses_input = QtWidgets.QLineEdit("3")
                self.analyses_input_layout.addWidget(self.analyses_input_label)
                self.analyses_input_layout.addWidget(self.analyses_input)

                self.buttons_layout = QtWidgets.QHBoxLayout()
                self.ok = QtWidgets.QPushButton("OK")
                self.ok.clicked.connect(lambda: self.ok_button())
                self.cancel = QtWidgets.QPushButton("Cancel")
                self.cancel.clicked.connect(lambda: self.cancel_button())
                self.buttons_layout.addStretch()
                self.buttons_layout.addWidget(self.ok)
                self.buttons_layout.addWidget(self.cancel)
                #self.name_input.setMaximumWidth(80)
                self.layout.addLayout(self.channel_input_layout)
                self.layout.addLayout(self.analyses_input_layout)
                self.layout.addLayout(self.buttons_layout)
                self.setLayout(self.layout)
            
            def ChangeText(self):
                self.analyses_input.setText(str(self.parent.str_to_int(self.channel_input.text()) - 1))

            def ok_button(self):
                new_analyses = self.parent.str_to_int(self.analyses_input.text())

                new_analysis_dict = {}
                # if an image is openened with a different number of analysis, rebuilds relevant analysis variables lists in settings with correct number of members
                if new_analyses < settings.analysis["n_analyses"]:
                    for key, value in settings.analysis.items():
                        if type(value) == list:
                            new_list = []
                            for i in range(new_analyses):
                                new_list.append(value[i])
                            new_analysis_dict.update({key:new_list})
                        else:
                            new_analysis_dict.update({key:value})
                    settings.analysis = new_analysis_dict.copy()
                    settings.analysis["n_analyses"] = new_analyses
                
                elif new_analyses > settings.analysis["n_analyses"]:
                    for key, value in settings.analysis.items():
                        if type(value) == list:
                            for i in range(new_analyses - settings.analysis["n_analyses"]):
                                value.append(value[0])
                        new_analysis_dict.update({key:value})
                    settings.analysis = new_analysis_dict.copy()
                    settings.analysis["n_analyses"] = new_analyses

                new_channels = self.parent.str_to_int(self.channel_input.text())

                if settings.channels["dapi_channel"] > new_channels:
                    settings.channels["dapi_channel"] = new_channels

                for n, item in enumerate(settings.analysis["analysis_channels"]):
                    if item > new_channels:
                        settings.analysis["analysis_channels"][n] = new_channels

                settings.channels["n_channels"] = new_channels
                
                self.parent.current_image.open_image(self.file_name)

                # clears and updates window widgets for new analysis
                # this could be tidied up - only two sections really need clearing, the left layout and threshold tab layout
                self.parent.clear_page(self.parent.wlayout)
                self.parent.container.deleteLater()
                self.parent.container = QWidget()
                self.parent.wlayout = self.parent.create_main_layout()
                self.parent.container.setLayout(self.parent.wlayout)
                self.parent.setCentralWidget(self.parent.container)

                self.parent.ZSlider.setMaximum(self.parent.current_image.n_slices)
                self.parent.draw_image()
                self.close()
                
            
            def cancel_button(self):
                self.close()
        
        file_name, _ = QtWidgets.QFileDialog.getOpenFileName(self,("Open Image"),".\\working",("Image Files (*.tif)"))

        if(file_name):
            self.settings_window = OpenImageSettingsWindow(parent = self, 
                                                           file_name = file_name)
            self.settings_window.show()

    def reset_settings(self):
        settings.import_settings("default_settings.txt", default = True)
        self.update_ui_from_settings()
        self.draw_image()

    def import_settings(self):
        file_name, _ = QtWidgets.QFileDialog.getOpenFileName(self,("Import Settings"),".\\",("Text Files (*.txt)"))
        settings.import_settings(file_name)
        self.update_ui_from_settings()
        self.draw_image()

    def export_settings(self):
        file_name, _ = QtWidgets.QFileDialog.getSaveFileName(self,("Export Settings"),".\\",("Text Files (*.txt)"))
        settings.export_settings(file_name)

    def update_ui_from_settings(self):
        self.sigma_input.setText(str(settings.segmentation["segment_sigma"]))
        self.low_thresh_input.setText(str(settings.segmentation["low_thresh_multiplier"]))
        self.high_thresh_input.setText(str(settings.segmentation["high_thresh_multiplier"]))
        self.distance_input.setText(str(settings.segmentation["min_thresh_distance"]))
        self.overlap_size_input.setText(str(settings.segmentation["min_overlap_size"]))
        self.object_size_input.setText(str(settings.segmentation["min_object_size"]))
        self.solidity_input.setText(str(settings.segmentation["min_solidity"]))
        self.intensity_multiplier_input.setText(str(settings.segmentation["min_intensity_multiplier"]))
        self.max_area_input.setText(str(settings.segmentation["max_nuclear_area"]))
        self.ratio_input.setText(str(settings.segmentation["min_ratio_circularity"]))
        self.distance_segment_enable.setChecked(settings.segmentation["distance_segment"])
        self.region_segment_enable.setChecked(settings.segmentation["region_segment"])
        self.stack_segment_enable.setChecked(settings.segmentation["stack_segment"])

        self.dapi_section.LUT_selector.setCurrentText(settings.channels["dapi_LUT"])
        self.dapi_section.channel_selector.setCurrentText(str(settings.channels["dapi_channel"]))

        for i in range(settings.analysis["n_analyses"]):
            self.analysis_section[i].channel_selector.setCurrentText(str(settings.analysis["analysis_channels"][i]))
            self.analysis_section[i].LUT_selector.setCurrentText(settings.analysis["analysis_LUTs"][i])

            self.thresh_analysis_section[i].name_input.setText(settings.analysis["analysis_names"][i])
            self.thresh_analysis_section[i].method_input.setCurrentText(settings.analysis["threshold"][i])
            self.thresh_analysis_section[i].background_subtraction_enable.setChecked(settings.analysis["background_subtract"][i])
            self.thresh_analysis_section[i].background_radius_input.setText(str(settings.analysis["background_radius"][i]))
            self.thresh_analysis_section[i].gauss_sigma_input.setText(str(settings.analysis["sigma"][i]))
            self.thresh_analysis_section[i].erode_input.setText(str(settings.analysis["erode"][i]))

        self.intensity_enable.setChecked(settings.analysis["measure_intensity"])

        self.adjacency_enable_input.setChecked(settings.adjacency["measure_adjacency"])
        self.adjacency_threshold_input.setText(str(settings.adjacency["adjacency_threshold"]))
        self.adjacency_cells_input.setCurrentText(str(settings.adjacency["adjacency_cells"]))
        self.channel_selector_input.setCurrentText(str(settings.adjacency["analysis_for_adjacency"]))
        self.adjacency_distance_input.setText(str(settings.adjacency["adjacency_expansion_distance"]))

    def open_batch_window(self):
        folder = str(QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory"))
        if folder:
            print(folder)
            self.current_image.batch(folder)

    def exit_button(self):
        sys.exit()

    def draw_image(self):
        def get_new_output(option,view):
            if option == "Input":
                output = np.zeros((self.current_image.height, self.current_image.width), dtype = np.int32)
                output = LUTs.LUTs["Black"](output)
                if self.dapi_section.show_selector.isChecked() == True:
                    output += LUTs.LUTs[settings.channels["dapi_LUT"]](self.current_image.input_image[self.ZSlider.value() - 1][settings.channels["dapi_channel"] - 1])
                for i in range(settings.analysis["n_analyses"]):
                    if self.analysis_section[i].show_selector.isChecked() == True:
                        output += LUTs.LUTs[settings.analysis["analysis_LUTs"][i]](self.current_image.input_image[self.ZSlider.value() - 1][int(self.analysis_section[i].channel_selector.currentText()) - 1])
                output[output > 1] = 1
                view.imshow(output, 
                            interpolation='none')
            elif option == 'Seg: After Region (1)':
                view.imshow(self.current_image.after_region[self.ZSlider.value() - 1],
                            cmap = LUTs.label_cmap)
            elif option=='Seg: After Distance (2)':
                view.imshow(self.current_image.after_distance[self.ZSlider.value() - 1],
                            cmap = LUTs.label_cmap)
            elif option=='Seg: After Stack (3)':
                view.imshow(self.current_image.after_stack[self.ZSlider.value() - 1],
                            cmap = LUTs.label_cmap)
            elif option=='Enlarged Cells':
                if self.current_image.adjacency_calculated == True:
                    view.imshow(self.current_image.adjacency_enlarged_segments[self.ZSlider.value() - 1],
                                cmap = LUTs.label_cmap,
                                vmin=0,
                                vmax=self.current_image.n_labels,
                                interpolation='none')
            elif option=='Adjacent Output':
                if self.current_image.adjacency_calculated == True:
                    adjacency_analysis = [name for name in settings.analysis["analysis_names"]].index(settings.adjacency["analysis_for_adjacency"])
                    adjacency_output = self.current_image.analyses[adjacency_analysis].adjacency_output_for_UI 
                    adjacency_output = np.zeros((self.current_image.n_slices, self.current_image.height, self.current_image.width), dtype = np.int32)

                    for i in range(self.current_image.n_slices):
                        for j in range(self.current_image.height):
                            for k in range(self.current_image.width):
                                adjacency_output[i][j][k] = self.current_image.analyses[adjacency_analysis].adjacency_value[self.current_image.adjacency_enlarged_segments[i][j][k]]
                    
                    view.imshow(adjacency_output[self.ZSlider.value()-1],
                                cmap = LUTs.adjacent_cmap,
                                interpolation='none')
                    
            elif option== 'Seg: Output (4)':
                view.imshow(self.current_image.segmented_image[self.ZSlider.value() - 1], 
                            cmap = LUTs.label_cmap, 
                            vmin = 0, 
                            vmax = self.current_image.n_labels, 
                            interpolation='none')
                
            elif "Thresh: Analysis" in option:
                analysis = int(option[-1])

                view.imshow(self.current_image.analyses[analysis - 1].thresholded_image[self.ZSlider.value() - 1],
                            cmap='Greys')


        #for left and right output views, clears current content and gets new content

        if self.left_view_lock.isChecked() == False:
            self.ax1.cla()
            get_new_output(self.left_view_input.currentText(), self.ax1)

        if self.right_view_lock.isChecked() == False:
            self.ax2.cla()
            get_new_output(self.right_view_input.currentText(), self.ax2)

        if self.OutlineCheck.isChecked() == True:
            labels=ski.segmentation.find_boundaries(self.current_image.segmented_image[self.ZSlider.value() - 1],mode='thick')
            self.ax1.imshow(labels, alpha=ski.img_as_float(labels), cmap = LUTs.outline_cmap)
            self.ax2.imshow(labels, alpha=ski.img_as_float(labels), cmap = LUTs.outline_cmap)

        if self.LabelCheck.isChecked()==True:
            Label_Properties=ski.measure.regionprops(self.current_image.segmented_image[self.ZSlider.value()-1])
            for i in range(len(Label_Properties)):
                self.ax1.text(Label_Properties[i].centroid[1],Label_Properties[i].centroid[0], str(Label_Properties[i].label), color=(1,1,0),size='x-small',ha='center',va='center')
                self.ax2.text(Label_Properties[i].centroid[1],Label_Properties[i].centroid[0], str(Label_Properties[i].label), color=(1,1,0),size='x-small',ha='center',va='center')

        self.ax1.axis('off')
        self.ax2.axis('off')
        self.ImageBoxLeft.figure.subplots_adjust(top = 1, bottom = 0, right = 1, left = 0, hspace = 0, wspace = 0)
        self.ImageBoxRight.figure.subplots_adjust(top = 1, bottom = 0, right = 1, left = 0, hspace = 0, wspace = 0)

        self.ImageBoxLeft.draw()
        self.ImageBoxRight.draw()

    def str_to_int(self, input):
            try:
                return int(input)
            except:
                return 0
            
    def str_to_float(self, input):
            try:
                return float(input)
            except:
                return 0
          
    def setting_change(self, dictionary, variable, value, idx = None):
        # this function is connected to UI input elements and changes the relvent setting in settings.py, by dictionary, variable name and, if necessary, analysis index.
        if idx == None:
            dictionary[variable] = value
        else:
            dictionary[variable][idx] = value

    def left_side(self):

        class analysis:
            def __init__(self, parent, name, channel, lut):
                self.Frame=QGroupBox(name)
                self.Frame.setFixedHeight(120)
                self.Layout=QtWidgets.QVBoxLayout()

                self.channel_layout=QtWidgets.QHBoxLayout()
                self.channel_label=QtWidgets.QLabel("Channel:")
                self.channel_selector = QtWidgets.QComboBox()
                for i in range(settings.channels["n_channels"]):
                    self.channel_selector.addItem(str(i + 1))
                self.channel_selector.setCurrentText(str(channel))
                self.channel_selector.currentTextChanged.connect(lambda: change_channel(self, parent))
                self.channel_layout.addWidget(self.channel_label)
                self.channel_layout.addWidget(self.channel_selector)

                self.LUT_layout=QtWidgets.QHBoxLayout()
                self.LUT_label=QtWidgets.QLabel("LUT:")
                self.LUT_selector = QtWidgets.QComboBox()
                self.LUT_selector.addItems(["Grey","Green","Cyan","Magenta"])
                self.LUT_selector.setCurrentText(lut)
                self.LUT_selector.currentTextChanged.connect(lambda: change_LUT(self, parent))
                self.LUT_layout.addWidget(self.LUT_label)
                self.LUT_layout.addWidget(self.LUT_selector)
                

                self.show_layout=QtWidgets.QHBoxLayout()
                self.show_label=QtWidgets.QLabel("Show:")
                self.show_selector = QtWidgets.QCheckBox()
                self.show_selector.setChecked(True)
                self.show_layout.addWidget(self.show_label)
                self.show_layout.addWidget(self.show_selector)
                self.show_selector.stateChanged.connect(lambda: parent.draw_image())

                self.Layout.addLayout(self.channel_layout)
                self.Layout.addLayout(self.LUT_layout)
                self.Layout.addLayout(self.show_layout)

                self.Frame.setLayout(self.Layout)
        
        def change_channel(self, parent):
            for i in range(settings.analysis["n_analyses"]):
                settings.analysis["analysis_channels"][i] = parent.str_to_int(parent.analysis_section[i].channel_selector.currentText())
                settings.channels["dapi_channel"] = parent.str_to_int(parent.dapi_section.channel_selector.currentText())
            parent.draw_image()

        def change_LUT(self, parent):
            for i in range(settings.analysis["n_analyses"]):
                settings.analysis["analysis_LUTs"][i] = parent.analysis_section[i].LUT_selector.currentText()
                settings.channels["dapi_LUT"] = parent.dapi_section.LUT_selector.currentText()
            parent.draw_image()
        
        leftcontrollayout=QtWidgets.QVBoxLayout()
        self.dapi_section = analysis(name = "Dapi", 
                                     parent = self,
                                     channel = settings.channels["dapi_channel"], 
                                     lut = settings.channels["dapi_LUT"])
        self.analysis_section = []
        for i in range(settings.analysis["n_analyses"]):
            self.analysis_section.append(analysis(name = "Analysis " + str(i+1), 
                                                  parent = self,
                                                  channel = str(settings.analysis["analysis_channels"][i]),
                                                  lut = settings.analysis["analysis_LUTs"][i]))
            
        ViewFrame=QGroupBox("View")
        ViewFrame.setFixedHeight(80)
        ViewLayout=QtWidgets.QVBoxLayout()

        OutlineLayout=QtWidgets.QHBoxLayout()
        OutlineLabel=QtWidgets.QLabel("Outline:")
        self.OutlineCheck = QtWidgets.QCheckBox()
        self.OutlineCheck.stateChanged.connect(lambda: self.draw_image())
        OutlineLayout.addWidget(OutlineLabel)
        OutlineLayout.addWidget(self.OutlineCheck)

        LabelLayout=QtWidgets.QHBoxLayout()
        LabelLabel=QtWidgets.QLabel("Labels:")
        self.LabelCheck = QtWidgets.QCheckBox()
        self.LabelCheck.stateChanged.connect(lambda: self.draw_image())
        LabelLayout.addWidget(LabelLabel)
        LabelLayout.addWidget(self.LabelCheck)

        ViewLayout.addLayout(OutlineLayout)
        ViewLayout.addLayout(LabelLayout)

        ViewFrame.setLayout(ViewLayout)

        leftcontrollayout.addWidget(ViewFrame)
        leftcontrollayout.addWidget(self.dapi_section.Frame)

        for i in range(settings.analysis["n_analyses"]):
            leftcontrollayout.addWidget(self.analysis_section[i].Frame)
        return leftcontrollayout

    def centre(self):

        #set out center - image and slider below image
        imagelayout = QtWidgets.QVBoxLayout()
        imagesublayout = QtWidgets.QHBoxLayout()

        #set up image
        self.ImageBoxLeft = FigureCanvas(Figure(figsize=(10, 10)))
        self.ImageBoxRight = FigureCanvas(Figure(figsize=(10, 10)))
        self.ImageBoxLeft.setMinimumWidth(600)
        self.ImageBoxRight.setMinimumWidth(600)
    
        self.ax1 = self.ImageBoxLeft.figure.subplots()
        self.ax2 = self.ImageBoxRight.figure.subplots()

        #set up slider for z-stacks
        self.ZSlider = QtWidgets.QSlider(Qt.Orientation.Horizontal)
        self.ZSlider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.ZSlider.setMinimum(1)
        self.ZSlider.setTickInterval(1)
        self.ZSlider.setMaximum(self.current_image.n_slices)
        self.ZSlider.setValue(1) 
        self.ZSlider.valueChanged.connect(lambda: self.draw_image())

        imagesublayout.addWidget(self.ImageBoxLeft)
        imagesublayout.addWidget(self.ImageBoxRight)
        imagelayout.addLayout(imagesublayout)
        imagelayout.addWidget(self.ZSlider)
        return imagelayout

    def right_side(self):

        def rename_analysis(self, parent, index):
            settings.analysis["analysis_names"][index] = parent.thresh_analysis_section[index].name_input.text()
            parent.channel_selector_input.clear()
            for i in range(settings.analysis["n_analyses"]):
                parent.channel_selector_input.addItem(parent.thresh_analysis_section[i].name_input.text())

        def segmentation_tab(self):

            def run_segment():
                self.current_image.segment()
                self.right_view_input.setCurrentText('Seg: Output(4)')
                self.draw_image()

            controllayout=QtWidgets.QVBoxLayout()

            button = QtWidgets.QPushButton("Segment")
            button.clicked.connect(lambda: run_segment())

            sigma_layout=QtWidgets.QHBoxLayout()
            sigma_label=QtWidgets.QLabel("Gaussian Blur Sigma:")
            self.sigma_input=QtWidgets.QLineEdit(str(settings.segmentation["segment_sigma"]))
            self.sigma_input.setMaximumWidth(40)
            self.sigma_input.textChanged.connect(lambda: self.setting_change(settings.segmentation, "segment_sigma", self.str_to_float(self.sigma_input.text())))
            sigma_layout.addWidget(sigma_label)
            sigma_layout.addWidget(self.sigma_input)

            ########################
            # region_segment frame #
            ########################

            region_frame=QGroupBox("Region Segmentation")
            region_layout=QtWidgets.QVBoxLayout()


            region_enable_layout=QtWidgets.QHBoxLayout()
            region_segment_label=QtWidgets.QLabel("Region Segment:")
            self.region_segment_enable=QtWidgets.QCheckBox()
            self.region_segment_enable.setChecked(settings.segmentation["region_segment"])
            self.region_segment_enable.stateChanged.connect(lambda: self.setting_change(settings.segmentation, "region_segment", self.region_segment_enable.isChecked()))
            region_enable_layout.addWidget(region_segment_label)
            region_enable_layout.addWidget(self.region_segment_enable)

            low_thresh_layout=QtWidgets.QHBoxLayout()
            low_thresh_label=QtWidgets.QLabel("Low Threshold:")
            self.low_thresh_input=QtWidgets.QLineEdit(str(settings.segmentation["low_thresh_multiplier"]))
            self.low_thresh_input.setMaximumWidth(40)
            self.low_thresh_input.textChanged.connect(lambda: self.setting_change(settings.segmentation, "low_thresh_multiplier", self.str_to_float(self.low_thresh_input.text())))
            low_thresh_layout.addWidget(low_thresh_label)
            low_thresh_layout.addWidget(self.low_thresh_input)

            high_thresh_layout=QtWidgets.QHBoxLayout()
            high_thresh_label=QtWidgets.QLabel("High Threshold:")
            self.high_thresh_input=QtWidgets.QLineEdit(str(settings.segmentation["high_thresh_multiplier"]))
            self.high_thresh_input.setMaximumWidth(40)
            self.high_thresh_input.textChanged.connect(lambda: self.setting_change(settings.segmentation, "high_thresh_multiplier", self.str_to_float(self.high_thresh_input.text())))
            high_thresh_layout.addWidget(high_thresh_label)
            high_thresh_layout.addWidget(self.high_thresh_input)

            region_layout.addLayout(region_enable_layout)
            region_layout.addLayout(low_thresh_layout)
            region_layout.addLayout(high_thresh_layout)
            region_frame.setLayout(region_layout)

            ########################
            #distance segment frame#
            ########################

            distance_frame=QGroupBox("Distance Segmentation")
            distance_frame_layout=QtWidgets.QVBoxLayout()

            distance_enable_layout=QtWidgets.QHBoxLayout()
            distance_segment_label=QtWidgets.QLabel("Distance Segment:")
            self.distance_segment_enable=QtWidgets.QCheckBox()
            self.distance_segment_enable.setChecked(settings.segmentation["distance_segment"])
            self.distance_segment_enable.stateChanged.connect(lambda: self.setting_change(settings.segmentation, "distance_segment", self.distance_segment_enable.isChecked()))
            distance_enable_layout.addWidget(distance_segment_label)
            distance_enable_layout.addWidget(self.distance_segment_enable)

            distance_layout=QtWidgets.QHBoxLayout()
            distance_label=QtWidgets.QLabel("Min. Distance:")
            self.distance_input=QtWidgets.QLineEdit(str(settings.segmentation["min_thresh_distance"]))
            self.distance_input.setMaximumWidth(40)
            self.distance_input.textChanged.connect(lambda: self.setting_change(settings.segmentation, "min_thresh_distance", self.str_to_int(self.distance_input.text())))
            distance_layout.addWidget(distance_label)
            distance_layout.addWidget(self.distance_input)

            distance_frame_layout.addLayout(distance_enable_layout)
            distance_frame_layout.addLayout(distance_layout)
            distance_frame.setLayout(distance_frame_layout)

            #####################
            #stack segment frame#
            #####################

            stack_frame=QGroupBox("Stack Segmentation")
            stack_layout=QtWidgets.QVBoxLayout()

            stack_enable_layout=QtWidgets.QHBoxLayout()
            stack_segment_label=QtWidgets.QLabel("Stack Segment:")
            self.stack_segment_enable=QtWidgets.QCheckBox()
            self.stack_segment_enable.setChecked(settings.segmentation["stack_segment"])
            self.stack_segment_enable.stateChanged.connect(lambda: self.setting_change(settings.segmentation, "stack_segment", self.stack_segment_enable.isChecked()))
            stack_enable_layout.addWidget(stack_segment_label)
            stack_enable_layout.addWidget(self.stack_segment_enable)

            overlap_size_layout=QtWidgets.QHBoxLayout()
            overlap_size_label=QtWidgets.QLabel("Min. Overlap Size:")
            self.overlap_size_input=QtWidgets.QLineEdit(str(settings.segmentation["min_overlap_size"]))
            self.overlap_size_input.setMaximumWidth(40)
            self.overlap_size_input.textChanged.connect(lambda: self.setting_change(settings.segmentation, "min_overlap_size", self.str_to_int(self.overlap_size_input.text())))
            overlap_size_layout.addWidget(overlap_size_label)
            overlap_size_layout.addWidget(self.overlap_size_input)

            stack_layout.addLayout(stack_enable_layout)
            stack_layout.addLayout(overlap_size_layout)
            stack_frame.setLayout(stack_layout)

            ####################
            #object stats frame#
            ####################
            object_stats_frame=QGroupBox("Objects")
            object_stats_layout=QtWidgets.QVBoxLayout()

            object_size_layout=QtWidgets.QHBoxLayout()
            object_size_label=QtWidgets.QLabel("Min. Object Size:")
            self.object_size_input=QtWidgets.QLineEdit(str(settings.segmentation["min_object_size"]))
            self.object_size_input.setMaximumWidth(40)
            self.object_size_input.textChanged.connect(lambda: self.setting_change(settings.segmentation, "min_object_size", self.str_to_int(self.object_size_input.text())))
            object_size_layout.addWidget(object_size_label)
            object_size_layout.addWidget(self.object_size_input)

            solidity_layout=QtWidgets.QHBoxLayout()
            solidity_label=QtWidgets.QLabel("Min. Object Solidity:")
            self.solidity_input=QtWidgets.QLineEdit(str(settings.segmentation["min_solidity"]))
            self.solidity_input.setMaximumWidth(40)
            self.solidity_input.textChanged.connect(lambda: self.setting_change(settings.segmentation, "min_solidity", self.str_to_float(self.solidity_input.text())))
            solidity_layout.addWidget(solidity_label)
            solidity_layout.addWidget(self.solidity_input)

            ratio_layout=QtWidgets.QHBoxLayout()
            ratio_label=QtWidgets.QLabel("Min. Object Circularity:")
            self.ratio_input=QtWidgets.QLineEdit(str(settings.segmentation["min_ratio_circularity"]))
            self.ratio_input.setMaximumWidth(40)
            self.ratio_input.textChanged.connect(lambda: self.setting_change(settings.segmentation, "min_ratio_circularity", self.str_to_float(self.ratio_input.text())))
            ratio_layout.addWidget(ratio_label)
            ratio_layout.addWidget(self.ratio_input)

            max_area_layout=QtWidgets.QHBoxLayout()
            max_area_label=QtWidgets.QLabel("Max. Object Area:")
            self.max_area_input=QtWidgets.QLineEdit(str(settings.segmentation["max_nuclear_area"]))
            self.max_area_input.setMaximumWidth(40)
            self.max_area_input.textChanged.connect(lambda: self.setting_change(settings.segmentation, "max_nuclear_area", self.str_to_int(self.max_area_input.text())))
            max_area_layout.addWidget(max_area_label)
            max_area_layout.addWidget(self.max_area_input)

            intensity_multiplier_layout=QtWidgets.QHBoxLayout()
            intensity_multiplier_label=QtWidgets.QLabel("Min. Object Intensity Multiplier:")
            self.intensity_multiplier_input=QtWidgets.QLineEdit(str(settings.segmentation["min_intensity_multiplier"]))
            self.intensity_multiplier_input.setMaximumWidth(40)
            self.intensity_multiplier_input.textChanged.connect(lambda: self.setting_change(settings.segmentation, "min_intensity_multiplier", self.str_to_float(self.intensity_multiplier_input.text())))
            intensity_multiplier_layout.addWidget(intensity_multiplier_label)
            intensity_multiplier_layout.addWidget(self.intensity_multiplier_input)

            object_stats_layout.addLayout(object_size_layout)
            object_stats_layout.addLayout(intensity_multiplier_layout)
            object_stats_layout.addLayout(solidity_layout)
            object_stats_layout.addLayout(max_area_layout)
            object_stats_layout.addLayout(ratio_layout)
            object_stats_frame.setLayout(object_stats_layout)

            controllayout.addWidget(button)
            controllayout.addLayout(sigma_layout)
            controllayout.addWidget(region_frame)
            controllayout.addWidget(distance_frame)
            controllayout.addWidget(stack_frame)
            controllayout.addWidget(object_stats_frame)


            return controllayout

        def threshold_tab(self):

            def run_threshold():
                self.current_image.analyse()
                self.draw_image()
                      
            class threshold_analysis:
                def __init__(self, parent, index, name, analysis_name, bg_subtract, bg_radius, sigma, erode, threshold_method):
                    self.parent = parent

                    self.frame = QGroupBox(name)
                    self.frame.setFixedHeight(160)
                    self.layout = QtWidgets.QVBoxLayout()

                    self.name_layout = QtWidgets.QHBoxLayout()
                    self.name_label = QtWidgets.QLabel("Name:")
                    self.name_input = QtWidgets.QLineEdit(analysis_name)
                    self.name_input.textChanged.connect(lambda: rename_analysis(self, parent, index))
                    self.name_input.setMaximumWidth(80)
                    self.name_layout.addWidget(self.name_label)
                    self.name_layout.addWidget(self.name_input)

                    self.background_subtraction_layout = QtWidgets.QHBoxLayout()
                    self.background_subtraction_enable = QtWidgets.QCheckBox("BG Subtract")
                    self.background_subtraction_enable.setChecked(bg_subtract)
                    self.background_subtraction_enable.stateChanged.connect(lambda: parent.setting_change(settings.analysis, "background_subtract", self.background_subtraction_enable.isChecked(), index))
                    self.background_radius_label = QtWidgets.QLabel("Radius:")
                    self.background_radius_input = QtWidgets.QLineEdit(str(bg_radius))
                    self.background_radius_input.setMaximumWidth(40)
                    self.background_radius_input.textChanged.connect(lambda: parent.setting_change(settings.analysis, "background_radius", parent.str_to_int(self.background_radius_input.text()), index))
                    self.background_subtraction_layout.addWidget(self.background_subtraction_enable)
                    self.background_subtraction_layout.addWidget(self.background_radius_label)
                    self.background_subtraction_layout.addWidget(self.background_radius_input)

                    self.gauss_layout = QtWidgets.QHBoxLayout()
                    self.gauss_label = QtWidgets.QLabel("Sigma:")
                    self.gauss_sigma_input = QtWidgets.QLineEdit(str(sigma))
                    self.gauss_sigma_input.setMaximumWidth(80)
                    self.gauss_sigma_input.textChanged.connect(lambda: parent.setting_change(settings.analysis, "sigma", parent.str_to_float(self.gauss_sigma_input.text()), index))
                    self.gauss_layout.addWidget(self.gauss_label)
                    self.gauss_layout.addWidget(self.gauss_sigma_input)

                    self.erode_layout = QtWidgets.QHBoxLayout()
                    self.erode_label = QtWidgets.QLabel("Erode:")
                    self.erode_input = QtWidgets.QLineEdit(str(erode))
                    self.erode_input.setMaximumWidth(40)
                    self.erode_input.textChanged.connect(lambda: parent.setting_change(settings.analysis, "erode", parent.str_to_int(self.erode_input.text()), index))
                    self.erode_layout.addWidget(self.erode_label)
                    self.erode_layout.addWidget(self.erode_input)

                    self.method_layout = QtWidgets.QHBoxLayout()
                    self.method_label = QtWidgets.QLabel("Method:")
                    self.method_input = QtWidgets.QComboBox()
                    self.method_input.addItems(['None', 'Isodata', 'Li', 'Mean','Minimum','Otsu','Triangle','Yen'])
                    self.method_input.setCurrentText(threshold_method)
                    self.method_input.currentTextChanged.connect(lambda: parent.setting_change(settings.analysis, "threshold", self.method_input.currentText(), index))
                    self.method_layout.addWidget(self.method_label)
                    self.method_layout.addWidget(self.method_input)

                    self.layout.addLayout(self.name_layout)
                    self.layout.addLayout(self.background_subtraction_layout)
                    self.layout.addLayout(self.gauss_layout)
                    self.layout.addLayout(self.erode_layout)
                    self.layout.addLayout(self.method_layout)
                    self.frame.setLayout(self.layout)

            self.threshold_layout = QtWidgets.QVBoxLayout()

            button_threshold = QtWidgets.QPushButton("Threshold")
            button_threshold.clicked.connect(run_threshold)

            
            self.intensity_layout = QtWidgets.QHBoxLayout()
            self.intensity_enable = QtWidgets.QCheckBox("Measure absolute intensity")
            self.intensity_enable.setChecked(settings.analysis["measure_intensity"])

            self.intensity_enable.stateChanged.connect(lambda: self.setting_change(settings.analysis, "measure_intensity", self.intensity_enable.isChecked()))
            self.intensity_layout.addWidget(self.intensity_enable)

            self.thresh_analysis_section = []
            for i in range(settings.analysis["n_analyses"]):
                self.thresh_analysis_section.append(threshold_analysis(parent = self,
                                                                       index = i,
                                                                       name = "Analysis " + str(i + 1),
                                                                       analysis_name = settings.analysis["analysis_names"][i],
                                                                       bg_subtract = settings.analysis["background_subtract"][i],
                                                                       bg_radius = settings.analysis["background_radius"][i],
                                                                       sigma = settings.analysis["sigma"][i],
                                                                       erode = settings.analysis["erode"][i],
                                                                       threshold_method = settings.analysis["threshold"][i]))

            self.threshold_layout.addWidget(button_threshold)
            for i in range(settings.analysis["n_analyses"]):
                self.threshold_layout.addWidget(self.thresh_analysis_section[i].frame)
            self.threshold_layout.addLayout(self.intensity_layout)
            return self.threshold_layout

        def adjacency_tab(self):

            def run_adjacency():
                if self.current_image.segmented == False or self.current_image.analysed == False:
                    print("Segmentation and thresholding required to calculate adjacency")
                else:
                    self.current_image.calculate_adjacency()
                    self.draw_image()

            self.layout = QtWidgets.QVBoxLayout()
            self.adjacency_frame = QGroupBox("Adjacency Analysis")
            self.adjacency_frame.setFixedHeight(220)
            self.adjacency_layout = QtWidgets.QVBoxLayout()

            self.adjaceny_button = QtWidgets.QPushButton("Calculate Adjacency")
            self.adjaceny_button.clicked.connect(lambda: run_adjacency())

            self.adjacency_enable_layout = QtWidgets.QHBoxLayout()
            self.adjacency_enable_label = QtWidgets.QLabel("Measure adjacency:")
            self.adjacency_enable_input = QtWidgets.QCheckBox()
            self.adjacency_enable_input.setChecked(settings.adjacency["measure_adjacency"])
            self.adjacency_enable_input.checkStateChanged.connect(lambda: self.setting_change(settings.adjacency,"measure_adjacency",self.adjacency_enable_input.isChecked()))
            self.adjacency_enable_layout.addWidget(self.adjacency_enable_label)
            self.adjacency_enable_layout.addWidget(self.adjacency_enable_input)

            self.channel_selector_layout=QtWidgets.QHBoxLayout()
            self.channel_selector_label=QtWidgets.QLabel("Analysis:")
            self.channel_selector_input = QtWidgets.QComboBox()
            for i in range(settings.analysis["n_analyses"]):
                self.channel_selector_input.addItem(settings.analysis["analysis_names"][i])
            self.channel_selector_input.setCurrentText(str(settings.adjacency["analysis_for_adjacency"]))
            self.channel_selector_input.currentTextChanged.connect(lambda: self.setting_change(settings.adjacency,'analysis_for_adjacency',self.channel_selector_input.currentText()))
            self.channel_selector_layout.addWidget(self.channel_selector_label)
            self.channel_selector_layout.addWidget(self.channel_selector_input)

            self.adjacency_threshold_layout=QtWidgets.QHBoxLayout()
            self.adjacency_threshold_label=QtWidgets.QLabel("Threshold:")
            self.adjacency_threshold_input=QtWidgets.QLineEdit(str(settings.adjacency["adjacency_threshold"]))
            self.adjacency_threshold_input.setMaximumWidth(40)
            self.adjacency_threshold_input.textChanged.connect(lambda: self.setting_change(settings.adjacency,"adjacency_threshold", self.str_to_float(self.adjacency_threshold_input.text())))
            self.adjacency_threshold_layout.addWidget(self.adjacency_threshold_label)
            self.adjacency_threshold_layout.addWidget(self.adjacency_threshold_input)

            self.adjacency_cells_layout=QtWidgets.QHBoxLayout()
            self.adjacency_cells_label=QtWidgets.QLabel("Number of cells:")
            self.adjacency_cells_input = QtWidgets.QComboBox()
            self.adjacency_cells_input.addItems(str(x) for x in range(1,11))
            self.adjacency_cells_input.setCurrentText(str(settings.adjacency["adjacency_cells"]))
            self.adjacency_cells_input.currentTextChanged.connect(lambda: self.setting_change(settings.adjacency,"adjacency_cells",self.str_to_int(self.adjacency_cells_input.currentText())))
            self.adjacency_cells_layout.addWidget(self.adjacency_cells_label)
            self.adjacency_cells_layout.addWidget(self.adjacency_cells_input)

            self.adjacency_distance_layout=QtWidgets.QHBoxLayout()
            self.adjacency_distance_label=QtWidgets.QLabel("Expansion distance:")
            self.adjacency_distance_input = QtWidgets.QLineEdit(str(settings.adjacency["adjacency_expansion_distance"]))
            self.adjacency_distance_input.textChanged.connect(lambda: self.setting_change(settings.adjacency,"adjacency_expansion_distance", self.str_to_int(self.adjacency_distance_input.text())))
            self.adjacency_distance_layout.addWidget(self.adjacency_distance_label)
            self.adjacency_distance_layout.addWidget(self.adjacency_distance_input)

            self.adjacency_layout.addLayout(self.adjacency_enable_layout)
            self.adjacency_layout.addLayout(self.channel_selector_layout)
            self.adjacency_layout.addLayout(self.adjacency_threshold_layout)
            self.adjacency_layout.addLayout(self.adjacency_cells_layout)
            self.adjacency_layout.addLayout(self.adjacency_distance_layout)
            self.adjacency_frame.setLayout(self.adjacency_layout)

            self.layout.addWidget(self.adjaceny_button)
            self.layout.addWidget(self.adjacency_frame)
            self.layout.addStretch()

            return self.layout
        
        ##############
        #set out tabs#
        ##############

        self.rightside = QtWidgets.QVBoxLayout()
        self.tabs = QTabWidget()
        self.SegmentationTab = QWidget()
        self.ThresholdTab = QWidget()
        self.AdjacencyTab = QWidget()
        self.tabs.addTab(self.SegmentationTab,"Segment")
        self.tabs.addTab(self.ThresholdTab,"Threshold")
        self.tabs.addTab(self.AdjacencyTab,"Adjacency")
        self.tabs.setFixedWidth(250)

        self.segmentation_tab_layout = segmentation_tab(self)
        self.threshold_tab_layout = threshold_tab(self)
        self.adjacency_tab_layout = adjacency_tab(self)


        self.SegmentationTab.setLayout(self.segmentation_tab_layout)
        self.ThresholdTab.setLayout(self.threshold_tab_layout)
        self.AdjacencyTab.setLayout(self.adjacency_tab_layout)

        #views#

        view_options = ['Input',
                         'Seg: After Region (1)',
                         'Seg: After Distance (2)', 
                         'Seg: After Stack (3)',
                         'Seg: Output (4)',]
        
        for analysis in range (settings.analysis["n_analyses"]):
            view_options.append('Thresh: Analysis ' + str(analysis + 1))
        
        view_options.append('Enlarged Cells')
        view_options.append('Adjacent Output')

    
        self.views=QtWidgets.QVBoxLayout()

        self.left_view_layout = QtWidgets.QHBoxLayout()
        left_view_label = QtWidgets.QLabel("Left:")
        left_view_label.setFixedWidth(30)
        self.left_view_input = QtWidgets.QComboBox()
        self.left_view_input.addItems(view_options)
        self.left_view_input.setMinimumWidth(150)
        self.left_view_input.setCurrentText('Input')
        self.left_view_input.currentTextChanged.connect(lambda: self.draw_image())
        self.left_view_lock_label = QtWidgets.QLabel("Lock:")
        self.left_view_lock = QtWidgets.QCheckBox()
        self.left_view_lock.setChecked(False)

        self.left_view_layout.addWidget(left_view_label)
        self.left_view_layout.addWidget(self.left_view_input)
        self.left_view_layout.addWidget(self.left_view_lock_label)
        self.left_view_layout.addWidget(self.left_view_lock)


        self.right_view_layout=QtWidgets.QHBoxLayout()
        right_view_label=QtWidgets.QLabel("Right:")
        right_view_label.setFixedWidth(30)
        self.right_view_input = QtWidgets.QComboBox()
        self.right_view_input.addItems(view_options)
        self.right_view_input.setMinimumWidth(150)
        self.right_view_input.setCurrentText('Seg: Output (4)')
        self.right_view_input.currentTextChanged.connect(lambda: self.draw_image())
        self.right_view_lock_label = QtWidgets.QLabel("Lock:")
        self.right_view_lock = QtWidgets.QCheckBox()
        self.right_view_lock.setChecked(False)     


        self.right_view_layout.addWidget(right_view_label)
        self.right_view_layout.addWidget(self.right_view_input)
        self.right_view_layout.addWidget(self.right_view_lock_label)
        self.right_view_layout.addWidget(self.right_view_lock)


        self.views.addLayout(self.left_view_layout)
        self.views.addLayout(self.right_view_layout)


        self.rightside.addWidget(self.tabs)
        self.rightside.addLayout(self.views)
        return self.rightside











