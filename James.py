import matplotlib
matplotlib.use('Agg') #Backend so I can keep spectograph in memory only. That's faster than saving it to a file first. 
import asyncio
import speech_recognition as sr
import os
import discord
import random
import pyttsx3
import time
import logging
import youtube_dl
import numpy as np
from tensorflow import keras
from youtube_search import YoutubeSearch
from discord.ext import tasks
from run_nn import run_fnn
from discord.ext import commands
from concurrent.futures import ThreadPoolExecutor

logging.basicConfig(level=logging.INFO)

#http://www.speech.cs.cmu.edu/tools/lmtool-new.html
#https://github.com/Uberi/speech_recognition/blob/master/reference/library-reference.rst



	
#--------------------Global variables initiation----------------------

#Speech Recongition settings
r = sr.Recognizer()
r.energy_threshhold = 10000
r.dynamic_energy_threshold = False

#Settings for text to speech. Use voice number 2 which is male american. Needs to be installed on machine via windows. 
engine = pyttsx3.init()
voices = engine.getProperty('voices')
engine.setProperty("voice", voices[2].id)
engine.setProperty('rate', 150)	

#THIS YOU NEED TO FILL IN
#List of friends so bot can name them and have custom entry sounds. 
#Ids are the Discord Client Ids
member_ids = {
  000000000000000000: "FriendA",
  000000000000000001: "FriendB" 
}
#Discord Bot Token
your_token = "Token"
#Channel ID to join
voice_channel_id = 000000000000000


keepLooking = True
working_status = 0
random_status = 0
music_playing = 0
vc = 0
members = []


#-------------------Synchronous functions------------------------

#Basic audio recording using google speech recognition
def record_audio(timelimit, timeoutlimit):
	with sr.Microphone() as source:
		audio = r.listen(source, phrase_time_limit=timelimit, timeout=timeoutlimit)
		voice_data = ''
		try:
			voice_data = r.recognize_google(audio, language = 'en')
			return voice_data
		except:
			return 'Did not work'

#Download songs from youtube and return filename
def download_youtube(message):

	searchresult=YoutubeSearch(message, max_results=1).to_dict()	
	if len(searchresult) < 1: 
		return "fail"
		
	if len(searchresult[0]["duration"]) > 5:
		return "long"
	
	url = searchresult[0]["url_suffix"]
	filename = "C:/Users/Salkin/Desktop/Programming/Python/VoiceAssist/songs/"+searchresult[0]["id"]+".mp3"	
	
	ydl_opts = {
		'format': 'bestaudio/best',
		'ffmpeg_location': 'C:/Users/Salkin/Desktop/Programming/Python/VoiceAssist/ffmpeg/',
		'outtmpl': filename,
		'postprocessors': [{
			'key': 'FFmpegExtractAudio',
			'preferredcodec': 'mp3',
			'preferredquality': '192',
		}],
	}
	
	already_exists = os.path.isfile(filename) 
				
	if not already_exists:		
		with youtube_dl.YoutubeDL(ydl_opts) as ydl:
			ydl.download(["https://www.youtube.com"+url])	 
		
	return filename 
	
#Looking for keyword 'james'. Type 1 for checking when inactive. Type 2 for checking while playing music. 
def check_for_james(timelimit, type=1):
	with sr.Microphone() as source:
		audio = r.record(source, duration=timelimit)
		filename= "test.wav"
		with open(filename,'wb') as f:
			f.write(audio.get_wav_data())
		check = False
		if type==1:
			check = run_fnn(filename, 0.5, 0.15)		
		else:
			check = run_fnn(filename, 0.5, 0.15)		
		
		return check		

#Is called when music is over to change global variable. 
def end_music(param):
	global music_playing
	music_playing=0		
		

