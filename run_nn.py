import numpy as np
import os
import pylab
import wave
import librosa
import pickle
import warnings
import random
from tensorflow.keras import models
from tensorflow.keras.preprocessing import image
from PIL import Image as PILImage
from sklearn.preprocessing import StandardScaler
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

#Pylab gives me an warning about tight_layout potentially making axes display wrong.
#This is not a problem here and can be ignored. 
warnings.simplefilter("ignore") 

#Load models for forward and for concurrent neural network
model_FNN = models.load_model('models/jamesmodel_2.h5')
model_CNN = models.load_model('models/cnn_model_4_2d555.h5')

#Load Normalisation parameters for forward neural network
ss = StandardScaler()
ss.mean_ = pickle.load( open( "models/model_mean.p", "rb" ) )
ss.var_ = pickle.load( open( "models/model_var.p", "rb" ) )
ss.scale_ = pickle.load( open( "models/model_scale.p", "rb" ) )

def get_wav_info(wav_file):
	wav = wave.open(wav_file, 'r')
	frames = wav.readframes(-1)
	sound_info = pylab.frombuffer(frames, 'int16')
	frame_rate = wav.getframerate()
	wav.close()
	return sound_info, frame_rate 

def run_cnn(filename, cnn_th):
	sound_info, frame_rate = get_wav_info(filename)
	#Use Pylab to draw spectograph on canvas and then take image from canvas.
	fig = pylab.figure(num=None, figsize=(19, 12))
	fig.add_axes([0,0,1,1])
	pylab.specgram(sound_info, Fs=frame_rate)
	fig.tight_layout()
	pylab.axis('off')
	pylab.draw()

	fig.canvas.draw()
	image_from_plot = np.frombuffer(fig.canvas.tostring_rgb(), dtype=np.uint8)
	image_from_plot = image_from_plot.reshape(fig.canvas.get_width_height()[::-1] + (3,))
	im = PILImage.fromarray(image_from_plot)
	im = im.resize((150,150))
	img_tensor = image.img_to_array(im) 
	img_tensor = np.expand_dims(img_tensor, axis=0)      
	img_tensor /= 255.   
	
	pylab.close()
	
	y= model_CNN.predict(img_tensor)	
	if y < cnn_th:
		r = random.randint(1,1000000)
		#I am saving all activations, which I can use later to improve prediction. 
		audiofile = 'Activations/Record-'+str(r)+'.wav'
		os.rename(filename, audiofile)
		print("C	NN: " + str(y))
		return True
	return False	
	
def run_fnn(filename, fnn_th, cnn_th):
	X, sample_rate = librosa.load(filename, res_type='kaiser_fast')
	mfccs = np.mean(librosa.feature.mfcc(y=X, n_mfcc=128).T,axis=0)
	X_test = np.array(mfccs)
	X_test = X_test.reshape(1,-1)
	X_test = ss.transform(X_test)
	y = model_FNN.predict(X_test)
	if y > fnn_th:
		#print("F	NN: " + str(y))	
		check2 = run_cnn(filename, cnn_th)
		return check2
	return False	
	