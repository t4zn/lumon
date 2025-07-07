import os
from supabase import create_client, Client
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

class SupabaseConfig:
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_ANON_KEY")
        self.client = None
        
        if self.supabase_url and self.supabase_key:
            try:
                self.client = create_client(self.supabase_url, self.supabase_key)
                logging.info("Supabase client initialized successfully")
            except Exception as e:
                logging.error(f"Failed to initialize Supabase client: {e}")
                self.client = None
        else:
            logging.warning("Supabase credentials not found in environment variables")
    
    def get_client(self) -> Client:
        """Get the Supabase client instance"""
        return self.client
    
    def is_connected(self) -> bool:
        """Check if Supabase connection is available"""
        return self.client is not None

# Global Supabase instance
supabase_config = SupabaseConfig()

def get_supabase_client() -> Client:
    """Get the global Supabase client instance"""
    return supabase_config.get_client()

def is_supabase_available() -> bool:
    """Check if Supabase is available"""
    return supabase_config.is_connected() 
