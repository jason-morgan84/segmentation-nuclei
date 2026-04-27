from scipy import ndimage
from PIL import Image as PilImage
import skimage as ski
import numpy as np
import os
import settings

class ImageProcessing():
    def __init__(self):
        self.input_image = 0
        self.segmented_image = 0
        self.after_region = 0
        self.after_distance = 0
        self.after_stack = 0
        self.region_threshold_intensity = 0
        self.region_absolute_intensity = 0
        self.adjacency_enlarged_segments = 0
        self.n_labels = 0 # after segmentation, records maximum label value. 
        self.label_area = 0
        self.segmented = False

        self.analyses = []
        self.analysed = False

        self.adjacency_calculated = False

        self.n_slices = 0
        self.height = 0
        self.width = 0

    class AnalysisData():
        def __init__(self, parent, index):
            self.channel = settings.analysis["analysis_channels"][index] - 1
            self.name = settings.analysis["analysis_names"][index]
            self.threshold_method = settings.analysis["threshold"][index]
            self.background_subtract = settings.analysis["background_subtract"][index]
            self.background_radius = settings.analysis["background_radius"][index]
            self.sigma = settings.analysis["sigma"][index]
            self.erode = settings.analysis["erode"][index]
            self.measure_absolute_intensity = settings.analysis["measure_intensity"]

            self.adjacency_expansion_distance = settings.adjacency["adjacency_expansion_distance"]
            self.adjacency_threshold = settings.adjacency["adjacency_threshold"]
   
            self.thresholded_image = np.zeros((parent.n_slices, parent.height, parent.width), dtype = np.int32)
            self.max_label_threshold_intensity = 0
            self.max_label_absoulte_intensity = 0
            self.adjacency_value = 0
            self.adjacency_output_for_UI = 0

    def open_image(self, file_name):
        n_channels = settings.channels["n_channels"]

        self.opened_image = PilImage.open(file_name)  

        self.height = self.opened_image.height
        self.width = self.opened_image.width

        self.n_slices = int(self.opened_image.n_frames/n_channels)


        #Import image data to correct format as 2D numpy array
        self.input_image = np.zeros((self.n_slices,
                            n_channels,
                            self.height,
                            self.width),
                            dtype=np.int32)
    
        for i in range(self.n_slices):
            for j in range(n_channels):
                self.opened_image.seek(i * n_channels + j)
                # if slices and channels seem to be reversed, try uncommenting following line and commenting line above.
                # self.opened_image.seek(j * n_channels + i)
                self.input_image[i,j] = ski.img_as_ubyte(np.asarray(self.opened_image))
          

        self.after_region = np.zeros((self.n_slices, self.height, self.width), dtype = np.int32)
        self.segmented_image = np.zeros((self.n_slices, self.height, self.width), dtype = np.int32)
        self.after_distance = np.zeros((self.n_slices, self.height, self.width), dtype = np.int32)
        self.after_stack = np.zeros((self.n_slices, self.height, self.width), dtype = np.int32)
        self.adjacency_enlarged_segments = 0

        self.segmented = False
        self.analyses = []
        self.analysed = False
        self.adjacency_calculated = False


    
    def segment(self):
        def remove_dark_regions(input_image, intensity_image, min_intensity):
            # expects input of a labelled image and an image with intensity values
            # calculates properties of regions, adds regions with value above threshold to list of acceptable regions
            # uses logical_and to return image that only contains labelled regions in acceptable list

            high_values=[]
            input_properties = ski.measure.regionprops(input_image, intensity_image = intensity_image)

            for region in input_properties:
                if region.intensity_mean * 255 > min_intensity:
                    high_values.append(region.label)
            
            return np.logical_and(input_image, np.isin(input_image, high_values))
        def region_segment(input_image, high, low):
            # uses sobel filter to find edges in input_image
            elevation_map = ski.filters.sobel(input_image)

            # creates an array of same size as input image. Where image values are less than a defined low value, has value of 1
            # where image values are greater than a defined high value, has value of 2
            # else has value of 0
            markers = np.zeros((self.height, self.width), dtype = np.int32)
            markers[input_image < low] = 1
            markers[input_image  > high] = 2

            # uses the skimage watershed function to fill regions with value 0, with basins defined by sobel edge filter.
            # fills with 1 from low value regions (outside nuclei)
            # fills with 2 from high value regions (inside nuclei)
            # because watershed is within defined basins, results in values of 2 inside nuclei and 1 outside
            # subtracting 1 from image results in binary image representing nulcei as 1
            segmentation = ski.segmentation.watershed(elevation_map, markers,watershed_line=True)
            segmentation = ndimage.binary_fill_holes(segmentation - 1)
            return segmentation
        def stack_segment(input_image1, input_image2, intensity_image2, min_intensity, min_overlap_size, min_object_size):
            
            # removes regions with average intensity below threshold from input_image2 (avoids segmentation by faint regions)
            input_image2 = remove_dark_regions(input_image2, intensity_image2, min_intensity)
            
            # finds regions where overlaps exist between images, ignores overlaps below a defined size
            overlap = np.logical_and(input_image1, input_image2)
            overlap = ski.morphology.label(overlap, connectivity = 1)
            overlap = ski.morphology.remove_small_objects(overlap, max_size = min_overlap_size)
            overlap, _, _ = ski.segmentation.relabel_sequential(overlap)
            n_labels = np.max(overlap)

            # uses watershed to fill regions in input_image1, using overlaps as sources
            filled = ski.segmentation.watershed(input_image1, markers = overlap, mask = input_image1, watershed_line = True)

            # filled image only contains regions that are in both slices. using np.logical_xor to find regions that are only in 
            # image 1 and gives those regions unique labels (by making sure the labels are bigger than current max label)
            unique = np.logical_xor(filled, input_image1)
            unique = ski.morphology.label(unique, connectivity = 1)
            unique = ski.morphology.remove_small_objects(unique, max_size = min_object_size)
            unique[np.where(unique != 0)] += n_labels

            #create final version of slice by adding filled overlapping label set to unique to this slice label set
            output, _, _ = ski.segmentation.relabel_sequential(unique + filled)
            return output
        def distance_segment(input_image, intensity_image, min_distance, min_solidity, max_nuclear_area, min_ratio_circularity):
            # carries out distance segmentation on input image.
            # input is assumed to be a binary image with 1 as foreground (nuclei) and 0 as background
            # output is further segmented regions each with a unique label

            # starts by calculating distance of each foreground point with min distance to background
            # the finds coordinates of local peaks (defined by min_distance in settings)
            # min_distance is a key parameter affecting the maximum size of segmented nuclei and how regions will be split up
            distance = ndimage.distance_transform_edt(input_image)

            coords = ski.feature.peak_local_max(distance, 
                                                min_distance = min_distance,
                                                labels = input_image)

            mask = np.zeros(distance.shape, dtype=bool)
            
            # adds local max coords measured above to image array mask
            mask[tuple(coords.T)] = True

            # uses label to give each non-adjacent coordinate a different value
            markers = ski.morphology.label(mask, connectivity = 1)

            # labels each segmented region with a different value.
            # ensures labels aren't repeated by multiplying both labelled values
            input_labelled = ski.morphology.label(input_image, connectivity=1)
            mask_labelled = mask * input_labelled

            # gets a list of the unique values (essentially a list of the values of each segmented region) where area of that region > 1
            unique_values = np.unique(mask_labelled[mask_labelled.nonzero()], return_counts = True)
            split_labels = unique_values[0][unique_values[1] > 1]

            # gets properties from original image of each segmented area
            label_properties = ski.measure.regionprops(input_labelled, intensity_image = intensity_image)
            labels_for_watershed = np.zeros(input_image.shape, dtype=bool)

            for i in range(np.count_nonzero(split_labels)):
                # calculates circularity for each labelled region
                # dimension circularity is 4*pi*area/perimeter^2. For a perfect circle this should give 1. As perimeter increases with respect to area circularity will decrease.
                dimension_circularity = (4 * 3.1415926535 * label_properties[split_labels[i]-1].area) / (label_properties[split_labels[i] - 1].perimeter ** 2)
                # uses calculations from label_properties or circularity to remove regions that don't match threshold values on these parameters
                if (label_properties[split_labels[i] - 1].solidity < min_solidity or 
                        dimension_circularity < min_ratio_circularity or 
                        label_properties[split_labels[i]-1].area_convex > max_nuclear_area) and \
                            label_properties[split_labels[i]-1].intensity_mean > min_intensity:
                    
                    #adds labels of acceptable regions to list for further processing
                    labels_for_watershed = labels_for_watershed + (input_labelled == split_labels[i])

            #watersheds using distance and markers previously calculated, only for labels filtered above
            watershed = ski.segmentation.watershed(-distance, markers, mask = labels_for_watershed, connectivity = 1, watershed_line = True)
            
            #removes original labels that have been watershed from labelled input image
            input_labelled = np.logical_xor(input_labelled, labels_for_watershed) * input_labelled

            #combines unwatershed and watershed labels
            input_labelled = input_labelled+watershed

            #clears labels and relabels to remove duplicates
            OutputLabels = ski.morphology.label(np.logical_and(input_labelled, 1), connectivity = 1)

            return OutputLabels
        def count_labels(labelled_image):
            # returns array of length n_slices with maximum label value in each slice
            output = np.zeros((self.n_slices))
            
            for i in range(self.n_slices):
                output[i] = np.max(labelled_image[i])

            return output
        def track_labels(input_image1, input_image2, min_overlap_size, min_object_size):
            # makes sure overlapping regions from stack to stack have the same labels so they can be tracked through the slices
            # works similarly to stack_segment by finding overlaps between the two slices and watershedding
            overlap = np.logical_and(input_image1, input_image2)
            overlap = ski.morphology.remove_small_objects(ski.morphology.label(overlap, connectivity = 1),max_size = min_overlap_size)
            overlap = np.logical_and(overlap, 1) * input_image1

            n = np.max(input_image1)

            overlapping = ski.segmentation.watershed(input_image2, markers = overlap, mask = input_image2, watershed_line = True)
            unique = np.logical_xor(overlapping, input_image2)
            unique = ski.morphology.label(unique, connectivity = 1)
            unique = ski.morphology.remove_small_objects(unique, max_size = min_object_size)
            unique[np.where(unique != 0)] += n

            output_image = overlapping + unique
            return output_image   
        
        # Parameter calculation
        # Use otsu threshold on max projected image to calculate intensity limits used for distance semgnetation
        # multipliers used based on experimentation with relevant image type to find best parameters for segmentation
        maxproject = np.max(self.input_image[:,settings.channels["dapi_channel"] - 1], axis=0)
        high_thresh = round(ski.filters.threshold_otsu(maxproject) * settings.segmentation["high_thresh_multiplier"], 1)
        low_thresh = round(ski.filters.threshold_otsu(maxproject) * settings.segmentation["low_thresh_multiplier"], 1)
        min_intensity = round(ski.filters.threshold_otsu(maxproject) * settings.segmentation["min_intensity_multiplier"], 1)

        blurred_input = np.zeros((self.n_slices, self.height, self.width), dtype = np.int32)

        # 2D Segmentation
        # applies various stages of segmentation as defined by settings.
        # usually, this involves: 
        #       1. gaussian blur,
        #       2. segmenting foreground regions (region_segment) by edge detection followed by watershedding
        #       3. further segment foreground regions into separate regions using distance transform (distance segment)
        #       4. completes segmentation by relabelling after erosion of existing regions (to introduce small gap between regions)
        for i in range(self.n_slices):

            blurred_input[i] = ndimage.gaussian_filter(self.input_image[i][settings.channels["dapi_channel"] - 1], sigma = settings.segmentation["segment_sigma"])

            if settings.segmentation["region_segment"] == True:
                self.after_region[i] = region_segment(input_image = blurred_input[i], 
                                                high = high_thresh,
                                                low = low_thresh)

            else:
                self.after_region[i] = blurred_input[i]

            if settings.segmentation["distance_segment"] == True:
                self.after_distance[i] = distance_segment(input_image = self.after_region[i],
                                                            intensity_image = blurred_input[i],
                                                            min_distance = settings.segmentation["min_thresh_distance"],
                                                            min_solidity = settings.segmentation["min_solidity"],
                                                            max_nuclear_area = settings.segmentation["max_nuclear_area"],
                                                            min_ratio_circularity = settings.segmentation["min_ratio_circularity"]) 
            else:
                self.after_distance[i] = self.after_region[i]
            
            self.after_stack[i] = ski.morphology.label(ndimage.binary_erosion(self.after_distance[i], iterations = 2),connectivity = 1)
            print("2D Segmented " + str(i + 1) + "/" + str(self.n_slices))
        
        # 3D segmentation
        # carries out Stack Segmentation using 3D information from adjacent slices (separated in Z plane) to better separate
        # overlapping nuclei. Compares overlapping regions between neighbouring z slices; if two regions in one slice overlap with 1 region
        # in the next slice, the one region is separated into two regions by watershedding from that overlapping intersection.
        # this process is repeated ascending and descending through stacks until the number of regions is equal in both directions
        
        Start_Labels = count_labels(self.after_stack)
        End_Labels = np.zeros((self.n_slices))
        if settings.segmentation["stack_segment"] == True:

            print("Stack Segmented " + str(End_Labels.sum() - Start_Labels.sum()) + "/" + str(End_Labels.sum()))

            while np.array_equal(Start_Labels, End_Labels) == False:
                Start_Labels = count_labels(self.after_stack)
                for i in range(self.n_slices - 1):
                    self.after_stack[i] = stack_segment(input_image1 = self.after_stack[i], 
                                                input_image2 = self.after_stack[i+1], 
                                                intensity_image2 = blurred_input[i+1], 
                                                min_intensity = min_intensity, 
                                                min_overlap_size = settings.segmentation["min_overlap_size"], 
                                                min_object_size = settings.segmentation["min_object_size"])
                    
                for i in range(self.n_slices - 1, 0, -1):
                    self.after_stack[i] = stack_segment(input_image1 = self.after_stack[i],
                                                input_image2 = self.after_stack[i-1],
                                                intensity_image2 = blurred_input[i-1],
                                                min_intensity = min_intensity,
                                                min_overlap_size = settings.segmentation["min_overlap_size"],
                                                min_object_size = settings.segmentation["min_object_size"])
                    
                End_Labels = count_labels(self.after_stack)

                print("Stack Segmented " + str(End_Labels.sum() - Start_Labels.sum()) + "/" + str(End_Labels.sum()))

        for i in range(self.n_slices):
            self.after_stack[i] = ski.morphology.label(remove_dark_regions(self.after_stack[i], blurred_input[i], min_intensity), connectivity=1)
        
        # makes sure overlapping regions between slices have the same labels
        self.segmented_image = self.after_stack.copy()
        for i in range(self.n_slices - 1):
            self.segmented_image[i + 1] = track_labels(self.segmented_image[i], 
                                                   self.segmented_image[i + 1], 
                                                   settings.segmentation["min_overlap_size"], 
                                                   settings.segmentation["min_object_size"])
        
        self.n_labels = np.max(self.segmented_image)

        for i in range(self.n_slices):
            self.segmented_image[i] = ski.segmentation.expand_labels(self.segmented_image[i], distance = 2)

        print("Segmentation Completed\n")
        self.segmented = True

    def threshold(self):

        # Goes through each analysis, first gets thresholding values from z-projected stack (so consistent thresholding values can 
        # be used based on the brightest values for the whole stack)
        # Each slice is then thresholded based on the calculated value

        for i in range (settings.analysis["n_analyses"]):
            self.analyses.append(self.AnalysisData(self, i))

        threshold_methods = {"Li": ski.filters.threshold_li, 
                             "Isodata": ski.filters.threshold_isodata,
                             "Mean": ski.filters.threshold_mean, 
                             "Minimum": ski.filters.threshold_minimum,
                             "Triangle": ski.filters.threshold_triangle,
                             "Otsu": ski.filters.threshold_otsu,
                             "Yen": ski.filters.threshold_yen }

        for analysis in self.analyses:
            print("Analysing", analysis.name,
                "in channel", analysis.channel + 1,
                "(of", str(settings.analysis["n_analyses"]) + ")",
                "with sigma of", analysis.sigma,
                "and", analysis.threshold_method,
                "thresholding gives", end = " ")
            
            if analysis.threshold_method != "None":
                maxproject = np.max(self.input_image[:,analysis.channel], axis=0)

                if analysis.background_subtract == 1:
                    background = ski.restoration.rolling_ball(maxproject, radius = analysis.background_radius)
                    maxproject = (maxproject - background)
                
                if analysis.sigma > 0:
                    maxproject = ndimage.gaussian_filter(maxproject, analysis.sigma)

                threshold = threshold_methods[analysis.threshold_method](maxproject)
            
            else:
                threshold = 0
           
            print(threshold)

            for j in range(self.n_slices):

                if analysis.background_subtract == 1:
                    background = ski.restoration.rolling_ball(self.input_image[j][analysis.channel], radius = analysis.background_radius)
                    analysis.thresholded_image[j] = (self.input_image[j][analysis.channel] - background)
                else:
                    analysis.thresholded_image[j] = self.input_image[j][analysis.channel]


                if analysis.sigma > 0:
                    analysis.thresholded_image[j] = ndimage.gaussian_filter(
                                                        analysis.thresholded_image[j], 
                                                        analysis.sigma)
    
                if analysis.threshold_method != "None":
                    analysis.thresholded_image[j] = analysis.thresholded_image[j] > threshold
                
                if analysis.erode > 0:
                    for k in range(analysis.erode):
                        analysis.thresholded_image[j] = ski.morphology.erosion(analysis.thresholded_image[j])
        self.analysed = True
        print("Thresholding Completed\n")

    def quantify_threshold(self):
        # for each analysis, goes through each slice for each labelled region and looks for maximum area, maximum 
        # intensity of thresholded image and, if absolute image intensity is being measured, the maximum intensity from the input image
        self.label_area = np.zeros((self.n_labels + 1), dtype = np.float32)
        for analysis in self.analyses:
            analysis.max_threshold_intensity = np.zeros((self.n_labels + 1), dtype = np.float32)
            analysis.max_absolute_intensity = np.zeros((self.n_labels + 1), dtype = np.float32)

            for i in range (self.n_slices):
                properties = ski.measure.regionprops(label_image = self.segmented_image[i], 
                                                        intensity_image = analysis.thresholded_image[i])
                
                for prop in properties:
                    n = prop.label
                    if prop.area > self.label_area[n]: 
                        self.label_area[n] = prop.area
                    if prop.intensity_mean > analysis.max_threshold_intensity[n]: 
                        analysis.max_threshold_intensity[n] = prop.intensity_mean

                if settings.analysis["measure_intensity"] == True and analysis.name == settings.analysis["intensity_channel"]:
                    properties = ski.measure.regionprops(label_image = self.segmented_image[i],
                                                        intensity_image = self.input_image[i][analysis.channel])
                    for prop in properties:
                        n = prop.label
                        if prop.intensity_mean > analysis.max_absolute_intensity[n]: 
                            analysis.max_absolute_intensity[n] = prop.intensity_mean

    def calculate_adjacency(self):

        adjacency_analysis = [name for name in settings.analysis["analysis_names"]].index(settings.adjacency["analysis_for_adjacency"])
        #set up list of lists for holding regions adjacent to each region
        adjacent_region_list = [[] for _ in range(self.n_labels + 1)]

        #define adjacency as array same size as number of regions, starting values of max cell radius
        self.analyses[adjacency_analysis].adjacency_value = np.full((self.n_labels + 1), settings.adjacency["adjacency_cells"], dtype=np.int32)
        self.adjacency_enlarged_segments = np.zeros((self.n_slices, self.height, self.width), dtype=np.int32)

        adjacency_values = self.analyses[adjacency_analysis].adjacency_value
        enlarged_segments = self.adjacency_enlarged_segments 
        
        #print("Adjacency analysis",settings.adjacency["adjacency_analysis"],"gives analysis number",adjacency_analysis)



        """THIS METHOD OF FINDING NEIGHBOURS IS FASTER FOR LOW NUMBERS OF LABELS BUT SLOWER FOR LARGER IMAGES WITH MORE LABELLED REGIONS"""
        # finds all neighbours of each labelled region. For each slice, enlarges labelled regions to fill gaps (gives enlarged)
        # loops through each region, gets that region alone, increases its size by 1 then logical_ands it to enlarged,
        # getting all neighbouring regions. Removes 0 and own label from list, then appends it to list of neighbours for that region.

        
        """buffer = 1
        for n, slice in enumerate(self.segmented_image):
            enlarged = ski.segmentation.expand_labels(label_image = slice,
                                                                    distance = settings.adjacency["adjacency_expansion_distance"]) 

            labels = np.unique(enlarged)
            enlarged_segments[n] = enlarged
            for label in labels:
                label_region = ski.segmentation.expand_labels((enlarged == label), buffer)
                neighbours = np.unique(np.logical_and(label_region,enlarged) * enlarged)
                neighbours = neighbours[(neighbours != label)][1:]
                adjacent_region_list[label] = np.unique(np.append(adjacent_region_list[label], [int(neighbour) for neighbour in neighbours])).astype(np.int32)"""

        """THIS IS SLOWER FOR SMALL NUMBERS OF LABELS (ski.graph.RAG IS FAIRLY SLOW) BUT FASTER FOR LARGE NUMBERS OF LABELS (LESS GOING ON IN LOOP OVER LABELS)"""
        #if data has been segmented, for each slice:
        #enlarge regions by expansion distance
        #use RAG graph to get data about regions
        #for each region that exists in current slice, get neighbours and append to list
        

        for i in range(self.n_slices):
            print("Measuring adjacency slice", i + 1)
            enlarged_segments[i] = ski.segmentation.expand_labels(label_image = self.segmented_image[i],
                                                                            distance = settings.adjacency["adjacency_expansion_distance"])   
               
            graph = ski.graph.RAG(enlarged_segments[i], connectivity = 2)

            for segment in np.unique(enlarged_segments[i]):
                for adjacent_segment in list(graph.neighbors(segment)):
                    adjacent_region_list[segment].append(adjacent_segment)

        #remove non-unique regions and region 0 (background) from all adjacency lists
        for i in range(self.n_labels + 1):
            adjacent_region_list[i] = np.unique(adjacent_region_list[i])
            adjacent_region_list[i] = np.delete(adjacent_region_list[i], np.where(adjacent_region_list[i] == 0))

        # go through each region - if the value of the channel of interest is above threshold, give adjaceny of 0
        # (for 0 cells to GFP) - if not, adds region number to list of remaining regions to test

        remaining_regions = set(range(1, self.n_labels))
        for region in remaining_regions.copy():
            if self.analyses[adjacency_analysis].max_threshold_intensity[region] > settings.adjacency["adjacency_threshold"]:
                adjacency_values[region] = 0
                remaining_regions.remove(region)
        
        # goes through each adjacency value from 0 to self.adjacency_cells. For each value, goes through all remaining unlablled
        # regions and, for each region, checks their neghbours to see if they equal the current adjaceny value. If they do, assign
        # the currently tested region an adjacency value 1 higher.

        for current_value in range(settings.adjacency["adjacency_cells"] - 1):
            for region in remaining_regions.copy():
                for neighbour in adjacent_region_list[region]:
                    if adjacency_values[neighbour] == current_value:
                        adjacency_values[region] = current_value + 1
                        remaining_regions.remove(region)
                        break
        
        #print(*[(n, int(item)) for (n, item) in enumerate(adjacency_values)],sep = "\n") 

        self.adjacency_calculated = True
        
        print("Adjacency Completed\n")
        
    def analyse(self):
        self.analyses = []
        for i in range (settings.analysis["n_analyses"]):
            self.analyses.append(self.AnalysisData(self, i))
        self.threshold()
        if self.n_labels == 0:
            print("Segmentation required to quantify regional thresholds")
        else:
            self.quantify_threshold()

    def export_output(self, heading, file_name = "default", prefix = ""):
            

        if file_name == "default":
            export_file_name, _ = os.path.splitext(self.opened_image.filename)
            export_file_name += ".txt"
        else:
            export_file_name = file_name

        output_file = open(export_file_name, "a")

        if heading == True:
            headings = ["Cell",
                        "Area",
                        ",".join([name for name in settings.analysis["analysis_names"]]),]
            if settings.analysis["measure_intensity"]: headings.append(settings.analysis["intensity_channel"] + "_intensity")
            if settings.adjacency["measure_adjacency"]: headings.append(settings.adjacency["adjacency_analysis"] + "_adjacency")
            output_file.write(",".join(headings) + "\n")

        for i in range(1, self.n_labels + 1):
            output_file.write(str(prefix) + str(i) + ",")
            try:
                output_file.write(str(self.label_area[i]) + ",")
            except (NameError, TypeError):
                output_file.write("0,")
            
            for analysis in self.analyses:
                try:
                    output_file.write(str(analysis.max_threshold_intensity[i]) + ",")
                except (AttributeError, IndexError):
                    output_file.write("0,")

            for analysis in self.analyses:
                if analysis.name == settings.analysis["intensity_channel"]:
                    try:
                        output_file.write(str(analysis.max_absolute_intensity[i]) + ",")
                    except (AttributeError, IndexError):
                        output_file.write("0,")
            
            for analysis in self.analyses:
                if analysis.name == settings.adjacency["analysis_for_adjacency"]:
                    try:
                        analysis.adjacency_value
                        output_file.write(str(analysis.adjacency_value[i]))
                    except (IndexError, TypeError):
                        output_file.write("0,")
            
            output_file.write("\n")


        output_file.close()
        print("Save Completed")     
    
    def batch(self, path):
        global nSlices
        global nChannels
        global Height
        global Width

        #app.quit()
        file_name = os.path.join(path,"batch.txt")
        print(file_name)

        file_list = []
        file_number = 0

        for (dirpath, dirnames, filenames) in os.walk(path):
            for file in filenames:
                if file[len(file)-3:]=="tif":
                    file_list.append(os.path.join(dirpath, file).replace("\\","/"))

        for file in file_list:
            file_number += 1

            # uses folder structure for labelling outputted images. First removes preceeding path from chosen batch folder
            post_path = file.replace(path + "/","")

            #replaces any spaces in file name with commas for separation
            post_path = post_path.replace(" ",",")

            #splits remaining path by directory structure (use directory structure to separate genotypes, dates etc)
            processed_file_name = (','.join(post_path.split("/")[-1:]))

            #removes .tif from filename
            processed_file_name = processed_file_name[:processed_file_name.find('.')]
            file_path = ','.join(post_path.split("/")[:-1])

            print(file +" ("+str(file_number)+"/"+str(len(file_list))+")")


            self.open_image(file)
            self.segment()
            self.analyse()
            if settings.adjacency["measure_adjacency"] == True: self.calculate_adjacency()

            prefix = file_path + "," + processed_file_name + ","
            if file_number == 1:
                self.export_output(heading = True, file_name = file_name, prefix = prefix)
            else:
                self.export_output(heading = False, file_name = file_name, prefix = prefix)


        settings.export_settings(os.path.join(path,"settings.txt"))
        

        print("Batch Completed")

    



