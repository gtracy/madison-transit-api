# CityParkingData represents the data model for the parking service
# and pre-populates fields where possible. The goal is to reduce dependence on the city and
# campus websites in an attempt to reduce api breakage due to html template
# changes or field format discrepancies (human data entry variability).
class ParkingData:
    def __init__(self):

        self.city_data = dict()
        self.city_data['availability_url'] = \
            'http://www.cityofmadison.com/parkingUtility/garagesLots/availability/'
        self.city_data['special_events_url'] = \
            'http://www.cityofmadison.com/parkingUtility/calendar/index.cfm'


        self.city_data['lots'] = [
            {
                'name': 'State Street Campus Garage',
                'operatedBy': 'city',
                'shortName': 'campus',  # minimum reliable unique string
                'address': {
                    'street': '430 N. Frances St',
                    'city': 'Madison',
                    'state': 'WI',
                    'postalCode': '53703'
                },
                'entrances': [
                    '400 N. Frances St',
                    '400 N. Lake St'
                ],
                'totalSpots': 243,
                'openSpots': None,
                'webUrl': 'http://www.cityofmadison.com/parkingUtility/garagesLots/facilities/stateStCampus.cfm',
                'specialEvents': []
            },
            {
                'name': 'Brayton Lot',
                'operatedBy': 'city',
                'shortName': 'brayton',  # minimum reliable unique string
                'address': {
                    'street': '1 South Butler St',
                    'city': 'Madison',
                    'state': 'WI',
                    'postalCode': '53703'
                },
                'entrances': [
                    {'street': '10 S. Butler St'}
                ],
                'totalSpots': 247,
                'openSpots': None,
                'webUrl': 'http://www.cityofmadison.com/parkingUtility/garagesLots/facilities/brayton.cfm',
                'specialEvents': []
            },
            {
                'name': 'Capitol Square North Garage',
                'operatedBy': 'city',
                'shortName': 'north',  # minimum reliable unique string
                'address': {
                    'street': '218 East Mifflin St',
                    'city': 'Madison',
                    'state': 'WI',
                    'postalCode': '53703'
                },
                'entrances': [
                    '100 N. Butler St', '200 E. Mifflin St', '100 N. Webster St'
                ],
                'totalSpots': 613,
                'openSpots': None,
                'webUrl': 'http://www.cityofmadison.com/parkingUtility/garagesLots/facilities/capSquareNorth.cfm',
                'specialEvents': []
            },
            {
                'name': 'Government East Garage',
                'operatedBy': 'city',
                'shortName': 'east',  # minimum reliable unique string
                'address': {
                    'street': '215 S. Pinckney St',
                    'city': 'Madison',
                    'state': 'WI',
                    'postalCode': '53703'
                },
                'entrances': [
                    '200 S. Pinckney St', '100 E. Wilson St'
                ],
                'totalSpots': 516,
                'openSpots': None,
                'webUrl': 'http://www.cityofmadison.com/parkingUtility/garagesLots/facilities/govtEast.cfm',
                'specialEvents': []
            },
            {
                'name': 'Overture Center Garage',
                'operatedBy': 'city',
                'shortName': 'overture',  # minimum reliable unique string
                'address': {
                    'street': '318 W. Mifflin St',
                    'city': 'Madison',
                    'state': 'WI',
                    'postalCode': '53703'
                },
                'entrances': [
                    '300 W. Dayton St', '300 W. Mifflin St'
                ],
                'totalSpots': 620,
                'openSpots': None,
                'webUrl': 'http://www.cityofmadison.com/parkingUtility/garagesLots/facilities/overture.cfm',
                'specialEvents': []
            },
            {
                'name': 'State Street Capitol Garage',
                'operatedBy': 'city',
                'shortName': 'state street capitol',  # minimum reliable unique string
                'address': {
                    'street': '214 N. Carroll St',
                    'city': 'Madison',
                    'state': 'WI',
                    'postalCode': '53703'
                },
                'entrances': [
                    '200 N. Carroll St', '100 W. Dayton St', '100 W. Johnson St '
                ],
                'totalSpots': 850,
                'openSpots': None,
                'webUrl': 'http://www.cityofmadison.com/parkingUtility/garagesLots/facilities/stateStCapitol.cfm',
                'specialEvents': []
            }
        ]

        self.campus_data = dict()
        self.campus_data['availability_url'] = \
            'http://transportation.wisc.edu/parking/lotinfo_occupancy.aspx'
        self.campus_data['special_events_url'] = \
            'http://transportation.wisc.edu/newsAndEvents/events.aspx'
        self.campus_data['lots'] = [
            {
               'shortName': '20',
               'name': 'University Avenue Ramp',
               'operatedBy': 'uw',
               'address': {
                 'street': '1390 University Avenue',
                 'city': 'Madison',
                 'state': 'WI',
                 'postalCode': '53706'
               },
               'entrances': [],
               'totalSpots': 220,
               'openSpots': None,
               'webUrl': 'https://fpm-www1.fpm.wisc.edu/smomap/lot.aspx?lot=20',
               'specialEvents': []
            },
            {
               'shortName': '27',
               'name': 'Nancy Nicholas Hall Garage',
               'operatedBy': 'uw',
               'address': {
                 'street': '1330 Linden Drive',
                 'city': 'Madison',
                 'state': 'WI',
                 'postalCode': '53706'
               },
               'entrances': [],
               'totalSpots': 48,
               'openSpots': None,
               'webUrl': 'https://fpm-www1.fpm.wisc.edu/smomap/lot.aspx?lot=27',
               'specialEvents': []
            },
            {
               'shortName': '36',
               'name': 'Observatory Drive Ramp',
               'operatedBy': 'uw',
               'address': {
                 'street': '1645 Observatory Drive',
                 'city': 'Madison',
                 'state': 'WI',
                 'postalCode': '53706'
               },
               'entrances': [],
               'totalSpots': 463,
               'openSpots': None,
               'webUrl': 'https://fpm-www1.fpm.wisc.edu/smomap/lot.aspx?lot=36',
               'specialEvents': []
            },
            {
               'shortName': '6U',
               'name': 'Helen C. White Garage Upper Level',
               'operatedBy': 'uw',
               'address': {
                 'street': '600 N. Park Street',
                 'city': 'Madison',
                 'state': 'WI',
                 'postalCode': '53706'
               },
               'entrances': [],
               'totalSpots': 95,
               'openSpots': None,
               'webUrl': 'https://fpm-www1.fpm.wisc.edu/smomap/lot.aspx?lot=06',
               'specialEvents': []
            },
            {
               'shortName': '6L',
               'name': 'Helen C. White Garage Lower Level',
               'operatedBy': 'uw',
               'address': {
                 'street': '600 N. Park Street',
                 'city': 'Madison',
                 'state': 'WI',
                 'postalCode': '53706'
               },
               'entrances': [],
               'totalSpots': 95,
               'openSpots': None,
               'webUrl': 'https://fpm-www1.fpm.wisc.edu/smomap/lot.aspx?lot=06',
               'specialEvents': []
            },
            {
               'shortName': '7',
               'name': 'Grainger Hall Garage',
               'operatedBy': 'uw',
               'address': {
                 'street': '325 N. Brooks Street',
                 'city': 'Madison',
                 'state': 'WI',
                 'postalCode': '53715'
               },
               'entrances': [],
               'totalSpots': 412,
               'openSpots': None,
               'webUrl': 'https://fpm-www1.fpm.wisc.edu/smomap/lot.aspx?lot=07',
               'specialEvents': []
            },
            {
               'shortName': '29',
               'name': 'North Park Street Ramp',
               'operatedBy': 'uw',
               'address': {
                 'street': '21 N. Park Street',
                 'city': 'Madison',
                 'state': 'WI',
                 'postalCode': '53715'
               },
               'entrances': [],
               'totalSpots': 340,
               'openSpots': None,
               'webUrl': 'https://fpm-www1.fpm.wisc.edu/smomap/lot.aspx?lot=029',
               'specialEvents': []
            },
            {
               'shortName': '46',
               'name': 'Lake & Johnson Ramp',
               'operatedBy': 'uw',
               'address': {
                 'street': '301 N. Lake Street',
                 'city': 'Madison',
                 'state': 'WI',
                 'postalCode': '53715'
               },
               'entrances': [],
               'totalSpots': 733,
               'openSpots': None,
               'webUrl': 'https://fpm-www1.fpm.wisc.edu/smomap/lot.aspx?lot=046',
               'specialEvents': []
            },
            {
               'shortName': '83',
               'name': 'Fluno Center Garage',
               'operatedBy': 'uw',
               'address': {
                 'street': '314 N. Frances Street',
                 'city': 'Madison',
                 'state': 'WI',
                 'postalCode': '53703'
               },
               'entrances': [],
               'totalSpots': 296,
               'openSpots': None,
               'webUrl': 'https://fpm-www1.fpm.wisc.edu/smomap/lot.aspx?lot=83',
               'specialEvents': []
            },
            {
               'shortName': '17',
               'name': 'Engineering Drive Ramp',
               'operatedBy': 'uw',
               'address': {
                 'street': '1525 Engineering Drive',
                 'city': 'Madison',
                 'state': 'WI',
                 'postalCode': '53706'
               },
               'entrances': [],
               'totalSpots': 822,
               'openSpots': None,
               'webUrl': 'https://fpm-www1.fpm.wisc.edu/smomap/lot.aspx?lot=17',
               'specialEvents': []
            },
            {
               'shortName': '80',
               'name': 'Union South Garage',
               'operatedBy': 'uw',
               'address': {
                 'street': '1308 West Dayton Street',
                 'city': 'Madison',
                 'state': 'WI',
                 'postalCode': '53715'
               },
               'entrances': [],
               'totalSpots': 168,
               'openSpots': None,
               'webUrl': 'https://fpm-www1.fpm.wisc.edu/smomap/lot.aspx?lot=80',
               'specialEvents': []
            },
            {
               'shortName': '76',
               'name': 'University Bay Drive Ramp',
               'operatedBy': 'uw',
               'address': {
                 'street': '2501 University Bay Drive',
                 'city': 'Madison',
                 'state': 'WI',
                 'postalCode': '53705'
               },
               'entrances': [],
               'totalSpots': 1290,
               'openSpots': None,
               'webUrl': 'https://fpm-www1.fpm.wisc.edu/smomap/lot.aspx?lot=76',
               'specialEvents': []
            }
        ]