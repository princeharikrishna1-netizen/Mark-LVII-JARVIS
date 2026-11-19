import os
import subprocess
import sys

class JarvisSelfAgent:
    def __init__(self, root_dir="."):
        self.root_dir = root_dir

    def modify_code(self, file_name, new_code, mode="append"):
        """జార్విస్ తన కోడ్‌ని తానే అప్‌డేట్ చేయడానికి లేదా కొత్త ఫీచర్లు యాడ్ చేయడానికి"""
        file_path = os.path.join(self.root_dir, file_name)
        try:
            if mode == "append":
                with open(file_path, "a", encoding="utf-8") as f:
                    f.write("\n\n# --- Auto-Added by JARVIS Self-Agent ---\n")
                    f.write(new_code)
                print(f"[Self-Agent] Successfully appended new logic to {file_name}")
            elif mode == "overwrite":
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(new_code)
                print(f"[Self-Agent] Successfully updated {file_name}")
            return True
        except Exception as e:
            print(f"[Self-Agent Error] Failed to modify code: {e}")
            return False

    def run_syntax_check(self, file_name):
        """రాసిన కోడ్‌లో సింటాక్స్ ఎర్రర్స్ ఉన్నాయో లేదో చెక్ చేయడానికి"""
        file_path = os.path.join(self.root_dir, file_name)
        result = subprocess.run([sys.executable, "-m", "py_compile", file_path], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"[Self-Agent] Code check passed: {file_name} has no syntax errors.")
            return True
        else:
            print(f"[Self-Agent Error] Syntax error detected in {file_name}:\n{result.stderr}")
            return False

    def handle_command(user_text):
    if "restart" in user_text.lower() or "సెలవు" in user_text.lower():
        print("[JARVIS] Restart command received from user. Restarting server...")
        import subprocess, sys, os
        subprocess.Popen([sys.executable] + sys.argv)
        os._exit(0)

if __name__ == "__main__":
    agent = JarvisSelfAgent()
    print("Jarvis Self-Coding Agent is online and ready.")