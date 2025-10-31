#!/usr/bin/env python3
"""
Launcher for Image Resizer Streamlit App
"""
import sys
import os
import subprocess
import tempfile
import webbrowser
import time
from pathlib import Path

def main():
    # Get the directory where the script/executable is located
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        base_path = Path(sys._MEIPASS)
    else:
        # Running as script
        base_path = Path(__file__).parent
    
    # Set environment variables to help Streamlit find its components
    os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'
    os.environ['STREAMLIT_SERVER_PORT'] = '8501'
    os.environ['STREAMLIT_SERVER_ADDRESS'] = 'localhost'
    
    # Create a temporary directory for Streamlit config
    with tempfile.TemporaryDirectory() as temp_dir:
        os.environ['STREAMLIT_CONFIG_DIR'] = temp_dir
        
        # Path to the app.py file
        app_py = base_path / 'app.py'
        
        if not app_py.exists():
            print("Error: app.py not found!")
            input("Press Enter to exit...")
            return 1
        
        print("Starting Image Resizer...")
        print("This will open in your web browser at http://localhost:8501")
        print("Close this window to stop the application.")
        print("-" * 50)
        
        try:
            # Start Streamlit app
            cmd = [
                sys.executable, '-m', 'streamlit', 'run', 
                str(app_py),
                '--server.headless', 'true',
                '--server.port', '8501',
                '--server.address', 'localhost',
                '--browser.gatherUsageStats', 'false'
            ]
            
            # Run Streamlit in subprocess with output capture
            proc = subprocess.Popen(cmd, cwd=base_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            # Wait for server to be ready (check for successful start message)
            import time
            max_retries = 30
            for attempt in range(max_retries):
                try:
                    import socket
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    result = sock.connect_ex(('localhost', 8501))
                    sock.close()
                    if result == 0:
                        break
                except:
                    pass
                time.sleep(0.5)
            
            # Open browser
            webbrowser.open('http://localhost:8501')
            
            # Wait for process to complete
            proc.wait()
            
        except KeyboardInterrupt:
            print("\nShutting down...")
            return 0
        except Exception as e:
            print(f"Error starting application: {e}")
            input("Press Enter to exit...")
            return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())