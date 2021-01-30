import os
import pandas as pd
import librosa
import numpy as np
import pickle
import matplotlib.pyplot as plt
from tensorflow import keras
from sklearn.preprocessing import StandardScaler
from tensorflow.keras.wrappers.scikit_learn import KerasClassifier
from tensorflow.keras.regularizers import l2


filelist = os.listdir("fnn_data") # Get file list of all .wav files we want to use for training
df = pd.DataFrame(filelist)

# Renaming the column name to file
df = df.rename(columns={0:'file'})

# Each file name has starts with a 0 or 1. These are my labels which I can now take into the seconds dataframe column:
isjames = []
for i in range(0, len(df)):
    isjames.append(int(df['file'][i].split('-')[0]))# We now assign the speaker to a new column 
df['isjames'] = isjames


#Calculates mfccs for every data point
def extract_features(files):
	file_name = os.path.join(os.path.abspath(datafile)+'/'+str(files.file))
	X, sample_rate = librosa.load(file_name,res_type='kaiser_fast')# Mel-frequency cepstral coefficients (MFCCs) from a time series 
	mfccs = np.mean(librosa.feature.mfcc(y=X, sr=sample_rate, n_mfcc=128).T,axis=0)# hort-time Fourier transform (STFT) to use in the chroma_stft
	
	#I also tried to use other features like the ones below, but found they did not improve perfomance in a meaningful way:	
	
	#stft = np.abs(librosa.stft(X))
	#chroma = np.mean(librosa.feature.chroma_stft(S=stft, sr=sample_rate).T,axis=0)
	#mel = np.mean(librosa.feature.melspectrogram(X, sr=sample_rate).T,axis=0)# spectral contrast
	#contrast = np.mean(librosa.feature.spectral_contrast(S=stft, sr=sample_rate).T,axis=0)
	#spectral_centroids = librosa.feature.spectral_centroid(X, sr=sample_rate)[0]
	#rms = librosa.feature.rms(y=X)[0]
	#tonnetz = np.mean(librosa.feature.tonnetz(y=librosa.effects.harmonic(X),sr=sample_rate).T,axis=0)
	
	return mfccs
	

#Split in train and test data
msk = np.random.rand(len(df)) < 0.9
df_train = df[msk]
df_test = df[~msk]

train_features = df_train.apply(extract_features, axis=1)
test_features = df_test.apply(extract_features, axis=1)

features_train = []
features_test = []

for index, value in train_features.items():
    features_train.append(train_features[index])


for index, value in test_features.items():
    features_test.append(test_features[index])


	
X_train = np.array(features_train)
Y_train = np.array(df_train['isjames'])

X_test = np.array(features_test)
Y_test = np.array(df_test['isjames'])

#Save data for later use. Useful if I want to try different model settings but don't want to prepare the data each time. 
pickle.dump(X_train, open( "X_train.p", "wb" ))
pickle.dump(Y_train, open( "Y_train.p", "wb" ))
pickle.dump(X_test, open( "X_test.p", "wb" ))
pickle.dump(Y_test, open( "Y_test.p", "wb" ))


n_input = 128 #Number of features 


"""
#This is only important if I want to load the data directly and prepare it for the first time
X_train = pickle.load(open("X_train.p", "rb" ) )
Y_train = pickle.load(open("Y_train.p", "rb" ) )
X_test = pickle.load(open("X_test.p", "rb" ) )
Y_test = pickle.load(open("Y_test.p", "rb" ) )
"""

#Normalise data and save for later use
ss = StandardScaler()
ss.fit(X_train)
X_train = ss.transform(X_train)
X_test = ss.transform(X_test)

pickle.dump(ss.mean_, open( "model_mean.p", "wb" ) )
pickle.dump(ss.var_, open( "model_var.p", "wb" ) )
pickle.dump(ss.scale_, open( "model_scale.p", "wb" ) )


#Define model
model = keras.models.Sequential()
	
regul=0.00001

activation='relu'
model.add(keras.layers.Dense(256, input_shape=(n_input,), activation=activation))
model.add(keras.layers.Dropout(0.5))
	
model.add(keras.layers.Dense(256, activation=activation, kernel_regularizer=l2(regul), bias_regularizer=l2(regul), activity_regularizer=l2(regul)))
model.add(keras.layers.Dropout(0.5))

model.add(keras.layers.Dense(128, activation=activation, kernel_regularizer=l2(regul), bias_regularizer=l2(regul), activity_regularizer=l2(regul)))
model.add(keras.layers.Dropout(0.4))

model.add(keras.layers.Dense(16, activation=activation, kernel_regularizer=l2(regul), bias_regularizer=l2(regul), activity_regularizer=l2(regul)))
model.add(keras.layers.Dropout(0))
	
	
model.add(keras.layers.Dense(1, activation='sigmoid'))
	
opt = keras.optimizers.Adam(learning_rate=0.0001)
model.compile(loss='binary_crossentropy', metrics='binary_accuracy', optimizer=opt)

#Use and early stop based on validation loss
early_stop = keras.callbacks.EarlyStopping(monitor='val_loss', min_delta=0, patience=42, verbose=1, mode='auto',)
	
	
#Epochs can be very high since I am using early stop
history = model.fit(X_train, Y_train, batch_size=300, epochs=3000, validation_data=(X_test, Y_test),callbacks=[early_stop], verbose=0) #with early stop
model.save('jamesmodel.h5') #save model 

#Look at results via matplotlib
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
