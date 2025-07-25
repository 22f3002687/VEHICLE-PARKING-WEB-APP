
import os
import csv
import json
import requests
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from weasyprint import HTML
from .extensions import celery, db
from .models import User, Reservation
from datetime import datetime, timedelta
from .config import GOOGLE_CHAT_WEBHOOK_URL, SENDER_EMAIL, SENDER_APP_PASSWORD, SMTP_SERVER, SMTP_PORT
from sqlalchemy import func


def send_to_google_chat(webhook_url, message):
    """Sends a message to a Google Chat webhook."""
    headers = {'Content-Type': 'application/json; charset=UTF-8'}
    data = json.dumps({'text': message})
    try:
        requests.post(webhook_url, headers=headers, data=data, timeout=10)
        print("Successfully sent message to Google Chat.")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error sending message to Google Chat: {e}")
        return False

def send_email(to_email, subject, html_content, attachment_path=None):
    """Sends an email with optional attachment"""
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(html_content, 'html'))

        if attachment_path and os.path.exists(attachment_path):
            with open(attachment_path, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f"attachment; filename=\"{os.path.basename(attachment_path)}\"")
            msg.attach(part)

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_APP_PASSWORD)
            server.send_message(msg)
            print(f"Successfully sent email to {to_email}")
        return True
    except Exception as e:
        print(f"Error sending email to {to_email}: {e}")
        return False


@celery.task
def announce_new_lot(lot_name, address):
    print(f"--- Announcing New Lot: {lot_name} ---")
    message = f"📢 *New Parking Lot Available!*\n\n*Name:* {lot_name}\n*Address:* {address}\n\nBook your spot now on Park Vehicle!"
    send_to_google_chat(GOOGLE_CHAT_WEBHOOK_URL, message)
    return "Announcement sent."

@celery.task
def send_daily_reminders():
    print("--- Running Daily Reminder Task ---")
    seven_days_ago = datetime.now() - timedelta(days=7) 
    last_booking_subquery = db.session.query(Reservation.user_id, func.max(Reservation.booking_timestamp).label('last_booking')).group_by(Reservation.user_id).subquery()
    inactive_users = db.session.query(User).outerjoin(last_booking_subquery, User.id == last_booking_subquery.c.user_id).filter((last_booking_subquery.c.last_booking < seven_days_ago) | (last_booking_subquery.c.last_booking == None)).filter(User.role == 'user').all()

    if not inactive_users:
        print("No inactive users found to remind.")
        send_to_google_chat(GOOGLE_CHAT_WEBHOOK_URL, "✅ Daily reminder job ran successfully. No inactive users found.")
        return "No inactive users."

    email_subject = "A Friendly Reminder from Park Vehicle"
    
    
    sent_count = 0
    for user in inactive_users:
        email_html = f"""<html>
        <body>
        <p>Hi {user.username},</p><p>It's been a while since your last booking. Don't forget to reserve a spot on Park Vehicle if you need one!</p><p>Best,<br>The Parking Vehicle Team
        </p>
        </body>
        </html>"""
        if send_email(user.email, email_subject, email_html):
            sent_count += 1
    
    summary_message = f"✅ Daily reminder job finished.\nSent emails to {sent_count}/{len(inactive_users)} inactive users."
    send_to_google_chat(GOOGLE_CHAT_WEBHOOK_URL, summary_message)
    
    print("--- Daily Reminder Task Finished ---")
    return f"Sent reminders to {sent_count} users."

