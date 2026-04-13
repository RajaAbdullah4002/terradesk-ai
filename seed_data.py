"""TerraDesk AI — Seed data for demo: realistic IT support tickets and KB articles."""

from database import init_db, add_kb_article, create_ticket, update_ticket


def seed_knowledge_base():
    """Populate the knowledge base with common IT support resolutions."""

    articles = [
        {
            "title": "MFA Authenticator App — Phone Replacement",
            "category": "Security / Access",
            "symptoms": "User changed phone, lost authenticator, MFA not working, can't log in, new phone, authenticator app missing",
            "resolution": "1. Admin signs into Entra ID > Users > select user. 2. Click Authentication Methods. 3. Click Require re-register MFA. 4. User signs in on new phone and re-registers Authenticator. 5. Verify MFA is working on new device.",
            "systems": ["Microsoft Entra ID", "Microsoft Authenticator"],
        },
        {
            "title": "Password Reset — Standard User",
            "category": "Microsoft 365",
            "symptoms": "Forgot password, password expired, can't log in, locked out, account locked, password reset",
            "resolution": "1. Open M365 Admin Centre > Users > Active Users. 2. Find user and click Reset Password. 3. Choose auto-generate or set manually. 4. Tick User must change password at next sign-in. 5. Send new credentials securely. 6. Confirm user can log in.",
            "systems": ["Microsoft 365", "Microsoft Entra ID"],
        },
        {
            "title": "Salesforce — New User Account Setup",
            "category": "Salesforce",
            "symptoms": "New starter needs Salesforce access, create Salesforce account, Salesforce onboarding, new consultant Salesforce",
            "resolution": "1. Log into Salesforce as Admin. 2. Setup > Users > New User. 3. Set username (email format), assign Profile and Role. 4. Assign Permission Sets as needed. 5. Save — Salesforce sends verification email to user. 6. Confirm user can log in and see correct data.",
            "systems": ["Salesforce"],
        },
        {
            "title": "Salesforce — Deactivate Departing User",
            "category": "Salesforce",
            "symptoms": "Offboarding Salesforce, remove Salesforce access, deactivate user, consultant leaving",
            "resolution": "1. Setup > Users > find user. 2. Click Edit, uncheck Active box. 3. Do NOT delete — deactivate only to preserve audit trail. 4. Reassign owned records to manager or team lead. 5. Remove from any queues or groups. 6. Document in offboarding checklist.",
            "systems": ["Salesforce"],
        },
        {
            "title": "Intune — Device Not Compliant",
            "category": "Intune / Device",
            "symptoms": "Laptop not compliant, device compliance failed, can't access Teams, Intune compliance error, conditional access blocked",
            "resolution": "1. User opens Company Portal app > check compliance status. 2. Identify which policy is failing (usually OS updates or encryption). 3. If OS update needed: Settings > Windows Update > Check for updates. 4. If BitLocker needed: Control Panel > BitLocker > Turn on. 5. After fixes, open Company Portal > Check Status to force re-evaluation. 6. If still failing, sync device in Intune admin centre.",
            "systems": ["Microsoft Intune", "Conditional Access"],
        },
        {
            "title": "SharePoint — Recover Deleted Files",
            "category": "SharePoint / Files",
            "symptoms": "Accidentally deleted file, missing document, file disappeared from SharePoint, recover deleted folder",
            "resolution": "1. Go to the SharePoint site where file was deleted. 2. Click Recycle Bin in left navigation. 3. Find the file/folder and select it. 4. Click Restore. 5. If not in first-stage recycle bin, check Second-stage recycle bin (Site Settings > Site Collection Admin). 6. Files remain recoverable for 93 days.",
            "systems": ["SharePoint Online"],
        },
        {
            "title": "Phishing Email — Investigation Steps",
            "category": "Security / Access",
            "symptoms": "Suspicious email, phishing attempt, dodgy link, fake Microsoft email, scam email reported",
            "resolution": "1. Ask user NOT to click any links or download attachments. 2. Check sender address — look for misspellings or look-alike domains. 3. In Exchange Admin Centre, run Message Trace to see if others received it. 4. If confirmed phishing: use Threat Explorer to delete from all mailboxes. 5. If user clicked link: reset password immediately, revoke all sessions in Entra ID, check for MFA changes. 6. Report to Microsoft via Report Message add-in. 7. Send awareness reminder to staff.",
            "systems": ["Microsoft Defender", "Exchange Online", "Microsoft Entra ID"],
        },
        {
            "title": "New Hire — Full Onboarding Checklist",
            "category": "Onboarding / Offboarding",
            "symptoms": "New starter, onboarding, new employee setup, provision new user, new consultant joining",
            "resolution": "1. Create M365 account in Admin Centre — assign E3/E5 licence. 2. Add to relevant Security Groups and Distribution Lists. 3. Add to Microsoft Teams channels. 4. Create Salesforce account with appropriate Profile. 5. Provision laptop — enrol in Intune. 6. Configure email signature. 7. Set up MFA with Microsoft Authenticator. 8. Grant SharePoint site access as needed. 9. Provide login credentials securely. 10. Log in asset register.",
            "systems": ["Microsoft 365", "Salesforce", "Microsoft Intune", "SharePoint Online"],
        },
        {
            "title": "Staff Departure — Full Offboarding Checklist",
            "category": "Onboarding / Offboarding",
            "symptoms": "Employee leaving, offboarding, remove access, consultant departing, last day, disable account",
            "resolution": "1. Disable M365 account (do not delete yet). 2. Remove all licences. 3. Deactivate Salesforce account — reassign owned records. 4. Remove from all Security Groups and Teams channels. 5. Convert mailbox to Shared Mailbox if manager needs access. 6. Transfer OneDrive files to manager. 7. Remote wipe company data via Intune (selective wipe). 8. Collect physical hardware. 9. Update asset register. 10. After 30-day retention, delete account.",
            "systems": ["Microsoft 365", "Salesforce", "Microsoft Intune", "SharePoint Online"],
        },
        {
            "title": "Teams — Meeting Room Audio/Video Issues",
            "category": "Network / Hardware",
            "symptoms": "Meeting room camera not working, no audio in meeting room, Teams room display issues, video conferencing broken, can't join meeting",
            "resolution": "1. Check all cables — USB, HDMI, power. 2. Restart the Teams Room device. 3. Check that the correct audio/video peripherals are selected in Teams settings. 4. Test with a different USB port. 5. Check for firmware updates on the conferencing hardware. 6. If persistent, try a different Teams account to rule out account-specific issues. 7. Escalate to vendor if hardware fault suspected.",
            "systems": ["Microsoft Teams", "Meeting Room Hardware"],
        },
    ]

    for article in articles:
        add_kb_article(
            title=article["title"],
            category=article["category"],
            symptoms=article["symptoms"],
            resolution=article["resolution"],
            systems=article.get("systems"),
        )

    print(f"Seeded {len(articles)} knowledge base articles.")


