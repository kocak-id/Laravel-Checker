import framework
# unique to module
import os
import re
import hashlib
import urllib

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('source', 'database', 'yes', 'source of module input')
        self.register_option('verbose', self.goptions['verbose']['value'], 'yes', self.goptions['verbose']['desc'])
        self.info = {
                     'Name': 'Hosting History',
                     'Author': 'thrapt (thrapt@gmail.com)',
                     'Description': 'Checks Netcraft for the Hosting History of given target.',
                     'Comments': [
                                  'Source options: database, <hostname>, <path/to/infile>',
                                 ]
                     }

    def do_run(self, params):
        if not self.validate_options(): return
        # === begin here ===
        self.netcraft()

    def netcraft(self):
        verbose = self.options['verbose']['value']
        cookies = {}

        # handle sources
        source = self.options['source']['value']
        if source == 'database':
            hosts = [x[0] for x in self.query('SELECT DISTINCT host FROM hosts WHERE host IS NOT NULL ORDER BY host')]
            if len(hosts) == 0:
                self.error('No hosts in the database.')
                return
        elif os.path.exists(source): hosts = open(source).read().split()
        else: hosts = [source]

        for host in hosts:
            url = 'http://uptime.netcraft.com/up/graph?site=%s' % (host)
            if verbose: self.output('URL: %s' % url)
            try: resp = self.request(url, cookies=cookies)
            except KeyboardInterrupt:
                print ''
            except Exception as e:
                self.error(e.__str__())
            if not resp: break

            if 'set-cookie' in resp.headers:
                # we have a cookie to set!
                if verbose: self.output('Setting cookie...')
                cookie = resp.headers['set-cookie']
                # this was taken from the netcraft page's JavaScript, no need to use big parsers just for that
                # grab the cookie sent by the server, hash it and send the response
                challenge_token = (cookie.split('=')[1].split(';')[0])
                response = hashlib.sha1(urllib.unquote(challenge_token))
                cookies = {
                            'netcraft_js_verification_response': '%s' % response.hexdigest(),
                            'netcraft_js_verification_challenge': '%s' % challenge_token,
                            'path' : '/'
                          }

                # Now we can request the page again
                if verbose: self.output('URL: %s' % url)
                try: resp = self.request(url, cookies=cookies)
                except KeyboardInterrupt:
                    print ''
                except Exception as e:
                    self.error(e.__str__())

            content = resp.text

            # instantiate history list and creater header row
            history = [['OS', 'Server', 'Last Changed', 'IP Address', 'Owner']]
            rows = re.findall(r'<tr class="T\wtr\d*">(?:\s|.)+?<\/div>', content)
            for row in rows:
                cell = re.findall(r'>(.*?)<', row)
                raw  = [cell[0], cell[2], cell[4], cell[6], cell[8]]
                history.append([x.strip() for x in raw])

            if len(history) > 0:
                self.build_table(history, True)
            else:
                self.output('No results found')