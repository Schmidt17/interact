"""
Utility for recording a sample from an audio device
and sending it via mqtt to the sampling computer.

This runs on the audio computer.
"""
import pyaudio
import numpy as np
import time
import paho.mqtt.client as mqcl
import json
import base64

SAMPLERATE = 44100

class Sampler:
    def __init__(self):
        self.name = "sampler"

        self.recording_channel = None
        self.channel_numbers = [1, 2, 3, 4]

        self.samples = []
        self.sample = None

        # networking stuff
        self.discard_own_messages = True
        self.mqtt_client = mqcl.Client(client_id=self.name, clean_session=True)
        self.mqtt_client.on_message = self.on_mqtt_message
        self.mqtt_client.on_connect = self.on_mqtt_connect

        mqtt_broker_ip = "localhost"
        self.mqtt_client.connect(mqtt_broker_ip, 1883, 60)
        self.mqtt_client.subscribe("timing/beats", qos=0)
        self.mqtt_client.subscribe("sampling", qos=1)
        self.mqtt_client.loop_start()

    def on_mqtt_message(self, client, userdata, msg):
        msg_dict = json.loads(msg.payload)
        if msg_dict['sender_id'] != self.name:
            if msg_dict['state']['record_pressed'] and self.recording_channel is None:
                self.start_recording(msg_dict['state']['source'])
            elif not (msg_dict['state']['record_pressed']) and not (self.recording_channel is None):
                self.stop_recording()

    def on_mqtt_connect(self, client, userdata, flags, rc):
        self.discard_own_messages = False  # enable fetching the last state from the broker
        # will be turned off when the first message is processed

    def send_sample(self):
        print("Sending sample")
        str_sample = base64.b64encode(self.sample).decode()

        sample_length = len(str_sample)
        sample_id = np.random.randint(1000)
        chunksize = 1024
        num_full_chunks = sample_length // chunksize
        remainder = sample_length % chunksize
        chunks = [str_sample[i*chunksize:(i+1)*chunksize] for i in range(num_full_chunks)]
        if remainder > 0:
            chunks.append(str_sample[-remainder:])
        num_chunks = len(chunks)

        for i, chunk in enumerate(chunks):
            payload = json.dumps({'sender_id': self.name, 'sample_id': sample_id, 'sample': chunk, 'chunk_number': i, 'num_chunks': num_chunks, 'rec_channel': self.recorded_channel})
            self.mqtt_client.publish("sampling/data", payload, qos=1, retain=False)
        print("Sent sample")

    def start_recording(self, source_id):
        print("start_recording")
        self.samples = []
        self.recording_channel = source_id

    def stop_recording(self):
        print("stop_recording")
        self.recorded_channel = self.recording_channel
        self.recording_channel = None
        self.sample = b''.join(self.samples)
        self.samples = []
        self.send_sample()

    def record_callback(self, in_data, frame_count, time_info, status):
        # extract the right channel from the data
        if not self.recording_channel is None:
            self.samples.append(in_data)
        return (None, pyaudio.paContinue)


pa = pyaudio.PyAudio()
sampler = Sampler()

# for i in range(pa.get_device_count()):
#   print(pa.get_device_info_by_index(i))
# exit()

instream = pa.open(rate=SAMPLERATE,
                    channels=2,
                    format=pyaudio.paInt16,
                    input=True,
                    input_device_index=4,
                    stream_callback=sampler.record_callback)

# keep the recording thread alive
try:
    while True:
        time.sleep(0.1)
except KeyboardInterrupt:
    instream.stop_stream()
    instream.close()

    pa.terminate()
