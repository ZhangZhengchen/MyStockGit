'''
Created on 2017 7 29

@author: zhengchenzhang
'''
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import tensorflow as tf
from PIL import Image
import numpy as np
import math
import argparse
import sys
import tempfile
import os

batch_size=30
Img_Width=1200
Img_Height=800
ClassNumber = 2
TrainDataNumber = 0
LearningRate = 0.001
import random

def ReadData(ImageDir):
    '''
    '''
    #Read Images
    ImageList = []
    TxtList = []
    for root,subdir,files in os.walk(ImageDir):
        for afile in files:
            #print(afile[-3:])
            if afile[-3:]=='txt':
                TxtList.append(os.path.join(root,afile))
            elif afile[-3:]=='png':
                ImageList.append(os.path.join(root,afile))
    #print(ImageList)
    label_list = []
    image_list = []
    for anitem in TxtList:
        f = open(anitem)
        alllines = f.readlines()
        f.close()
        for aline in alllines:
            temp = aline.strip().split(':::')
            imgfilename = os.path.join(ImageDir,temp[0]+'.png')
            #print(imgfilename)
            if not imgfilename in ImageList:
                continue
            else:
                image_list.append(imgfilename)
                label_list.append(int(temp[1]))
    #print(image_list)
    label_list = tf.one_hot(indices=label_list,depth=ClassNumber)
    
    images = tf.convert_to_tensor(image_list, dtype=tf.string)
    labels = tf.convert_to_tensor(label_list, dtype=tf.float32)
    # Makes an input queue
    input_queue = tf.train.slice_input_producer([images, labels],shuffle=True)
    def read_images_from_disk(input_queue):
        """Consumes a single filename and label as a ' '-delimited string.
        Args:
          filename_and_label_tensor: A scalar string tensor.
        Returns:
          Two tensors: the decoded image, and the string label.
        """
        label = input_queue[1]
        file_contents = tf.read_file(input_queue[0])
        example = tf.image.decode_png(file_contents, channels=1)
        example = tf.image.resize_image_with_crop_or_pad(example,80,120)
        example = tf.cast(example,dtype=tf.float32)
        print(example.shape)
        print(len(image_list))
        #example = tf.reshape(example, [len(image_list),Img_Height,Img_Width, 1])
        return example, label
    image, label = read_images_from_disk(input_queue)
    batch = tf.train.batch([image,label],batch_size=batch_size,dynamic_pad=True)
    '''image = []
    for anitem in image_list:
        file_contents = tf.read_file(anitem)
        example = tf.image.decode_png(file_contents)
        example = tf.image.resize_image_with_crop_or_pad(example,80,120)
        example = tf.cast(example,dtype=tf.float32)
        #print(example.shape)
        image.append(example)
    images = tf.convert_to_tensor(image, dtype=tf.float32)'''
    #print(images.shape)
    # Optional Image and Label Batching
    return [batch[0],batch[1],len(image_list)]


# The MNIST dataset has 10 classes, representing the digits 0 through 9.
#NUM_CLASSES = 10

