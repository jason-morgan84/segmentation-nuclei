Introduction
------------

The aim of this software is to segment DAPI stained nuclei in Z-stack images from confocal microscopes and to then measure absolute and thresholded intensity within those nuclei in channels of interest.

The input should be an 8-bit tif (16- or 24- bit images may work, but may not) with DAPI in one channel (the software may work for other nuclear markers, depending on the settings used).

The output is a list of segmented nuclei, along with their maximum area and maximum thresholded and absolute intensities in other channels in a comma-separated text file. Optionally, the minimum distance of each nuclei from a nucleus positive for a particular channel can also be output.

Once the correct settings have been chosen, batch processing of large numbers of images is possible, and the folder structure will be maintained in the output file. For example, for the file "Plate1 Image2" in the sub-folder "260521\RasPositive" will have the data for each nucleus preceded by "260521,RasPositive,Plate1,Image2".

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
