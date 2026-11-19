import os
import json
from datetime import datetime
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

class JarvisSecurityAndBriefing:
    def __init__(self):
        # Generate or load an AES-GCM key for secure token audit
        self.encryption_key = AESGCM.generate_key(bit_length=256)
        self.aesgcm = AESGCM(self.encryption_key)

    def generate_morning_briefing(self):
        """Proactive contextual morning briefing combining weather, schedules, and admin tasks"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        briefing = {
            "title": "JARVIS Proactive Briefing",
            "timestamp": current_time,
            "greeting": "Good morning Hari! Ready for today's property registration and legal document tasks.",
            "weather": "Local weather optimal for office commute.",
            "pending_tasks": [
                "Review daily Encumbrance Certificate (EC) backups",
                "Check Tahasildar / Municipal office check-slip queue",
                "Verify default system printer network printer readiness"
            ]
        }
        return briefing

    def encrypt_session_token(self, token_str: str) -> bytes:
        """Encrypts session token using AES-GCM for secure local storage sync"""
        nonce = os.urandom(12)
        encrypted_token = self.aesgcm.encrypt(nonce, token_str.encode('utf-8'), None)
        return nonce + encrypted_token

    def decrypt_session_token(self, encrypted_data: bytes) -> str:
        """Decrypts AES-GCM encrypted session token"""
        nonce = encrypted_data[:12]
        ciphertext = encrypted_data[12:]
        decrypted_token = self.aesgcm.decrypt(nonce, ciphertext, None)
        return decrypted_token.decode('utf-8')

# Test execution
if __name__ == "__main__":
    sb = JarvisSecurityAndBriefing()
    print(json.dumps(sb.generate_morning_briefing(), indent=2))
    
    sample_token = "jarvis_secure_auth_token_98765"
    enc = sb.encrypt_session_token(sample_token)
    dec = sb.decrypt_session_token(enc)
    print(f"[Security Audit] AES-GCM Token Encryption & Decryption Successful: {dec == sample_token}")