import framework
# unique to module
from urlparse import urlparse

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('domain', self.goptions['domain']['value'], 'yes', self.goptions['domain']['desc'])
        self.register_option('store', False, 'yes', 'add discovered hosts to the database.')
        self.info = {
                     'Name': 'Whois POC Harvester',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Uses the ARIN Whois RWS to harvest POC data from whois queries for the given domain.',
                     'Comments': [
                                  'Source options: [ db | <domain> | ./path/to/file | query <sql> ]',
                                  ]
                     }

    def module_run(self):
        domain = self.options['domain']['value']
        store = self.options['store']['value']

        headers = {'Accept': 'application/json'}
        cnt = 0
        new = 0
        url = 'http://whois.arin.net/rest/pocs;domain=%s' % (domain)
        self.verbose('URL: %s' % url)
        resp = self.request(url, headers=headers)
        if 'Your search did not yield any results.' in resp.text:
            self.output('No contacts found.')
            return
        if not resp.json:
            self.error('Invalid JSON response for \'%s\'.\n%s' % (domain, resp.text))
            return
        handles = [x['@handle'] for x in resp.json['pocs']['pocRef']]
        for handle in handles:
            url = 'http://whois.arin.net/rest/poc/%s' % (handle)
            self.verbose('URL: %s' % url)
            resp = self.request(url, headers=headers)
            if resp.json: jsonobj = resp.json
            else:
                self.error('Invalid JSON response for \'%s\'.\n%s' % (handle, resp.text))
                continue
            poc = jsonobj['poc']
            title = 'Whois contact'
            city = poc['city']['$'].title()
            country = poc['iso3166-1']['name']['$'].title()
            fname = poc['firstName']['$'] if 'firstName' in poc else None
            lname = poc['lastName']['$']
            emails = poc['emails']['email'] if type(poc['emails']['email']) == list else [poc['emails']['email']]
            email = emails[0]['$']
            state = poc['iso3166-2']['$'].upper()
            region = '%s, %s' % (city, state)
            name = ' '.join([x for x in [fname, lname] if x])
            self.output('%s (%s) - %s (%s - %s)' % (name, email, title, region, country))
            if store: new += self.add_contact(fname=fname, lname=lname, email=email, title=title, region=region, country=country)
            cnt += 1
        self.output('%d total contacts found.' % (cnt))
        if new: self.alert('%d NEW contacts found!' % (new))
        