from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D
from tensorflow.keras.layers import Activation, Dropout, Flatten, Dense
from tensorflow.keras import backend as K
from tensorflow.keras import models
import matplotlib.pyplot as plt

# Settings
img_width, img_height = 150, 150
batch_size = 16


if K.image_data_format() == 'channels_first':
    input_shape = (3, img_width, img_height)
else:
    input_shape = (img_width, img_height, 3)


#Define settings for image generation. In my case only rescale and width, height shift range
train_datagen = ImageDataGenerator(
        rotation_range=0,
        width_shift_range=0.05,
        height_shift_range=0.05,
        rescale=1./255,
        shear_range=0.0,
        zoom_range=0.0,
        horizontal_flip=False,
        fill_mode='nearest')

#Test set has no shifts but is only rescaled
test_datagen = ImageDataGenerator(rescale=1./255)


#Load test and validation data from directory. They need to be set up beforehand.
train_generator = train_datagen.flow_from_directory(
        'Plot2/train', 
        target_size=(img_width, img_height),  
        batch_size=batch_size,
        class_mode='binary')

validation_generator = test_datagen.flow_from_directory(
    'Plot2/validation',
    target_size=(img_width, img_height),
    batch_size=batch_size,
    class_mode='binary')

	
print("Loaded")		
		

#Define Model 
model = Sequential()
model.add(Conv2D(32, (5, 5), input_shape=input_shape))
model.add(Activation('relu'))
model.add(MaxPooling2D(pool_size=(2, 2)))

model.add(Conv2D(32, (5, 5)))
model.add(Activation('relu'))
model.add(MaxPooling2D(pool_size=(2, 2)))

model.add(Conv2D(64, (5, 5)))
model.add(Activation('relu'))
model.add(MaxPooling2D(pool_size=(2, 2)))

model.add(Flatten()) 
model.add(Dense(64))
model.add(Activation('relu'))
model.add(Dropout(0.5))
model.add(Dense(1))
model.add(Activation('sigmoid'))

model.compile(loss='binary_crossentropy',
              optimizer='rmsprop',
              metrics=['binary_accuracy'])


#Fit model with data. Steps per epoch are the number of images available divided by batch_size. 
history = model.fit_generator(
        train_generator,
        steps_per_epoch=1844 // batch_size,
        epochs=50,
        validation_data=validation_generator,
        validation_steps=148 // batch_size)
		
#Save Model
model.save('cnn_model.h5')

#Plot accuracy and loss with training history 
train_accuracy = history.history['binary_accuracy']
val_accuracy = history.history['val_binary_accuracy']

train_loss = history.history['loss']
val_loss = history.history['val_loss']
plt.figure()
plt.plot(train_accuracy, label='Training Accuracy', color='#185fad')
plt.plot(val_accuracy, label='Validation Accuracy', color='orange')
plt.plot(train_loss, label='Training Loss', color='#185fad')
plt.plot(val_loss, label='Validation Loss', color='orange')
#plt.legend(fontsize = 18);
plt.show()