def seed_sample_tickets():
    """Create sample tickets in various states for demo purposes."""

    tickets = [
        {
            "subject": "Can't log in after phone upgrade",
            "description": "I upgraded to a new iPhone yesterday and now I can't get past the MFA prompt. My authenticator app isn't set up on the new phone.",
            "requester": "Sarah Chen",
            "category": "Security / Access",
            "priority": "High",
            "assigned_to": "Blair Douglass",
            "status": "Resolved",
            "resolution_steps": ["Reset MFA registration in Entra ID", "User re-enrolled Authenticator on new phone", "Verified login successful"],
        },
        {
            "subject": "New consultant needs Salesforce access",
            "description": "James Wright is starting on Monday as a senior consultant. He needs a Salesforce account with standard consultant permissions and access to the Melbourne rate cards.",
            "requester": "HR Team",
            "category": "Salesforce",
            "priority": "Medium",
            "assigned_to": "Carolyn Hayward",
            "status": "Resolved",
            "resolution_steps": ["Created Salesforce user account", "Assigned Consultant profile", "Added rate card permission set", "Sent login credentials"],
        },
        {
            "subject": "Laptop blocked from accessing Teams",
            "description": "My laptop shows a compliance error and I can't open Teams or Outlook. It says my device doesn't meet security requirements.",
            "requester": "David Park",
            "category": "Intune / Device",
            "priority": "High",
            "assigned_to": "Blair Douglass",
            "status": "In Progress",
            "resolution_steps": ["Checking Intune compliance status", "Likely missing Windows update"],
        },
        {
            "subject": "Deleted project folder from SharePoint",
            "description": "I accidentally deleted the entire Q1 2026 project folder from the Melbourne SharePoint site. Can it be recovered? It had about 50 documents in it.",
            "requester": "Lisa Thompson",
            "category": "SharePoint / Files",
            "priority": "High",
            "assigned_to": "Blair Douglass",
            "status": "Open",
        },
        {
            "subject": "Suspicious email from Microsoft support",
            "description": "I received an email saying my Microsoft 365 account will be suspended unless I verify my identity via a link. The sender address looks slightly off. I haven't clicked anything yet.",
            "requester": "Mark Williams",
            "category": "Security / Access",
            "priority": "High",
            "assigned_to": "Blair Douglass",
            "status": "Open",
        },
        {
            "subject": "Wi-Fi keeps dropping in Level 3 meeting room",
            "description": "The Wi-Fi in the Level 3 boardroom keeps disconnecting during video calls. It's happened three times this week during client meetings.",
            "requester": "Reception",
            "category": "Network / Hardware",
            "priority": "Medium",
            "assigned_to": "Blair Douglass",
            "status": "Open",
        },
        {
            "subject": "Consultant leaving Friday — full offboarding needed",
            "description": "Rachel Kumar's last day is this Friday. Need full offboarding: disable accounts, collect laptop, transfer files to her manager Tom.",
            "requester": "HR Team",
            "category": "Onboarding / Offboarding",
            "priority": "Medium",
            "assigned_to": "Blair Douglass",
            "status": "Open",
        },
        {
            "subject": "Salesforce rate card import error",
            "description": "I tried to import the new rate cards into the Salesforce price book but keep getting a validation error on the CSV. Can someone check the format?",
            "requester": "Finance Team",
            "category": "Salesforce",
            "priority": "Low",
            "assigned_to": "Carolyn Hayward",
            "status": "Open",
        },
    ]

    for t in tickets:
        ref = create_ticket(
            subject=t["subject"],
            description=t["description"],
            requester=t["requester"],
            category=t.get("category"),
            priority=t.get("priority", "Medium"),
            assigned_to=t.get("assigned_to"),
            resolution_steps=t.get("resolution_steps"),
        )

        if t.get("status") and t["status"] != "Open":
            update_ticket(ref, status=t["status"])

    print(f"Seeded {len(tickets)} sample tickets.")


if __name__ == "__main__":
    init_db()
    seed_knowledge_base()
    seed_sample_tickets()
    print("Done — database seeded.")