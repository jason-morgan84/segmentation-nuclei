#get N = sum of each histogram bin (should also equal number of pixels in image)
#n = number of histogram bins (255)

#for each grey level frequency fi, get pi = fi/N (i = 1 to 256)


#calculate cumulative probabilities for each potential threshold (t = 1-256) (or 0 - 255?) for foreground (F[t]) and background (B[t]):
# PB[t] = sum(pi[1 to t])
# PF[t] = sum(pi[t+1 to n])

# calculate entropy for foreground and background 
# EB[t] = - sum { (pi[i]/PB[i])*ln(pi[i]/PB[i])} where i = 1 to t
# EF[t] = - sum { (pi[i]/PF[i])*ln(pi[i]/PF[i])} where i = t + 1 to 256

# calculat total entropy 
# E[t] = EB[t] + EF[t]

# find the value of t with biggest E

import numpy as np

def MaxEntropy(image):

    N = 0
    n = 256

    PB = np.zeros(n)
    PF = np.zeros(n)

    EB = np.zeros(n)
    EF = np.zeros(n)

    E = np.zeros(n)

    t = 0

    histogram = np.histogram(image, bins = 256)

    for bin in histogram:
        N += bin

    

    return t