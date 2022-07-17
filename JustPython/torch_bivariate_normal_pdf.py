import numpy as np
import torch

def torch_bivariate_normal_pdf(domain, mean, variance):
  X = torch.arange(-domain+mean, domain+mean, variance)
  Y = torch.arange(-domain+mean, domain+mean, variance)
  X, Y = torch.meshgrid(X, Y)
  R = torch.sqrt(X**2 + Y**2)
  Z = ((1. / np.sqrt(2 * np.pi)) * torch.exp(-.5*R**2))
  return X.numpy()+mean, Y.numpy()+mean, Z.numpy()