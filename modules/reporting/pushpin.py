import framework
# unique to module
import re
import webbrowser
import time
import codecs

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('map_filename', '%s/pushpin_map.html' % (self.workspace), 'yes', 'path and filename for pushpin map report')
        self.register_option('media_filename', '%s/pushpin_media.html' % (self.workspace), 'yes', 'path and filename for pushpin media report')
        self.register_option('latitude', self.goptions['latitude']['value'], 'yes', 'latitude of the epicenter')
        self.register_option('longitude', self.goptions['longitude']['value'], 'yes', 'longitude of the epicenter')
        self.register_option('radius', self.goptions['radius']['value'], 'yes', 'radius from the epicenter in kilometers')
        self.info = {
                     'Name': 'PushPin Report Generator',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Creates a media and map HTML report for all of the PushPin data stored in the database.',
                     'Comments': []
                     }

    def build_content(self, sources):
        icons = {
                 'flickr': 'http://maps.google.com/mapfiles/ms/icons/orange-dot.png',
                 'picasa': 'http://maps.google.com/mapfiles/ms/icons/purple-dot.png',
                 'shodan': 'http://maps.google.com/mapfiles/ms/icons/yellow-dot.png',
                 'twitter': 'http://maps.google.com/mapfiles/ms/icons/blue-dot.png',
                 'youtube': 'http://maps.google.com/mapfiles/ms/icons/red-dot.png',
                 }
        media_content = ''
        map_content = ''
        for source in sources:
            count = source[0]
            source = source[1]
            media_content += '<div class="media_column %s">\n<div class="media_header"><div class="media_summary">%s</div>%s</div>\n' % (source.lower(), count, source.capitalize())
            items = self.query('SELECT * FROM pushpin WHERE source=?', (source,))
            items.sort(key=lambda x: x[9], reverse=True)
            for item in items:
                item = [self.to_unicode_str(x) if x != None else u'' for x in item]
                media_content += '<div class="media_row"><div class="prof_cell"><a href="%s" target="_blank"><img class="prof_img" src="%s" /></a></div><div class="data_cell"><div class="trigger" id="trigger" lat="%s" lon="%s">[<a href="%s" target="_blank">%s</a>] %s<br /><span class="time">%s</span></div></div></div>\n' % (item[4], item[5], item[7], item[8], item[3], item[2], re.sub('[\r\n]+', '<br />', self.html_escape(item[6])), item[9])
                map_details = "<table><tr><td class='prof_cell'><a href='%s' target='_blank'><img class='prof_img' src='%s' /></a></td><td class='data_cell'>[<a href='%s' target='_blank'>%s</a>] %s<br /><span class='time'>%s</span></td></tr></table>" % (item[4], item[5], item[3], item[2], re.sub('[\r\n]+', '<br />', self.html_escape(item[6])), item[9])
                map_content += '\t\tadd_marker({position: new google.maps.LatLng(%s,%s),title:"%s",icon:"%s",map:map},{details:"%s"});\n' % (item[7], item[8], item[2], icons[source.lower()], map_details)
            media_content += '</div>\n'
        return media_content, map_content

    def write_markup(self, template, filename, content):
        temp_content = open(template).read()
        page = temp_content % (self.options['latitude']['value'], self.options['longitude']['value'], self.options['radius']['value'], content)
        file = codecs.open(filename, 'w', 'utf-8')
        file.write(page)
        file.close()

    def module_run(self):
        sources = self.query('SELECT COUNT(source), source FROM pushpin GROUP BY source')
        media_content, map_content = self.build_content(sources)
        self.write_markup('./data/template_media.html', self.options['media_filename']['value'], media_content)
        self.output('Media data written to \'%s\'' % (self.options['media_filename']['value']))
        self.write_markup('./data/template_map.html', self.options['map_filename']['value'], map_content)
        self.output('Mapping data written to \'%s\'' % (self.options['map_filename']['value']))

        w = webbrowser.get()
        w.open(self.options['media_filename']['value'])
        time.sleep(2)
        w.open(self.options['map_filename']['value'])
