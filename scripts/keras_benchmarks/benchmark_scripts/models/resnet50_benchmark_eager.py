'''
Model constructed using keras/applications.

Benchmark a Resnet50 model.
'''

from __future__ import print_function

import keras
#from keras import applications
#from keras.utils import multi_gpu_model

from models import timehistory
from data_generator import generate_img_input_data
if keras.backend.backend() == 'tensorflow':
  import tensorflow as tf
if keras.backend.backend() == 'cntk':
  from gpu_mode import cntk_gpu_mode_config, finalize
import tensorflow.contrib.eager as tfe
import numpy as np

def crossentropy_from_logits(y_true, y_pred):
    return tf.keras.backend.categorical_crossentropy(target=y_true,
                                                   output=y_pred,
                                                   from_logits=True)

def device_and_data_format():
  return ('/gpu:0', 'channels_first') if tfe.num_gpus() else ('/cpu:0',
                                                              'channels_last')

class Resnet50Benchmark:

  def __init__(self):
    self.test_name = "resnet50"
    self.sample_type = "images"
    self.total_time = 0
    self.batch_size = 64
    self.epochs = 4
    self.num_samples = 1000
    self.test_type = 'tf.keras, eager_mode' 

  def run_benchmark(self, gpus=0, use_dataset_tensors=False):
    print("Running model ", self.test_name)
    #tfe.enable_eager_execution()
    tf.keras.backend.set_learning_phase(True)

    input_shape = (self.num_samples, 3, 224, 224)
    num_classes = 1000
    
    x_train = np.random.randint(0, 255, input_shape)
    y_train = np.random.randint(0, num_classes, (input_shape[0],))
    y_train = tf.keras.utils.to_categorical(y_train, num_classes)

    if tf.keras.backend.backend() == "tensorflow" and gpus >= 1:
      tf.keras.backend.set_image_data_format('channels_first')

    if tf.keras.backend.image_data_format() == 'channels_last':
      x_train = x_train.transpose(0, 2, 3, 1)
    print("data format is ", keras.backend.image_data_format())
    x_train /= 255
    x_train = x_train.astype('float32')
    y_train = y_train.astype('float32')

    device, data_format = device_and_data_format()
    with tf.device(device):
    	#model = tf.keras.applications.ResNet50(weights=None)
        inputs = tf.keras.layers.Input(shape=(3, 224, 224))
        outputs = tf.keras.applications.ResNet50(include_top=False,
                                           pooling='avg',
                                           weights=None)(inputs)
        predictions = tf.keras.layers.Dense(num_classes)(outputs)
        model = tf.keras.models.Model(inputs, predictions)
    	model.compile(loss=crossentropy_from_logits,
                    optimizer=tf.train.RMSPropOptimizer(learning_rate=0.0001, decay=1e-6),
                    metrics=['accuracy'])


    	time_callback = timehistory.TimeHistory()

    	model.fit(x_train, y_train, batch_size=self.batch_size, epochs=self.epochs,
                shuffle=True, callbacks=[time_callback])

    	self.total_time = 0
    	for i in range(1, self.epochs):
      		self.total_time += time_callback.times[i]

    if tf.keras.backend.backend() == "tensorflow":
      tf.keras.backend.clear_session()

