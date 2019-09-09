import pyaudio
import numpy as np
import time
import paho.mqtt.client as mqcl
import json
import base64
import wave
import os

class SampleReceiver:
    def __init__(self):
        self.name = "sample_receiver"
        self.sample_folder = "samples"
        self.source_labels = ["Baum", "Harfe", "Gedengel", "Mic"]

        self.timeout = 5.
        self.last_arrival_time = 0.

        self.chunk_count = 0
        self.sample_id = None
        self.sample_chunks = {}

        self.mqtt_client = mqcl.Client(client_id=self.name, clean_session=True)
        self.mqtt_client.on_message = self.on_mqtt_message

        self.mqtt_client.connect("localhost", 1883, 60)
        self.mqtt_client.subscribe("sampling/data", qos=1)
        self.mqtt_client.loop_start()


    def on_mqtt_message(self, client, userdata, msg):
        msg_dict = json.loads(msg.payload)

        if not self.sample_id is None and msg_dict['sample_id'] == self.sample_id:
            if not msg_dict['chunk_number'] in self.sample_chunks:
                self.sample_chunks[msg_dict['chunk_number']] = base64.b64decode(msg_dict['sample'])
                self.chunk_count += 1
                self.last_arrival_time = time.time()

        if self.sample_id is None:
            self.sample_id = msg_dict['sample_id']
            self.sample_chunks[msg_dict['chunk_number']] = base64.b64decode(msg_dict['sample'])
            self.chunk_count = 1

        if msg_dict['sample_id'] == self.sample_id and self.chunk_count == msg_dict['num_chunks']:
            print("Saving .wav")
            sample = b''
            for i in range(self.chunk_count):
                sample += self.sample_chunks[i]
            self.sample_chunks = {}
            self.sample_id = None
            self.chunk_count = 0

            wfile = wave.open(os.path.join(self.sample_folder, self.source_labels[msg_dict['rec_channel']] + "_" + time.strftime("%H%M%S") + ".wav"), 'w')
            wfile.setnchannels(1)
            wfile.setsampwidth(2)
            wfile.setframerate(44100)

            wfile.writeframes(sample)
            wfile.close()

    def check_for_timeout(self, current_time):
        if (not self.sample_id is None) and current_time - self.last_arrival_time > self.timeout:
            print("Transmission timed out, aborting")
            self.sample_id = None
            self.chunk_count = 0
            self.sample_chunks = {}

if __name__ == "__main__":
    sample_receiver = SampleReceiver()

    while True:
        sample_receiver.check_for_timeout(time.time())
        time.sleep(0.1)
        # keep the thread alive