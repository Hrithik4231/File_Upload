from google.generativeai.generative_models import GenerativeModel
from google.generativeai.client import configure

API_KEY = "AIzaSyCXTRu_0RJsk_VVs13vuLcPpq4l5cmo2I0" 
configure(api_key=API_KEY)
model = GenerativeModel("gemini-1.5-flash")
