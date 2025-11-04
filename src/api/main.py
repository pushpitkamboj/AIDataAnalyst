from fastapi import FastAPI, UploadFile, File, HTTPException, Form
import tempfile, os
from supabase import create_client, Client
SUPABASE_URL = "https://twypdtqllbeaaxkbduju.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InR3eXBkdHFsbGJlYWF4a2JkdWp1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTk2NDMwMDIsImV4cCI6MjA3NTIxOTAwMn0.OcKMKcb5lWgl7-DWUzS_VyQNlQ4k4lvkMy-E04cQJTE"
BUCKET_NAME = "data_csv"
from pydantic import BaseModel
from langgraph_sdk.client import get_client
from langchain_core.messages import HumanMessage
from datetime import datetime
import uuid
from dotenv import load_dotenv
load_dotenv()
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or specific frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = get_client(url = "http://localhost:2024")  #langgraph

class ReqBody(BaseModel):
    db_url: str | None = None
    query: str
    

# @app.post("/upload")
# async def upload_data(
#     file: UploadFile | None = File(None),
#     db_url: str | None = Form(None),
#     query: str = Form(...)
# ):
#     supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
#     supabase_uploaded_path = None
#     tmp_path = None
#     state = None
    
#     req = ReqBody(db_url=db_url, query=query)
#     try:
#         if file and req.db_url:
#             return {
#                 "final_answer": "please don't upload both things, the platform is not ready yet to work for both data, we are working on it"
#             }
            
#         if file:
#             if not file.filename.lower().endswith(".csv"):
#                 raise HTTPException(status_code=400, detail="Only CSV files are allowed")

#             with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
#                 tmp_path = tmp.name
#                 content = await file.read() if file else None
#                 if content:
#                     tmp.write(content)
                    
#                 with open(tmp_path, "rb") as f:
#                     res = supabase.storage.from_(BUCKET_NAME).upload(
#                         file.filename, f, {"content-type": "text/csv"}
#                     )
#                     supabase_uploaded_path = res.path 
                        
#                 public_url = (
#                     supabase.storage
#                     .from_(BUCKET_NAME)
#                     .get_public_url(supabase_uploaded_path)
#                 )
            
#             state = {
#                 "csv_url": public_url,
#                 "messages": HumanMessage(content=req.query),
#             }
            
#         elif data.db_url:
#             state = {
#                 "db_url": data.db_url,
#                 "messages": HumanMessage(content=req.query)
#             }
#         else:
#             return {
#                 "final_answer": "please upload at least one of the things, connection string or csv file"
#             }
            
#         thread = await client.threads.create() 
#         run = await client.runs.wait(assistant_id="agent", thread_id=None, input=state)
#         result = run["result"]
        
#         return {
#             "final_answer": result
#         }
        
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"{e}")

#     finally:
#         if tmp_path and os.path.exists(tmp_path):
#             os.remove(tmp_path)
       
       
DbUrl = None
CsvUrl = None

