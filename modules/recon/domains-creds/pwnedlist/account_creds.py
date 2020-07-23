import module
# unique to module
import os

class Module(module.Module):

    def __init__(self, params):
        module.Module.__init__(self, params, query='SELECT DISTINCT username FROM creds WHERE username IS NOT NULL and password IS NULL ORDER BY username')
        self.info = {
                     'Name': 'PwnedList - Account Credentials Fetcher',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Queries the PwnedList API for credentials associated with the given usernames. Updates the \'creds\' table with the results.',
                     'Comments': [
                                  'API Query Cost: 1 query per request.'
                                  ]
                     }

    def module_run(self, accounts):
        key = self.get_key('pwnedlist_api')
        secret = self.get_key('pwnedlist_secret')
        decrypt_key = secret[:16]
        iv = self.get_key('pwnedlist_iv')

        # setup API call
        method = 'accounts.query'
        url = 'https://api.pwnedlist.com/api/1/%s' % (method.replace('.','/'))

        # build the payload
        payload = {'account_identifier': ','.join(accounts), 'daysAgo': 0}
        payload = self.build_pwnedlist_payload(payload, method, key, secret)
        # make request
        resp = self.request(url, payload=payload)
        if resp.json: jsonobj = resp.json
        else:
            self.error('Invalid JSON response.\n%s' % (resp.text))
            return
        if len(jsonobj['results']) == 0:
            self.output('No results returned.')
        else:
            cnt = 0
            new = 0
            for cred in jsonobj['results']:
                username = cred['plain']
                password = self.aes_decrypt(cred['password'], decrypt_key, iv)
                leak = cred['leak_id']
                self.output('%s:%s' % (username, password))
                cnt += 1
                new += self.add_creds(username, password, None, leak)
                self.query('DELETE FROM creds WHERE username = \'%s\' and password IS NULL and hash IS NULL' % (username))
            self.summarize(new, cnt)
