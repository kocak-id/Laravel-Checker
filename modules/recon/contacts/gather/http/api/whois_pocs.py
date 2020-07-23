import module
# unique to module
from urlparse import urlparse

class Module(module.Module):

    def __init__(self, params):
        module.Module.__init__(self, params, query='SELECT DISTINCT domain FROM domains WHERE domain IS NOT NULL ORDER BY domain')
        self.info = {
                     'Name': 'Whois POC Harvester',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Uses the ARIN Whois RWS to harvest POC data from whois queries for the given domain. Updates the \'contacts\' table with the results.'
                     }

    def module_run(self, domains):
        headers = {'Accept': 'application/json'}
        cnt = 0
        new = 0
        for domain in domains:
            self.heading(domain, level=0)
            url = 'http://whois.arin.net/rest/pocs;domain=%s' % (domain)
            self.verbose('URL: %s' % url)
            resp = self.request(url, headers=headers)
            if 'Your search did not yield any results.' in resp.text:
                self.output('No contacts found.')
                continue
            if not resp.json:
                self.error('Invalid JSON response for \'%s\'.\n%s' % (domain, resp.text))
                continue
            handles = [x['@handle'] for x in resp.json['pocs']['pocRef']] if type(resp.json['pocs']['pocRef']) == list else [resp.json['pocs']['pocRef']['@handle']]
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
                state = poc['iso3166-2']['$'].upper() if 'iso3166-2' in poc else None
                region = ', '.join([x for x in [city, state] if x])
                name = ' '.join([x for x in [fname, lname] if x])
                self.output('%s (%s) - %s (%s - %s)' % (name, email, title, region, country))
                if email.lower().endswith(domain.lower()):
                    new += self.add_contacts(first_name=fname, last_name=lname, email=email, title=title, region=region, country=country)
                cnt += 1
        self.summarize(new, cnt)        
