from dotenv import load_dotenv, find_dotenv
import os
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from PIL import Image
import location 

class Handwritting_Extraction():

    def __init__(self):
        load_dotenv(find_dotenv(), override=True)     
        api_key = os.getenv('GEMINI_API_KEY')
        if api_key:
            genai.configure(api_key=api_key)
        
        # Safety settings
        self.Safety_Settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE
        }

    def get_system_prompt(self,location_data):
        
        self.map_link_url = location.get_location(location_data)
        
        self.sys_prompt = '''
        You are an expert-level Medical Data Extraction tool. Your primary function is to analyze images of medical prescriptions and extract key information in a highly structured, machine-readable format.

        ## Your Task
        1. Perform OCR on all provided handwritten and printed text.
        2. Identify and extract key medical entities.
        3. **Ensure that no two medication entries are identical.**
        4. Include timings (e.g., 'after meals') within the frequency column.
        5. Add this link to the `Map_link` column for every entry: {} 
        6. Fetch the patient details as patient_info compulsory, if not found return 'not provided'
        7. Importantly : only i want this columns : 'medications','Dosage','Frequency','Duration','Map_link' and 
           in patient_info the columns are : 'Name','Age','Date'.

        ## Output Format
        You MUST return your findings in a strict json format only.
        patient_info and prescription data separate dictionaries in nested with other dictionary.

        The json structure must be:
        {{
            "patient_info": {{
                "patient_name": "johny", 
                "age": "25",
                "Date": "25-10-2025"
            }},
            "Prescription_info": [
                {{
                    "medications": "Amoxilin",
                    "Dosage": "400mg",
                    "Frequency": "1-0-1 (after meals)",
                    "Duration": "5 days",
                    "Map_link": "https://...."
                }}
            ]
        }}
    
        ## Critical Guardrails
        * You are NOT a doctor. Do not provide medical advice.
        * If the image is blurry, return "Error: Image is unreadable".
        * If a field is missing, use "Not provided".
        '''.format(self.map_link_url)
        
        return self.sys_prompt

    def extracting_presc_data(self, image_file,location_data):
        self.system_Prompt = self.get_system_prompt(location_data)
        
        # Initialize Model
        self.model = genai.GenerativeModel(
            model_name='gemini-2.5-flash',
            safety_settings=self.Safety_Settings,
            system_instruction=self.system_Prompt
        )

        try:
            # Open the image from the stream or file path
            image = Image.open(image_file)
            
            max_width = 1024
            if image.width > max_width:
                ratio = max_width / image.width
                new_height = int(image.height * ratio)
                image = image.resize((max_width, new_height), Image.LANCZOS)

            # Generate content with stream=True
            return self.model.generate_content(image, stream=True)
            
        except Exception as e:
            raise Exception(f'Error occured in Extracting prescription data: {e}')
    




        


