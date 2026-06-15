from database.models import SessionLocal, Room, Message, engine, Base
import uuid
from datetime import datetime, timedelta

def seed():
    # Recreate tables
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    now = datetime.utcnow()
    
    # Incident 1: APT Lateral Movement (Mapped to Slack Channel)
    r1 = Room(
        id="slack_channel_C0BAHRX5B3Q",
        title="INC-2041: Lateral Movement via compromised VPN profile",
        source="Splunk Alert",
        severity="P1 - Critical",
        status="closed",
        created_at=now - timedelta(days=30),
        timeline=[
            "2026-05-15T08:01:00 - Initial Access: Successful VPN login for user 'bsmith' from unknown Russian IP (95.163.213.11).",
            "2026-05-15T08:05:00 - Suspicious execution: 'bsmith' account executed powershell.exe with Base64 encoded payload on host WIN-DC01.",
            "2026-05-15T08:10:00 - IOC Found: VirusTotal confirmed IP 95.163.213.11 is a known APT29 jump host.",
            "2026-05-15T08:15:00 - Lateral Movement: RDP session established from WIN-DC01 to WIN-FILESRV.",
            "2026-05-15T08:30:00 - Mitigation: Disabled 'bsmith' AD account and isolated WIN-DC01 and WIN-FILESRV."
        ]
    )
    
    # Incident 2: AWS Data Exfil
    r2 = Room(
        id=str(uuid.uuid4()),
        title="INC-2105: AWS S3 Mass Download",
        source="AWS GuardDuty",
        severity="P2 - High",
        status="closed",
        created_at=now - timedelta(days=14),
        timeline=[
            "2026-06-01T14:22:00 - Alert: Anomalous AWS IAM Role behavior (role: 'arn:aws:iam::123:role/DataPipeline').",
            "2026-06-01T14:25:00 - Splunk Search: Role 'DataPipeline' performed 50,000 GetObject calls on S3 bucket 'ksec-customer-data' in 10 minutes.",
            "2026-06-01T14:30:00 - Investigation: API calls originated from AWS EC2 instance i-0abcd1234, which is internet facing.",
            "2026-06-01T14:40:00 - Findings: EC2 instance had a vulnerable Apache Struts version. Attacker achieved RCE and dumped IAM credentials from metadata service.",
            "2026-06-01T14:50:00 - Mitigation: Revoked IAM Role session, terminated EC2 instance, patched Struts across fleet."
        ]
    )
    
    # Incident 3: Okta Brute Force / MFA Fatigue
    r3 = Room(
        id=str(uuid.uuid4()),
        title="INC-2180: Okta MFA Fatigue Attack on Executive",
        source="Okta Admin",
        severity="P1 - Critical",
        status="closed",
        created_at=now - timedelta(days=2),
        timeline=[
            "2026-06-13T02:00:00 - Alert: 45 failed login attempts for user 'ceojohn' in Okta from 5 different countries.",
            "2026-06-13T02:15:00 - Tactic identified: Password Spraying followed by MFA Fatigue (push bombing).",
            "2026-06-13T02:20:00 - Event: User 'ceojohn' accidentally accepted the 46th Okta Push notification while asleep.",
            "2026-06-13T02:21:00 - Access: Attacker successfully logged into Jira (SEC-4512) and downloaded sensitive financial attachments.",
            "2026-06-13T02:30:00 - IOC: Attacker IP 45.3.36.252 identified as Malicious Tor Exit Node on VirusTotal.",
            "2026-06-13T02:40:00 - Mitigation: Invalidated all Okta sessions, enforced FIDO2 WebAuthn keys instead of Push notifications."
        ]
    )
    
    db.add_all([r1, r2, r3])
    db.commit()
    print("Database flushed and seeded with realistic incidents.")
    db.close()

if __name__ == "__main__":
    seed()
