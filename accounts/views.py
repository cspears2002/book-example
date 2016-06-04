from django.shortcuts import render

import uuid
import sys
from accounts.models import Token
from django.shortcuts import render
from django.core.mail import send_mail


def send_login_email(request):
    print('login view', file=sys.stderr)
    email = request.POST['email']
    uid = str(uuid.uuid4())
    Token.objects.create(email=email, uid=uid)
    url = 'http://localhost/accounts/login/{uid}/'.format(uid=uid)
    send_mail(
        'Your login link for Superlists',
        'Use this link to log into the site:\n\n {url}\n'.format(url=url),
        'noreply@superlists',
        [email],
    )
    return render('login_email_sent.html')
