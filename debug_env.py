import os
import sys
import traceback
from dotenv import load_dotenv

def debug_environment():
    # Print comprehensive system and environment information
    print("=" * 50)
    print("COMPREHENSIVE ENVIRONMENT DIAGNOSTIC")
    print("=" * 50)
    
    # System and Python Information
    print("\n1. SYSTEM INFORMATION:")
    print(f"Python Version: {sys.version}")
    print(f"Python Executable: {sys.executable}")
    print(f"Current Working Directory: {os.getcwd()}")
    
    # Python Path
    print("\n2. PYTHON PATH:")
    for path in sys.path:
        print(f"  - {path}")
    
    # Environment Variable Search
    print("\n3. ENVIRONMENT VARIABLE SEARCH:")
    possible_env_paths = [
        os.path.join(os.getcwd(), '.env'),
        os.path.join(os.path.dirname(__file__), '.env'),
        os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    ]
    
    loaded = False
    for env_path in possible_env_paths:
        print(f"Checking .env at: {env_path}")
        if os.path.exists(env_path):
            print(f"  - Found .env file at {env_path}")
            load_dotenv(env_path)
            loaded = True
            
            # Print .env file contents (without sensitive information)
            print("  .env File Contents:")
            with open(env_path, 'r') as f:
                for line in f:
                    if line.strip() and not line.startswith('#'):
                        key = line.split('=')[0]
                        print(f"    - {key}=***")
            break
    
    if not loaded:
        print("WARNING: No .env file found!")
    
    # Environment Variables
    print("\n4. ENVIRONMENT VARIABLES:")
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    
    print(f"SUPABASE_URL: {supabase_url}")
    print(f"SUPABASE_KEY present: {bool(supabase_key)}")
    
    # Project Module Import Test
    print("\n5. PROJECT MODULE IMPORT TEST:")
    try:
        import sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
        
        from app.core.config import settings, get_settings
        print("Config Import Successful:")
        print(f"  - Settings SUPABASE_URL: {settings.SUPABASE_URL}")
        print(f"  - Settings SUPABASE_KEY present: {bool(settings.SUPABASE_KEY)}")
    except Exception as e:
        print(f"Error importing config: {e}")
        traceback.print_exc()
    
    # Supabase Client Creation Test
    print("\n6. SUPABASE CLIENT CREATION TEST:")
    try:
        from supabase import create_client, Client
        from app.core.config import settings
        
        client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        print("Supabase Client Created Successfully!")
    except Exception as e:
        print(f"Supabase Client Creation Failed: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    debug_environment()
