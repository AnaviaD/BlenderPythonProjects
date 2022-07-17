import math
import numpy as np

def py_bivariate_normal_pdf(domain, mean, variance):
    X = [[-mean+x*variance for x in range(int((-domain+mean)//variance), 
                                                   int((domain+mean)//variance)+1)] 
                  for _ in range(int((-domain+mean)//variance), 
                                 int((domain+mean)//variance)+1)]
    Y = [*map(list, zip(*X))]
    R = [[math.sqrt(a**2 + b**2) for a, b in zip(c, d)] for c, d in zip(X, Y)]
    Z = [[(1. / math.sqrt(2 * math.pi)) * math.exp(-.5*r**2) for r in r_sub] for r_sub in R]
    X = [*map(lambda a: [b+mean for b in a], X)]
    Y = [*map(lambda a: [b+mean for b in a], Y)]
    return  np.array(X), np.array(Y), np.array(Z)