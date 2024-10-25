import os
import time
from tqdm import tqdm
import openai

# For caching
import json
import hashlib

# Modify your own openai config
# openai.api_base = os.environ["OPENAI_API_BASE"]
# openai.api_version = os.environ["OPENAI_API_VERSION"]

openai.api_key = os.environ["OPENAI_API_KEY"]


# Can't seem to figure out where this is called
def connect_gpt4(message, prompt):
    response = openai.ChatCompletion.create(
                    model="gpt-4o-mini", 
                    messages = [{"role":"system","content":f"{message}"}, #"You are a helpful assisant. Help the user to complete SQL and no explanation is needed."
                                {"role":"user", "content":f"{prompt}"}],
                    temperature=0,
                    max_tokens=800, #800
                    top_p=1,
                    frequency_penalty=0,
                    presence_penalty=0,
                    stop = None)
    return response['choices'][0]['message']['content']


def collect_response(prompt, max_tokens = 800, stop = None, cache_dir="./cache", db_id=None, query=None, step=""):

    # Make the cache folder
    os.makedirs(cache_dir, exist_ok=True)

    # Hash based on API parameters
    hash_params = json.dumps({"prompt": prompt, "max_tokens": max_tokens, "stop": stop}, sort_keys=True)
    hash_key = hashlib.sha256(hash_params.encode('utf-8')).hexdigest()
    print(hash_key)
    cache_filename = os.path.join(cache_dir, f"{db_id}_{query}_{step}_{hash_key}.json")

    if os.path.isfile(cache_filename):
        print("<--------- cached response ----------------->")
        with open(cache_filename, 'r') as f:
            return json.load(f)

    while 1:
            flag = 0
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-4o-mini", 
                    messages = [{"role":"system","content":"You are an AI assistant that helps people find information."}, #"You are a helpful assisant. Help the user to complete SQL and no explanation is needed."
                                {"role":"user", "content":f"{prompt}"}],
                    temperature=0,
                    max_tokens=max_tokens, #800
                    top_p=1,
                    frequency_penalty=0,
                    presence_penalty=0,
                    stop = stop)
                # store response to .json
                # track: model, queries, responses
                response = response['choices'][0]['message']['content']
                flag = 1
                
                with open(cache_filename, 'w') as f:
                    json.dump(response, f)

            except Exception as e:
                print(e)
                time.sleep(1)
            if flag == 1:
                break
    return response

