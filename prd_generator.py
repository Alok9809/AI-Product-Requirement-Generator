import os
import json
import logging
from datetime import datetime
from bson import ObjectId
from dotenv import load_dotenv

# Load env variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LLMService:
    """Helper service to connect to Gemini API using available SDKs (google-genai or google-generativeai)."""
    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not self.api_key:
            logger.warning("No Gemini API key found in GEMINI_API_KEY or GOOGLE_API_KEY env variables.")
        
        self.client_type = None
        self.client = None
        
        # Try importing new google-genai SDK first
        try:
            from google import genai
            from google.genai import types
            self.genai = genai
            self.types = types
            if self.api_key:
                self.client = genai.Client(api_key=self.api_key)
                self.client_type = "google-genai"
                logger.info("Successfully initialized new google-genai Client.")
        except ImportError:
            logger.info("google-genai SDK not available. Trying legacy google-generativeai SDK.")
        
        # Fallback to legacy google-generativeai SDK
        if not self.client_type:
            try:
                import google.generativeai as legacy_genai
                self.legacy_genai = legacy_genai
                if self.api_key:
                    legacy_genai.configure(api_key=self.api_key)
                    self.client_type = "google-generativeai"
                    logger.info("Successfully configured legacy google-generativeai SDK.")
            except ImportError:
                logger.error("Neither google-genai nor google-generativeai SDK is installed.")

    def generate_json(self, system_prompt: str, user_prompt: str) -> dict:
        """Call Gemini to generate content and parse it as JSON."""
        if not self.api_key:
            return self._get_mock_fallback(system_prompt, user_prompt)
            
        try:
            raw_text = ""
            model_name = "gemini-2.5-flash" if self.client_type == "google-genai" else "gemini-1.5-flash"
            
            logger.info(f"Generating content using {self.client_type} with model {model_name}...")
            
            if self.client_type == "google-genai":
                # Using new SDK
                config = self.types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    response_mime_type="application/json",
                    temperature=0.2
                )
                response = self.client.models.generate_content(
                    model=model_name,
                    contents=user_prompt,
                    config=config
                )
                raw_text = response.text
            elif self.client_type == "google-generativeai":
                # Using legacy SDK
                model = self.legacy_genai.GenerativeModel(
                    model_name=model_name,
                    system_instruction=system_prompt
                )
                response = model.generate_content(
                    user_prompt,
                    generation_config={"response_mime_type": "application/json", "temperature": 0.2}
                )
                raw_text = response.text
            else:
                raise Exception("No client initialized.")
                
            return self._parse_json_response(raw_text)
            
        except Exception as e:
            logger.error(f"Error calling LLM API: {str(e)}. Falling back to structured default data.")
            return self._get_mock_fallback(system_prompt, user_prompt)

    def _parse_json_response(self, text: str) -> dict:
        """Parse raw response text, cleaning up code block backticks if present."""
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        return json.loads(text)

    def _get_mock_fallback(self, system_prompt: str, user_prompt: str) -> dict:
        """Generate high-quality static mock responses for testing/offline scenarios."""
        logger.info("Providing mock fallback data...")
        # Check if the prompt is for Business Analyst or Product Manager
        if "personas" in system_prompt.lower():
            # Business Analyst Mock Output
            return {
                "problem_statement": "The existing workflow for product idea realization is highly fragmented. Teams face issues in translating high-level vision into functional requirements, resulting in misalignment, missed details, and prolonged launch delays.",
                "personas": [
                    {
                        "name": "Sarah Miller",
                        "role": "Product Leader",
                        "details": "Manage multiple roadmap priorities in a fast-paced environment. Wants structured specifications quickly to align developers.",
                        "pain_points": "Spends hours writing PRDs from scratch; developers complain about missing edge cases.",
                        "goals": "Generate high-quality initial requirements in minutes to jumpstart development sprint planning."
                    },
                    {
                        "name": "Alex Chen",
                        "role": "Tech Lead / Architect",
                        "details": "Technical owner responsible for sizing features, planning sprints, and ensuring system design aligns with product requirements.",
                        "pain_points": "Vague user stories that require multiple follow-ups, leading to coding delays and rework.",
                        "goals": "Receive detailed acceptance criteria and non-functional requirements to write clean, modular code."
                    }
                ],
                "risks": [
                    {
                        "risk": "Hallucinations or generic requirements that do not fit the specific market niche.",
                        "mitigation": "Provide rich context parameters (industry, platform, guidelines) in UI inputs and implement feedback loops."
                    },
                    {
                        "risk": "Data privacy and intellectual property concerns with sending proprietary product ideas to public LLM API.",
                        "mitigation": "Allow configuring private API keys and avoid persisting sensitive user input on shared platforms."
                    }
                ]
            }
        else:
            # Product Manager Mock Output
            return {
                "user_stories": [
                    {
                        "title": "Enter Product Idea",
                        "role": "Product Manager",
                        "want": "to input a high-level product idea with specific target constraints",
                        "benefit": "I can quickly initiate a comprehensive requirements generation workflow",
                        "acceptance_criteria": "1. Input field must support up to 1000 characters.\n2. Optional inputs for target audience and constraints should be available.\n3. Validate that input is not empty before submitting."
                    },
                    {
                        "title": "View Sectioned Output",
                        "role": "Product Designer",
                        "want": "to view generated requirements split into tabbed sections (personas, requirements, risks)",
                        "benefit": "I can review specific aspects of the PRD easily without reading a wall of text",
                        "acceptance_criteria": "1. UI should display distinct tabs for Personas, Stories, Requirements, and Risks.\n2. Elements should use cards and lists with clear visual hierarchy."
                    }
                ],
                "functional_requirements": [
                    {
                        "module": "Input & Configuration",
                        "feature": "Rich Context Inputs",
                        "description": "Provide specialized drop-downs for target industry, target platforms (iOS, Android, Web), and key regulations (HIPAA, GDPR).",
                        "priority": "High"
                    },
                    {
                        "module": "PRD Management",
                        "feature": "Export to Markdown",
                        "description": "Add a one-click download button that compiles the parsed JSON structure into a clean markdown document (.md).",
                        "priority": "High"
                    }
                ],
                "non_functional_requirements": [
                    {
                        "category": "Performance",
                        "description": "The requirements generation workflow should complete in under 15 seconds, providing real-time progress indicators."
                    },
                    {
                        "category": "Usability",
                        "description": "Streamlit frontend must follow HSL modern color palette guidelines and be responsive across desktop and tablet screen sizes."
                    }
                ]
            }

