import os
import uuid
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging
from supabase_config import get_supabase_client, is_supabase_available

class DatabaseService:
    def __init__(self):
        self.supabase = get_supabase_client()
        self.is_available = is_supabase_available()
    
    def create_user(self, email: str, password: str, username: str, redirect_to: str = None) -> Dict[str, Any]:
        """Create a new user account with Supabase Auth and email confirmation link. Checks for existing username and inserts into profiles."""
        if not self.is_available:
            return {"success": False, "error": "Database not available"}
        try:
            # Check if username already exists
            username_check = self.supabase.table("profiles").select("id").eq("username", username).execute()
            if username_check.data and len(username_check.data) > 0:
                return {"success": False, "error": "Username already exists"}

            options = {
                "data": {"username": username, "email": email}
            }
            if redirect_to:
                options["email_confirm_redirect"] = redirect_to
            response = self.supabase.auth.sign_up({
                "email": email,
                "password": password,
                "options": options
            })
            # Supabase Python SDK returns user and error
            if hasattr(response, 'user') and response.user:
                user_id = response.user.id
                # Try to insert into profiles
                try:
                    profile_insert = self.supabase.table("profiles").insert({
                        "id": user_id,
                        "username": username,
                        "email": email
                    }).execute()
                    if profile_insert.data:
                        return {"success": True, "user_id": user_id, "message": "User created successfully. Please check your email to confirm your account."}
                    else:
                        # Rollback: delete user from auth.users if profile insert fails
                        self.supabase.table("auth.users").delete().eq("id", user_id).execute()
                        return {"success": False, "error": "Username already exists or profile creation failed. Please try a different username."}
                except Exception as e:
                    # Rollback: delete user from auth.users if profile insert fails
                    self.supabase.table("auth.users").delete().eq("id", user_id).execute()
                    error_msg = str(e)
                    if 'duplicate key value violates unique constraint' in error_msg or 'Username already exists' in error_msg:
                        return {"success": False, "error": "Username already exists"}
                    return {"success": False, "error": "Profile creation failed: " + error_msg}
            elif hasattr(response, 'error') and response.error:
                # Check for duplicate email error
                error_msg = str(response.error)
                if 'already registered' in error_msg or 'User already registered' in error_msg or 'duplicate key value violates unique constraint' in error_msg:
                    return {"success": False, "error": "Email already exists"}
                return {"success": False, "error": error_msg}
            else:
                return {"success": False, "error": "Unknown error during registration."}
        except Exception as e:
            logging.error(f"Error creating user: {e}")
            return {"success": False, "error": str(e)}
    
    def authenticate_user(self, email: str, password: str) -> Dict[str, Any]:
        """Authenticate user login and check email confirmation status."""
        if not self.is_available:
            return {"success": False, "error": "Database not available"}
        try:
            response = self.supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            # Supabase returns user and session; user.confirmed_at is set if confirmed
            if hasattr(response, 'user') and response.user:
                user_confirmed = getattr(response.user, 'confirmed_at', None) is not None
                return {
                    "success": True,
                    "user_id": response.user.id,
                    "session": response.session,
                    "user_confirmed": user_confirmed,
                    "message": "Login successful" if user_confirmed else "Email not confirmed"
                }
            elif hasattr(response, 'error') and response.error:
                return {"success": False, "error": str(response.error)}
            else:
                return {"success": False, "error": "Invalid credentials"}
        except Exception as e:
            logging.error(f"Error authenticating user: {e}")
            return {"success": False, "error": str(e)}
    
    def create_chat_session(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Create a new chat session"""
        if not self.is_available:
            return {"success": False, "error": "Database not available"}
        
        try:
            session_id = str(uuid.uuid4())
            session_data = {
                "id": session_id,
                "user_id": user_id,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            response = self.supabase.table("chat_sessions").insert(session_data).execute()
            
            if response.data:
                return {
                    "success": True,
                    "session_id": session_id,
                    "message": "Chat session created"
                }
            else:
                return {"success": False, "error": "Failed to create chat session"}
                
        except Exception as e:
            logging.error(f"Error creating chat session: {e}")
            return {"success": False, "error": str(e)}
    
    def save_chat_message(self, session_id: str, message_type: str, content: str, 
                         plant_data: Optional[Dict] = None, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Save a chat message"""
        if not self.is_available:
            return {"success": False, "error": "Database not available"}
        
        try:
            message_data = {
                "session_id": session_id,
                "message_type": message_type,
                "content": content,
                "plant_data": json.dumps(plant_data) if plant_data else None,
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            response = self.supabase.table("chat_messages").insert(message_data).execute()
            
            if response.data:
                return {
                    "success": True,
                    "message_id": response.data[0]["id"],
                    "message": "Message saved successfully"
                }
            else:
                return {"success": False, "error": "Failed to save message"}
                
        except Exception as e:
            logging.error(f"Error saving chat message: {e}")
            return {"success": False, "error": str(e)}
    
    def get_chat_history(self, session_id: str, limit: int = 10) -> Dict[str, Any]:
        """Get chat history for a session"""
        if not self.is_available:
            return {"success": False, "error": "Database not available"}
        
        try:
            response = self.supabase.table("chat_messages")\
                .select("*")\
                .eq("session_id", session_id)\
                .order("timestamp", desc=True)\
                .limit(limit)\
                .execute()
            
            if response.data:
                # Reverse to get chronological order
                messages = list(reversed(response.data))
                return {
                    "success": True,
                    "messages": messages,
                    "count": len(messages)
                }
            else:
                return {"success": True, "messages": [], "count": 0}
                
        except Exception as e:
            logging.error(f"Error getting chat history: {e}")
            return {"success": False, "error": str(e)}
    
    def save_plant_identification(self, user_id: str, plant_name: str, confidence: float, 
                                image_url: Optional[str] = None) -> Dict[str, Any]:
        """Save plant identification result"""
        if not self.is_available:
            return {"success": False, "error": "Database not available"}
        
        try:
            plant_data = {
                "user_id": user_id,
                "plant_name": plant_name,
                "confidence": confidence,
                "image_url": image_url,
                "identified_at": datetime.utcnow().isoformat()
            }
            
            response = self.supabase.table("plant_identifications").insert(plant_data).execute()
            
            if response.data:
                return {
                    "success": True,
                    "identification_id": response.data[0]["id"],
                    "message": "Plant identification saved"
                }
            else:
                return {"success": False, "error": "Failed to save plant identification"}
                
        except Exception as e:
            logging.error(f"Error saving plant identification: {e}")
            return {"success": False, "error": str(e)}
    
    def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Get user profile information"""
        if not self.is_available:
            return {"success": False, "error": "Database not available"}
        
        try:
            response = self.supabase.table("profiles")\
                .select("*")\
                .eq("id", user_id)\
                .single()\
                .execute()
            
            if response.data:
                return {
                    "success": True,
                    "profile": response.data
                }
            else:
                return {"success": False, "error": "Profile not found"}
                
        except Exception as e:
            logging.error(f"Error getting user profile: {e}")
            return {"success": False, "error": str(e)}

    def update_username(self, user_id: str, username: str) -> dict:
        """Update the username for a user."""
        if not self.is_available:
            return {"success": False, "error": "Database not available"}
        try:
            # Check if username already exists
            username_check = self.supabase.table("profiles").select("id").eq("username", username).execute()
            if username_check.data and len(username_check.data) > 0:
                return {"success": False, "error": "Username already exists"}
            response = self.supabase.table("profiles").update({"username": username}).eq("id", user_id).execute()
            if response.data:
                return {"success": True}
            else:
                return {"success": False, "error": "Failed to update username"}
        except Exception as e:
            logging.error(f"Error updating username: {e}")
            return {"success": False, "error": str(e)}

    def update_password(self, user_id: str, old_password: str, new_password: str) -> dict:
        """Update the password for a user using Supabase Auth."""
        if not self.is_available:
            return {"success": False, "error": "Database not available"}
        try:
            # Get user email from profile
            profile = self.get_user_profile(user_id)
            if not profile.get("success"):
                return {"success": False, "error": "Profile not found"}
            email = profile["profile"].get("email")
            if not email:
                return {"success": False, "error": "Email not found in profile"}
            # Re-authenticate and update password
            auth_res = self.supabase.auth.sign_in_with_password({"email": email, "password": old_password})
            if hasattr(auth_res, 'user') and auth_res.user:
                update_res = self.supabase.auth.update_user({"password": new_password})
                if hasattr(update_res, 'user') and update_res.user:
                    return {"success": True}
                elif hasattr(update_res, 'error') and update_res.error:
                    return {"success": False, "error": str(update_res.error)}
                else:
                    return {"success": False, "error": "Failed to update password"}
            else:
                return {"success": False, "error": "Old password incorrect"}
        except Exception as e:
            logging.error(f"Error updating password: {e}")
            return {"success": False, "error": str(e)}

    def update_country(self, user_id: str, country: str) -> dict:
        """Update the country for a user."""
        if not self.is_available:
            return {"success": False, "error": "Database not available"}
        try:
            response = self.supabase.table("profiles").update({"country": country}).eq("id", user_id).execute()
            if response.data:
                return {"success": True}
            else:
                return {"success": False, "error": "Failed to update country"}
        except Exception as e:
            logging.error(f"Error updating country: {e}")
            return {"success": False, "error": str(e)}

    def update_profile_pic(self, user_id: str, file_url: str) -> dict:
        """Update the profile picture URL for a user."""
        if not self.is_available:
            return {"success": False, "error": "Database not available"}
        try:
            response = self.supabase.table("profiles").update({"profile_pic": file_url}).eq("id", user_id).execute()
            if response.data:
                return {"success": True}
            else:
                return {"success": False, "error": "Failed to update profile picture"}
        except Exception as e:
            logging.error(f"Error updating profile picture: {e}")
            return {"success": False, "error": str(e)}

# Global database service instance
db_service = DatabaseService() 
