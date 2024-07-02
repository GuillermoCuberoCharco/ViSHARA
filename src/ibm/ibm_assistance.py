# Original source: https://github.com/Laura-VFA/Affective-Proactive-EVA-Robot/blob/main/services/cloud/ibm_api.py

# IBM Watson wrapper
# (Watson Assistant, NLU Emotion Analysis)
import os
from datetime import datetime
from google.cloud import translate_v2 as translate
from ibm_watson import AssistantV2, NaturalLanguageUnderstandingV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from dotenv import load_dotenv

load_dotenv()
current_dir = os.path.dirname(os.path.abspath(__file__))
credentials_path = os.path.join(
    current_dir, "vishara-415010-002552ca9ca0.json")
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path

api_key = os.getenv('ASSISTANT_APIKEY')
assistant_id = os.getenv('ASSISTANT_LIVE_ENV_ID')
service_url = os.getenv('ASSISTANT_URL')
nlu_api_key = os.getenv('NLU_APIKEY')
nlu_url = os.getenv('NLU_URL')

translate_client = translate.Client()

assistant_authenticator = IAMAuthenticator(api_key)
assistant = AssistantV2(
    version='2021-06-14',
    authenticator=assistant_authenticator
)
assistant.set_service_url(service_url)

try:
    response = assistant.create_session(assistant_id=assistant_id).get_result()
    print("Session created successfully:", response)
except Exception as e:
    print("Failed to create session:", e)

nlu_authenticator = IAMAuthenticator(nlu_api_key)
nlu = NaturalLanguageUnderstandingV1(
    version='2021-06-14',
    authenticator=nlu_authenticator
)
nlu.set_service_url(nlu_url)

SESSION_TIME = 20
last_query_time = None
session_id = response['session_id']


def translate_text(text, target='en'):

    result = translate_client.translate(text, target_language=target)
    return result['translatedText']


def create_session():
    # Create Watson Assistant session

    global session_id, assistant_id

    response = assistant.create_session(
        assistant_id=assistant_id
    ).get_result()

    session_id = response['session_id']


def is_session_active():
    # Empty query to check if session is active

    global last_query_time

    return last_query_time is not None and (datetime.now() - last_query_time).total_seconds() < SESSION_TIME


def analyze_mood(text):
    translated_text = translate_text(text, target='en')
    print("Translated text:", translated_text)
    nlu_options = {
        'text': translated_text,
        'features': {
            'emotion': {}
        },
        'language': 'en'
    }

    try:
        response = nlu.analyze(**nlu_options).get_result()
        print("Response from NLU:", response)
    except Exception:
        return {}
    else:
        return response['emotion']['document']['emotion']


def get_watson_response(input_text, assistant, assistant_id, session_id):
    try:
        response = assistant.message(
            assistant_id=assistant_id,
            session_id=session_id,
            input={
                'message_type': 'text',
                'text': input_text
            }
        ).get_result()
        print("Response from Watson Assistant:", response)
        context = response.get('context', {})
        skill = context.get('skill', {})
        main_skill = skill.get('main skill', {})
        user_defined = main_skill.get('user_defined', {})

        mood = analyze_mood(input_text)
        print("Mood: ", mood)

        return response, user_defined, mood
    except Exception as e:
        print("Failed to get response from Watson Assistant:", e)
        return None, None, None
