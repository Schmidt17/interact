"""
Utility for recording a sample from an audio device
and sending it via mqtt to the sampling computer.

This runs on the audio computer.
"""
import pyaudio
import numpy as np

