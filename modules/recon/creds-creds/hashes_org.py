import module
# unique to module
import StringIO
import time
import xml.etree.ElementTree

class Module(module.Module):

    def __init__(self, params):
        module.Module.__init__(self, params, query='SELECT DISTINCT hash FROM creds WHERE hash IS NOT NULL and password IS NULL')
        self.info = {
                     'Name': 'Hashes.org Hash Lookup',
                     'Author': 'Tim Tomes (@LaNMaSteR53) and Mike Lisi (@MikeCodesThings)',
                     'Description': 'Uses the Hashes.org API to perform a reverse hash lookup. Updates the \'creds\' table with the positive results.',
                     'Comments': [
                                  'Hash types supported: MD5, MD4, NTLM, LM, DOUBLEMD5, TRIPLEMD5, MD5SHA1, SHA1, MYSQL5, SHA1MD5, DOUBLESHA1, RIPEMD160'
                                  ]
                     }

    def module_run(self, hashes):
        url = 'https://hashes.org/api.php'
        first = True
        for hashstr in hashes:
            # rate limit requests
            if first:
                first = False
            else:
                # 20 hashes per minute
                time.sleep(3)
            # build the payload
            payload = {'do': 'check', 'hash1': hashstr}
            resp = self.request(url, payload=payload)
            tree = resp.xml
            # check for and report error conditions
            # None condition check required as tree elements with no children return False
            if tree.find('error') is not None:
                error = tree.find('error').text
                # continue processing valid hashes
                if 'invalid' in error:
                    self.verbose('Unsupported type for hash: %s' % (hashstr))
                    continue
                # any other error results in termination
                else:
                    self.error(error)
                    return
            # process the response
            request = tree
            hashstr = request.find('hash').text
            if request.find('found').text == 'true':
                plaintext = request.find('plain').text
                if hashstr != plaintext:
                    hashtype = request.find('type').text
                    self.alert('%s (%s) => %s' % (hashstr, hashtype, plaintext))
                    self.query('UPDATE creds SET password=\'%s\', type=\'%s\' WHERE hash=\'%s\'' % (plaintext, hashtype, hashstr))
            else:
                self.verbose('Value not found for hash: %s' % (hashstr))
