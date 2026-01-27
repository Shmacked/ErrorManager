import uuid
from fastapi import Request, Response

def get_session_id(request: Request, response: Response):
    # 1. Look for an existing session_id in the cookies
    session_id = request.cookies.get("chat_session_id")
    
    # 2. If it doesn't exist, create a new one
    if not session_id:
        session_id = str(uuid.uuid4())
        # Set the cookie on the response so the browser saves it
        # 'httponly=True' prevents JavaScript from stealing the ID
        response.set_cookie(key="chat_session_id", value=session_id, httponly=True)
        
    return session_id
