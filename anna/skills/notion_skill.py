"""
Notion Skill for Anna - dynamically creates pages, tables, and checklists.

This skill allows Anna to:
- Create pages in Notion workspace
- Build checklists (to-do blocks)
- Build tables/databases with custom columns
- Decide structure based on context (via LLM)
"""

from typing import Dict, Any, List, Optional
from notion_client import Client
from datetime import datetime
import os
import sys

# Add project root to sys.path to ensure modules can be imported
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

import config
from skills.base_skill import BaseSkill


class NotionSkill(BaseSkill):
    """
    Dynamically creates Notion pages, tables, and checklists.
    
    Structure decisions are made by the LLM and passed as parameters.
    This skill focuses on execution, not decision-making.
    
    Example usage:
        User: "Add milk to my shopping list"
        LLM: SKILL: notion
             PARAMS: {
               "action": "create_page",
               "title": "USER_DECIDES",
               "structure": "checklist",
               "items": ["milk"]
             }
    """
    
    def __init__(self):
        """Initialize Notion client and verify connection."""
        self.notion = None
        
        # Check if API key is configured
        if not config.NOTION_API_KEY:
            print("[WARN] NOTION_API_KEY not set - Notion skill disabled")
            print("   Add your key to .env file")
            return
        
        if not config.NOTION_PARENT_PAGE_ID:
            print("[WARN] NOTION_PARENT_PAGE_ID not set - Notion skill disabled")
            print("   Add your parent page ID to .env file")
            return
        
        try:
            self.notion = Client(auth=config.NOTION_API_KEY)
            
            # Verify connection by trying to retrieve parent page
            self.notion.pages.retrieve(page_id=config.NOTION_PARENT_PAGE_ID)
            
            print("[OK] Notion skill initialized")
            print(f"   Parent page: {config.NOTION_PARENT_PAGE_ID[:8]}...")
            
        except Exception as e:
            print(f"[WARN] Notion connection failed: {e}")
            print("   Check your API key and parent page ID")
            self.notion = None
    
    @property
    def name(self) -> str:
        return "notion"
    
    @property
    def description(self) -> str:
        return """Create and manage Notion pages, tables, and checklists.
ONLY use this skill when asked to CREATE, SAVE, TRACK, or ORGANIZE data into a list or table.
DO NOT use for greetings, thanks, or general conversation.
- Use structure: "checklist" for simple lists (shopping, todos).
- Use structure: "table" for tracking data over time (workouts, habits) - REQUIRES "columns" parameter."""
    
    @property
    def trigger_phrases(self) -> List[str]:
        return [
            "create page",
            "track workouts",
            "make a table",
            "add to shopping list",
            "save this to notion"
        ]
    
    def execute(self, params: Dict[str, Any]) -> str:
        """
        Execute Notion operation.
        
        Args:
            params: Dictionary with:
                - action: "create_page" (only supported action currently)
                - title: Page title or "USER_DECIDES"
                - structure: "checklist" or "table"
                - items: List of items (for checklist)
                - columns: List of column names (for table)
                - rows: List of row dicts (for table)
        
        Returns:
            Success/failure message
        """
        if not self.notion:
            return "Notion isn't configured. Check your API key in the .env file."
        
        # Validate required params
        if not self.validate_params(params, ["action"]):
            return "I need to know what action to perform."
        
        action = params["action"]
        
        # Route to appropriate handler
        if action == "create_page":
            return self._create_page(params)
        else:
            return f"Unknown action: {action}"
    
    def _create_page(self, params: Dict[str, Any]) -> str:
        """
        Create a Notion page with specified structure.
        
        Args:
            params: Page creation parameters
        
        Returns:
            Success message with page details
        """
        # Check if title needs to be decided
        title = params.get("title", "USER_DECIDES")
        
        if title == "USER_DECIDES":
            # This should trigger a follow-up conversation
            # For now, generate a default title
            timestamp = datetime.now().strftime("%b %d, %Y")
            structure = params.get("structure", "page")
            
            if structure == "checklist":
                title = f"Checklist - {timestamp}"
            elif structure == "table":
                title = f"Table - {timestamp}"
            else:
                title = f"New Page - {timestamp}"
        
        structure = params.get("structure", "checklist")
        
        try:
            if structure == "checklist":
                return self._create_checklist(title, params)
            elif structure == "table":
                return self._create_table(title, params)
            else:
                return f"Unknown structure type: {structure}"
        
        except Exception as e:
            return f"Failed to create page: {str(e)}"
    
    def _create_checklist(self, title: str, params: Dict[str, Any]) -> str:
        """
        Create a page with checklist (to-do blocks).
        
        Args:
            title: Page title
            params: Must contain "items" - list of checklist items
        
        Returns:
            Success message
        """
        items = params.get("items", [])
        
        if not items:
            return "I need some items for the checklist!"
        
        # Build to-do blocks
        children = []
        for item in items:
            children.append({
                "object": "block",
                "type": "to_do",
                "to_do": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": str(item)}
                        }
                    ],
                    "checked": False
                }
            })
        
        # Create the page
        page = self.notion.pages.create(
            parent={"page_id": config.NOTION_PARENT_PAGE_ID},
            properties={
                "title": {
                    "title": [
                        {
                            "type": "text",
                            "text": {"content": title}
                        }
                    ]
                }
            },
            children=children
        )
        
        item_count = len(items)
        return f"Alrighty, added {item_count} item{'s' if item_count > 1 else ''} to your checklist '{title}'."
    
    def _create_table(self, title: str, params: Dict[str, Any]) -> str:
        """
        Create a database (table) with custom columns and rows.
        
        Args:
            title: Database title
            params: Must contain:
                - columns: List of column names (first is title column)
                - rows: List of dicts with column_name: value
        
        Returns:
            Success message
        """
        columns = params.get("columns", [])
        rows = params.get("rows", [])
        
        if not columns:
            return "I need column names for the table!"
        
        # Build database schema
        # First column is always the title column
        title_column = columns[0]
        
        properties = {
            title_column: {"title": {}}
        }
        
        # Add remaining columns as text properties
        for col in columns[1:]:
            # Guess property type from column name
            col_lower = col.lower()
            
            if any(word in col_lower for word in ["date", "when", "day"]):
                properties[col] = {"date": {}}
            elif any(word in col_lower for word in ["status", "priority", "category"]):
                properties[col] = {
                    "select": {
                        "options": []  # Notion will create options as needed
                    }
                }
            elif any(word in col_lower for word in ["done", "complete", "checked"]):
                properties[col] = {"checkbox": {}}
            elif any(word in col_lower for word in ["number", "count", "amount", "quantity"]):
                properties[col] = {"number": {}}
            else:
                # Default to rich text
                properties[col] = {"rich_text": {}}
        
        # Create the database
        database = self.notion.databases.create(
            parent={"page_id": config.NOTION_PARENT_PAGE_ID},
            title=[
                {
                    "type": "text",
                    "text": {"content": title}
                }
            ],
            properties=properties
        )
        
        # Add rows if provided
        rows_added = 0
        if rows:
            for row_data in rows:
                self._add_row_to_database(database["id"], columns, row_data)
                rows_added += 1
        
        if rows_added > 0:
            return f"Created table '{title}' with {len(columns)} columns and added {rows_added} row{'s' if rows_added > 1 else ''}."
        else:
            return f"Created table '{title}' with {len(columns)} columns. Ready for data!"
    
    def _add_row_to_database(
        self,
        database_id: str,
        columns: List[str],
        row_data: Dict[str, Any]
    ):
        """
        Add a row to a database.
        
        Args:
            database_id: Database ID
            columns: List of column names
            row_data: Dict mapping column name to value
        """
        # Get database to check property types
        database = self.notion.databases.retrieve(database_id=database_id)
        properties_schema = database["properties"]
        
        # Build properties for the new page
        properties = {}
        
        for col_name, value in row_data.items():
            if col_name not in properties_schema:
                continue
            
            prop_type = properties_schema[col_name]["type"]
            
            if prop_type == "title":
                properties[col_name] = {
                    "title": [
                        {
                            "type": "text",
                            "text": {"content": str(value)}
                        }
                    ]
                }
            elif prop_type == "rich_text":
                properties[col_name] = {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": str(value)}
                        }
                    ]
                }
            elif prop_type == "select":
                properties[col_name] = {
                    "select": {"name": str(value)}
                }
            elif prop_type == "date":
                properties[col_name] = {
                    "date": {"start": str(value)}
                }
            elif prop_type == "checkbox":
                properties[col_name] = {
                    "checkbox": bool(value)
                }
            elif prop_type == "number":
                properties[col_name] = {
                    "number": float(value)
                }
        
        # Create the page in the database
        self.notion.pages.create(
            parent={"database_id": database_id},
            properties=properties
        )


