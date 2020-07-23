import framework
# unique to module
import os
import urllib

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('source', 'database', 'yes', 'source of module input')
        self.register_option('verbose', self.goptions['verbose']['value'], 'yes', self.goptions['verbose']['desc'])
        self.info = {
                     'Name': 'Dot Net Nuke Remote File Upload Vulnerability Checker',
                     'Author': 'Jay Turla (@shipcod3)',
                     'Description': 'Checks the hosts for a DNN fcklinkgallery page which is possibly vulnerable to Remote File Upload.',
                     'Comments': [
                                  'Source options: database, <hostname>, <path/to/infile>',
                                  'http://www.exploit-db.com/exploits/12700/'
                                  ]
                     }

    def do_run(self, params):
        if not self.validate_options(): return
        # === begin here ===
        self.check_for_dnnfcklink()
    
    def check_for_dnnfcklink(self):
        verbose = self.options['verbose']['value']
        
        # handle sources
        source = self.options['source']['value']
        if source == 'database':
            hosts = [x[0] for x in self.query('SELECT DISTINCT host FROM hosts WHERE host IS NOT NULL ORDER BY host')]
            if len(hosts) == 0:
                self.error('No hosts in the database.')
                return
        elif os.path.exists(source): hosts = open(source).read().split()
        else: hosts = [source]

        # check all hosts for DNN fcklinkgallery page
        protocols = ['http', 'https']
        cnt = 0
        for host in hosts:
            for proto in protocols:
                url = '%s://%s/Providers/HtmlEditorProviders/Fck/fcklinkgallery.aspx/' % (proto, host)
                try:
                    resp = self.request(url, redirect=False)
                    code = resp.status_code
                except KeyboardInterrupt:
                    print ''
                    return
                except:
                   code = 'Error'
                if code == 200:
                    self.alert('%s => %s. Possible DNN fcklinkgallery page found!' % (url, code))
                    cnt += 1
                else:
                    if verbose: self.output('%s => %s' % (url, code))
        self.output('%d DNN fcklinkgallery pages found.' % (cnt))
