#!/usr/bin/env python
import rospy
from stt.msg import STT
import std_msgs
import base64
import json

from sound_play.msg import SoundRequest
from sound_play.libsoundplay import SoundClient
from googleapiclient import discovery
import httplib2
from oauth2client.client import GoogleCredentials

DISCOVERY_URL = ('https://{api}.googleapis.com/$discovery/rest?'
                 'version={apiVersion}')

TOPIC_FROM = "stt_recognize"
TOPIC_TO = "stt_result"
TMP_VOICE_FILE = "/tmp/voice.wav"

def get_speech_service():
    credentials = GoogleCredentials.get_application_default().create_scoped(
        ['https://www.googleapis.com/auth/cloud-platform'])
    http = httplib2.Http()
    credentials.authorize(http)

    return discovery.build(
        'speech', 'v1beta1', http=http, discoveryServiceUrl=DISCOVERY_URL)

def create_stt_recognizer():
    return GoogleSTT()

class GoogleSTT():
  def __init__(self):
    self._subscriber = rospy.Subscriber(TOPIC_FROM, STT, self._callback)
    self._publisher = rospy.Publisher(TOPIC_TO, std_msgs.msg.String, queue_size=10)

    rospy.init_node('google_stt_node', anonymous = True, log_level=rospy.DEBUG)
    rospy.loginfo(rospy.get_caller_id()+" Create Google STT node complete...")
    rospy.sleep(1)

  def _callback(self, msg):
    filename = msg.filename

    rospy.loginfo(rospy.get_caller_id()+" FILENAME = " +filename)
   
    with open(filename, 'rb') as speech:
      speech_content = base64.b64encode(speech.read())

    service = get_speech_service()
    service_request = service.speech().syncrecognize(
        body={
            'config': {
                'encoding': 'LINEAR16',  # raw 16-bit signed LE samples
                'sampleRate': 16000,  # 16 khz
                'languageCode': 'en-US',  # a BCP-47 language tag
            },
            'audio': {
                'content': speech_content.decode('UTF-8')
                }
            })

    response = service_request.execute()
#{"results": [{"alternatives": [{"confidence": 0.9840146, "transcript": "how old is the Brooklyn Bridge"}]}]}
    print(json.dumps(response))
    if 'results' in response:
      print "Got result..."
      transcript = response.get("results",{})[0].get("alternatives",{})[0].get("transcript", {})
      print "TEXT=" + transcript
      msg = std_msgs.msg.String()
      msg.data = transcript
      self._publisher.publish(msg)
    else:
      print "Can't recognize the audio file..."

  def on_shutdown(self):
    rospy.loginfo(rospy.get_caller_id()+" Shutdown Google TTS node complete...")
    self._subscriber.unsubscribe(self._topic_from)


if __name__ == '__main__':
  try:
    create_stt_recognizer()
  except rospy.ROSInterruptException:
    pass

  rospy.spin()