# The MNIST images are always 28x28 pixels.
#IMAGE_WIDTH = 1200
#IMAGE_HEIGHT = 800
#IMAGE_PIXELS = IMAGE_WIDTH * IMAGE_HEIGHT
class MyGraph:
    def __init__(self, DataDir, keep_prob=0.5,is_training=True):
        self.graph = tf.Graph()
        with self.graph.as_default():
            self.TrainData = ReadData(TrainDir)
            print(self.TrainData[1][0])
            #self.TrainData[0] = tf.cast(self.TrainData[0],dtype=tf.float32)
            self.y = self.TrainData[1]
            self.x_image = tf.reshape(self.TrainData[0], [-1, 80, 120, 1])
            
            # First convolutional layer - maps one grayscale image to 32 feature maps.
            self.W_conv1 = self.weight_variable([5, 7, 1, 32])
            self.b_conv1 = self.bias_variable([32])
            self.h_conv1 = tf.nn.relu(self.conv2d(self.x_image, self.W_conv1) + self.b_conv1)
            
            # Pooling layer - downsamples by 2X.
            self.h_pool1 = self.max_pool_2x2(self.h_conv1)
            
            # Second convolutional layer -- maps 32 feature maps to 64.
            self.W_conv2 = self.weight_variable([5, 7, 32, 64])
            self.b_conv2 = self.bias_variable([64])
            self.h_conv2 = tf.nn.relu(self.conv2d(self.h_pool1, self.W_conv2) + self.b_conv2)
            
            # Second pooling layer.
            self.h_pool2 = self.max_pool_2x2(self.h_conv2)
            
            #print(self.h_pool2.shape)
            # Fully connected layer 1 -- after 2 round of downsampling, our 28x28 image
            # is down to 7x7x64 feature maps -- maps this to 1024 features.
            self.W_fc1 = self.weight_variable([20 * 30 * 64, 256])
            self.b_fc1 = self.bias_variable([256])
            
            self.h_pool2_flat = tf.reshape(self.h_pool2, [-1, 20*30*64])
            self.h_fc1 = tf.nn.relu(tf.matmul(self.h_pool2_flat, self.W_fc1) + self.b_fc1)
            
            # Dropout - controls the complexity of the model, prevents co-adaptation of
            # features.
            self.keep_prob = tf.convert_to_tensor(keep_prob, dtype=tf.float32)
            self.h_fc1_drop = tf.nn.dropout(self.h_fc1, self.keep_prob)
            
            # Map the 1024 features to 10 classes, one for each digit
            self.W_fc2 = self.weight_variable([256, ClassNumber])
            self.b_fc2 = self.bias_variable([ClassNumber])
            
            self.y_conv = tf.matmul(self.h_fc1_drop, self.W_fc2) + self.b_fc2
            print(self.y)
            print(self.y_conv)
            #self.cross_entropy = tf.nn.softmax_cross_entropy_with_logits(labels=self.y,logits=self.y_conv)
            #self.cross_entropy = tf.reduce_mean(self.cross_entropy)
            self.loss = tf.squared_difference(self.y_conv, self.y)
            self.loss_sum = tf.reduce_sum(self.loss)
            # Training Scheme
            self.global_step = tf.Variable(0, name='global_step', trainable=False)
            self.optimizer = tf.train.AdamOptimizer(learning_rate=LearningRate)
            self.train_op = self.optimizer.minimize(self.loss_sum, global_step=self.global_step)
            
            tf.summary.scalar('loss', self.loss_sum)
            self.merged = tf.summary.merge_all()
            
    def GetBatch(self):
        self.batch = tf.train.batch(self.TrainData,batch_size=batch_size,shapes=[(None,80,120,None),(None,2,1)],dynamic_pad=True)
    
    def GetImageFromABatch(self,i):
        self.x_image = tf.reshape(self.batch[0][i], [-1, 800, 1200, 1])
        self.y = self.batch[1][i]


    def conv2d(self,x, W):
        """conv2d returns a 2d convolution layer with full stride."""
        return tf.nn.conv2d(x, W, strides=[1, 1, 1, 1], padding='SAME')
    
    
    def max_pool_2x2(self,x):
        """max_pool_2x2 downsamples a feature map by 2X."""
        return tf.nn.max_pool(x, ksize=[1, 2, 2, 1],
                            strides=[1, 2, 2, 1], padding='SAME')
    
    
    def weight_variable(self,shape):
        """weight_variable generates a weight variable of a given shape."""
        initial = tf.truncated_normal(shape, stddev=0.1)
        return tf.Variable(initial)
    
    
    def bias_variable(self,shape):
        """bias_variable generates a bias variable of a given shape."""
        initial = tf.constant(0.1, shape=shape)
        return tf.Variable(initial)

def main(TrainDir,TestDir,LogDir):
    g = MyGraph(TestDir)
    lognumber = random.randint(1,1000000)
    LogDir = os.path.join(LogDir,str(lognumber))
    if os.path.isdir(LogDir):
        print('This log number generated before. Try again')
        return
    else:
        os.mkdir(LogDir)
    with g.graph.as_default():
        sv = tf.train.Supervisor(logdir=LogDir,save_model_secs=0)
        with sv.managed_session() as sess:
            for epoch in range(1, 2000): 
                if sv.should_stop(): break
                #g.GetBatch()
                for step in range(batch_size):
                    print('step=='+str(step))
                    #g.GetImageFromABatch(step)
                    sess.run(g.train_op)
                # Write checkpoint files at every epoch
                gs = sess.run(g.global_step) 
                sv.saver.save(sess, LogDir +'/model_epoch_%02d_gs_%d' % (epoch, gs))

if __name__ == '__main__':
    #parser = argparse.ArgumentParser()
    #parser.add_argument('--data_dir', type=str,
    #                    default='/tmp/tensorflow/mnist/input_data',
    #                    help='Directory for storing input data')
    #FLAGS, unparsed = parser.parse_known_args()
    #tf.app.run(main=main, argv=[sys.argv[0]] + unparsed)
    
    TrainDir = './data/Stock/Train'
    TestDir = './data/Stock/Test'
    LogDir = './data/Stock/Log'
    main(TrainDir, TestDir, LogDir)