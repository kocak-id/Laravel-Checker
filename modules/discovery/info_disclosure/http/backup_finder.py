import framework
# unique to module

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('source', 'db', 'yes', 'source of hosts used for module input')
        self.register_option('uri', 'wp-config.php', 'yes', 'URI to the original filename')
        self.register_option('searchstr', '<?php', 'yes', 'string to search for in the response for false positive reduction')
        self.register_option('verbose', self.goptions['verbose']['value'], 'yes', self.goptions['verbose']['desc'])
        self.info = {
                     'Name': 'Backup File Finder',
                     'Author': 'Jay Turla (@shipcod3) and Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Checks hosts for exposed backup files. The default configuration searches for wp-config.php files which contain WordPress database configuration information.',
                     'Comments': [
                                  'Source options: [ db | <hostname> | ./path/to/file | query <sql> ]',
                                  'Reference: http://feross.org/cmsploit/',
                                  'Google Dork: i.e. inurl:wp-config.conf ext:conf',
                                  ]
                     }

    def do_run(self, params):
        if not self.validate_options(): return
        # === begin here ===
        self.wpconfig()
    
    def wpconfig(self):
        verbose = self.options['verbose']['value']
        uri = self.options['uri']['value']
        searchstr = self.options['searchstr']['value']
        
        hosts = self.get_source(self.options['source']['value'], 'SELECT DISTINCT host FROM hosts WHERE host IS NOT NULL ORDER BY host')
        if not hosts: return

        protocols = ['http', 'https']

        # some files are inspired by cmsploit
        uris = [uri, uri[:uri.rindex('.')]]
        exts = ['.txt', '.save', '.save.1', '.save.2', '.swp', '.swo', '.conf', '.old', '.bak', '~', '-', '#', '%23']
        filenames = []
        # mangle root uris to create a list of possible backup filenames
        for rooturi in uris:
            for ext in exts:
                filenames.append('%s%s' % (rooturi, ext))

        cnt = 0
        for host in hosts:
            flag = 0
            for proto in protocols:
                for filename in filenames:
                    url = '%s://%s/%s' % (proto, host, filename)
                    try:
                        resp = self.request(url, redirect=False)
                        code = resp.status_code
                    except KeyboardInterrupt:
                        print ''
                        return
                    except:
                        code = 'Error'
                    if code == 200 and searchstr in resp.text:
                        self.alert('%s => %s. \'%s\' file found!' % (url, code, filename))
                        cnt += 1
                        flag = 1
                        break
                    else:
                        if verbose: self.output('%s => %s' % (url, code))
                if flag: break
        self.output('%d \'%s\' backup pages found' % (cnt, uri))