@celery.task
def send_monthly_reports():
    print("--- Running Monthly Report Task ---")
    users = User.query.filter_by(role='user').all()
    report_dir = os.path.join(os.path.abspath(os.path.dirname(__name__)), 'reports')
    os.makedirs(report_dir, exist_ok=True)

    for user in users:
        last_month = datetime.now() - timedelta(days=30)
        reservations = Reservation.query.filter(Reservation.user_id == user.id, Reservation.is_active == False, Reservation.parking_timestamp >= last_month).all()

        total_spent = sum(r.parking_cost for r in reservations if r.parking_cost)
        spots_booked = len(reservations)
        
        lot_counts = {}
        for r in reservations:
            if r.spot and r.spot.lot:
                lot_counts[r.spot.lot.location_name] = lot_counts.get(r.spot.lot.location_name, 0) + 1
        most_used_lot = max(lot_counts, key=lot_counts.get) if lot_counts else "N/A"

        report_html = f"""
        <html>
        <head>
        <style>
        body {{ font-family: sans-serif; }} 
        h1 {{ color: #333; }} 
        ul {{ list-style-type: none; padding: 0; }} 
        li {{ background: #f4f4f4; margin: 5px 0; padding: 10px; border-radius: 5px; }}
        </style>
        </head>
        <body>
        <h1>Monthly Parking Report for {user.username}</h1>
        <p>Hi {user.username},</p>
        <p>Here is your activity summary for the last 30 days:</p>
        <ul>
            <li><b>Total Spots Booked:</b> {spots_booked}</li>
            <li><b>Total Amount Spent:</b> ₹{total_spent:.2f}</li>
            <li><b>Most Used Parking Lot:</b> {most_used_lot}</li>
        </ul>
        <p>Thank you for using Park Vehicle!</p>
        </body>
        </html>
        """
        
        pdf_filename = f"{user.username}_report_{datetime.now().strftime('%Y_%m')}.pdf"
        pdf_filepath = os.path.join(report_dir, pdf_filename)
        HTML(string=report_html).write_pdf(pdf_filepath)
        
        email_subject = "Your Park Vehicle Monthly Report"
        send_email(user.email, email_subject, report_html, attachment_path=pdf_filepath)

    summary_message = f"✅ Monthly report job finished.\nProcessed and sent reports for {len(users)} users."
    send_to_google_chat(GOOGLE_CHAT_WEBHOOK_URL, summary_message)

    print("--- Monthly Report Task Finished ---")
    return f"Generated reports for {len(users)} users."

@celery.task
def export_csv_task(user_id):
    print(f"--- Starting CSV Export for User ID: {user_id} ---")
    user = User.query.get(user_id)
    if not user: return
        
    history = Reservation.query.filter_by(user_id=user_id, is_active=False).order_by(Reservation.booking_timestamp.desc()).all()
    export_dir = os.path.join(os.path.abspath(os.path.dirname(__name__)), 'exports')
    os.makedirs(export_dir, exist_ok=True)
    filename = f"{user.username}_parking_history_{datetime.now().strftime('%Y%m%d')}.csv"
    filepath = os.path.join(export_dir, filename)

    headers = ['Lot Name', 'Spot Number', 'Booked On', 'Parked On', 'Left On', 'Cost (INR)']
    with open(filepath, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(headers)
        for r in history:
            lot_name = r.spot.lot.location_name if r.spot and r.spot.lot else 'N/A'
            spot_number = r.spot.spot_number if r.spot else 'N/A'
            writer.writerow([lot_name, spot_number, r.booking_timestamp.strftime('%Y-%m-%d %H:%M:%S'), r.parking_timestamp.strftime('%Y-%m-%d %H:%M:%S') if r.parking_timestamp else 'N/A', r.leaving_timestamp.strftime('%Y-%m-%d %H:%M:%S') if r.leaving_timestamp else 'N/A', f"{r.parking_cost:.2f}" if r.parking_cost is not None else '0.00'])
    
    email_subject = "Your Park Vehicle History Export"
    email_body = f"""<html>
    <body>
    <p>Hi {user.username},</p><p>Attached is your parking history export as requested.</p>
    </body>
    </html>"""
    send_email(user.email, email_subject, email_body, attachment_path=filepath)
    
    completion_message = f"✅ Hi {user.username}, your CSV export is complete and has been sent to your email: {user.email}."
    send_to_google_chat(GOOGLE_CHAT_WEBHOOK_URL, completion_message)

    print(f"--- CSV Export for User ID: {user_id} finished. ---")
    return f"Export successful for {user.username}."
