import os
import poplib
import re
import time

from django.core import mail
from django.test import override_settings

from .base import FunctionalTest

TEST_EMAIL = 'edith.testuser@yahoo.com'
SUBJECT = 'Your login link for Superlists'





class LoginTest(FunctionalTest):

    def setUp(self):
        # tidy up an emails from previous runs before we start
        self.cleanup_superlists_emails()
        super().setUp()


    def last_few_emails(self):
        # return up to 10 latest emails. new connection each time.
        inbox = poplib.POP3_SSL('pop.mail.yahoo.com')
        inbox.user(TEST_EMAIL)
        inbox.pass_(os.environ.get('YAHOO_PASSWORD'))
        last_id, _ = inbox.stat()
        for email_id in reversed(range(max(last_id - 10, 1), last_id + 1)):
            _, lines, __ = inbox.retr(email_id)
            yield inbox, email_id, [l.decode('utf8') for l in lines]


    def cleanup_superlists_emails(self):
        subject_line = 'Subject: {}'.format(SUBJECT)
        for inbox, email_id, lines in self.last_few_emails():
            if subject_line in lines:
                print('deleting email id', email_id)
                inbox.dele(email_id)


    def wait_for_login_email(self):
        start = time.time()
        subject_line = 'Subject: {}'.format(SUBJECT)
        while time.time() - start < 60:
            print('checking last few emails')
            for inbox, email_id, lines in self.last_few_emails():
                if subject_line in lines:
                    self.addCleanup(lambda: inbox.dele(email_id))
                    return '\n'.join(lines)
            time.sleep(5)
        self.fail('No email with correct subject line found')


    @override_settings(EMAIL_BACKEND=mail._original_email_backend)
    def test_can_get_email_link_to_log_in(self):
        # Edith goes to the awesome superlists site
        # and notices a "Log in" section in the navbar for the first time
        # It's telling her to enter her email address, so she does

        self.browser.get(self.server_url)
        self.browser.find_element_by_name('email').send_keys(
            TEST_EMAIL + '\n'
        )

        # A message appears telling her an email has been sent
        body = self.browser.find_element_by_tag_name('body')
        self.assertIn('Check your email', body.text)

        # She checks her email and finds a message
        email_body = self.wait_for_login_email()

        # It has a url link in it
        self.assertIn('Use this link to log in', email_body)
        url_search = re.search(r'http://.+/.+$', email_body)
        if not url_search:
            self.fail('Could not find url in email body:\n{}'.format(email_body))
        url = url_search.group(0)
        self.assertIn(self.server_url, url)

        # she clicks it
        self.browser.get(url)

        # she is logged in!
        self.browser.find_element_by_link_text('Log out')
        navbar = self.browser.find_element_by_css_selector('.navbar')
        self.assertIn(TEST_EMAIL, navbar.text)

