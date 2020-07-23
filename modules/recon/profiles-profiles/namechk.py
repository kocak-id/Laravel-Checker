from recon.core.module import BaseModule
from recon.mixins.threads import ThreadingMixin
import re
from hashlib import sha1
from hmac import new as hmac

class Module(BaseModule, ThreadingMixin):

    meta = {
        'name': 'NameChk.com Username Validator',
        'author': 'Tim Tomes (@LaNMaSteR53) and thrapt (thrapt@gmail.com)',
        'description': 'Leverages NameChk.com to validate the existance of usernames on specific web sites and updates the \'profiles\' table with the results.',
        'comments': (
            'Note: The global timeout option may need to be increased to support slower sites.',
        ),
        'query': 'SELECT DISTINCT username FROM profiles WHERE username IS NOT NULL',
    }

    def module_run(self, usernames):
        # hardcoded key for hmac
        key = '1Sx8srDg1u57Ei2wqX65ymPGXu0f7uAig13u'
        # retrieve list of sites
        self.verbose('Retrieving site data...')
        url = 'http://namechk.com/Content/sites.min.js'
        resp = self.request(url)
        # extract sites info from the js file
        pattern = 'n:"([^"]+)",r:\d+,i:(\d+),s:"([^"]+)",b:"([^"]+)"'
        sites = re.findall(pattern, resp.text.replace('\n', ''))
        # reset url for site requests
        url = 'http://namechk.com/check'
        # required header for site requests
        headers = {'X-Requested-With': 'XMLHttpRequest'}
        for username in usernames:
            self.heading(username, level=0)
            # validate memberships
            self.thread(sites, key, url, headers, username)

    def module_thread(self, site, key, url, headers, username):
        i = site[1]
        name = site[0]
        # build the hmac payload
        message = "POST&%s?i=%s&u=%s" % (url, i, username)
        b64_hmac_sha1 = '%s' % hmac(key, message, sha1).digest().encode('base64')[:-1]
        payload = {'i': i, 'u': username, 'o_0': b64_hmac_sha1}
        # build and send the request
        try:
            resp = self.request(url, method='POST', headers=headers, payload=payload)
        except Exception as e:
            self.error('%s: %s' % (name, e.__str__()))
        else:
            x = resp.text
            if int(x) > 0:
                if int(x) == 2:
                    # update profiles table
                    profile_url = site[3].replace('{0}', '%s') % username
                    self.add_profiles(username=username, resource=name, url=profile_url, category='social')
                    self.query('DELETE FROM profiles WHERE username = ? and url IS NULL', (username,))
                    self.alert('%s: %s' % (name, STATUSES[x]))
                else:
                    self.verbose('%s: %s' % (name, STATUSES[x]))
            else:
                self.error('%s: %s' % (name, 'Unknown error.'))

STATUSES = {
    '1': 'Available',
    '2': 'User Exists!',
    '3': 'Unknown',
    '4': 'Indefinite'
}
