#Segmentation variables
segmentation = {"segment_sigma": 2.0,                                   #window.sigma_input.text()
                "low_thresh_multiplier": 0.1,                           #window.low_thresh_input.text()
                "high_thresh_multiplier": 0.5,                          #window.high_thresh_input.text()
                "min_thresh_distance": 5,                               #window.distance_input.text()
                "min_overlap_size": 50,                                 #window.overlap_size_input.text()
                "min_object_size": 40,                                  #window.object_size_input.text()
                "min_solidity": 0.8,                                    #window.solidity_input.text()
                "min_intensity_multiplier": 0.7,                        #window.intensity_multiplier_input.text()
                "max_nuclear_area": 2500,                               #window.max_area_input.text()
                "min_ratio_circularity": 0.5,                           #window.ratio_input.text()
                "distance_segment": True,                               #window.distance_segment_enable.isChecked()
                "region_segment": True,                                 #window.region_segment_enable.isChecked()
                "stack_segment": True}                                  #window.stack_segment_enable.isChecked()

#channel variables
channels = {"n_channels": 4,
            "dapi_channel": 4,
            "dapi_LUT": "Grey"}
                     
#Analysis variables
analysis = {"n_analyses": 3,
            "analysis_channels": [1,2,3],                               #window.analysis_section[].channel_selector.currentText()
            "analysis_names": ["ImpL2","GFP","InR"],                    #window.thresh_analysis_section[].name_input.text()
            "analysis_LUTs": ["Magenta","Green","Cyan"],                #self.analysis_section[].LUT_selector.currentText()             
            "threshold": ["Triangle","Otsu","Triangle"],                #window.thresh_analysis_section[].method_input.currentText()
            "background_subtract": [True,False,True],                   #window.thresh_analysis_section[].background_subtraction_enable.text()
            "background_radius": [5,5,5],                               #window.thresh_analysis_section[].background_radius_input.text()
            "sigma": [3,3,3],                                           #window.thresh_analysis_section[].gauss_sigma_input.text()
            "erode": [0,0,0],                                           #window.thresh_analysis_section[].erode_input.text()
            "stack behaviour": ["Stack", "Stack", "Stack"],

            "measure_intensity": True,                                  #window.intensity_enable.isChecked()
            "intensity_channel": "InR"}                                 #window.intensity_analysis_input.currentText()

#Adjacency variables
adjacency = {"measure_adjacency": False,                                #window.adjacency_enable_input.isChecked()
            "adjacency_threshold": 0.8,                                 #window.adjacency_threshold_input.text()
            "adjacency_cells": 5,                                       #window.adjacency_cells_input.currentText()
            "analysis_for_adjacency": "GFP",                            #window.channel_selector_input.currentText()
            "adjacency_expansion_distance": 50}                         #window.adjacency_distance_input.text()

settings_sections = [segmentation, channels, analysis, adjacency]


def export_settings(file_name, auto_save = False):
    with open(file_name, "w") as output_file:
        for section in settings_sections:
            for key, value in section.items():
                output_file.write(key + " = " + str(value)+"\n")
        if auto_save == True:
            output_file.write(auto_save)
    if auto_save == False:
        print("Settings exported")


def import_settings(file_name, default = False):
    success = True
    with open(file_name, "r") as input_file:
        for section in settings_sections:
            for key, value in section.items():
                new_key, new_value = input_file.readline().rstrip().split(" = ")
                if key == new_key:
                    if "," in new_value: 
                        # if line contains a list, remove punctuation and split into list
                        # then convert each item in list to proper type
                        new_value = new_value.replace("[","").replace("]","").replace("'","").split(", ")
                        for n, item in enumerate(new_value):
                            try:
                                new_value[n] = eval(item)

                            except NameError:
                                new_value[n] = new_value[n]
                    section[new_key] = type(value)(new_value)
                else:
                    success = False
        
    if success == True and default == False:
        print ("Settings imported")
    elif success == False:
        print ("Settings input failed")
        import_settings("default_settings.txt", True)
    elif success == True and default == True:
        print("Settings reset")
            


