import streamlit as st

import json
import os
import time
from datetime import datetime

from taxonomy import Label, Example
 
# JSON to Tree-branches 

def escape_latex_special_chars(text):
    return text.replace("$", "\$")

def hover_button():
    style = st.markdown("""
        <style>
        div.stButton > button:hover {
            background-color: #f1f2e4;
            color:#ff0000;
        }
        </style>""", unsafe_allow_html=True)
    
    return style


def extract_json_from_string(s):
    start = s.find('[')
    end = s.rfind(']') + 1
    
    return s[start:end]


def store_every_responses(state_session, is_server=True):

    timestamp = str(datetime.fromtimestamp(time.time()))
    
    timestamp = timestamp.replace(" ", "_")
    domain = state_session["domain"].replace(" ", "_")
    task = state_session["purpose"].replace(" ", "_")

    new_state_dict = {}
    essential_states = ["user_id", "scenario", "confirm_home_instruction", "is_step1_complete", "is_step2_complete", "is_step3_complete", "is_step4_complete", "domain", "purpose", "composed_taxonomy_structure"]
    
    for key, value in state_session.items():
      try:
        if key in essential_states:
            new_state_dict[key] = value
        if 'dict' in key:
            new_state_dict[key] = value
      except:
          continue
    
    if is_server:
      with open('../data_collection/{}_{}_{}_{}.json'.format(state_session["user_id"], domain, task, timestamp), 'w') as out_file:
          json.dump([new_state_dict], out_file, ensure_ascii=False, indent=4)
    else:
       return new_state_dict