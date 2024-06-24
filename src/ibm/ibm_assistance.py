# Original source: https://github.com/Laura-VFA/Affective-Proactive-EVA-Robot/blob/main/services/cloud/ibm_api.py

# IBM Watson wrapper
# (Watson Assistant, NLU Emotion Analysis)
import os
from datetime import datetime
from ibm_watson import AssistantV2, NaturalLanguageUnderstandingV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('ASSISTANT_APIKEY')
assistant_id = os.getenv('ASSISTANT_LIVE_ENV_ID')
service_url = os.getenv('ASSISTANT_URL')
nlu_api_key = os.getenv('NLU_APIKEY')
nlu_url = os.getenv('NLU_URL')

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


def generate_response(input_text):
    response = assistant.message(
        assistant_id=assistant_id,
        session_id=session_id,
        input={
            'message_type': 'text',
            'text': input_text
        }
    ).get_result()
    print("Response from Watson Assistant:", response)
    context = response['context']
    return response, context


def analyze_mood(text):
    nlu_options = {
        'text': text,
        'features': {
            'emotion': {}
        },
        'language': 'en'
    }

    try:
        response = nlu.analyze(**nlu_options).get_result()
    except Exception:
        return {}
    else:
        return response['emotion']['document']['emotion']


if __name__ == "__main__":
    print("Starting IBM Watson API...")
    create_session()
    try:
        test_input = "Hola, estoy triste"
        response, context = generate_response(test_input)
        print("Response: ", response)
        print("Context: ", context)
    except KeyError as e:
        print(f"KeyError: {e}")
    except Exception as e:
        print(f"Failed to generate respond: {e}")

    mood = analyze_mood(test_input)
    print("Mood: ", mood)
