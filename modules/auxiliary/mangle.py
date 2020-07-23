import _cmd
import __builtin__
# unique to module
import sqlite3
import socket

class Module(_cmd.base_cmd):

    def __init__(self, params):
        _cmd.base_cmd.__init__(self, params)
        self.options = {
                        'domain': self.goptions['domain'],
                        'pattern': '<fn>.<ln>'
                        }

    def do_info(self, params):
        print ''
        print 'Info:'
        print '====='
        print 'Applies a mangle pattern to all of the contacts stored in the database, creating email addresses for each harvested contact.'
        print ''
        print 'Pattern options: <fi>,<fn>,<li>,<ln>'
        print 'Example:         <fi>.<ln> => j.doe@domain.com'
        print ''

    def do_run(self, params):
        self.mutate_contacts()

    def mutate_contacts(self):
        conn = sqlite3.connect(self.goptions['dbfilename'])
        c = conn.cursor()
        contacts = c.execute('SELECT rowid, fname, lname FROM contacts ORDER BY fname').fetchall()
        for contact in contacts:
            row = contact[0]
            fname = contact[1]
            lname = contact[2]
            fn = fname.lower()
            fi = fname[:1].lower()
            ln = lname.lower()
            li = lname[:1].lower()
            try:
                email = '%s@%s' % (self.options['pattern'], self.options['domain'])
                email = email.replace('<fn>', fn)
                email = email.replace('<fi>', fi)
                email = email.replace('<ln>', ln)
                email = email.replace('<li>', li)
            except:
                self.error('Invalid Mutation Pattern \'%s\'.' % (type))
                break
            print '[Mutation] %s %s => %s' % (fname, lname, email)
            c.execute('UPDATE contacts SET email=? WHERE rowid=?', (email, row))
        conn.commit()
        conn.close()