import framework
import __builtin__
# unique to module
import pwnedlist
import os
import json
import re

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.options = {
                        'leak_id': '0b35c0ba48a899baeea2021e245d6da8'
                        }
        self.info = {
                     'Name': 'PwnedList - Leak Details Fetcher',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Queries the PwnedList API for information about the leak IDs in the given source.',
                     'Comments': []
                     }

    def do_run(self, params):
        self.leak_lookup()

    def leak_lookup(self):
        # api key management
        key = self.manage_key('pwned_key', 'PwnedList API Key')
        if not key: return
        secret = self.manage_key('pwned_secret', 'PwnedList API Secret')
        if not secret: return

        # API query guard
        ans = raw_input('This operation will use 1 API queries. Do you want to continue? [Y/N]: ')
        if ans.upper() != 'Y': return

        # setup API call
        method = 'leaks.info'
        url = 'https://pwnedlist.com/api/1/%s' % (method.replace('.','/'))
        payload = {'leakId': self.options['leak_id']}
        payload = pwnedlist.build_payload(payload, method, key, secret)
        # make request
        try: resp = self.request(url, payload=payload)
        except KeyboardInterrupt:
            print ''
            return
        except Exception as e:
            self.error(e.__str__())
            return
        if resp.json: jsonobj = resp.json
        else:
            self.error('Invalid JSON returned from the API.')
            return

        # handle output
        leak = jsonobj['leaks'][0]
        for key in leak.keys():
            header = ' '.join(key.split('_')).title()
            self.output('%s: %s' % (header, leak[key]))