import os
import poplib
import re
import time

from django.core import mail
from django.test import override_settings

from .base import FunctionalTest

TEST_EMAIL = 'edith.testuser@yahoo.com'
CODE_FINDER = r'^Use this code to log in: (.+)$'


class LoginTest(FunctionalTest):

    def get_inbox_connection(self):
        inbox = poplib.POP3_SSL('pop.mail.yahoo.com')
        self.addCleanup(inbox.quit)
        inbox.user(TEST_EMAIL)
        inbox.pass_(os.environ.get('YAHOO_PASSWORD'))
        return inbox


    def wait_for_email(self, subject):
        start = time.time()
        subject_line = 'Subject: {}'.format(subject)
        inbox = self.get_inbox_connection()
        last_email_id, _ = inbox.stat()
        while time.time() - start < 60:
            last_email_id -= 1
            print('getting msg no.', last_email_id)
            _, lines, __ = inbox.retr(last_email_id)
            decoded_lines = [l.decode('utf8') for l in lines]
            if subject_line in decoded_lines:
                self.addCleanup(lambda: inbox.delete(last_email_id))
                return '\n'.join(lines)
            time.sleep(5)


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
        email_body = self.wait_for_email('Your login link for Superlists')

        # It has a url link in it
        self.assertIn('Use this link to log in', email_body)
        url_search = re.search(r'http://.+/.+/', email_body)
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

