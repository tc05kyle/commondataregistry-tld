"""Production email service using SendGrid with enhanced features"""
import os
import sys
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content, Attachment, FileContent, FileName, FileType, Disposition
import streamlit as st
from typing import Optional, List, Dict, Any
import base64
import json
from datetime import datetime

class EmailService:
    def __init__(self):
        self.api_key = os.getenv('SENDGRID_API_KEY')
        self.from_email = os.getenv('SENDGRID_FROM_EMAIL', "noreply@dataregistry.com")
        self.from_name = os.getenv('SENDGRID_FROM_NAME', "Data Registry Platform")
        self.template_id_approval = os.getenv('SENDGRID_TEMPLATE_APPROVAL')
        self.template_id_rejection = os.getenv('SENDGRID_TEMPLATE_REJECTION')
        
        if not self.api_key:
            st.warning("SendGrid API key not configured. Email features will be disabled.")
            self.sg = None
        else:
            self.sg = SendGridAPIClient(self.api_key)
            self._verify_connection()
    
    def _verify_connection(self):
        """Verify SendGrid connection and configuration"""
        try:
            # Test API key by getting account details
            response = self.sg.client.user.get()
            if response.status_code == 200:
                st.success("SendGrid connection verified successfully")
            else:
                st.warning(f"SendGrid connection warning: {response.status_code}")
        except Exception as e:
            st.error(f"SendGrid verification failed: {e}")
            self.sg = None
    
    def send_email(self, to_email, subject, text_content=None, html_content=None):
        """Send email using SendGrid"""
        try:
            message = Mail(
                from_email=Email(self.from_email),
                to_emails=To(to_email),
                subject=subject
            )
            
            if html_content:
                message.content = Content("text/html", html_content)
            elif text_content:
                message.content = Content("text/plain", text_content)
            else:
                raise ValueError("Either text_content or html_content must be provided")
            
            response = self.sg.send(message)
            return True
            
        except Exception as e:
            st.error(f"Email sending failed: {e}")
            return False
    
    def send_approval_notification(self, to_email, entity_type, canonical_id):
        """Send approval notification email"""
        subject = f"Your {entity_type} Registration Approved"
        
        html_content = f"""
        <html>
        <body>
            <h2>Registration Approved</h2>
            <p>Congratulations! Your {entity_type.lower()} registration has been approved.</p>
            <p><strong>Canonical ID:</strong> {canonical_id}</p>
            <p>You can now use this ID to access our data management services.</p>
            <br>
            <p>Best regards,<br>Data Registry Platform Team</p>
        </body>
        </html>
        """
        
        text_content = f"""
        Registration Approved
        
        Congratulations! Your {entity_type.lower()} registration has been approved.
        
        Canonical ID: {canonical_id}
        
        You can now use this ID to access our data management services.
        
        Best regards,
        Data Registry Platform Team
        """
        
        return self.send_email(to_email, subject, text_content, html_content)
    
    def send_rejection_notification(self, to_email, entity_type, reason):
        """Send rejection notification email"""
        subject = f"Your {entity_type} Registration Status"
        
        html_content = f"""
        <html>
        <body>
            <h2>Registration Update</h2>
            <p>We regret to inform you that your {entity_type.lower()} registration could not be approved at this time.</p>
            <p><strong>Reason:</strong> {reason}</p>
            <p>Please feel free to submit a new registration request after addressing the concerns mentioned above.</p>
            <br>
            <p>Best regards,<br>Data Registry Platform Team</p>
        </body>
        </html>
        """
        
        text_content = f"""
        Registration Update
        
        We regret to inform you that your {entity_type.lower()} registration could not be approved at this time.
        
        Reason: {reason}
        
        Please feel free to submit a new registration request after addressing the concerns mentioned above.
        
        Best regards,
        Data Registry Platform Team
        """
        
        return self.send_email(to_email, subject, text_content, html_content)
    
    def send_verification_email(self, to_email, verification_token, entity_type):
        """Send email verification"""
        subject = "Verify Your Email Address"
        
        # Note: In a real implementation, you would have a verification endpoint
        verification_url = f"https://dataregistry.com/verify?token={verification_token}"
        
        html_content = f"""
        <html>
        <body>
            <h2>Email Verification Required</h2>
            <p>Thank you for registering with the Data Registry Platform.</p>
            <p>Please verify your email address by clicking the link below:</p>
            <p><a href="{verification_url}">Verify Email Address</a></p>
            <p>If you cannot click the link, copy and paste this URL into your browser:</p>
            <p>{verification_url}</p>
            <br>
            <p>Best regards,<br>Data Registry Platform Team</p>
        </body>
        </html>
        """
        
        text_content = f"""
        Email Verification Required
        
        Thank you for registering with the Data Registry Platform.
        
        Please verify your email address by visiting this URL:
        {verification_url}
        
        Best regards,
        Data Registry Platform Team
        """
        
        return self.send_email(to_email, subject, text_content, html_content)
    
    def send_admin_notification(self, admin_email, entity_type, entity_name):
        """Send notification to admin about new registration"""
        subject = f"New {entity_type} Registration Pending"
        
        html_content = f"""
        <html>
        <body>
            <h2>New Registration Pending Approval</h2>
            <p>A new {entity_type.lower()} registration is pending your approval.</p>
            <p><strong>Entity:</strong> {entity_name}</p>
            <p>Please log in to the admin dashboard to review and approve this registration.</p>
            <br>
            <p>Best regards,<br>Data Registry Platform System</p>
        </body>
        </html>
        """
        
        text_content = f"""
        New Registration Pending Approval
        
        A new {entity_type.lower()} registration is pending your approval.
        
        Entity: {entity_name}
        
        Please log in to the admin dashboard to review and approve this registration.
        
        Best regards,
        Data Registry Platform System
        """
        
        return self.send_email(admin_email, subject, text_content, html_content)
