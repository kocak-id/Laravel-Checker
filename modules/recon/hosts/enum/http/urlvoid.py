import framework
# unique to module
import re

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('source', 'db', 'yes', 'source of hosts for module input (see \'info\' for options)')
        self.info = {
                     'Name': 'URLVoid Domain Lookup',
                     'Author': 'Micah Hoffman (@WebBreacher)',
                     'Description': 'Checks urlvoid.com for information about the security of the given host.',
                     'Comments': [
                                  'Source options: [ db | <hostname> | ./path/to/file | query <sql> ]'
                                  ]
                     }
   
    def module_run(self):
        hosts = self.get_source(self.options['source']['value'], 'SELECT DISTINCT host FROM hosts WHERE host IS NOT NULL ORDER BY host')
        if not hosts: return

        for host in hosts:
            url = 'http://www.urlvoid.com/scan/%s/' % (host)
            self.verbose('URL: %s' % url)
            try: resp = self.request(url)
            except KeyboardInterrupt:
                print ''
                return
            except Exception as e:
                self.error(e.__str__())
                return

            if '<h1>AN ERROR OCCURRED</h1>' in resp.text:
                self.output('No data returned for \'%s\'' % (host))
                continue

            # Get and display the results
            blacklisted = re.search(r'Blacklist Status</td><td><span.+>(\w.+)</span>', resp.text)
            if blacklisted.group(1) == "BLACKLISTED":
                self.alert('\'%s\' is BLACKLISTED! (ruhroh)' % (host))
                detection = re.search(r'Detection Ratio</td><td>(\d+ / \d+) \(<font', resp.text)
                self.output('Detection Ratio was %s' % detection.group(1))
                detected_sites = re.findall(r'Favicon" />(.+?)</td><td><img src=".+?" alt="Alert" title="Detected!".+?"nofollow" href="(.+?)" title', resp.text)
                tdata = [['Site', 'Link']]
                for site in detected_sites:
                    tdata.append([site[0].strip(), site[1].strip()])
                self.table(tdata, True)
            else:
                self.output('\'%s\' not blacklisted...whew!' % (host))
