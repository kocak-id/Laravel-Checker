import module
# unique to module
from urlparse import urlparse

class Module(module.Module):

    def __init__(self, params):
        module.Module.__init__(self, params, query='SELECT DISTINCT netblock FROM netblocks WHERE netblock IS NOT NULL')
        self.info = {
            'Name': 'Whois Company Harvester',
            'Author': 'Tim Tomes (@LaNMaSteR53)',
            'Description': 'Uses the ARIN Whois RWS to harvest Companies data from whois queries for the given netblock. Updates the \'companies\' table with the results.'
        }

    def module_run(self, netblocks):
        headers = {'Accept': 'application/json'}
        for netblock in netblocks:
            self.heading(netblock, level=0)
            urls = [
                'http://whois.arin.net/rest/cidr/%s' % (netblock),
                'http://whois.arin.net/rest/ip/%s' % (netblock.split('/')[0]),
            ]
            for url in urls:
                self.verbose('URL: %s' % url)
                resp = self.request(url, headers=headers)
                if 'No record found for the handle provided.' in resp.text:
                    self.output('No companies found.')
                    continue
                for ref in ['orgRef', 'customerRef']:
                    if ref in resp.json['net']:
                        company = resp.json['net'][ref]['@name']
                        handle = resp.json['net'][ref]['$']
                        self.output('%s (%s)' % (company, handle))
                        self.add_companies(company=company, description=handle)