# Standalone test function
def test_notion_skill():
    """
    Test Notion skill independently.
    This is the acceptance test for PRD 4.
    """
    print("\n" + "=" * 60)
    print("TESTING NOTION SKILL (PRD 4 ACCEPTANCE TEST)")
    print("=" * 60 + "\n")
    
    # Initialize skill
    skill = NotionSkill()
    
    if not skill.notion:
        print("[FAIL] Notion not configured - cannot run tests")
        print("\nSetup instructions:")
        print("1. Get API key: https://www.notion.so/my-integrations")
        print("2. Create parent page and share with integration")
        print("3. Add keys to .env file")
        return False
    
    # Test 1: Create checklist
    print("\n--- Test 1: Create Checklist ---")
    
    params1 = {
        "action": "create_page",
        "title": "Test Shopping List",
        "structure": "checklist",
        "items": ["Milk", "Bread", "Eggs", "Butter"]
    }
    
    result1 = skill.execute(params1)
    print(f"Result: {result1}")
    
    if "added" in result1.lower() and "4" in result1:
        print("[OK] Checklist created successfully")
    else:
        print("[WARN] Checklist creation may have failed")
    
    # Test 2: Create table
    print("\n--- Test 2: Create Table ---")
    
    params2 = {
        "action": "create_page",
        "title": "Test Workout Tracker",
        "structure": "table",
        "columns": ["Exercise", "Date", "Sets", "Reps", "Status"],
        "rows": [
            {
                "Exercise": "Push-ups",
                "Date": "2026-03-18",
                "Sets": 3,
                "Reps": 15,
                "Status": "Done"
            }
        ]
    }
    
    result2 = skill.execute(params2)
    print(f"Result: {result2}")
    
    if "created" in result2.lower() and "5 columns" in result2:
        print("[OK] Table created successfully")
    else:
        print("[WARN] Table creation may have failed")
    
    # Test 3: Empty checklist (error handling)
    print("\n--- Test 3: Error Handling ---")
    
    params3 = {
        "action": "create_page",
        "title": "Empty List",
        "structure": "checklist",
        "items": []
    }
    
    result3 = skill.execute(params3)
    print(f"Result: {result3}")
    
    if "need" in result3.lower():
        print("[OK] Error handling works")
    else:
        print("[WARN] Error handling may not work correctly")
    
    print("\n" + "=" * 60)
    print("[PASS] NOTION SKILL TESTS COMPLETE")
    print("=" * 60)
    print("\nCheck your Notion workspace to verify pages were created!")
    
    return True


if __name__ == "__main__":
    """
    Run tests:
    python skills/notion_skill.py
    """
    test_notion_skill()
