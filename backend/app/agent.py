from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferMemory
from typing import Dict, Any
from .tools import DriveTools, create_tools, parse_user_intent
from .drive_service import GoogleDriveService
from .config import config

class DriveConversationalAgent:
    def __init__(self, drive_service: GoogleDriveService):
        self.drive_service = drive_service
        self.drive_tools = DriveTools(drive_service)
        
        # Initialize Gemini (no system message support)
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-pro",
            temperature=0.7,
            google_api_key=config.GEMINI_API_KEY
        )
        
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # Create LangChain-compatible tools
        self.tools = create_tools(self.drive_tools)
        self.agent = self._create_agent()
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            memory=self.memory,
            verbose=True,
            handle_parsing_errors=True
        )
    
    def _create_agent(self):
        """Create the LangChain agent with Gemini (no system message)"""
        prompt = ChatPromptTemplate.from_messages([
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "You are a helpful Google Drive assistant. {input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        return create_openai_tools_agent(self.llm, self.tools, prompt)
    
    async def process_query(self, query: str, user_id: str = None) -> Dict[str, Any]:
        """Process user query and return response"""
        intent = parse_user_intent(query)
        
        try:
            response = await self.agent_executor.ainvoke({
                "input": f"User asked: {query}. Please search Google Drive and respond helpfully.",
                "user_id": user_id
            })
            
            return {
                "success": True,
                "response": response.get("output", "I couldn't process that request."),
                "intent": intent
            }
        except Exception as e:
            print(f"Agent error: {e}")
            return await self._direct_search(query, intent)
    
    async def _direct_search(self, query: str, intent: Dict) -> Dict[str, Any]:
        """Direct search without agent (fallback)"""
        filters = intent.get('filters', {})
        
        if 'file_type' in filters:
            files = self.drive_service.search_files(
                file_types=[filters['file_type']],
                max_results=20
            )
        elif 'date_range' in filters:
            days_map = {
                'today': 1,
                'yesterday': 2,
                'last_week': 7,
                'last_month': 30,
                'last_3_months': 90,
                'last_year': 365
            }
            days = days_map.get(filters['date_range'], 30)
            files = self.drive_service.get_recent_files(days=days, max_results=20)
        elif intent.get('search_term'):
            files = self.drive_service.search_files(
                query=intent['search_term'],
                max_results=20
            )
        else:
            files = self.drive_service.search_files(max_results=20)
        
        if files:
            response_text = f"I found {len(files)} files in the folder:\n\n"
            for file in files[:10]:
                response_text += f"📄 **{file.get('name')}**\n"
                response_text += f"   Type: {file.get('mimeType', 'Unknown')}\n"
                response_text += f"   Modified: {file.get('modifiedTime', 'Unknown')[:10]}\n\n"
            
            if len(files) > 10:
                response_text += f"...and {len(files) - 10} more files."
        else:
            response_text = "I couldn't find any files matching your search in this folder. Try using different keywords or check if the folder contains such files."
        
        return {
            "success": True,
            "response": response_text,
            "intent": intent,
            "files_found": len(files)
        }
    
    def clear_memory(self):
        """Clear conversation memory"""
        self.memory.clear()