@app.post("/upload")
async def upload_data(
    file: UploadFile | None = File(None),
    db_url: str | None = Form(None),
    # query: str = Form(...),
):
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    tmp_path: Optional[str] = None
    state = None

    # Build a simple ReqBody-like object for validation/consistency
    class ReqBody:
        def __init__(self, db_url): #removed query
            self.db_url = db_url
            # self.query = query

    req = ReqBody(db_url=db_url)

    try:
        # mutually exclusive: either file OR db_url
        if file and req.db_url:
            return {
                "final_answer": "please don't upload both things, the platform is not ready to work with both simultaneously"
            }

        if file:
            # basic check for filename
            if not file.filename or not file.filename.lower().endswith(".csv"):
                raise HTTPException(status_code=400, detail="Only CSV files are allowed")

            # Read uploaded file once (UploadFile is async file-like)
            contents = await file.read()
            if not contents:
                raise HTTPException(status_code=400, detail="Uploaded file is empty")

            # create a temp file and write bytes, then close it before uploading
            td = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
            tmp_path = td.name
            try:
                # write bytes and ensure flushed & closed
                td.write(contents)
                td.flush()
                td.close()
            except Exception:
                # ensure it's closed on error
                try:
                    td.close()
                except Exception:
                    pass
                raise

            # upload to supabase: open the file for reading in binary
            # IMPORTANT: supabase-py expects bytes/file-like depending on client version.
            # We open the file and pass the file object.
            
            try:
                with open(tmp_path, "rb") as f:
                    ext = os.path.splitext(file.filename)[1] or ".csv"
                    supabase_storage_file = f"{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}{ext}"
                    res = supabase.storage.from_(BUCKET_NAME).upload(supabase_storage_file, f, {"content-type": "text/csv"})
            except Exception as exc:
                raise HTTPException(status_code=500, detail=f"Supabase upload call failed: {exc}")

            # check upload response for common client shapes
            # supabase-py sometimes returns dict {'error': None, 'data': {'path': '...'}}
            # adapt to whichever response shape your client returns
            uploaded_path = None
            if isinstance(res, dict):
                # try multiple common keys
                if res.get("error"):
                    raise HTTPException(status_code=500, detail=f"Supabase error: {res['error']}")
                data = res.get("data") or res.get("Data") or {}
                uploaded_path = data.get("path") or data.get("Key") or None
                # fallback: some clients return a string path directly
                if not uploaded_path:
                    uploaded_path = data or res.get("path") or res.get("Key")
            else:
                # unknown shape — try attribute access
                uploaded_path = getattr(res, "path", None) or getattr(res, "key", None)

            if not uploaded_path:
                # still not found — include whatever res is for debugging
                raise HTTPException(status_code=500, detail=f"Upload succeeded but could not determine path. supabase response: {res}")

            # get public url — client shapes vary: sometimes dict with 'publicUrl' or 'publicURL' or method returns dict
            try:
                pub = supabase.storage.from_(BUCKET_NAME).get_public_url(uploaded_path)
                # pub may be dict or object; try common keys
                public_url = None
                if isinstance(pub, dict):
                    public_url = pub.get("publicUrl") or pub.get("publicURL") or pub.get("public_url") or pub.get("public")
                else:
                    public_url = getattr(pub, "publicUrl", None) or getattr(pub, "publicURL", None) or getattr(pub, "public_url", None)
                # final fallback: if supabase client returns a string
                if not public_url and isinstance(pub, str):
                    public_url = pub
                if not public_url:
                    # include raw object for debug
                    raise HTTPException(status_code=500, detail=f"Could not derive public URL from response: {pub}")
                
                
                #CsvUrl = public_url #######
                return {"message": public_url}
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to get public url: {e}")

            # state = {
            #     "csv_url": public_url,
            #     "messages": HumanMessage(content = req.query),  # adapt to the expected shape your client needs
            # }

        elif req.db_url:
            
            # DbUrl = req.db_url  ###########
            # state = {
            #     "db_url": req.db_url,
            #     "messages": HumanMessage(content = req.query),
            # }
            return {
                "message": req.db_url
            }
        else:
            return {
                "final_answer": "please upload at least one of the things: connection string or csv file"
            }

        # create a thread and pass the correct thread id to runs.wait
        # thread = await client.threads.create()
        # thread_id = thread.get("thread_id")

        # run = await client.runs.wait(assistant_id="agent", thread_id=thread_id, input=state)
        # result = run.get("result") if isinstance(run, dict) else getattr(run, "result", run)

        return {"final_answer": "nothing worked"}

    except HTTPException:
        raise
    except Exception as e:
        # return a bit more debugable message for now
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}")

    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass
       
class reqBody(BaseModel):
    query: str
    csv_url: str | None = None
    db_url: str | None = None
    
@app.post("/query")
async def query(payload: reqBody):

    if payload.db_url:
        state = {
            "db_url": payload.db_url,
            "messages": payload.query
        }
        thread_id = str(uuid.uuid4())          # e.g. '3fa85f64-5717-4562-b3fc-2c963f66afa6'
        thread = await client.threads.create(thread_id=thread_id)
        run = await client.runs.wait(assistant_id="agent", thread_id=thread_id, input=state)
        output_states = await client.threads.get_state(thread_id)

        result = output_states["values"]["result"]

        return {"message": result}
    
    elif payload.csv_url:
        state = {
            "csv_url": payload.csv_url,
            "messages": payload.query
        }
        thread_id = str(uuid.uuid4())
        thread = await client.threads.create(thread_id=thread_id)
        run = await client.runs.wait(assistant_id="agent", thread_id=thread_id, input=state)
        # result = run.get("result") if isinstance(run, dict) else getattr(run, "result", run)
        # image_url = result.get("image_urls")
        # if image_urls
        # val = run.to_dict(orient="records")
        output_states = await client.threads.get_state(thread_id)
        
        result = output_states["values"]["result"]
        return {"message": result}
    
    return {
        "message": "none worked"
    }

@app.get("/health")
def health():
    return{
        "message": "health is ok"
    }          

# class UriBody(BaseModel):
#     uri: str

# @app.post("/upload-uri")
# def upload_connection_string(body: UriBody):
#     response = (
#         supabase.table("db_url")
#         .insert({"id": 42, "uri": body.uri})
#         .execute()
#     )
#     return {"message": response}

# #from this api

# # connect to your deployed graph (local or cloud)


# # update (merge) or modify state before run

# print(result)
