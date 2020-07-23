import module
# unique to module
import re

class Module(module.Module):

    def __init__(self, params):
        module.Module.__init__(self, params)
        self.register_option('source', 'db', 'yes', 'source of addresses for module input (see \'show info\' for options)')
        self.info = {
                     'Name': 'w3dt.net NetBIOS Lookup',
                     'Author': 'Brendan Coles (bcoles[at]gmail.com)',
                     'Description': 'Leverages w3dt.net to gather NetBIOS information from the given host IP addresses.',
                     'Comments': [
                                  'Source options: [ db | <address> | ./path/to/file | query <sql> ]',
                                  'Shodan: http://www.shodanhq.com/?q=netbios%%20workgroup'
                                  ]
                     }
   
    def module_run(self):
        hosts = self.get_source(self.options['source'], 'SELECT DISTINCT ip_address FROM hosts WHERE ip_address IS NOT NULL')

        for host in hosts:
            # request NetBIOS info
            url = 'https://w3dt.net/tools/netbios/?submit=Scan!&clean_opt=1&host=%s' % (host)
            self.verbose('URL: %s' % url)
            resp = self.request(url, timeout=20)

            # extract and present results
            content = resp.text
            result = re.search(r'<pre>(.+?)\r\n\r\n', content, re.S)
            if result:
                self.alert("NetBIOS is enabled.\n%s" % result.group(1))
            else:
                self.verbose('w3dt.net was unable to retrieve NetBIOS information from %s.' % host)
