from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
from dotenv import load_dotenv
from supabase import create_client, Client
import uuid
from datetime import datetime

# Load environment variables
load_dotenv()

app = FastAPI(title="PowerSync + Supabase API", version="1.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Supabase client setup
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not supabase_url or not supabase_key:
    raise ValueError("Missing Supabase environment variables")

supabase: Client = create_client(supabase_url, supabase_key)

# Pydantic models
class ListCreate(BaseModel):
    name: str

class ListResponse(BaseModel):
    id: str
    name: str
    created_at: str
    updated_at: str

class TodoCreate(BaseModel):
    list_id: str
    description: str
    completed: bool = False

class TodoUpdate(BaseModel):
    completed: bool

class TodoResponse(BaseModel):
    id: str
    list_id: str
    description: str
    completed: bool
    created_at: str
    updated_at: str

# Dependency to get Supabase client
def get_supabase_client():
    return supabase

# Root endpoint
@app.get("/")
async def root():
    return {"message": "PowerSync + Supabase API", "status": "running"}

# Health check
@app.get("/api/health")
async def health_check():
    try:
        # Test Supabase connection
        result = supabase.table("lists").select("count", count="exact").execute()
        return {
            "status": "healthy",
            "supabase_connected": True,
            "lists_count": result.count
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "supabase_connected": False,
            "error": str(e)
        }

# Lists endpoints
@app.post("/api/lists", response_model=ListResponse)
async def create_list(list_data: ListCreate, supabase_client=Depends(get_supabase_client)):
    try:
        result = supabase_client.table("lists").insert({
            "name": list_data.name
        }).execute()
        
        if result.data:
            return result.data[0]
        else:
            raise HTTPException(status_code=400, detail="Failed to create list")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating list: {str(e)}")

@app.get("/api/lists", response_model=List[ListResponse])
async def get_lists(supabase_client=Depends(get_supabase_client)):
    try:
        result = supabase_client.table("lists").select("*").order("created_at", desc=True).execute()
        return result.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching lists: {str(e)}")

@app.get("/api/lists/{list_id}", response_model=ListResponse)
async def get_list(list_id: str, supabase_client=Depends(get_supabase_client)):
    try:
        result = supabase_client.table("lists").select("*").eq("id", list_id).single().execute()
        if result.data:
            return result.data
        else:
            raise HTTPException(status_code=404, detail="List not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching list: {str(e)}")

@app.delete("/api/lists/{list_id}")
async def delete_list(list_id: str, supabase_client=Depends(get_supabase_client)):
    try:
        # Delete todos first (cascade should handle this, but being explicit)
        supabase_client.table("todos").delete().eq("list_id", list_id).execute()
        
        # Delete the list
        result = supabase_client.table("lists").delete().eq("id", list_id).execute()
        
        return {"message": "List deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting list: {str(e)}")

# Todos endpoints
@app.post("/api/todos", response_model=TodoResponse)
async def create_todo(todo_data: TodoCreate, supabase_client=Depends(get_supabase_client)):
    try:
        result = supabase_client.table("todos").insert({
            "list_id": todo_data.list_id,
            "description": todo_data.description,
            "completed": todo_data.completed
        }).execute()
        
        if result.data:
            return result.data[0]
        else:
            raise HTTPException(status_code=400, detail="Failed to create todo")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating todo: {str(e)}")

@app.get("/api/todos", response_model=List[TodoResponse])
async def get_all_todos(supabase_client=Depends(get_supabase_client)):
    try:
        result = supabase_client.table("todos").select("*").order("created_at", desc=True).execute()
        return result.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching todos: {str(e)}")

@app.get("/api/lists/{list_id}/todos", response_model=List[TodoResponse])
async def get_todos_by_list(list_id: str, supabase_client=Depends(get_supabase_client)):
    try:
        result = supabase_client.table("todos").select("*").eq("list_id", list_id).order("created_at", desc=True).execute()
        return result.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching todos: {str(e)}")

@app.put("/api/todos/{todo_id}", response_model=TodoResponse)
async def update_todo(todo_id: str, todo_update: TodoUpdate, supabase_client=Depends(get_supabase_client)):
    try:
        result = supabase_client.table("todos").update({
            "completed": todo_update.completed,
            "updated_at": datetime.now().isoformat()
        }).eq("id", todo_id).execute()
        
        if result.data:
            return result.data[0]
        else:
            raise HTTPException(status_code=404, detail="Todo not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating todo: {str(e)}")

@app.delete("/api/todos/{todo_id}")
async def delete_todo(todo_id: str, supabase_client=Depends(get_supabase_client)):
    try:
        result = supabase_client.table("todos").delete().eq("id", todo_id).execute()
        return {"message": "Todo deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting todo: {str(e)}")

# PowerSync specific endpoints
@app.get("/api/sync/status")
async def sync_status():
    """Endpoint to check sync status"""
    try:
        # Check if we can access both tables
        lists_result = supabase.table("lists").select("count", count="exact").execute()
        todos_result = supabase.table("todos").select("count", count="exact").execute()
        
        return {
            "status": "ready",
            "tables": {
                "lists": lists_result.count,
                "todos": todos_result.count
            },
            "message": "Database is ready for PowerSync"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Database not ready: {str(e)}"
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)