import google.generativeai as genai
import os
import json
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.5-flash')
prompt = 'Analyze the citizen complaints. For each, extract the zone_id, topic, sentiment (negative|neutral|positive), and urgency (high|medium|low). Return a JSON array of objects with exactly these keys.\n\nComplaints:\nZone: 12.99_77.585, Text: Taxi stand overflowing onto the main road.'
res = model.generate_content(prompt)
print(res.text)
