from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferMemory
from typing import Dict, Any
from .tools import DriveTools, parse_user_intent
from .drive_service import GoogleDriveService
from .config import config

class DriveConversationalAgent:
    def __init__(self, drive_service: GoogleDriveService):
        self.drive_service = drive_service
        self.drive_tools = DriveTools(drive_service)
        
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-pro",
            temperature=0.7,
            google_api_key=config.GEMINI_API_KEY
        )
        
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        self.agent = self._create_agent()
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self._get_tools(),
            memory=self.memory,
            verbose=True,
            handle_parsing_errors=True
        )
    
    def _get_tools(self):
        """Get all available tools"""
        from langchain.tools import tool
        
        @tool
        def search_pdf_files() -> str:
            """Search for PDF files in the folder"""
            results = self.drive_tools.search_by_filetype('pdf', 30)
            if results:
                file_list = '\n'.join([f"📄 {f['name']}" for f in results])
                return f"Found {len(results)} PDF files:\n{file_list}"
            return "No PDF files found in the folder."
        
        @tool
        def search_spreadsheet_files() -> str:
            """Search for spreadsheet files (Excel, Sheets)"""
            results = self.drive_tools.search_by_filetype('spreadsheet', 30)
            if results:
                file_list = '\n'.join([f"📊 {f['name']}" for f in results])
                return f"Found {len(results)} spreadsheet files:\n{file_list}"
            return "No spreadsheet files found in the folder."
        
        @tool
        def search_image_files() -> str:
            """Search for image files"""
            results = self.drive_tools.search_by_filetype('image', 30)
            if results:
                file_list = '\n'.join([f"🖼️ {f['name']}" for f in results])
                return f"Found {len(results)} image files:\n{file_list}"
            return "No image files found in the folder."
        
        @tool
        def list_all_files() -> str:
            """List all files in the Google Drive folder"""
            results = self.drive_tools.search_all_files(50)
            if results:
                response = f"📁 Folder contains {len(results)} files:\n\n"
                for f in results[:20]:
                    response += f"• {f['name']}\n"
                if len(results) > 20:
                    response += f"\n... and {len(results) - 20} more files"
                return response
            return "No files found in the folder."
        
        @tool
        def search_invoices() -> str:
            """Search for invoices (looks in 'invoices' folder)"""
            results = self.drive_tools.search_in_folder('invoices', 30)
            if results:
                file_list = '\n'.join([f"📄 {f['name']}" for f in results])
                return f"Found 'invoices' folder with {len(results)} files:\n{file_list}"
            return "No 'invoices' folder found."
        
        @tool
        def search_recent_files(days: int = 7) -> str:
            """Search files modified in the last N days"""
            results = self.drive_tools.search_recent_files(days, 30)
            if results:
                file_list = '\n'.join([f"📄 {f['name']}" for f in results])
                return f"Found {len(results)} files modified in the last {days} days:\n{file_list}"
            return f"No files found modified in the last {days} days."
        
        return [search_pdf_files, search_spreadsheet_files, search_image_files, 
                list_all_files, search_invoices, search_recent_files]
    
    def _create_agent(self):
        prompt = ChatPromptTemplate.from_messages([
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "You are a Google Drive assistant. {input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        return create_openai_tools_agent(self.llm, self._get_tools(), prompt)
    
    async def process_query(self, query: str, user_id: str = None) -> Dict[str, Any]:
        intent = parse_user_intent(query)
        
        try:
            # Handle specific intents directly (faster)
            if intent['search_type'] == 'all_files':
                files = self.drive_tools.search_all_files(30)
                if files:
                    response = f"📁 Found {len(files)} files in the folder:\n\n"
                    for f in files[:15]:
                        response += f"• {f['name']}\n"
                    return {"success": True, "response": response, "files_found": len(files)}
            
            elif intent['search_type'] == 'filetype':
                file_type = intent['filters'].get('file_type')
                files = self.drive_tools.search_by_filetype(file_type, 30)
                if files:
                    type_display = {
                        'spreadsheet': '📊 Spreadsheet',
                        'image': '🖼️ Image',
                        'pdf': '📄 PDF',
                        'presentation': '📽️ Presentation'
                    }.get(file_type, file_type)
                    response = f"Found {len(files)} {type_display} files:\n\n"
                    for f in files[:15]:
                        response += f"• {f['name']}\n"
                    return {"success": True, "response": response, "files_found": len(files)}
                else:
                    return {"success": True, "response": f"No {file_type} files found in the folder.", "files_found": 0}
            
            elif intent['search_type'] == 'invoices':
                files = self.drive_tools.search_in_folder('invoices', 30)
                if files:
                    response = f"📁 Found 'invoices' folder with {len(files)} files:\n\n"
                    for f in files[:15]:
                        response += f"• {f['name']}\n"
                    return {"success": True, "response": response, "files_found": len(files)}
                else:
                    return {"success": True, "response": "Found 'invoices' folder but it appears to be empty or doesn't exist.", "files_found": 0}
            
            elif intent['search_type'] == 'recent':
                days = intent['filters'].get('days', 7)
                files = self.drive_tools.search_recent_files(days, 30)
                if files:
                    response = f"Found {len(files)} files modified in the last {days} days:\n\n"
                    for f in files[:15]:
                        response += f"• {f['name']}\n"
                    return {"success": True, "response": response, "files_found": len(files)}
                else:
                    return {"success": True, "response": f"No files found modified in the last {days} days.", "files_found": 0}
            
            elif intent['search_type'] == 'filename':
                files = self.drive_tools.search_by_filename(intent['search_term'], 30)
                if files:
                    response = f"Found {len(files)} files matching '{intent['search_term']}':\n\n"
                    for f in files[:15]:
                        response += f"• {f['name']}\n"
                    return {"success": True, "response": response, "files_found": len(files)}
                else:
                    return {"success": True, "response": f"No files found matching '{intent['search_term']}'.", "files_found": 0}
            
            # Use agent for complex queries
            response = await self.agent_executor.ainvoke({
                "input": query
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
        """Fallback direct search"""
        filters = intent.get('filters', {})
        
        if 'file_type' in filters:
            files = self.drive_tools.search_by_filetype(filters['file_type'], 20)
        elif intent.get('search_term'):
            files = self.drive_tools.search_by_filename(intent['search_term'], 20)
        else:
            files = self.drive_tools.search_all_files(20)
        
        if files:
            response_text = f"I found {len(files)} files in the folder:\n\n"
            for file in files[:10]:
                response_text += f"📄 **{file.get('name')}**\n"
                response_text += f"   Type: {file.get('mimeType', 'Unknown')}\n"
                response_text += f"   Modified: {file.get('modifiedTime', 'Unknown')[:10]}\n\n"
        else:
            response_text = "I couldn't find any files matching your search in this folder."
        
        return {
            "success": True,
            "response": response_text,
            "intent": intent,
            "files_found": len(files) if files else 0
        }
    
    def clear_memory(self):
        self.memory.clear()