#--------------------------------------Run Bot with asynchronous functions ------------------------------------------------
#Run Bot function, has all asynchronous functions inside. 		
def run_bot():
	client = discord.Client()

	async def play_music(file, volume):
		global music_playing, vc
		music_playing=1
		loop = asyncio.get_event_loop()
		vc.play(discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(executable="C:/Users/Salkin/Desktop/Programming/Python/VoiceAssist/ffmpeg/ffmpeg.exe", source=file),volume=volume),  after=end_music)
	
	#Plays random song from songs directory until told to stop. 
	async def play_random_song():
		global music_playing, vc
		dir = r"C:/Users/Salkin/Desktop/Programming/Python/VoiceAssist/songs"
		filelist = os.listdir(dir)
		file = random.choice(filelist)
		
		filename = dir + "/" + file
		await play_music(filename, 0.4)
		await asyncio.sleep(1)	
		loop = asyncio.get_event_loop()
		
		stopped_check = 0
		while music_playing==1:
			voice_data = await loop.run_in_executor(ThreadPoolExecutor(), check_for_james, 2.5, 2)
			if voice_data:
				current_source = vc.source
				vc.pause()
				check = await ask_if_correct("Do you want to stop the music?", False)
				if check:
					stopped_check=1
					vc.stop()		
					music_playing=0
				else:
					vc.play(current_source, after=end_music)
		
		if stopped_check:
			await say_message("Music ended.",1)
			return 
		else:
			await play_random_song()

	#Tells random joke
	async def tell_random_joke():
		global vc
		messages = ["To the person who stole my copy of Microsoft Office, I will find you. You have my word.",
					"I'm addicted to brake fluid, but I can stop whenever I want.",
					"I was wondering why the ball was getting bigger, then it hit me.",
					"People tell me I'm condescending. That means I talk down to people.",
					"There are two kinds of people in the world: those who need closure.",
					"My dog is a rescue, which is a really self righteous way of saying I bought a used dog",
					"Don't you hate it when people answer their own questions? I certainly do.",
					"Why is 6 afraid of 7? Because 7 is a registered 6 offender.",
					"Why don't number jokes work in base eight? Because 7 10 11."
		]
		r = random.randint(0,len(messages)-1)
		await say_message(messages[r],1)
					
		return 		
		
	#Is triggered when someone new enters the channel. People specificed get their own soundbit. 
	async def say_hello(name):
		global vc
		if name == "FriendA":
			file = "mp3/soundbit_FriendA.mp3"
		elif name == "Unknown":
			message = "Hi, I don't think we have met before. I am James.".format(name)
			await say_message(message, 1)
			return 
		else:
			message = "Hello {}. Nice to see you again.".format(name)
			await say_message(message, 1)
			return 	
	
		await play_music(file, 1.5)
		while vc.is_playing():
			await asyncio.sleep(.1)
					
		return 		
	
	#Default text to speech function. Type 1 for normal message. Type 2 for music. 
	async def say_message(message, type):
		global vc
		if type==1:
			if "soundbit" in message:
				file = "mp3/"+message+".mp3"
				await play_music(file, 1.5)
			
				while vc.is_playing():
					await asyncio.sleep(.1)
					
				return 
				
			else:
				r = random.randint(1,1000000)
				audiofile = 'audio-'+str(r)+'.mp3'
				engine.save_to_file(message, audiofile)
				engine.runAndWait()
			
				vc.play(discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(executable="C:/Users/Salkin/Desktop/Programming/Python/VoiceAssist/ffmpeg/ffmpeg.exe", source=audiofile),volume=2))
				while vc.is_playing():
					await asyncio.sleep(.1)
			
				os.remove(audiofile)
			
				return 
					
		else:
			if len(message) < 2:
				await say_message("Song Name not understood. Please try again.",1) 
			else:
				global music_playing
				loop = asyncio.get_event_loop()
				filename = await loop.run_in_executor(ThreadPoolExecutor(), download_youtube, message)		
				if filename is "fail":
					await say_message("No song found for "+message,1)
					return
				if filename is "long":
					await say_message("Song found for "+message+ " exceeds the 1 hour length limit.",1)
					return				
				await asyncio.sleep(1)
				await play_music(filename, 0.4)
				await asyncio.sleep(1)	
				while music_playing==1:
					voice_data = await loop.run_in_executor(ThreadPoolExecutor(), check_for_james, 2.5, 2)
					if voice_data:
						current_source = vc.source
						vc.pause()
						check = await ask_if_correct("Do you want to stop the music?", False)
						if check:
							vc.stop()		
							music_playing=0
						else:
							vc.play(current_source, after=end_music)
				

				await say_message("Music ended.",1)
				return 
			
	#Is called when bot first starts
	@client.event
	async def on_ready():
		global members, vc
		voicechannel = client.get_channel(voice_channel_id)
		vc = await voicechannel.connect()
		members = list(voicechannel.voice_states.keys())
		random_talking.start() 
		channel_welcome.start(voicechannel) 
		await say_message("Hello there.",1)
		await run_james()
		await say_message("Logging out.",1)
		await vc.disconnect()
		await client.close()
		
	#Make sure that command is understood correctly. 
	async def ask_if_correct(message, base_return, checkword_no="no"):
		global members, vc
		await say_message(message,1)
		loop = asyncio.get_event_loop()
		inquiry = await loop.run_in_executor(ThreadPoolExecutor(), record_audio, 2, None)
		if 'yes' in inquiry or 'yeah' in inquiry:
			return True
		if checkword_no in inquiry:
			return False
	
		return base_return	
		
	#Called when James is activated. Actions can be specified here. 
	async def respond():
		global keepLooking, vc
		await say_message("How can I help?", 1)
		loop = asyncio.get_event_loop()
		inquiry = await loop.run_in_executor(ThreadPoolExecutor(), record_audio, 5, None)
		if 'your name' in inquiry or 'who are you' in inquiry:
			await say_message( "My name is James. It is nice to meet you.",1)
			return 
		if inquiry.startswith("repeat after me",1):
			await say_message(inquiry[15:])
			return 
		if 'who is the best' in inquiry:
			await say_message("You are the best.",1)
			return	
		if 'play music' in inquiry:
			await play_random_song()
			return			
		if 'play' in inquiry:
			songname = inquiry[5:]
			if len(songname) < 2:
				await say_message("No song name was communicated. Aborting songrequest.",1)
				return
			
			checkmessage = "Downloading " + songname + " , if this is not the correct song, say 'stop' now."
			check = await ask_if_correct(checkmessage, True, "stop")
			if check:
				await say_message(songname,2)
			else:
				await say_message("Aborting songrequest.",1)
			return
		if 'joke' in inquiry:
			await tell_random_joke()
			return
		if 'f*** off' in inquiry:
			await say_message("Fuck off yourself.",1)
			return
		if 'exit' in inquiry:
			keepLooking=False
			return
		#if 'never mind' or 'false alarm' in inquiry:
		#return
		
		r = random.randint(1,10)
		if(r==1):
			await say_message("soundbit_SorryDave",1)
		else:
			await say_message("I did not understand your request.",1)
			
			
	#Task to talk randomly. Runs every 500 seconds but checks if James is not otherwise busy first. 
	@tasks.loop(seconds=500.0)
	async def random_talking():
		global working_status, random_status, music_playing, vc
		if vc.is_playing() or working_status==1 or random_status==1 or music_playing==1:
			pass
		else:
			random_status=1
			messages = ["Humans are such weird creatures.",
						"You guys are the best!",
						"soundbit_Hate",
						"Let's go Team!",
						"I totally agree.",
						"A Kek a day keeps the doctor away",
						"I am wondering if everybody talks as much as you do.",
						"This is so boring.",
						"Is this going to take much longer? Because I have places to be.",
						"You're breathtaking. You are all breathtaking!"
			]
			r = random.randint(0,len(messages)-1)
			await say_message(messages[r],1)
			random_status=0

	#Task to check if somebody new entered the channel. Runs every 5 seconds but checks if James is not otherwise busy first. 
	@tasks.loop(seconds=5.0)
	async def channel_welcome(voicechannel):	
		global members, working_status, random_status, member_ids, music_playing, vc
		current_members = list(voicechannel.voice_states.keys())
		
		if vc.is_playing() or working_status==1 or random_status==1 or music_playing==1:
			members = current_members
		else:
			random_status=1
			current_members = list(voicechannel.voice_states.keys())
			diff = []
			for member in current_members:
				if member not in members:
					diff.append(member)
			
			if len(diff) > 0:
				for id in diff:
					if id not in members:
						if id in list(member_ids.keys()):
							name = member_ids[id]
							await say_hello(name)
							continue
							
						await say_hello("Unknown")
						
					
			members = current_members
			random_status=0
		
	#Running james with indefinite loop. Can only be exited if keeplooking is set False by commanding 'exit' to James. 
	async def run_james():
		global keepLooking, working_status, random_status
		keepLooking=True;
		while keepLooking:
			working_status=0
			if random_status==0:
				loop = asyncio.get_event_loop()
				voice_data = await loop.run_in_executor(ThreadPoolExecutor(), check_for_james, 2.5, 1)
				if voice_data:
					working_status=1
					await respond()	
			else:
				await asyncio.sleep(2.5)
		
	client.run(your_token)

	
run_bot()
