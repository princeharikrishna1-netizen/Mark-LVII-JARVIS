"""
JARVIS Automated Testing Suite
- Automatically runs checks and tests on new code modifications and plugins
  to ensure existing functionality is not broken.
"""
import os
import importlib.util
import sys

def run_tests():
    print("[TEST SUITE] Starting automated verification for Mark-LVII...")
    
    # 1. Check if core plugins directory exists
    plugins_dir = "plugins"
    if not os.path.exists(plugins_dir):
        print("[TEST FAIL] Plugins directory missing!")
        return False
    
    print("[TEST PASS] Plugins directory verified.")

    # 2. Verify syntax and loading of all active plugins
    plugin_files = [f for f in os.listdir(plugins_dir) if f.endswith('.py')]
    success_count = 0
    
    for pf in plugin_files:
        path = os.path.join(plugins_dir, pf)
        try:
            spec = importlib.util.spec_from_file_location(pf[:-3], path)
            mod = importlib.util.module_from_spec(spec)
            sys.modules[pf[:-3]] = mod
            spec.loader.exec_module(mod)
            print(f"  -> Plugin test passed: {pf}")
            success_count += 1
        except Exception as e:
            print(f"  -> [TEST ERROR] Plugin failed to load {pf}: {str(e)}")
            return False

    print(f"[TEST PASS] All {success_count} plugins verified successfully without syntax errors.")
    print("[TEST SUITE] Automated check completed successfully, Hari!")
    return True

if __name__ == "__main__":
    run_tests()