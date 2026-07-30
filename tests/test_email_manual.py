### TESTING
from app.notifications.email_sender import send_email

send_email(
    to_address="sardarbey0@gmail.com",
    subject="Test from Nisaab",
    body="If you're reading this, email sending works!"
)
print("Sent (check your inbox)")