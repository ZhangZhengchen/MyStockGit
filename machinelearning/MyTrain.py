'''
Created on 2017 7 29

@author: zhengchenzhang
'''
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import tensorflow as tf
import numpy as np
import os
import imageio
from sklearn import preprocessing
import operator

Img_Width=600
Img_Height=400
Img_Channel = 4
TagDimension = 1
TrainDataNumber = 0
LearningRate = 1e-4

def ReadData(DataDir):
    '''
    @param DataDir: include images and label files
    '''
    ImageList = []
    TxtList = []
    for root,subdir,files in os.walk(DataDir):
        for afile in files:
            #print(afile[-3:])
            if afile[-3:]=='txt':
                TxtList.append(os.path.join(root,afile))
            elif afile[-3:]=='png':
                ImageList.append(os.path.join(root,afile))
    
    Features = []
    Labels = []
    for anitem in TxtList:
        f = open(anitem)
        alllines = f.readlines()
        f.close()
        for aline in alllines:
            temp = aline.strip().split(':::')
            imgfilename = os.path.join(DataDir,temp[0]+'.png')
            #print(imgfilename)
            if not imgfilename in ImageList:
                continue
            else:
                aimagefeature = imageio.imread(imgfilename)
                #print(aimagefeature.shape)
                alabel = [float(temp[2])]
                Features.append(np.array(aimagefeature))
                Labels.append(alabel)
    return np.array(Features),np.array(Labels)

beTrain = False
beTest = False
bePredict = True
beLoad = True

if beTrain:
    TrainFeatures,TrainLabels = ReadData('./data/Stock/train')
    TrainLabels = preprocessing.scale(TrainLabels)
    print(np.shape(TrainFeatures))
    print(np.shape(TrainLabels))
    print(TrainLabels[0:30])

def GetBatch(batch_size):
    index_array = np.arange(len(TrainLabels))
    np.random.shuffle(index_array)
    Features = []
    Labels = []
    i = 0
    #print(index_array[0:10])
    while len(Features)<batch_size:
        Features.append(TrainFeatures[index_array[i]])
        Labels.append(TrainLabels[index_array[i]])
        i+=1
    return [np.array(Features),np.array(Labels)]

# The MNIST dataset has 10 classes, representing the digits 0 through 9.
#NUM_CLASSES = 10

# The MNIST images are always 28x28 pixels.
#IMAGE_WIDTH = 1200
#IMAGE_HEIGHT = 800
#IMAGE_PIXELS = IMAGE_WIDTH * IMAGE_HEIGHT
class MyGraph:
    def __init__(self, keep_prob=0.5,is_training=True):
        self.graph = tf.Graph()
        with self.graph.as_default():
            
            self.x_image = tf.placeholder(tf.float32,[None,Img_Height,Img_Width,Img_Channel])
            self.y = tf.placeholder(tf.float32,[None,TagDimension])

            
            # First convolutional layer - maps one grayscale image to 32 feature maps.
            self.W_conv1 = self.weight_variable([20, 100, Img_Channel, 8])
            self.b_conv1 = self.bias_variable([8])
            self.h_conv1 = tf.nn.relu(self.conv2d(self.x_image, self.W_conv1) + self.b_conv1)
            print(self.h_conv1)
            # Pooling layer - downsamples by 2X.
            self.h_pool1 = self.max_pool_2x2(self.h_conv1)
            print(self.h_pool1)
            # Second convolutional layer -- maps 32 feature maps to 64.
            self.W_conv2 = self.weight_variable([40, 40, 8, 16])
            self.b_conv2 = self.bias_variable([16])
            self.h_conv2 = tf.nn.relu(self.conv2d(self.h_pool1, self.W_conv2) + self.b_conv2)
            print(self.h_conv2)
            # Second pooling layer.
            self.h_pool2 = self.max_pool_5x5(self.h_conv2)
            print(self.h_pool2)
            #print(self.h_pool2.shape)
            # Fully connected layer 1 -- after 2 round of downsampling, our 28x28 image
            # is down to 7x7x64 feature maps -- maps this to 1024 features.
            self.W_fc1 = self.weight_variable([40 * 60 * 16, 512])
            self.b_fc1 = self.bias_variable([512])
            
            self.h_pool2_flat = tf.reshape(self.h_pool2, [-1, 40*60*16])
            self.h_fc1 = tf.tanh(tf.matmul(self.h_pool2_flat, self.W_fc1) + self.b_fc1)
            print(self.h_fc1)
            # Dropout - controls the complexity of the model, prevents co-adaptation of
            # features.
            self.keep_prob = tf.convert_to_tensor(keep_prob, dtype=tf.float32)
            self.h_fc1_drop = tf.nn.dropout(self.h_fc1, self.keep_prob)
            print(self.h_fc1_drop)
            
            # Map the 1024 features to 10 classes, one for each digit
            self.W_fc2 = self.weight_variable([512, 10])
            self.b_fc2 = self.bias_variable([10])
            self.y_conv_1 = tf.matmul(self.h_fc1_drop, self.W_fc2) + self.b_fc2
            
            # Map the 1024 features to 10 classes, one for each digit
            self.W_fc3 = self.weight_variable([10, TagDimension])
            self.b_fc3 = self.bias_variable([TagDimension])
            
            self.y_conv = tf.matmul(self.y_conv_1, self.W_fc3) + self.b_fc3
            print(self.y)
            print(self.y_conv)
            self.y_final = tf.tanh(self.y_conv)
            #self.cross_entropy = tf.nn.softmax_cross_entropy_with_logits(labels=self.y,logits=self.y_conv)
            #self.cross_entropy = tf.reduce_mean(self.cross_entropy)
            self.loss = tf.squared_difference(self.y_final, self.y)
            print(self.loss)
            self.loss_sum = tf.reduce_sum(self.loss)
            print(self.loss_sum)
            # Training Scheme
            self.global_step = tf.Variable(0, name='global_step', trainable=False)
            self.optimizer = tf.train.AdamOptimizer(learning_rate=LearningRate)
            self.train_op = self.optimizer.minimize(self.loss_sum, global_step=self.global_step)
            
            #tf.summary.scalar('loss', self.loss_sum)
            #self.merged = tf.summary.merge_all()
            
    def conv2d(self,x, W):
        """conv2d returns a 2d convolution layer with full stride."""
        return tf.nn.conv2d(x, W, strides=[1, 1, 1, 1], padding='SAME')
    
    
    def max_pool_2x2(self,x):
        """max_pool_2x2 downsamples a feature map by 2X."""
        return tf.nn.max_pool(x, ksize=[1, 2, 2, 1],
                            strides=[1, 2, 2, 1], padding='SAME')
        
    def max_pool_4x4(self,x):
        """max_pool_4x4 downsamples a feature map by 4X."""
        return tf.nn.max_pool(x, ksize=[1, 4, 4, 1],
                            strides=[1, 4, 4, 1], padding='SAME')
        
    def max_pool_5x5(self,x):
        """max_pool_5x5 downsamples a feature map by 3X."""
        return tf.nn.max_pool(x, ksize=[1, 5, 5, 1],
                            strides=[1, 5, 5, 1], padding='SAME')
    
    
    def weight_variable(self,shape):
        """weight_variable generates a weight variable of a given shape."""
        initial = tf.truncated_normal(shape, stddev=0.1)
        return tf.Variable(initial)
    
    
    def bias_variable(self,shape):
        """bias_variable generates a bias variable of a given shape."""
        initial = tf.constant(0.1, shape=shape)
        return tf.Variable(initial)

