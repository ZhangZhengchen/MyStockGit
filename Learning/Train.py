'''
Created on 2017 7 29

@author: zhengchenzhang
'''
import tensorflow as tf
from PIL import Image
import numpy as np

filename_queue = tf.train.string_input_producer(['./data/AAPL_2015-11-30.png']) #  list of files to read
reader = tf.WholeFileReader()
key, value = reader.read(filename_queue)

my_img = tf.image.decode_png(value) 
init_op = tf.global_variables_initializer()
with tf.Session() as sess:
    sess.run(init_op)
    coord = tf.train.Coordinator()
    threads = tf.train.start_queue_runners(coord=coord)
    for i in range(1): #length of your filename list
        image = my_img.eval() #here is your image Tensor :) 
    print(image.shape)
    Image.fromarray(np.asarray(image)).show()
    coord.request_stop()
    coord.join(threads)