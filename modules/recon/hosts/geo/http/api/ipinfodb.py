import module
# unique to module
import json

class Module(module.Module):

    def __init__(self, params):
        module.Module.__init__(self, params, query='SELECT DISTINCT ip_address FROM hosts WHERE ip_address IS NOT NULL ORDER BY ip_address')
        self.info = {
                     'Name': 'IPInfoDB GeoIP',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Leverages the ipinfodb.com API to geolocate a host by IP address. Updates the \'hosts\' table with the results.'
                     }
   
    def module_run(self, hosts):
        api_key = self.get_key('ipinfodb_api')
        for host in hosts:
            url = 'http://api.ipinfodb.com/v3/ip-city/?key=%s&ip=%s&format=json' % (api_key, host)
            resp = self.request(url)
            if resp.json:
                jsonobj = resp.json
            else:
                self.error('Invalid JSON response for \'%s\'.\n%s' % (host, resp.text))
                continue
            if jsonobj['statusCode'].lower() == 'error':
                self.error(jsonobj['statusMessage'])
                continue
            location = []
            for name in ['cityName', 'regionName']:
                if jsonobj[name]:
                    location.append(str(jsonobj[name]).title())
            data = [', '.join(location)]
            data.append(jsonobj['countryName'].title())
            data.append(str(jsonobj['latitude']))
            data.append(str(jsonobj['longitude']))
            data.append(host)
            self.output('%s - %s,%s - %s, %s' % (data[4], data[2], data[3], data[0], data[1]))
            # only store results if input came from the database
            if self.options['source'] == 'default':
                self.query('UPDATE hosts SET region=?, country=?, latitude=?, longitude=? WHERE ip_address=?', tuple(data))