def main(LogDir):
    batch_size = 16
    g = MyGraph()
    #lognumber = random.randint(1,1000000)
    #LogDir = os.path.join(LogDir,str(lognumber))
    #if os.path.isdir(LogDir):
    #    print('This log number generated before. Try again')
    #    return
    #else:
    #    os.mkdir(LogDir)
    with g.graph.as_default():
        config = tf.ConfigProto()
        config.gpu_options.allow_growth = True
        sess = tf.Session(config=config)
        sess.run(tf.global_variables_initializer())
        
        saver = tf.train.Saver()
        save_file = './tmp/cnn_model_'

        load_file = './tmp/cnn_model_2000'
        if beLoad:
            saver.restore(sess, load_file)
            
        if beTrain:   
            for i in range(4000):
                Features,Labels = GetBatch(batch_size)
                sess.run(g.train_op,feed_dict={g.x_image:Features,g.y:Labels})
                if i%50==0:
                    loss = sess.run(g.loss_sum,feed_dict={g.x_image:Features,g.y:Labels})
                    print("step %d, training accuracy %g"%((i),loss))
                if (i+1)%1000==0:
                    saver.save(sess, save_file+str(i+1))
            saver.save(sess,save_file+'final')
        if beTest:
            TestFeature,TestLabel = ReadData('./data/Stock/test')
            for i in range(len(TestFeature)):
                thisFeature = TestFeature[i]
                thisLabel = TestLabel[i]
                #print(np.shape(thisFeature),np.shape(thisLabel))
                pred_labels,accuracy = sess.run([g.y_conv,g.loss_sum],feed_dict={g.x_image:[thisFeature],g.y:[thisLabel]})
                print(pred_labels,thisLabel)
                if i>200:
                    break
        
        if bePredict:
            predictdir = './data/Stock/predict'
            TestFeature,TestLabel = ReadData(predictdir)
            TxtList = []
            for root,subdir,files in os.walk(predictdir):
                for afile in files:
                    #print(afile[-3:])
                    if afile[-3:]=='txt':
                        TxtList.append(os.path.join(root,afile))
            AllPredVal = {}
            for i in range(len(TestFeature)):
                thisFeature = TestFeature[i]
                thisLabel = TestLabel[i]
                #print(np.shape(thisFeature),np.shape(thisLabel))
                pred_labels,accuracy = sess.run([g.y_conv,g.loss_sum],feed_dict={g.x_image:[thisFeature],g.y:[thisLabel]})
                AllPredVal[TxtList[i]] = pred_labels[0][0]
            sorted_x = sorted(AllPredVal.items(), key=operator.itemgetter(1))
            print(sorted_x[0:10])
            print(sorted_x[-10:])
                
            
        '''sv = tf.train.Supervisor(logdir=LogDir,save_model_secs=0)
        with sv.managed_session() as sess:
            for epoch in range(1, 2000): 
                if sv.should_stop(): break
                #g.GetBatch()
                for step in range(batch_size):
                    print('step=='+str(step))
                    Features,Labels = GetBatch(batch_size)
                    print(type(Features),type(Labels))
                    sess.run(g.train_op,feed_dict={g.x_image:Features,g.y:Labels})
                # Write checkpoint files at every epoch
                gs = sess.run(g.global_step) 
                sv.saver.save(sess, LogDir +'/model_epoch_%02d_gs_%d' % (epoch, gs))'''

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
    main(LogDir)