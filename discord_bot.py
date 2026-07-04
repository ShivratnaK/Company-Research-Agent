import requests


def send_report(bot_token, channel_id, applicant_name, applicant_email, company_name, company_website, pdf_buffer):
    if not bot_token or not channel_id:
        return False, "Discord not configured"
    try:
        message = (
            f"📊 **New Company Research Report**\n\n"
            f"👤 **Applicant:** {applicant_name}\n"
            f"📧 **Email:** {applicant_email}\n"
            f"🏢 **Company:** {company_name}\n"
            f"🌐 **Website:** {company_website}"
        )
        # Send message + PDF file together
        pdf_buffer.seek(0)
        filename = f"{company_name.replace(' ', '_')}_report.pdf"
        resp = requests.post(
            f"https://discord.com/api/v10/channels/{channel_id}/messages",
            headers={"Authorization": f"Bot {bot_token}"},
            data={"content": message},
            files={"file": (filename, pdf_buffer, "application/pdf")},
            timeout=15
        )
        if resp.status_code in [200, 201]:
            return True, "Sent successfully"
        return False, f"Discord error: {resp.status_code} — {resp.text}"
    except Exception as e:
        return False, str(e)
