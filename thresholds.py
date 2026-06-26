

import numpy as np
import math

def MaxEntropy(image):

    """A new method for gray-level picture thresholding using the entropy of the histogram N. Kapur, P.K. Sahoo, A.K.C. Wong"""
    #get N = sum of each histogram bin (should also equal number of pixels in image)
    #n = number of histogram bins (255)

    #for each grey level frequency fi, get pi = fi/N (i = 1 to 256)

    #calculate cumulative probabilities for each potential threshold (t = 1-256) (or 0 - 255?) for foreground (F[t]) and background (B[t]):
    # PB[t] = sum(pi[1 to t])
    # PF[t] = sum(pi[t+1 to n])

    # calculate entropy for foreground and background (only where there's data in the histogram to avoid divide by 0/natural log of 0)
    # EB[t] = - sum { (pi[i]/PB[t])*ln(pi[i]/PB[t])} where i = 1 to t
    # EF[t] = - sum { (pi[i]/PF[t])*ln(pi[i]/PF[t])} where i = t + 1 to 256

    # calculat total entropy 
    # E[t] = EB[t] + EF[t]

    # find the value of t with biggest E

    N = 0
    n = 256

    PI = np.zeros(n)

    PB = np.zeros(n)
    PF = np.zeros(n)

    EB = 0
    EF = 0

    E = 0

    threshold_bin = 0

    histogram, _ = np.histogram(image, bins = 256, range = (0, 256))

    N = histogram.sum()

    for t, bin in enumerate(histogram):
        PI[t] = bin/N

    PB[0] = PI[0]
    PF[0] = 1 - PB[0]


    for t in range(1, n):
        PB[t] = PB[t - 1] + PI[t]
        PF[t] = 1 - PB[t]

    for t in range(1, n):
        EB = 0
        for i in range (0, t):
            if histogram[i] != 0: EB += PI[i]/PB[t] * math.log(PI[i]/PB[t])
        EB = EB * -1

        EF = 0
        for i in range (t + 1, n):
            if histogram[i] != 0: EF += PI[i]/PF[t] * math.log(PI[i]/PF[t])
        EF = EF * -1

        if (EF + EB) > E:
            E = EF + EB
            threshold_bin = t

    return threshold_bin + 1