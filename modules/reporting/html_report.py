import framework
# unique to module

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('filename', '%s/results.html' % (self.workspace), 'yes', 'path and filename for report output')
        self.register_option('sanitize', True, 'yes', 'mask sensitive data in the report')
        self.register_option('company', self.goptions['company']['value'], 'yes', 'name for report header')
        self.info = {
                     'Name': 'HTML Report Generator',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Creates a HTML report.',
                     'Comments': []
                     }

    def sanitize_html(self, htmlstring):
        # escape HTML with entities
        escapes = {'"': '&quot;',
                   "'": '&#39;',
                   '<': '&lt;',
                   '>': '&gt;'}
        #for seq, esc in escapes.iteritems():
        #    htmlstring = htmlstring.replace(seq, esc)
        htmlstring = ''.join([char for char in htmlstring if ord(char) >= 32 and ord(char) <= 126])
        return htmlstring

    def build_tables(self, tables):
        table_content = ''
        for table in tables:
            columns = [x[1] for x in self.query('PRAGMA table_info(%s)' % (table))]
            row_headers = '<tr><th>%s</th></tr>' % ('</th><th>'.join(columns))
            rows = self.query('SELECT %s FROM %s ORDER BY 1' % (', '.join(columns), table))
            if not rows: continue
            row_content = ''
            for row in rows:
                values = [unicode(x) if x != None else u'' for x in row]
                if table == 'creds' and self.options['sanitize']['value']:
                    values[1] = '%s%s%s' % (values[1][:1], '*'*(len(values[1])-2), values[1][-1:])
                row_content += '<tr><td>%s</td></tr>' % ('</td><td>'.join(values))
            table_content += '<div class="table_container"><table><caption>%s</caption>%s%s</table></div>' % (table.upper().replace('_', ' '), row_headers, row_content)
        return table_content

    def module_run(self):
        filename = self.options['filename']['value']
        try:
            outfile = open(filename, 'wb')
        except:
            self.error('Invalid path or filename.')
            return

        # template
        template = """
<!DOCTYPE HTML>
<html>
<head>
<title>Recon-ng Reconnaissance Report</title>
<style>
body {
    font-family: Arial, Helvetica, sans-serif;
    font-size: .75em;
    color: black;
    background-color: white;
    text-align: center;
}
.main {
    display: inline-block;
    margin-left: auto;
    margin-right: auto;
    width: 100%%;
}
.title {
    font-size: 3em;
}
.subtitle {
    font-size: 2em;
}
caption {
    font-weight: bold;
    font-size: 1.25em;
}
table {
    margin-left: auto; 
    margin-right: auto;
    white-space: nowrap;
}
td, th {
    padding: 2px 20px;
    border-style: solid;
    border-width: 1px;
    color: black;
    background-color: white;
}
td {
    text-align: left;
}
.table_container {
    margin: 10px 0;
}
.leaks {
    width: 1200px;
    white-space: normal;
}
.spacer {
    height: 1em;
    border: 0px;
    background-color: transparent;
}
</style>
</head>
<body>
    <div class="main">
        <div class='title'>%s</div>
        <div class='subtitle'>Recon-ng Reconnaissance Report</div>
        <div>
            %s
        </div>
    </div>
</body>
</html>"""

        # dashboard table
        table_content = self.build_tables(['dashboard'])

        # summary results table
        tables = [x[0] for x in self.query('SELECT name FROM sqlite_master WHERE type=\'table\'') if x[0] not in ['leaks', 'dashboard']]
        row_headers = '<tr><th>table</th><th>count</th></tr>'
        row_content = ''
        for table in tables:
            count = self.query('SELECT COUNT(*) FROM %s' % (table))[0][0]
            row_content += '<tr><td>%s</td><td>%s</td></tr>' % (table, count)
        table_content += '<div class="table_container"><table><caption>SUMMARY</caption>%s%s</table></div>' % (row_headers, row_content)

        # main content tables
        tables = ['hosts', 'contacts', 'creds']
        table_content += self.build_tables(tables)

        # table of leaks associated with creds
        leaks = self.query('SELECT DISTINCT leak FROM creds WHERE leak IS NOT NULL')
        if leaks:
            columns = [x[1] for x in self.query('PRAGMA table_info(leaks)')]
            if columns:
                row_content = ''
                for leak in [x[0] for x in leaks]:
                    row = self.query('SELECT * FROM leaks WHERE leak_id = \'%s\'' % (leak))[0]
                    values = [x if x != None else '' for x in row]
                    for i in range(0,len(columns)):
                        row_content += '<tr><td><strong>%s</strong></td><td>%s</td></tr>' % (columns[i], values[i])
                    row_content += '<tr><td class="spacer"></td></tr>'
                table_content += '<div class="table_container"><table class="leaks"><caption>ASSOCIATED LEAK DATA</caption>%s</table></div>' % (row_content)
            else:
                self.output('Associate leak data omitted. Please run the \'leaks_dump\' module to populate the database and try again.')

        # all other tables
        tables.extend(['leaks', 'dashboard'])
        tables = [x[0] for x in self.query('SELECT name FROM sqlite_master WHERE type=\'table\'') if x[0] not in tables]
        table_content += self.build_tables(tables)

        markup = template % (self.options['company']['value'], table_content)
        outfile.write(self.sanitize_html(markup))
        outfile.close()
        self.output('Report generated at \'%s\'.' % (filename))
