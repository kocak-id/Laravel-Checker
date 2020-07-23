import cmd
import sqlite3
import re
import os
import sys
import textwrap
import socket
import datetime
import subprocess
import __builtin__
# prep python path for supporting modules
sys.path.append('./libs/')
#import requests
import urllib
import urllib2
import cookielib
import json

class module(cmd.Cmd):
    def __init__(self, params):
        cmd.Cmd.__init__(self)
        self.prompt = (params[0])
        self.modulename = params[1]
        self.ruler = '-'
        self.spacer = '  '
        self.module_delimiter = '/' # match line ~257 recon-ng.py
        self.nohelp = '%s[!] No help on %%s%s' % (R, N)
        self.do_help.__func__.__doc__ = '''Displays this menu'''
        self.doc_header = 'Commands (type [help|?] <topic>):'
        self.goptions = __builtin__.goptions
        self.workspace = __builtin__.workspace
        self.options = {}

    #==================================================
    # CMD OVERRIDE METHODS
    #==================================================

    def default(self, line):
        self.do_shell(line)

    def emptyline(self):
        # disables running of last command when no command is given
        # return flag to tell interpreter to continue
        return 0

    def precmd(self, line):
        if __builtin__.script:
            sys.stdout.write('%s\n' % (line))
        if __builtin__.record:
            recorder = open(self.goptions['rec_file']['value'], 'ab')
            recorder.write('%s\n' % (line))
            recorder.flush()
            recorder.close()
        return line

    def onecmd(self, line):
        cmd, arg, line = self.parseline(line)
        if not line:
            return self.emptyline()
        if line == 'EOF':
            # reset stdin for raw_input
            sys.stdin = sys.__stdin__
            __builtin__.script = 0
            return 0
        if cmd is None:
            return self.default(line)
        self.lastcmd = line
        if cmd == '':
            return self.default(line)
        else:
            try:
                func = getattr(self, 'do_' + cmd)
            except AttributeError:
                return self.default(line)
            return func(arg)

    # make help menu more attractive
    def print_topics(self, header, cmds, cmdlen, maxcol):
        if cmds:
            self.stdout.write("%s\n"%str(header))
            if self.ruler:
                self.stdout.write("%s\n"%str(self.ruler * len(header)))
            for cmd in cmds:
                self.stdout.write("%s %s\n" % (cmd.ljust(15), getattr(self, 'do_' + cmd).__doc__))
            self.stdout.write("\n")

    #==================================================
    # SUPPORT METHODS
    #==================================================

    def boolify(self, s):
        return {'true': True, 'false': False}[s.lower()]

    def autoconvert(self, s):
        if s.lower() in ['none', "''", '""']:
            return None
        for fn in (self.boolify, int, float):
            try: return fn(s)
            except ValueError: pass
            except KeyError: pass
        return s

    def display_modules(self, modules):
        key_len = len(max(modules, key=len)) + len(self.spacer)
        last_category = ''
        for module in sorted(modules):
            category = module.split(self.module_delimiter)[0]
            if category != last_category:
                # print header
                print ''
                last_category = category
                print '%s%s:' % (self.spacer, last_category.title())
                print '%s%s' % (self.spacer, self.ruler*key_len)
            # print module
            print '%s%s' % (self.spacer*2, module)
        print ''

    def display_workspaces(self):
        dirnames = []
        for name in os.listdir('./workspaces'):
            if os.path.isdir('./workspaces/%s' % (name)):
                if name == self.goptions['workspace']['value']:
                    name += '*'
                dirnames.append([name])
        dirnames.insert(0, ['Workspaces'])
        self.table(dirnames, header=True)
        self.output('\'*\' denotes the active workspace.')

    def display_dashboard(self):
        # display activity table
        self.heading('Activity Summary')
        rows = self.query('SELECT * FROM dashboard')
        tdata = [['Module', 'Runs']]
        for row in rows:
            tdata.append(row)
        if rows:
            self.table(tdata, header=True)
        else:
            print '\n%sThis workspace has no record of activity.' % (self.spacer)
        # display sumary results table
        self.heading('Results Summary')
        tables = [x[0] for x in self.query('SELECT name FROM sqlite_master WHERE type=\'table\'')]
        tdata = [['Category', 'Quantity']]
        for table in tables:
            if not table in ['leaks', 'dashboard']:
                count = self.query('SELECT COUNT(*) FROM %s' % (table))[0][0]
                tdata.append([table.title(), count])
        self.table(tdata, header=True)

    def sanitize(self, obj, encoding='utf-8'):
        # checks if obj is unicode and converts if not
        if isinstance(obj, basestring):
            if not isinstance(obj, unicode):
                obj = unicode(obj, encoding)
        return obj

    def unescape(self, s):
        '''Unescapes HTML markup and returns an unescaped string.'''
        import htmllib
        p = htmllib.HTMLParser(None)
        p.save_bgn()
        p.feed(s)
        return p.save_end()

    def is_hash(self, hashstr):
        hashdict = [
            {"pattern": "[a-fA-F0-9]", "len": 16},
            {"pattern": "[a-fA-F0-9]", "len": 32},
            {"pattern": "[a-fA-F0-9]", "len": 40},
            {"pattern": "^\*[a-fA-F0-9]", "len": 41},
            {"pattern": "[a-fA-F0-9]", "len": 56},
            {"pattern": "[a-fA-F0-9]", "len": 64},
            {"pattern": "[a-fA-F0-9]", "len": 96},
            {"pattern": "[a-fA-F0-9]", "len": 128}
        ]
        for hashitem in hashdict:
            if len(hashstr) == hashitem["len"] and re.match(hashitem["pattern"], hashstr):
                return True
        return False

    #==================================================
    # OUTPUT METHODS
    #==================================================

    def error(self, line):
        '''Formats and presents errors.'''
        print '%s[!] %s%s' % (R, line, N)

    def output(self, line):
        '''Formats and presents normal output.'''
        print '%s[*]%s %s' % (B, N, line)

    def alert(self, line):
        '''Formats and presents important output.'''
        print '%s[*]%s %s' % (G, N, line)

    def verbose(self, line):
        '''Formats and presents output if in verbose mode.'''
        if self.goptions['verbose']['value']:
            self.output(line)

    def heading(self, line, level=1):
        '''Formats and presents styled banner text'''
        print ''
        if level == 0:
            print self.ruler*len(line)
            print line.upper()
            print self.ruler*len(line)
        if level == 1:
            print '%s%s' % (self.spacer, line.title())
            print '%s%s' % (self.spacer, self.ruler*len(line))

    def table(self, tdata, header=False, table=None):
        '''Accepts a list of rows and outputs a table.'''
        if len(set([len(x) for x in tdata])) > 1:
            self.error('Row lengths not consistent.')
            return
        lens = []
        cols = len(tdata[0])
        for i in range(0,cols):
            lens.append(len(max([unicode(x[i]) if x[i] != None else '' for x in tdata], key=len)))
        # build ascii table
        if len(tdata) > 0:
            separator_str = '%s+-%s%%s-+' % (self.spacer, '%s---'*(cols-1))
            separator_sub = tuple(['-'*x for x in lens])
            separator = separator_str % separator_sub
            data_str = '%s| %s%%s |' % (self.spacer, '%s | '*(cols-1))
            # top of ascii table
            print ''
            print separator
            if table: columns = None
            # ascii table data
            if header:
                rdata = tdata.pop(0)
                data_sub = tuple([rdata[i].center(lens[i]) for i in range(0,cols)])
                print data_str % data_sub
                print separator
                # build column names for database table out of header row
                if table: columns = [self.sanitize(x).lower() for x in rdata]
            for rdata in tdata:
                data_sub = tuple([unicode(rdata[i]).ljust(lens[i]) if rdata[i] != None else ''.ljust(lens[i]) for i in range(0,cols)])
                print data_str % data_sub
            # bottom of ascii table
            print separator
            print ''

            # build database table
            if table:
                # create database table
                if not columns: columns = ['column_%s' % (i) for i in range(0,len(tdata[0]))]
                metadata = ','.join(['\'%s\' TEXT' % (x) for x in columns])
                self.query('CREATE TABLE IF NOT EXISTS %s (%s)' % (table, metadata))
                # insert rows into database table
                for rdata in tdata:
                    data = {}
                    for i in range(0, len(columns)):
                        data[columns[i]] = rdata[i]
                    self.insert(table, data)
                self.output('\'%s\' table created in the database' % (table))

    #==================================================
    # DATABASE METHODS
    #==================================================

    def display_schema(self):
        '''Displays the database schema'''
        conn = sqlite3.connect('%s/data.db' % (self.workspace))
        cur = conn.cursor()
        cur.execute('SELECT name FROM sqlite_master WHERE type=\'table\'')
        tables = [x[0] for x in cur.fetchall()]
        for table in tables:
            cur.execute('PRAGMA table_info(%s)' % (table))
            columns = [(x[1],x[2]) for x in cur.fetchall()]
            name_len = len(max([x[0] for x in columns], key=len))
            type_len = len(max([x[1] for x in columns], key=len))
            print ''
            print '%s+%s+' % (self.spacer, self.ruler*(name_len+type_len+5))
            print '%s| %s |' % (self.spacer, table.center(name_len+type_len+3))
            print '%s+%s+' % (self.spacer, self.ruler*(name_len+type_len+5))
            for column in columns:
                print '%s| %s | %s |' % (self.spacer, column[0].ljust(name_len), column[1].center(type_len))
            print '%s+%s+' % (self.spacer, self.ruler*(name_len+type_len+5))
        print ''

    def add_host(self, host, ip_address=None, region=None, country=None, latitude=None, longitude=None):
        '''Adds a host to the database and returns the affected row count.'''
        data = dict(
            host = self.sanitize(host),
            ip_address = self.sanitize(ip_address),
            region = self.sanitize(region),
            country = self.sanitize(country),
            latitude = self.sanitize(latitude),
            longitude = self.sanitize(longitude),
        )

        return self.insert('hosts', data, ('host',))

    def add_contact(self, fname, lname, title, email=None, region=None, country=None):
        '''Adds a contact to the database and returns the affected row count.'''
        data = dict(
            fname = self.sanitize(fname),
            lname = self.sanitize(lname),
            title = self.sanitize(title),
            email = self.sanitize(email),
            region = self.sanitize(region),
            country = self.sanitize(country),
        )

        return self.insert('contacts', data, ('fname', 'lname', 'title'))

    def add_cred(self, username, password=None, hashtype=None, leak=None):
        '''Adds a credential to the database and returns the affected row count.'''
        data = {}
        data['username'] = self.sanitize(username)
        if password and not self.is_hash(password): data['password'] = self.sanitize(password)
        if password and self.is_hash(password): data['hash'] = self.sanitize(password)
        if hashtype: data['type'] = self.sanitize(hashtype)
        if leak: data['leak'] = self.sanitize(leak)

        return self.insert('creds', data, data.keys())

    def insert(self, table, data, unique_columns=[]):
        '''Inserts items into database and returns the affected row count.
        table - the table to insert the data into
        data - the information to insert into the database table in the form of a dictionary
               where the keys are the column names and the values are the column values
        unique_columns - a list of column names that should be used to determine if the.
                         information being inserted is unique'''

        columns = data.keys()

        if not unique_columns:
            query = u'INSERT INTO %s (%s) VALUES (%s)' % (
                table,
                ','.join(columns),
                ','.join('?'*len(columns))
            )
        else:
            query = u'INSERT INTO %s (%s) SELECT %s WHERE NOT EXISTS(SELECT * FROM %s WHERE %s)' % (
                table,
                ','.join(columns),
                ','.join('?'*len(columns)),
                table,
                ' and '.join([column + '=?' for column in unique_columns])
            )

        values = [data[column] for column in columns] + [data[column] for column in unique_columns]

        conn = sqlite3.connect('%s/data.db' % (self.workspace))
        cur = conn.cursor()
        try: cur.execute(query, values)
        except sqlite3.OperationalError as e:
            self.error('Invalid query. %s %s' % (type(e).__name__, e.message))
            return
        conn.commit()
        conn.close()
        return cur.rowcount

    def query(self, params, return_results=True):
        '''Queries the database and returns the results as a list.'''
        # based on the do_ouput method
        if not params:
            self.help_query()
            return
        conn = sqlite3.connect('%s/data.db' % (self.workspace))
        cur = conn.cursor()
        try: cur.execute(params)
        except sqlite3.OperationalError as e:
            self.error('Invalid query. %s %s' % (type(e).__name__, e.message))
            return False
        if not return_results:
            if cur.rowcount == -1 and cur.description:
                header = tuple([x[0] for x in cur.description])
                tdata = cur.fetchall()
                if not tdata:
                    self.output('No data returned.')
                else:
                    tdata.insert(0, header)
                    self.table(tdata, True)
                    self.output('%d rows returned' % (len(tdata)))
            else:
                conn.commit()
                self.output('%d rows affected.' % (cur.rowcount))
            conn.close()
            return
        else:
            # a rowcount of -1 typically refers to a select statement
            if cur.rowcount == -1:
                rows = cur.fetchall()
                result = rows
            # a rowcount of 1 == success and 0 == failure
            else:
                conn.commit()
                result = cur.rowcount
            conn.close()
            return result

    #==================================================
    # OPTIONS METHODS
    #==================================================

    def display_options(self, params):
        '''Lists options'''
        spacer = self.spacer
        if params == 'info':
            spacer = self.spacer*2
        if self.options:
            pattern = '%s%%s  %%s  %%s  %%s' % (spacer)
            key_len = len(max(self.options, key=len))
            val_len = len(max([str(self.options[x]['value']) for x in self.options], key=len))
            if val_len < 13: val_len = 13
            print ''
            print pattern % ('Name'.ljust(key_len), 'Current Value'.ljust(val_len), 'Req', 'Description')
            print pattern % (self.ruler*key_len, (self.ruler*13).ljust(val_len), self.ruler*3, self.ruler*11)
            for key in sorted(self.options):
                value = self.options[key]['value'] if self.options[key]['value'] != None else ''
                reqd = self.options[key]['reqd']
                desc = self.options[key]['desc']
                print pattern % (key.upper().ljust(key_len), str(value).ljust(val_len), reqd.ljust(3), desc)
            print ''
        else:
            if params != 'info': print ''
            print '%sNo options available for this module.' % (spacer)
            print ''

    def register_option(self, name, value, reqd, desc, options=None):
        # can't use not because empty dictonary would eval as true
        if options == None: options = self.options
        options[name.lower()] = {'value':value, 'reqd':reqd, 'desc':desc}

    def validate_options(self):
        for option in self.options:
            # if value type is bool or int, then we know the options is set
            if not type(self.options[option]['value']) in [bool, int]:
                if self.options[option]['reqd'].lower() == 'yes' and not self.options[option]['value']:
                    self.error('Value required for the \'%s\' option.' % (option))
                    return False
        return True

    def get_source(self, params, query=None):
        source = params.split()[0].lower()
        if source == 'query':
            query = ' '.join(params.split()[1:])
            results = self.query(query, True)
            if not results:
                self.error('No items found.')
                sources = []
            elif len(results[0]) > 1:
                self.error('Too many columns of data returned.')
                source = []
            else: sources = [x[0] for x in results]
        elif source == 'db' and query:
            rows = self.query(query)
            if not rows:
                self.error('No items found.')
                sources = []
            else: sources = [x[0] for x in rows]
        elif os.path.exists(source):
            sources = open(source).read().split()
        else:
            sources = [source]
        return sources

    #==================================================
    # API KEY METHODS
    #==================================================

    def display_keys(self):
        conn = sqlite3.connect(self.goptions['key_file']['value'])
        cur = conn.cursor()
        cur.execute('SELECT * FROM keys')
        rows = cur.fetchall()
        conn.close()
        tdata = [('Name', 'Value')]
        for row in rows:
            tdata.append((row[0], row[1]))
        self.table(tdata, True)

    def manage_key(self, key_name, key_text):
        '''Automates the API key retrieval and storage process.'''
        key = self.get_key_from_db(key_name)
        if not key:
            key = self.get_key_from_user(key_text)
            if not key:
                self.error('No %s.' % (key_text))
                return False
            if self.add_key_to_db(key_name, key):
                self.output('%s added.' % (key_text))
            else:
                self.output('Error adding %s.' % (key_text))
        return key

    def get_key_from_db(self, key_name):
        '''Retrieves an API key from the API key storage database.'''
        conn = sqlite3.connect(self.goptions['key_file']['value'])
        cur = conn.cursor()
        cur.execute('SELECT value FROM keys WHERE name=?', (key_name,))
        row = cur.fetchone()
        conn.close()
        if row:
            return str(row[0])
        else:
            return False

    def get_key_from_user(self, key_text='API Key'):
        '''Retrieves an API key from the user.'''
        try:
            key = raw_input("Enter %s (blank to skip): " % (key_text))
            return str(key)
        except KeyboardInterrupt:
            print ''
            return False

    def add_key_to_db(self, key_name, key_value):
        '''Adds an API key to the API key storage database.'''
        conn = sqlite3.connect(self.goptions['key_file']['value'])
        cur = conn.cursor()
        try: cur.execute('INSERT INTO keys VALUES (?,?)', (key_name, key_value))
        except sqlite3.OperationalError:
            return False
        except sqlite3.IntegrityError:
            try: cur.execute('UPDATE keys SET value=? WHERE name=?', (key_value, key_name))
            except sqlite3.OperationalError:
                return False
        conn.commit()
        conn.close()
        return True

    #==================================================
    # REQUEST METHODS
    #==================================================

    def search_bing_api(self, query, limit=0):
        api_key = self.manage_key('bing', 'Bing API key')
        if not api_key: return
        url = 'https://api.datamarket.azure.com/Data.ashx/Bing/Search/v1/Web'
        payload = {'Query': query, '$format': 'json'}
        results = []
        cnt = 1
        self.verbose('Searching Bing for: %s' % (query))
        while True:
            resp = None
            resp = self.request(url, payload=payload, auth=(api_key, api_key))
            sys.stdout.write('.'); sys.stdout.flush()
            if resp.json == None:
                self.error('Invalid JSON response.\n%s' % (resp.text))
                continue
            # add new results
            if 'results' in resp.json['d']:
                results.extend(resp.json['d']['results'])
            # check limit
            if limit == cnt:
                break
            cnt += 1
            # check if more pages
            if '__next' in resp.json['d']:
                payload['$skip'] = resp.json['d']['__next'].split('=')[-1]
            else:
                break
        print ''
        return results

    def search_google_api(self, query, limit=0):
        api_key = self.manage_key('google_api', 'Google API key')
        if not api_key: return
        cse_id = self.manage_key('google_cse', 'Google CSE ID')
        if not cse_id: return
        url = 'https://www.googleapis.com/customsearch/v1'
        payload = {'alt': 'json', 'prettyPrint': 'false', 'key': api_key, 'cx': cse_id, 'q': query}
        results = []
        cnt = 1
        self.verbose('Searching Google for: %s' % (query))
        while True:
            resp = None
            resp = self.request(url, payload=payload)
            sys.stdout.write('.'); sys.stdout.flush()
            if resp.json == None:
                self.error('Invalid JSON response.\n%s' % (resp.text))
                continue
            # add new results
            if 'items' in resp.json:
                results.extend(resp.json['items'])
            # check limit
            if limit == cnt:
                break
            cnt += 1
            # check if more pages
            if 'nextPage' in resp.json['queries']:
                payload['start'] = resp.json['queries']['nextPage'][0]['startIndex']
            else:
                break
        print ''
        return results

    def request(self, url, method='GET', timeout=None, payload={}, headers={}, cookies={}, auth=(), redirect=True):
        '''Makes a web request and returns a response object.'''
        # set request arguments
        # process user-agent header
        headers['User-Agent'] = self.goptions['user-agent']['value']
        # process payload
        payload = urllib.urlencode(payload)
        # process cookies
        if len(cookies.keys()) > 0:
            cookie_value = '; '.join('%s=%s' % (key, cookies[key]) for key in cookies.keys())
            headers['Cookie'] = cookie_value
        # process basic authentication
        if len(auth) == 2:
            authorization = ('%s:%s' % (auth[0], auth[1])).encode('base64').replace('\n', '')
            headers['Authorization'] = 'Basic %s' % (authorization)
        # process socket timeout
        timeout = timeout or self.goptions['socket_timeout']['value']
        socket.setdefaulttimeout(timeout)
        
        # set handlers
        handlers = [] #urllib2.HTTPHandler(debuglevel=1)
        # process redirect and add handler
        if redirect == False:
            handlers.append(NoRedirectHandler)
        # process proxies and add handler
        if self.goptions['proxy']['value']:
            proxies = {'http': self.goptions['proxy_server']['value'], 'https': self.goptions['proxy_server']['value']}
            handlers.append(urllib2.ProxyHandler(proxies))
        # create cookie jar
        cj = cookielib.CookieJar()
        handlers.append(urllib2.HTTPCookieProcessor(cj))

        # install opener
        opener = urllib2.build_opener(*handlers)
        urllib2.install_opener(opener)
        
        # process method and make request
        if method == 'GET':
            if payload: url = '%s?%s' % (url, payload)
            req = urllib2.Request(url, headers=headers)
        elif method == 'POST':
            req = urllib2.Request(url, data=payload, headers=headers)
        elif method == 'HEAD':
            if payload: url = '%s?%s' % (url, payload)
            req = urllib2.Request(url, headers=headers)
            req.get_method = lambda : 'HEAD'
        else:
            raise Exception('Request method \'%s\' is not a supported method.' % (method))
        try:
            resp = urllib2.urlopen(req)
        except urllib2.HTTPError as e:
            resp = e

        # build and return response object
        return ResponseObject(resp, cj)

    #==================================================
    # COMMAND METHODS
    #==================================================

    def do_exit(self, params):
        '''Exits current prompt level'''
        return True

    # alias for exit
    def do_back(self, params):
        '''Exits current prompt level'''
        return True

    def do_info(self, params):
        '''Displays module information'''
        pattern = '%s%s:'
        for item in ['Name', 'Author', 'Description']:
            print ''
            print pattern % (self.spacer, item)
            print pattern[:-1] % (self.spacer*2, textwrap.fill(self.info[item], 100, initial_indent='', subsequent_indent=self.spacer*2))
        print ''
        print pattern % (self.spacer, 'Options')
        self.display_options('info')
        if self.info['Comments']:
            print pattern % (self.spacer, 'Comments')
            for comment in self.info['Comments']:
                print pattern[:-1] % (self.spacer*2, textwrap.fill(comment, 100, initial_indent='', subsequent_indent=self.spacer*2))
            print ''

    def do_set(self, params):
        '''Sets module options'''
        options = params.split()
        if len(options) < 2: self.help_set()
        else:
            name = options[0].lower()
            if name in self.options:
                value = ' '.join(options[1:])
                print '%s => %s' % (name.upper(), value)
                self.options[name]['value'] = self.autoconvert(value)
            else: self.error('Invalid option.')

    def do_query(self, params):
        '''Queries the database'''
        self.query(params, False)

    def do_show(self, params):
        '''Shows various framework items'''
        if params:
            arg = params.lower()
            if arg.split()[0] == 'modules':
                if len(arg.split()) > 1:
                    param = arg.split()[1]
                    modules = [x for x in __builtin__.loaded_modules if x.startswith(param)]
                    if not modules:
                        self.error('Invalid module category.')
                        return
                else:
                    modules = __builtin__.loaded_modules
                self.display_modules(modules)
                return
            elif arg == 'options':
                self.display_options(None)
                return
            elif arg == 'workspaces':
                self.display_workspaces()
                return
            elif arg == 'schema':
                self.display_schema()
                return
            elif arg == 'keys':
                self.display_keys()
                return
            elif arg == 'dashboard':
                self.display_dashboard()
                return
            elif arg in [x[0] for x in self.query('SELECT name FROM sqlite_master WHERE type=\'table\'')]:
                self.query('SELECT * FROM %s ORDER BY 1' % (arg), False)
                return
        self.help_show()

    def do_search(self, params):
        '''Searches available modules'''
        if not params:
            self.help_search()
            return
        text = params.split()[0]
        self.output('Searching for \'%s\'...' % (text))
        modules = [x for x in __builtin__.loaded_modules if text in x]
        if not modules:
            self.error('No modules found containing \'%s\'.' % (text))
        else:
            self.display_modules(modules)

    def do_record(self, params):
        '''Records commands to a resource file'''
        arg = params.lower()
        rec_file = self.goptions['rec_file']['value']
        if arg == 'start':
            if __builtin__.record == 0:
                __builtin__.record = 1
                self.output('Recording commands to \'%s\'' % (rec_file))
            else: self.output('Recording is already started.')
        elif arg == 'stop':
            if __builtin__.record == 1:
                __builtin__.record = 0
                self.output('Recording stopped. Commands saved to \'%s\'' % (rec_file))
            else: self.output('Recording is already stopped.')
        elif arg == 'status':
            status = 'started' if __builtin__.record == 1 else 'stopped'
            self.output('Command recording is %s.' % (status))
        else:
            self.help_record()

    def do_shell(self, params):
        '''Executed shell commands'''
        proc = subprocess.Popen(params, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
        self.output('Command: %s' % (params))
        stdout = proc.stdout.read()
        stderr = proc.stderr.read()
        if stdout: sys.stdout.write('%s%s%s' % (O, stdout, N))
        if stderr: sys.stdout.write('%s%s%s' % (R, stderr, N))

    def do_run(self, params):
        '''Runs the module'''
        if not self.validate_options(): return
        self.module_run()
        self.query('INSERT OR REPLACE INTO dashboard (module, runs) VALUES (\'%(x)s\', COALESCE((SELECT runs FROM dashboard WHERE module=\'%(x)s\')+1, 1))' % {'x': self.modulename})

    def module_run(self):
        pass

    def do_resource(self, params):
        '''Executes commands from a resource file'''
        if params:
            if os.path.exists(params):
                sys.stdin = open(params)
                __builtin__.script = 1
                return
            else:
                self.error('Script file not found.')
                return
        self.help_resource()        

    #==================================================
    # HELP METHODS
    #==================================================

    def help_set(self):
        print 'Usage: set <option> <value>'
        self.display_options(None)

    def help_query(self):
        print 'Usage: query <sql>'
        print ''
        print 'SQL Examples:'
        print '%s%s' % (self.spacer, 'SELECT columns|* FROM table_name')
        print '%s%s' % (self.spacer, 'SELECT columns|* FROM table_name WHERE some_column=some_value')
        print '%s%s' % (self.spacer, 'DELETE FROM table_name WHERE some_column=some_value')
        print '%s%s' % (self.spacer, 'INSERT INTO table_name (column1, column2,...) VALUES (value1, value2,...)')
        print '%s%s' % (self.spacer, 'UPDATE table_name SET column1=value1, column2=value2,... WHERE some_column=some_value')

    def help_show(self):
        print 'Usage: show [modules|options|workspaces|schema|keys|<table>]'

    def help_shell(self):
        print 'Usage: [shell|!] <command>'
        print '...or just type a command at the prompt.'

    def help_record(self):
        print 'Usage: record [start|stop|status]'

    def help_resource(self):
        print 'Usage: resource <filename>'

    #==================================================
    # COMPLETE METHODS
    #==================================================

    def complete_set(self, text, *ignored):
        return [x for x in self.options if x.startswith(text)]

    def complete_show(self, text, line, *ignored):
        args = line.split()
        if len(args) > 1 and args[1].lower() == 'modules':
            if len(args) > 2: return [x for x in __builtin__.loaded_modules if x.startswith(args[2])]
            else: return [x for x in __builtin__.loaded_modules]
        tables = [x[0] for x in self.query('SELECT name FROM sqlite_master WHERE type=\'table\'')]
        options = ['modules', 'options', 'workspaces', 'schema', 'keys']
        options.extend(tables)
        return [x for x in options if x.startswith(text)]

#=================================================
# CUSTOM CLASSES & WRAPPERS
#=================================================

class NoRedirectHandler(urllib2.HTTPRedirectHandler):

    def http_error_302(self, req, fp, code, msg, headers):
        pass

    http_error_301 = http_error_303 = http_error_307 = http_error_302

class ResponseObject(object):

    def __init__(self, resp, cj):
        # set hidden text property
        self.__text__ = resp.read()
        # set inherited properties
        self.url = resp.geturl()
        self.status_code = resp.getcode()
        self.headers = resp.headers.dict
        # detect and set encoding property
        self.encoding = resp.headers.getparam('charset')
        self.cookies = cj

    @property
    def text(self):
        if self.encoding:
            return self.__text__.decode(self.encoding)
        else:
            return self.__text__

    @property
    def json(self):
        try:
            return json.loads(self.text)
        except ValueError:
            return None
