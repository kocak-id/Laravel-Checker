import framework
# unique to module

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('source', 'db', 'yes', 'source of module input')
        self.register_option('verbose', self.goptions['verbose']['value'], 'yes', self.goptions['verbose']['desc'])
        self.info = {
                     'Name': 'Dot Net Nuke Remote File Upload Vulnerability Checker',
                     'Author': 'Jay (@shipcod3)',
                     'Description': 'Checks the hosts for a DNN fcklinkgallery page which is possibly vulnerable to Remote File Upload.',
                     'Comments': [
                                  'Source options: db, <hostname>, <path/to/infile>',
                                  'http://www.exploit-db.com/exploits/12700/',
                                  ]
                     }

    def do_run(self, params):
        if not self.validate_options(): return
        # === begin here ===
        self.check_for_dnnfcklink()
    
    def check_for_dnnfcklink(self):
        verbose = self.options['verbose']['value']
        
        hosts = self.get_source(self.options['source']['value'], 'SELECT DISTINCT host FROM hosts WHERE host IS NOT NULL ORDER BY host')
        if not hosts: return

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
                if code == 200 and '> Link Gallery' in resp.text:
                    self.alert('%s => %s. Possible DNN Fcklinkgallery page found!' % (url, code))
                    cnt += 1
                else:
                    if verbose: self.output('%s => %s' % (url, code))
        self.output('%d DNN Fcklinkgallery pages found' % (cnt))
