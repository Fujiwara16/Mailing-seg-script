import subprocess
import time

def cleanup_port_5001():
    """
        Properly clean up port 5001
        Solving for the issue where the port is already in use and OAuth flow is not able to start
    """
    try:
        # Check if port 5001 is in use using lsof
        result = subprocess.run(['lsof', '-ti', ':5001'], capture_output=True, text=True, timeout=5)
        if result.stdout.strip():  # Port is in use
            print("⚠️  Port 5001 is in use, killing processes...")
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                if pid.strip():
                    try:
                        subprocess.run(['kill', '-9', pid.strip()], check=False, timeout=3)
                        print(f"🔧 Killed process {pid.strip()}")
                    except Exception as e:
                        print(f"⚠️  Could not kill process {pid.strip()}: {e}")
            # Wait for port to be released
            time.sleep(2)
            # Verify port is now free
            verify_result = subprocess.run(['lsof', '-ti', ':5001'], capture_output=True, text=True, timeout=5)
            if verify_result.stdout.strip():
                print("❌ Port 5001 is still in use after cleanup")
                return False
            else:
                print("✅ Port 5001 is now available")
                return True
        else:
            print("🔧 Port 5001 is available")
            return True
    except subprocess.TimeoutExpired:
        print("⚠️  Timeout checking port 5001")
        return False
    except Exception as e:
        print(f"⚠️  Could not check port 5001: {e}")
        return False