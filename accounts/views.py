import uuid
import sys
from accounts.models import Token
from django.core.mail import send_mail
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.shortcuts import redirect, render


def send_login_email(request):
    print('sending email', file=sys.stderr)
    email = request.POST['email']
    uid = str(uuid.uuid4())
    Token.objects.create(email=email, uid=uid)
    url = 'http://localhost/accounts/login/?uid={uid}/'.format(uid=uid)
    send_mail(
        'Your login link for Superlists',
        'Use this link to log into the site:\n\n {url}\n'.format(url=url),
        'noreply@superlists',
        [email],
    )
    return render('login_email_sent.html')


def login(request):
    print('login view', file=sys.stderr)
    uid = request.GET.get('uid')
    user = authenticate(uid=uid)
    if user is not None:
        auth_login(request, user)
    return redirect('/')


def logout(request):
    auth_logout(request)
    return redirect('/')