class BusinessAnalystAgent:
    """Agent responsible for initial product analysis, defining the problem, personas, and risks."""
    def __init__(self, llm_service: LLMService):
        self.llm = llm_service
        self.system_prompt = (
            "You are an expert Business Analyst. Your role is to analyze a product idea and define the core problem it solves, "
            "detailed user personas, and major project risks with mitigations.\n"
            "You must return your output strictly in JSON format matching this schema:\n"
            "{\n"
            "  \"problem_statement\": \"A clear explanation of the core problem and pain points this product addresses\",\n"
            "  \"personas\": [\n"
            "    {\n"
            "      \"name\": \"Name of persona\",\n"
            "      \"role\": \"Role/Title\",\n"
            "      \"details\": \"Brief background or context about this person\",\n"
            "      \"pain_points\": \"Core pain points or challenges they face\",\n"
            "      \"goals\": \"What they aim to achieve using this product\"\n"
            "    }\n"
            "  ],\n"
            "  \"risks\": [\n"
            "    {\n"
            "      \"risk\": \"Description of potential risk (technical, adoption, market)\",\n"
            "      \"mitigation\": \"Actionable strategy to mitigate this risk\"\n"
            "    }\n"
            "  ]\n"
            "}"
        )

    def analyze(self, idea: str, target_audience: str = "General", constraints: str = "None") -> dict:
        user_prompt = (
            f"Analyze the following product idea:\n"
            f"Idea: {idea}\n"
            f"Target Audience: {target_audience}\n"
            f"Constraints: {constraints}\n\n"
            f"Provide a structured analysis in JSON."
        )
        return self.llm.generate_json(self.system_prompt, user_prompt)

