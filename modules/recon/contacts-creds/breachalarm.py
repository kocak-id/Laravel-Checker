import module
# unique to module

class Module(module.Module):

    def __init__(self, params):
        module.Module.__init__(self, params, query='SELECT DISTINCT email FROM contacts WHERE email IS NOT NULL ORDER BY email')
        self.info = {
                     'Name': 'BreachAlarm Lookup',
                     'Author': 'Dan Woodruff (@dewoodruff)',
                     'Description': 'Leverages breachalarm.com to determine if email addresses are associated with leaked credentials. Adds compromised email addresses to the \'credentials\' table.'
                     }

    def module_run(self, emails):
        total = 0
        emailsFound = 0
        # lookup each hash
        url = 'https://breachalarm.com/account-check'
        for emailstr in emails:
            # build the request
            payload = {'email': emailstr}
            resp = self.request(url, method="POST", payload=payload)
            # retrieve the json response
            jsonobj = resp.json
            numFound = jsonobj['num']
            # if any breaches were found, show the number found and the last found date
            if numFound > 0:
                last = jsonobj['last']
                self.alert('%s => Found! Seen %s times as recent as %s.' % (emailstr, numFound, last))
                emailsFound += self.add_credentials(emailstr)
                total += 1
            else:
                self.verbose('%s => safe.' % (emailstr))
        self.summarize(emailsFound, total)
