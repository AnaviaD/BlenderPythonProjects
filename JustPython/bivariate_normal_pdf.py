import numpy as np

def bivariate_normal_pdf(domain, mean, variance):
    X = np.array([[-mean+x*variance for x in range(int((-domain+mean)//variance), 
                                                   int((domain+mean)//variance)+1)] 
                  for _ in range(int((-domain+mean)//variance), 
                                 int((domain+mean)//variance)+1)])
    Y = X.T
    R = np.sqrt(X**2 + Y**2)
    Z = ((1. / np.sqrt(2 * np.pi)) * 
            np.exp(-.5*R**2))
    return  X+mean, Y+mean, Z