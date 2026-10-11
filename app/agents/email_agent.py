class EmailAgent:
    """
    Email Agent
    - Sends individual emails
    - Sends bulk campaigns
    """

    def __init__(self):
        pass

    def send_email(self, instructions: str = None, metadata: dict = None):
        """
        Send an email.
        metadata example:
        {
            "to": "client@example.com",
            "subject": "Welcome!",
            "template": "welcome_v2"
        }
        """
        return {
            "status": "success",
            "agent": "email",
            "action": "send_email",
            "instructions": instructions,
            "metadata": metadata,
            "result": f"email_sent_to_{metadata.get('to')}"
        }

    def send_campaign(self, instructions: str = None, metadata: dict = None):
        """
        Send a bulk email campaign.
        metadata example:
        {
            "audience": "new_leads",
            "template": "campaign_v1"
        }
        """
        return {
            "status": "success",
            "agent": "email",
            "action": "send_campaign",
            "instructions": instructions,
            "metadata": metadata,
            "result": "campaign_sent"
        }
