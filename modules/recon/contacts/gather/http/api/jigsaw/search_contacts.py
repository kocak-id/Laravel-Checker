import module
# unique to module
import urllib
import time

class Module(module.Module):

    def __init__(self, params):
        module.Module.__init__(self, params, query='SELECT DISTINCT company FROM companies WHERE company IS NOT NULL ORDER BY company')
        self.register_option('keywords', None, 'no', 'additional keywords to identify company')
        self.info = {
                     'Name': 'Jigsaw Contact Enumerator',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Harvests contacts from the Jigsaw.com API. Updates the \'contacts\' table with the results.'
                     }

    def module_run(self, companies):
        self.api_key = self.get_key('jigsaw_api')
        self.tot = 0
        self.new = 0
        for company in companies:
            company_id = self.get_company_id(company)
            if company_id:
                self.get_contacts(company_id)
        self.summarize(self.new, self.tot)

    def get_company_id(self, company_name):
        self.heading(company_name, level=0)
        keywords = self.options['keywords']
        all_companies = []
        cnt = 0
        size = 50
        params = ' '.join([x for x in [company_name, keywords] if x])
        url = 'https://www.jigsaw.com/rest/searchCompany.json'
        #while True:
        payload = {'token': self.api_key, 'name': params, 'offset': cnt, 'pageSize': size}
        self.verbose('Query: %s?%s' % (url, urllib.urlencode(payload)))
        resp = self.request(url, payload=payload, redirect=False)
        jsonobj = resp.json
        if jsonobj['totalHits'] == 0:
            self.output('No company matches found.')
            return
        else:
            companies = jsonobj['companies']
            for company in companies:
                if company['activeContacts'] > 0:
                    location = '%s, %s, %s' % (company['city'], company['state'], company['country'])
                    all_companies.append((company['companyId'], company['name'], company['activeContacts'], location))
            #cnt += size
            #if cnt > jsonobj['totalHits']: break
            # jigsaw rate limits requests per second to the api
            #time.sleep(.25)
        if len(all_companies) == 0:
            self.output('No contacts available for companies matching \'%s\'.' % (self.options['company']))
            return
        if len(all_companies) == 1:
            company_id = all_companies[0][0]
            company_name = all_companies[0][1]
            contact_cnt = all_companies[0][2]
            self.output('Unique company match found: [%s - %s (%s contacts)]' % (company_name, company_id, contact_cnt))
            return company_id
        id_len = len(max([str(x[0]) for x in all_companies], key=len))
        for company in all_companies:
            self.output('[%s] %s - %s (%s contacts)' % (str(company[0]).ljust(id_len), company[1], company[3], company[2]))
        company_id = raw_input('Enter Company ID from list [%s - %s]: ' % (all_companies[0][1], all_companies[0][0]))
        if not company_id: company_id = all_companies[0][0]
        return company_id

    def get_contacts(self, company_id):
        self.output('Gathering contacts...')
        cnt = 0
        size = 100
        url = 'https://www.jigsaw.com/rest/searchContact.json'
        while True:
            payload = {'token': self.api_key, 'companyId': company_id, 'offset': cnt, 'pageSize': size}
            resp = self.request(url, payload=payload, redirect=False)
            jsonobj = resp.json
            for contact in jsonobj['contacts']:
                contact_id = contact['contactId']
                fname = self.html_unescape(contact['firstname'])
                # fname includes the preferred name as an element that needs to be removed
                fname = ' '.join(fname.split()[:2]) if len(fname.split()) > 2 else fname
                lname = self.html_unescape(contact['lastname'])
                name = '%s %s' % (fname, lname)
                fname, mname, lname = self.parse_name(name)
                title = self.html_unescape(contact['title'])
                city = self.html_unescape(contact['city']).title()
                state = self.html_unescape(contact['state']).upper()
                region = []
                for item in [city, state]:
                    if item: region.append(item)
                region = ', '.join(region)
                country = self.html_unescape(contact['country']).title()
                self.output('[%s] %s - %s (%s - %s)' % (contact_id, name, title, region, country))
                self.new += self.add_contacts(first_name=fname, middle_name=mname, last_name=lname, title=title, region=region, country=country)
                self.tot += 1
            cnt += size
            if cnt > jsonobj['totalHits']: break
            # jigsaw rate limits requests per second to the api
            time.sleep(.25)
