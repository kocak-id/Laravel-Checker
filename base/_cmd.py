import cmd
import sqlite3
import os
import sys
import urllib2
import socket
import __builtin__

class base_cmd(cmd.Cmd):
    def __init__(self, params):
        cmd.Cmd.__init__(self)
        self.prompt = (params)
        self.nohelp = '%s[!] No help on %%s%s' % (R, N)
        self.do_help.__func__.__doc__ = """Displays this menu"""
        self.do_info.__func__.__doc__ = """Displays module info"""
        self.do_run.__func__.__doc__ = """Runs the module"""
        self.doc_header = 'Commands (type help <topic>):'
        self.goptions = __builtin__.goptions
        self.options = {}

    #==================================================
    # OVERRIDE METHODS
    #==================================================

    def default(self, line):
        print '%s[!] Unknown syntax: %s%s' % (R, line, N)

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

    def error(self, line):
        print '%s[!] %s%s' % (R, line, N)

    def boolify(self, s):
        return {'true': True, 'false': False}[s.lower()]
    
    def autoconvert(self, s):
        for fn in (self.boolify, int, float):
            try: return fn(s)
            except ValueError: pass
            except KeyError: pass
        return s

    def sanitize(self, obj, encoding='utf-8'):
        # checks if obj is unicode and converts if not
        if isinstance(obj, basestring):
            if not isinstance(obj, unicode):
                obj = unicode(obj, encoding)
        return obj

    def add_host(self, host, addr=''):
        host = self.sanitize(host)
        addr = self.sanitize(addr)
        conn = sqlite3.connect(self.goptions['dbfilename'])
        c = conn.cursor()
        hosts = [x[0] for x in c.execute('SELECT host from hosts ORDER BY host').fetchall()]
        if not host in hosts:
            c.execute('INSERT INTO hosts VALUES (?, ?)', (host, addr))
        conn.commit()
        conn.close()

    def add_contact(self, fname, lname, title, email='', status=''):
        fname = self.sanitize(fname)
        lname = self.sanitize(lname)
        title = self.sanitize(title)
        email = self.sanitize(email)
        status = self.sanitize(status)
        conn = sqlite3.connect(self.goptions['dbfilename'])
        c = conn.cursor()
        contacts = c.execute('SELECT fname, lname, title from contacts ORDER BY fname').fetchall()
        if not (fname, lname, title) in contacts:
            c.execute('INSERT INTO contacts VALUES (?, ?, ?, ?, ?)', (fname, lname, email, status, title))
        conn.commit()
        conn.close()

    def manage_key(self, key_name, key_text=''):
        key = self.get_key_from_file(key_name)
        if not key:
            key = self.get_key_from_user(key_text)
            if not key:
                self.error('No API Key.')
                return
            self.add_key_to_file(key_name, key)
        return key

    def get_key_from_file(self, key_name):
        if os.path.exists(self.goptions['keyfilename']):
            for line in open(self.goptions['keyfilename']):
                key, value = line.split('::')[0], line.split('::')[1]
                if key == key_name:
                    return value.strip()
        else:
            self.error('Invalid keyfile path or name.')
        return False

    def get_key_from_user(self, key_text='API Key'):
        try: key = raw_input("Enter %s (blank to skip): " % (key_text))
        except KeyboardInterrupt:
            sys.stdout.write('\n')
            key = False
        return key

    def add_key_to_file(self, key_name, key_value):
        keys = []
        if os.path.exists(self.goptions['keyfilename']):
            # remove the old key if duplicate
            for line in open(self.goptions['keyfilename']):
                key = line.split('::')[0]
                if key != key_name:
                    keys.append(line)
        keys = ''.join(keys)
        try:
            file = open(self.goptions['keyfilename'], 'w')
            file.write(keys)
            file.write('%s::%s\n' % (key_name, key_value))
            file.close()
            print '[*] \'%s\' key added to \'%s\'.' % (key_name, self.goptions['keyfilename'])
        except:
            self.error('Invalid keyfile path or name.')

    def unescape(self, s):
        import htmllib
        p = htmllib.HTMLParser(None)
        p.save_bgn()
        p.feed(s)
        return p.save_end()

    # currently only works for http connections, not https
    def web_req(self, req):
        if self.goptions['proxy']:
            opener = urllib2.build_opener(AvoidRedirectHandler, urllib2.ProxyHandler({'http': self.goptions['proxyhost']}))
            socket.setdefaulttimeout(8)
        else: opener = urllib2.build_opener(AvoidRedirectHandler)
        urllib2.install_opener(opener)
        return urllib2.urlopen(req)

    #==================================================
    # FRAMEWORK METHODS
    #==================================================

    def do_exit(self, params):
        """Exits the module"""
        return True

    def do_options(self, params):
        """Lists module options"""
        print ''
        print 'Options:'
        print '========'
        for key in sorted(self.options.keys()):
            value = self.options[key]
            print '%s %s %s' % (key.ljust(12), type(value).__name__.ljust(5), str(value))
        print ''

    def do_set(self, params):
        """Sets module options"""
        options = params.split()
        if len(options) < 2:
            self.help_set()
            self.do_options(None)
        else:
            name = options[0]
            if name in self.options.keys():
                value = ' '.join(options[1:])
                print '%s => %s' % (name, value)
                self.options[name] = self.autoconvert(value)
            else: self.error('Invalid option.')

    #==================================================
    # HELP METHODS
    #==================================================

    def help_set(self):
        print 'Usage: set <option> <value>'

class AvoidRedirectHandler(urllib2.HTTPRedirectHandler):
    def http_error_302(self, req, fp, code, msg, headers):
        pass
    http_error_301 = http_error_303 = http_error_307 = http_error_302