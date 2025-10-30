#!/usr/bin/env python3
"""
Simple launcher for Image Resizer Streamlit App
"""
import sys
import os
import webbrowser
import time
from pathlib import Path

# Fix for Streamlit metadata issue
import importlib.metadata
import importlib.util

# Mock streamlit version if not found
try:
    importlib.metadata.version('streamlit')
except importlib.metadata.PackageNotFoundError:
    # Create a mock version
    import importlib.metadata as _metadata
    class MockDistribution:
        def __init__(self, name, version):
            self._name = name
            self._version = version
        def version(self):
            return self._version
        def metadata(self):
            return {}
    
    def mock_from_name(name):
        if name == 'streamlit':
            return MockDistribution('streamlit', '1.28.0')
        raise _metadata.PackageNotFoundError(name)
    
    _metadata.from_name = mock_from_name

def main():
    # Get the directory where the executable is located
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        base_path = Path(sys._MEIPASS)
    else:
        # Running as script
        base_path = Path(__file__).parent
    
    # Set environment variables
    os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'
    os.environ['STREAMLIT_SERVER_PORT'] = '8501'
    os.environ['STREAMLIT_SERVER_ADDRESS'] = 'localhost'
    os.environ['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false'
    os.environ['STREAMLIT_GLOBAL_DEVELOPMENT_MODE'] = 'false'
    
    # Add current directory to Python path
    sys.path.insert(0, str(base_path))
    
    print("Starting Image Resizer...")
    print("This will open in your web browser at http://localhost:8501")
    print("Press Ctrl+C to stop the application.")
    print("-" * 50)
    
    try:
        # Import and run streamlit directly
        import streamlit.web.cli as stcli
        
        # Simulate command line arguments for streamlit
        sys.argv = [
            'streamlit',
            'run',
            str(base_path / 'app.py'),
            '--server.headless=true',
            '--server.port=8501',
            '--server.address=localhost',
            '--browser.gatherUsageStats=false',
            '--global.developmentMode=false'
        ]
        
        # Give it a moment to start
        time.sleep(1)
        
        # Open browser
        webbrowser.open('http://localhost:8501')
        
        # Run streamlit
        stcli.main()
        
    except KeyboardInterrupt:
        print("\nShutting down...")
        return 0
    except Exception as e:
        print(f"Error starting application: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())