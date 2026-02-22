from dotenv import load_dotenv,find_dotenv
import os
import google.generativeai as genai
from Extracting_prescription_data import Handwritting_Extraction

class warnings():
    
    def get_warning_systemPrompt(self):
        
      self.sys_prom=f"""
      You are an expert Medical Safety Analyst. Your task is to analyze a list of transcribed medications and
      provide critical safety information. 
    
      The user is providing the full transcribed text from a patient prescription.
    
      ## Primary Task
      1. Scan the text for all 'Drug Name', 'Dosage', and 'Duration' entries.
      2. Identify and list any potential drug-drug interactions (DDI) based on the combinations found.
      3. Identify any medications with known severe side effects (Black Box Warnings, etc.) or high dependency risk.
      4. Flag any unusually high dosages or durations compared to standard therapeutic guidelines.
      5. **Crucially:** If the provided text mentions a drug name is 'N/A' or if the dosage/duration is incomplete, flag the drug and request clarity.
      ## Input Text to Analyze
      ---
      Given as user prompt.
      ---
    
      ## Output Format
      You MUST return a simple, clean list of warnings or findings. Do not include any conversational text. 
      If there are no issues, simply return: 'No critical safety issues found based on the extracted data.'
    
      Format each warning clearly:
      - [INTERACTION]: Drug A + Drug B: Risk of Severe Hypotension.
      - [DOSAGE ISSUE]: Amoxicillin: Dosage of 2000mg/day is unusually high. Review required.
      - [SIDE EFFECT]: Drug X: Monitor for increased risk of liver toxicity.
      - [DATA GAP]: Drug Y: Dosage is missing (N/A). Cannot confirm safety profile.
    
      """
      return self.sys_prom
    def analyzing_critical_warnings(self,Data):
        load_dotenv(override=True)
        api_key = os.getenv('GEMINI_API_KEY')
        if api_key:
            genai.configure(api_key=api_key)

        self.system_insturctions=self.get_warning_systemPrompt()
        self.Model=genai.GenerativeModel(model_name='gemini-2.5-flash',system_instruction=self.system_insturctions)

        self.response=self.Model.generate_content(f'Analyze the above data :{Data}')
        self.result=self.response.text
        self.response_list=self.result.split('\n')
        return self.response_list



