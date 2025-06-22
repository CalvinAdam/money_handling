import streamlit as st
import pandas as pd
import requests
import json
from dotenv import load_dotenv
import os

st.title("Read receipts")

# load your environment containing the api key
BASEDIR = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(BASEDIR, '.env'))
API_KEY = os.getenv("API_KEY")