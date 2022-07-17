import numpy as np
import tensorflow as tf

def tf_bivariate_normal_pdf(domain, mean, variance):
  X = tf.range(start=-domain+mean, limit=domain+mean, delta=variance)
  Y = tf.range(start=-domain+mean, limit=domain+mean, delta=variance)
  X, Y = tf.meshgrid(X, Y)
  R    = tf.sqrt(X**2 + Y**2)
  Z    = ((1. / tf.sqrt(2 * np.pi)) * tf.exp(-.5*R**2))
  with tf.Session() as sess:
    X, Y, Z = sess.run([X, Y, Z])
  return X+mean, Y+mean, Z