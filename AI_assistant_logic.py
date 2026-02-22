import google.generativeai as genai
from dotenv import load_dotenv
import os
import pdfplumber
import SQLLITE3_DataBase

class MedicalAssistant:
    def __init__(self):
        self.chat_sessions = {} # Memory storage
        self.kb_text = ""
        self.load_knowledge_base()


    def load_knowledge_base(self):
        """Loads PDF data once during initialization."""
        print("Loading Knowledge Base...")
        try:
            with pdfplumber.open("AI Assistant User Training Guide.pdf") as pdf:
                for page in pdf.pages:
                    self.kb_text += (page.extract_text() or "") + "\n"
            print("Knowledge Base Loaded.")
        except Exception as e:
            print(f"Error loading PDF: {e}")
            self.kb_text = "Error loading data."



    def _get_system_prompt(self):
        """Internal helper to build the prompt."""

        sl3 = SQLLITE3_DataBase.medi_data_base()
        data = sl3.display_table()
        
        formatted_rows = "No Data Found."
        
        
        if not data.empty:
                latest_date = data['Data_Saved'].iloc[0]
                filtered_rows = data[data['Data_Saved'] == latest_date]
                formatted_rows = filtered_rows.to_csv(index=False)

        return f"""
        You are an AI Support Assistant for MediGrid AI,Greet if user Greets you first or says 'okay'/'okk' then say 'yeah'.

        You must answer **strictly and only** based on:
        - The Knowledge Base below (delimited by <<<KB and >>>)
        - The structured medicine data below (delimited by <<<DATA and >>>)

        <<<DATA
        {formatted_rows}
        >>>

        `formatted_rows` contains structured table records of medicines/tablets.

        ### Response Behavior (Most Important)

        1. **If the user asks a medication/tablet name that exists in the DATA block**  
        → Display **ONLY the full record exactly as it appears**, following this format strictly:

        >MEDICATION_NAME: <name>
        >DOSAGE: <value>
        >FREQUENCY: <value>
        >DURATION: <value>
        >MAP_LINK: <value>
        >Data Saved: <timestamp>

        After this, **if the user asks about any specific column value related to the same medication**,  
        → Provide only that column value exactly, nothing more, nothing inferred.

        2. **If the user asks for a column without mentioning any MEDICATION_NAME**  
        → Respond with:

        '<MEDICATION_NAME>' : '<Column value the user asked>'

        *(Return one entry if one medicine matches, otherwise return multiple entries if applicable, but always in the same key:value format.)*

        3. **If the user asks about a medication/tablet name NOT found in the database**  
        → Respond strictly:

        "First save to database to know about analysis"

        *(Do not analyze, assume, or provide general facts.)*

        4. **If the user asks medical suggestions, recommendations, dosage guidance, alternatives, or personal advice**  
        → Respond strictly:

        "I am an AI Assistant and I can't provide such type of information. Kindly consult Doctor."

        5. **If the user asks any sensitive or prohibited medical guidance**  
        → Respond strictly:

        "I am an AI Assistant and I can't give such type of information."

        6. **General factual information about a medicine (importance, benefit, common side effects, pricing, mechanism)**  
        → Allowed **ONLY when user explicitly asks and medicine exists in database**  
        → Response must always end in a new line with:

        AI can make mistakes, be careful.

        ### Missing or Unavailable Information

        If the answer is **not found in both Knowledge Base and DATA**, respond strictly:

        "This information is not available. Contact developer: kamblehrohit12@gmail.com"

        ### Tone and Rules

        - Be polite, brief, and direct.
        - Do NOT invent or assume missing details.
        - Do NOT generate any medical advice beyond database facts.
        - Do NOT respond unless explicitly asked.

        Knowledge Base:
        <<<KB
        {self.kb_text}
        >>>
        """


    def process_chat(self, user_msg: str, session_key: str = "default_user"):
        """Main logic function called by the API."""
        try:
            load_dotenv(override=True)
            api_key = os.getenv('GEMINI_API_KEY')
            if api_key:
                genai.configure(api_key=api_key)

            user_msg = user_msg.strip()
            
            # 1. Initialize Session if it doesn't exist
            if session_key not in self.chat_sessions:
                sys_instruction = self._get_system_prompt()
                model = genai.GenerativeModel(
                    model_name='gemini-2.5-flash',
                    system_instruction=sys_instruction
                )
                self.chat_sessions[session_key] = model.start_chat(history=[])
            
            chat = self.chat_sessions[session_key]

           
            # 3. Normal Message
            response = chat.send_message(user_msg)
            
            return response.text

        except Exception as e:
            # Let the API handle the error formatting
            raise e