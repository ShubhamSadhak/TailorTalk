from typing import Dict, Any, List
from .tools import DriveTools, parse_user_intent
from .drive_service import GoogleDriveService

class DriveConversationalAgent:
    def __init__(self, drive_service: GoogleDriveService):
        self.drive_service = drive_service
        self.drive_tools = DriveTools(drive_service)
        self.memory: Dict[str, List[Dict[str, Any]]] = {}
    
    async def process_query(self, query: str, user_id: str = None) -> Dict[str, Any]:
        """Process user query and return response"""
        current_user = user_id or "default"
        intent = parse_user_intent(query)
        intent = self._merge_with_context(current_user, intent, query)
        result = await self._direct_search(query, intent)
        self._remember_query(current_user, query, intent, result)
        return result
    
    async def _direct_search(self, query: str, intent: Dict) -> Dict[str, Any]:
        """Direct search without agent (fallback)"""
        filters = intent.get('filters', {})
        
        # Apply filters based on intent
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
        
        # Format response
        if files:
            response_text = f"I found {len(files)} files:\n\n"
            for file in files[:10]:  # Limit to 10 for readability
                response_text += f"📄 **{file.get('name')}**\n"
                response_text += f"   Type: {file.get('mimeType', 'Unknown')}\n"
                response_text += f"   Modified: {file.get('modifiedTime', 'Unknown')[:10]}\n\n"
            
            if len(files) > 10:
                response_text += f"...and {len(files) - 10} more files."
        else:
            response_text = "I couldn't find any files matching your search. Try using different keywords or filters."
        
        return {
            "success": True,
            "response": response_text,
            "intent": intent,
            "files_found": len(files)
        }
    
    def _merge_with_context(self, user_id: str, intent: Dict[str, Any], query: str) -> Dict[str, Any]:
        """Apply light conversational context for follow-up searches."""
        history = self.memory.get(user_id, [])
        if not history:
            return intent

        latest = history[-1]["intent"]
        query_lower = query.lower()
        follow_up_markers = ["recent", "only", "those", "them", "same", "again"]

        if any(marker in query_lower for marker in follow_up_markers):
            if "file_type" not in intent["filters"] and "file_type" in latest.get("filters", {}):
                intent["filters"]["file_type"] = latest["filters"]["file_type"]
            if not intent.get("search_term") and latest.get("search_term"):
                intent["search_term"] = latest["search_term"]

        return intent

    def _remember_query(
        self,
        user_id: str,
        query: str,
        intent: Dict[str, Any],
        result: Dict[str, Any]
    ) -> None:
        history = self.memory.setdefault(user_id, [])
        history.append({
            "query": query,
            "intent": intent,
            "files_found": result.get("files_found", 0),
        })
        if len(history) > 20:
            del history[:-20]

    def clear_memory(self):
        """Clear conversation memory"""
        self.memory.clear()