class ProductManagerAgent:
    """Agent responsible for translating BA analysis into actionable user stories and functional/non-functional requirements."""
    def __init__(self, llm_service: LLMService):
        self.llm = llm_service
        self.system_prompt = (
            "You are an expert Product Manager. Your role is to take a product idea along with a Business Analyst's analysis "
            "and construct user stories, functional requirements, and non-functional requirements.\n"
            "You must return your output strictly in JSON format matching this schema:\n"
            "{\n"
            "  \"user_stories\": [\n"
            "    {\n"
            "      \"title\": \"Short action-oriented title\",\n"
            "      \"role\": \"The type of user (e.g. Patient, Doctor)\",\n"
            "      \"want\": \"The feature/action they want to perform\",\n"
            "      \"benefit\": \"The value or benefit they gain\",\n"
            "      \"acceptance_criteria\": \"Detailed numbered checklist of when this story is completed\"\n"
            "    }\n"
            "  ],\n"
            "  \"functional_requirements\": [\n"
            "    {\n"
            "      \"module\": \"Core module/section name (e.g., Auth, Dashboard)\",\n"
            "      \"feature\": \"Feature name\",\n"
            "      \"description\": \"Detailed description of functional behavior\",\n"
            "      \"priority\": \"High/Medium/Low\"\n"
            "    }\n"
            "  ],\n"
            "  \"non_functional_requirements\": [\n"
            "    {\n"
            "      \"category\": \"Category (e.g. Security, Performance, Scalability, Compliance)\",\n"
            "      \"description\": \"Specific, measurable constraint\"\n"
            "    }\n"
            "  ]\n"
            "}"
        )

    def analyze(self, idea: str, ba_analysis: dict) -> dict:
        user_prompt = (
            f"Create requirements based on the product idea: '{idea}'\n\n"
            f"Business Analyst Analysis:\n"
            f"{json.dumps(ba_analysis, indent=2)}\n\n"
            f"Provide a structured requirements output in JSON."
        )
        return self.llm.generate_json(self.system_prompt, user_prompt)

class DatabaseManager:
    """Manages connection to MongoDB and CRUD operations, falling back to in-memory store if connection fails."""
    def __init__(self):
        self.uri = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
        self.db_name = "prd_generator_db"
        self.collection_name = "generated_prds"
        self.client = None
        self.db = None
        self.collection = None
        self.is_connected = False
        
        # In-memory storage fallback
        self.in_memory_db = []

        try:
            from pymongo import MongoClient
            import pymongo.errors
            # Short timeout to avoid blocking startup if MongoDB is not running
            self.client = MongoClient(self.uri, serverSelectionTimeoutMS=2000)
            # Force a command to test connection
            self.client.server_info()
            self.db = self.client[self.db_name]
            self.collection = self.db[self.collection_name]
            self.is_connected = True
            logger.info("Successfully connected to MongoDB.")
        except Exception as e:
            logger.warning(f"MongoDB connection failed: {str(e)}. Running with in-memory fallback database.")

    def save_prd(self, idea: str, target_audience: str, constraints: str, ba_data: dict, pm_data: dict) -> str:
        """Saves generated PRD data and returns the unique string ID of the saved document."""
        full_markdown = compile_prd_markdown(idea, target_audience, constraints, ba_data, pm_data)
        
        doc = {
            "timestamp": datetime.utcnow(),
            "product_idea": idea,
            "target_audience": target_audience,
            "constraints": constraints,
            "ba_data": ba_data,
            "pm_data": pm_data,
            "full_prd_markdown": full_markdown
        }

        if self.is_connected:
            try:
                res = self.collection.insert_one(doc)
                return str(res.inserted_id)
            except Exception as e:
                logger.error(f"Error saving to MongoDB: {str(e)}. Saving to in-memory database.")
        
        # Fallback to in-memory
        doc["_id"] = ObjectId()
        self.in_memory_db.append(doc)
        return str(doc["_id"])

    def get_history(self) -> list:
        """Retrieves history list of saved product requirements, sorted by timestamp descending."""
        history = []
        if self.is_connected:
            try:
                cursor = self.collection.find({}, {"product_idea": 1, "timestamp": 1}).sort("timestamp", -1)
                for doc in cursor:
                    history.append({
                        "id": str(doc["_id"]),
                        "product_idea": doc["product_idea"],
                        "timestamp": doc["timestamp"]
                    })
                return history
            except Exception as e:
                logger.error(f"Error reading history from MongoDB: {str(e)}.")
        
        # In-memory history
        for doc in reversed(self.in_memory_db):
            history.append({
                "id": str(doc["_id"]),
                "product_idea": doc["product_idea"],
                "timestamp": doc["timestamp"]
            })
        return history

    def get_prd_by_id(self, prd_id: str) -> dict:
        """Retrieve full PRD data dict by string ID."""
        if self.is_connected:
            try:
                doc = self.collection.find_one({"_id": ObjectId(prd_id)})
                if doc:
                    doc["id"] = str(doc["_id"])
                    return doc
            except Exception as e:
                logger.error(f"Error finding document by ID in MongoDB: {str(e)}.")
        
        # In-memory retrieval
        for doc in self.in_memory_db:
            if str(doc["_id"]) == prd_id:
                doc_copy = doc.copy()
                doc_copy["id"] = str(doc_copy["_id"])
                return doc_copy
        return None

    def delete_prd(self, prd_id: str) -> bool:
        """Delete PRD from database."""
        if self.is_connected:
            try:
                res = self.collection.delete_one({"_id": ObjectId(prd_id)})
                return res.deleted_count > 0
            except Exception as e:
                logger.error(f"Error deleting document from MongoDB: {str(e)}.")
                return False
        
        # In-memory deletion
        for idx, doc in enumerate(self.in_memory_db):
            if str(doc["_id"]) == prd_id:
                self.in_memory_db.pop(idx)
                return True
        return False

