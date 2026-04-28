Introduction
------------

The aim of this software is to segment DAPI stained nuclei in Z-stack images from confocal microscopes and to then measure absolute and thresholded intensity of channels of interest within those nuclei.

The input should be an 8-bit tif (16- or 24- bit images may work, but may not) with DAPI in one channel (the software may work for other nuclear markers, depending on the settings used).

The output is a list of segmented nuclei, along with their maximum area and maximum thresholded and absolute intensities in other channels in a comma-separated text file. Optionally, the minimum distance of each nuclei from a nucleus positive for a particular channel can also be output.

Requirements
------------

To use the software, the following libraries must be installed in Python:

Matplotlib

NumPy

scikit-image (version 0.26.0)

SciPy (version 1.17.1)

PyQt6

cmap (https://cmap-docs.readthedocs.io/en/latest/)

Using the software UI
---------------------

Download all files in the repository into the same folder and run Main.py.

This will open the UI with an example image.

The scroll bar at the bottom of the window lets you move through Z-Stacks.

The settings on the left side of the window let you adjust LUTs and channel visability. There are also options for outlining and numbering nuclei once they have been segmented.

The settings on the right side change the parameters for segmentation, thresholding and adjacency calculation.

The contents of the two image views can be changed in the bottom right. This allows you to view segmentation output as well as intermediate stages, thresholding output and adjacency output. The views can be locked, which is useful for comparing the same outputs with different settings.

Opening an image
----------------
To open your own image, click File/Open Image and chose the image location. 

A second window will now open, asking for the number of _channels_ and _analyses_.

The channels from your input image must be correct for proper viewing of images (depending on the set up for your tif file, you may find that even with the correct channels the views don't seem to work correctly. If this is the case, try uncommenting line 73 in image.py and commenting line 74).

The analyses define how the software evaluates your images. Typically, there would be C - 1 analyses, where C is the number of channels (as analyses cannot be carried out on the channel with a nuclear marker). However, if you're not interested in a particular channel you can reduce the number of analyses further. You can also carry out more than one analyses on the same channel, for example, where you wanted to measure intensity with two different thresholding methods to capture different properties of that channel.

The number of channels and analyses can only be changed when opening a new image.

Finally, chose a channel for your nuclear marker to the left side of the window.

Settings
--------
Where settings have been changed, they can be imported or exported using the Settings menu.

They can also be reset to the default settings, which can be changed by overwriting the default_settings.txt file.

If the software crashes for any reason, the current settings will be saved in autosave.txt

Settings can be changed manually, but any changes to the names of settings, rather than their values, will result in that setting file failing to load.

Segmentation
------------
Nuclei are segmented in three steps:

1. Region segmentation using sobel edge detection and watershedding. This includes options for low and high threshold. These act as multipliers to the overall image intensity - any image pixel with an intensity below low threshold * average intensity are considered background for watershedding, any image pixel with an intensity over high threshold * average intensity are considered foreground (a nucleus).

2. Distance segmentation to split up regions, using a distance transform then finding local maxima and watershedding (the minimum distance between maxima is a key property defining over- and under-segmentation of images).

3. Stack segmentation. This loops up and down the slices looking for segmented regions in one slice that represents multiple segmented regions in neighbouring slices. The key setting here is minimum overlap size. If the area of overlap of two regions in neighbouring slices is less than this value, that overlap will not be used to split up those regions.

Other settings for segmentation define properties for an object to be considered a nucleus. Objects that are smaller (or larger), less circular, less solid (a measure of concavity of the object), less bright (as a multiple of average image intensity) are not considered to be nuclei.

Thresholding
------------
The threshold function binarises images using a chosen auto-thresholding techniques for each analyis (set up in the Threshold tab).

For each analysis, you can choose whether a background subtraction is performed (and its radius), whether a guassian filter is applied (and its radius), whether any erosion is applied to the final thresholded image (to counteract the effects of gaussian filter) and an auto-thresholding method.

Available methods of auto-thresholding are:
    Isodata
    Li
    Mean
    Minimum
    Otsu
    Triangle
    Yen    

The maximum intensity of the thresholded image in each segmented region (comparing across slices) is then saved for export, along with the maximum area of that region and the maximum intensity of the unprocessed image.

Adjacency
---------
The adjacency functions allows you to quantify the minimum distance of each nucleus from a nucleus positive for a marker in a given channel. It does this by enlarging each segment to fill gaps, finding the neighbour(s) of each nucleus then looping through each label to calculate the minimum distance from a positive cell.

Settings are the analysis of interest, the minimum thresholded intensity a segment should be to be considered positive for this analysis, the maximum number of nuclei distance to calculate and how much to enlarge each segment.


Batch Processing
----------------
Once the correct settings have been chosen, batch processing of large numbers of images is possible.

To do this, choose 'Batch Processing' from the file menu and select a folder. The folder structure will be maintained in the output file, and file names will be split at spaces. 

For example, for the file "Plate1 Image2" in the sub-folder "260521\RasPositive", the output data for each nucleus will be preceded by "260521,RasPositive,Plate1,Image2".



