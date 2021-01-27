# James - A Voice Controlled Discord Bot

This is the source code for James: A voice activated and controlled Discord bot. There are two main parts:

1. The bot and all its components. 

2. The code used to train the neural networks for "James" keyword recognition. 

### Prerequisites

All packages needed are in the requirements.txt.

By default, James hear only the sound from your default microphone. So, only you would be able to talk with James. If you want your friends to also communicate with James, you need to put their sound as input as well. In my case, I am using [Voicemeter](https://vb-audio.com/Voicemeeter/) to simulate a virtual microphone. That way everything I can hear, I can direct to the virtual microphone. In turn, James can hear everything I can hear and talk to everyone in my channel. 

### Installation and Usage

The main code of the bot is in [James.py](James.py). It still needs your Discord Bot token, list of friends James should be able to recognise, as well as the channel he is supposed to connect to. This is all the information needed to run James. Once started, James can be activated by calling for his name. 

In [run_nn.py](run_nn.py) is the Code to run the neural networks. Every 2.5s James checks if he has been called using these neural networks. The models for these networks are in models. This is only important if you want to change the keyword and want to create your own models. In this case you can find the training code for the neural networks in [Training](Training) folder.

## Additional Documentation and Acknowledgments

* Something