def compile_prd_markdown(idea: str, target_audience: str, constraints: str, ba_data: dict, pm_data: dict) -> str:
    """Format parsed JSON outputs from BA and PM agents into a professional markdown document."""
    
    # 1. Title & Metadata
    md = f"# Product Requirement Document (PRD)\n\n"
    md += f"**Product Idea:** {idea}\n"
    md += f"**Target Audience:** {target_audience}\n"
    md += f"**Key Constraints:** {constraints}\n"
    md += f"**Generated At:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"
    md += "---\n\n"

    # 2. Problem Statement
    md += "## 1. Problem Statement\n"
    md += f"{ba_data.get('problem_statement', 'No problem statement provided.')}\n\n"
    
    # 3. Target Personas
    md += "## 2. Target Personas\n"
    for idx, persona in enumerate(ba_data.get("personas", []), 1):
        md += f"### Persona {idx}: {persona.get('name', 'N/A')} ({persona.get('role', 'N/A')})\n"
        md += f"- **Details:** {persona.get('details', 'N/A')}\n"
        md += f"- **Pain Points:** {persona.get('pain_points', 'N/A')}\n"
        md += f"- **Goals:** {persona.get('goals', 'N/A')}\n\n"

    # 4. User Stories
    md += "## 3. User Stories\n"
    for idx, story in enumerate(pm_data.get("user_stories", []), 1):
        md += f"### US-{idx:03d}: {story.get('title', 'N/A')}\n"
        md += f"**As a** {story.get('role', 'N/A')},  \n"
        md += f"**I want to** {story.get('want', 'N/A')},  \n"
        md += f"**So that** {story.get('benefit', 'N/A')}.  \n\n"
        md += "**Acceptance Criteria:**\n"
        ac = story.get('acceptance_criteria', 'N/A')
        # Formatting acceptance criteria lines
        if isinstance(ac, str):
            md += f"{ac}\n\n"
        elif isinstance(ac, list):
            for criteria in ac:
                md += f"- {criteria}\n"
            md += "\n"

    # 5. Functional Requirements
    md += "## 4. Functional Requirements\n"
    md += "| Module | Feature | Description | Priority |\n"
    md += "| :--- | :--- | :--- | :--- |\n"
    for req in pm_data.get("functional_requirements", []):
        md += f"| {req.get('module', 'N/A')} | {req.get('feature', 'N/A')} | {req.get('description', 'N/A')} | **{req.get('priority', 'Medium')}** |\n"
    md += "\n"

    # 6. Non-Functional Requirements
    md += "## 5. Non-Functional Requirements\n"
    for req in pm_data.get("non_functional_requirements", []):
        md += f"- **[{req.get('category', 'General')}]** {req.get('description', 'N/A')}\n"
    md += "\n"

    # 7. Risks & Mitigations
    md += "## 6. Risks & Mitigations\n"
    md += "| Risk Description | Mitigation Strategy |\n"
    md += "| :--- | :--- |\n"
    for risk in ba_data.get("risks", []):
        md += f"| {risk.get('risk', 'N/A')} | {risk.get('mitigation', 'N/A')} |\n"
    md += "\n"

    return md
