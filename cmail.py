import smtplib #to send email from one mail another
from email.message import EmailMessage #module used to create email template
def send_mail(to,subject,body):
    server=smtplib.SMTP_SSL('smtp.gmail.com',465)
    server.login('anushakottapalli2005@gmail.com','sjtw zbjv rdem nnqo')
    msg=EmailMessage()
    msg['FROM']='anushakottapalli2005@gmail.com'
    msg['TO']=to
    msg['SUBMIT']=subject
    msg.set_content(body)
    server.send_message(msg)
    server.close()