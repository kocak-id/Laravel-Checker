import framework
# unique to module
import urllib
import json
import re

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('string', '"%s"' % (self.goptions['domain']['value']), 'yes', 'string to search for')
        self.register_option('type', 'url', 'yes', 'type of search (see \'info\' for options)')
        self.register_option('bsqli', True, 'yes', 'search for blind sqli')
        self.register_option('sqli', True, 'yes', 'search for sqli')
        self.register_option('xss', True, 'yes', 'search for xss')
        self.register_option('vulns', False, 'yes', 'if found, display vulnerabily information')
        self.register_option('store', None, 'no', 'name of database table to store search results or data will not be stored.')
        self.info = {
                     'Name': 'punkSPIDER Vulnerabilty Finder',
                     'Author': 'Tim Tomes (@LaNMaSteR53) and thrapt (thrapt@gmail.com)',
                     'Description': 'Leverages punkSPIDER to search for previosuly discovered vulnerabltiies on the given host(s).',
                     'Comments': [
                                  'The default configuration searches for vulnerabilites in the globally set target domain.',
                                  'Type options: [ url | title ]',
                                  ]
                     }
   
    def module_run(self):
        search_type = self.options['type']['value']
        if search_type.lower() not in ['url', 'title']:
            self.error('Invalid search type \'%s\'.' % (search_type))
            return
        search_str = self.options['string']['value']
        url = 'http://punkspider.hyperiongray.com/service/search/domain/'
        payload = {'searchkey': search_type, 'searchvalue': search_str, 'filtertype': 'OR'}
        for item in ['bsqli', 'sqli', 'xss']:
            if self.options[item]['value']:
                payload[item] = '1'

        tdata = []
        vuln_domains = {}
        vulns = 0
        hits = 0
        pages = 0
        page = 1
        # get search results
        while True:
            payload['pagenumber'] = page
            self.verbose('URL: %s?%s' % (url, urllib.urlencode(payload)))
            try: resp = self.request(url, payload=payload)
            except KeyboardInterrupt:
                print ''
                return
            except Exception as e:
                self.error(e.__str__())
                return

            jsonobj = resp.json
            results = jsonobj['data']['domainSummaryDTOs']
            if results:
                for result in results:
                    bsqli = result['bsqli']
                    sqli = result['sqli']
                    xss = result['xss']
                    site = result['id']
                    timestamp = result['timestamp']
                    tdata.append([site, timestamp, bsqli, sqli, xss])
                    #self.output('[ %s xss | %s sqli | %s bsqli ] %s (%s)' % (xss, sqli, bsqli, site, timestamp))
                    if any([bsqli, sqli, xss]):
                        vuln_domains[result['id']] = '.'.join(re.search('//(.+?)/', result['id']).group(1).split('.')[::-1])
                page += 1
            else:
                if tdata:
                    tdata.insert(0, ['Host', 'Time', 'BSQLi', 'SQLi', 'XSS'])
                    self.table(tdata, header=True, table=self.options['store']['value'])
                hits = jsonobj['data']['rowsFound']
                pages = jsonobj['data']['numberOfPages']
                break

        # get vulnerbilities for positive results
        if vuln_domains and self.options['vulns']['value']:
            self.heading('Vulnerabilties', 1)
            for domain in vuln_domains:
                url = 'http://punkspider.hyperiongray.com/service/search/detail/%s' % vuln_domains[domain]
                try: resp = self.request(url, payload=payload)
                except KeyboardInterrupt:
                    print ''
                    return
                except Exception as e:
                    self.error(e.__str__())
                    return

                jsonobj = resp.json
                results = jsonobj['data']
                if results:
                    self.alert('Domain: %s' % (domain))
                    for result in results:
                        print ''
                        vulns += 1
                        self.output('Bug: %s' % (result['bugType']))
                        self.output('URL: %s' % (result['vulnerabilityUrl']))
                        self.output('Parameter: %s' % (result['parameter']))
                print self.ruler*50

        self.output('%d results.' % (hits))
        self.output('%d pages.' % (pages))
        if vulns: self.alert('%d vulnerabilties!' % (vulns))
