# packages required for framework integration
import framework
# module specific packages
import re
import json

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('adobe_db', './data/adobe_top_100.json', 'yes', 'JSON file containing the Adobe hashes and passwords')
        self.register_option('source', 'db', 'yes', 'source of hashes for module input (see \'info\' for options)')
        self.info = {
                     'Name': 'Adobe Hash Lookup',
                     'Author': 'Ethan Robish (@EthanRobish)',
                     'Description': 'Uses a local Adobe hash database to perform a reverse hash lookup and updates the \'creds\' table of the database with the positive results.',
                     'Comments': [
                                  'Source options: [ db | <hash> | ./path/to/file | query <sql> ]',
                                  'Hash types supported: Adobe\'s base64 format',
                                  ]
                     }
                     
    def module_run(self):
        adobe_leak_id = '26830509422781c65919cba69f45d889'
        
        # Move all Adobe leak hashes the passwords column to the hashes column and set the hashtype to Adobe
        if self.options['source']['value'] == 'db':
            self.query('UPDATE creds SET hash=password, password=NULL, type=\'Adobe\' WHERE hash IS NULL AND leak IS \'%s\'' % adobe_leak_id)
        
        # Find all hashes from the Adobe leak
        query = 'SELECT DISTINCT hash FROM creds WHERE hash IS NOT NULL AND password IS NULL AND leak IS \'%s\'' % adobe_leak_id
        hashes = self.get_source(self.options['source']['value'], query)
        
        with open(self.options['adobe_db']['value']) as db_file:
            adobe_db = json.load(db_file)

        # lookup each hash
        for hashstr in hashes:
            if hashstr in adobe_db:
                plaintext = adobe_db[hashstr]
                self.alert('%s => %s' % (hashstr, plaintext))
                # Move the base64 hash from the password field to the hash field and set the plaintext password.
                self.query('UPDATE creds SET password=\'%s\' WHERE hash=\'%s\'' % (plaintext, hashstr))
            else:
                self.verbose('Value not found for hash: %s' % (hashstr))