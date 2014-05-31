# CityParkingData represents the complete collection of parking lots
# pre-populated with "static" data where possible. The goal is to
# reduce api breakage due to html template changes or field format
# discrepancies by limiting the # of fields pulled dynamically.
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
                    'street': '430 North Frances Street',
                    'city': 'Madison',
                    'state': 'WI',
                    'postalCode': '53703'
                },
                'coordinates': {
                    'lat': 43.074067,
                    'lng': -89.39624099999999
                },
                'entrances': [
                    '400 North Frances Street',
                    '400 North Lake Street'
                ],
                'totalSpots': 1065,
                'openSpots': None,
                'webUrl': 'http://www.cityofmadison.com/parkingUtility/garagesLots/facilities/stateStCampus.cfm'
            },
            {
                'name': 'Brayton Lot',
                'operatedBy': 'city',
                'shortName': 'brayton',  # minimum reliable unique string
                'address': {
                    'street': '1 South Butler Street',
                    'city': 'Madison',
                    'state': 'WI',
                    'postalCode': '53703'
                },
                'coordinates': {
                    'lat': 43.076728,
                    'lng': -89.3802089
                },
                'entrances': [
                    {'street': '10 South Butler Street'}
                ],
                'totalSpots': 247,
                'openSpots': None,
                'webUrl': 'http://www.cityofmadison.com/parkingUtility/garagesLots/facilities/brayton.cfm'
            },
            {
                'name': 'Capitol Square North Garage',
                'operatedBy': 'city',
                'shortName': 'north',  # minimum reliable unique string
                'address': {
                    'street': '218 East Mifflin Street',
                    'city': 'Madison',
                    'state': 'WI',
                    'postalCode': '53703'
                },
                'coordinates': {
                    'lat': 43.077627,
                    'lng': -89.38321499999999
                },
                'entrances': [
                    '100 North Butler Street', '200 East Mifflin Street', '100 North Webster Street'
                ],
                'totalSpots': 613,
                'openSpots': None,
                'webUrl': 'http://www.cityofmadison.com/parkingUtility/garagesLots/facilities/capSquareNorth.cfm'
            },
            {
                'name': 'Government East Garage',
                'operatedBy': 'city',
                'shortName': 'east',  # minimum reliable unique string
                'address': {
                    'street': '215 South Pinckney Street',
                    'city': 'Madison',
                    'state': 'WI',
                    'postalCode': '53703'
                },
                'coordinates': {
                    'lat': 43.073934,
                    'lng': -89.380245
                },
                'entrances': [
                    '200 South Pinckney Street', '100 East Wilson Street'
                ],
                'totalSpots': 516,
                'openSpots': None,
                'webUrl': 'http://www.cityofmadison.com/parkingUtility/garagesLots/facilities/govtEast.cfm'
            },
            {
                'name': 'Overture Center Garage',
                'operatedBy': 'city',
                'shortName': 'overture',  # minimum reliable unique string
                'address': {
                    'street': '318 West Mifflin Street',
                    'city': 'Madison',
                    'state': 'WI',
                    'postalCode': '53703'
                },
                'entrances': [
                    '300 West Dayton Street', '300 West Mifflin Street'
                ],
                'coordinates': {
                    'lat': 43.073353,
                    'lng': -89.38928299999999
                },
                'totalSpots': 620,
                'openSpots': None,
                'webUrl': 'http://www.cityofmadison.com/parkingUtility/garagesLots/facilities/overture.cfm'
            },
            {
                'name': 'State Street Capitol Garage',
                'operatedBy': 'city',
                'shortName': 'state street capitol',  # minimum reliable unique string
                'address': {
                    'street': '214 North Carroll Street',
                    'city': 'Madison',
                    'state': 'WI',
                    'postalCode': '53703'
                },
                'coordinates': {
                    'lat': 43.0753667,
                    'lng': -89.388021
                },
                'entrances': [
                    '200 North Carroll Street', '100 West Dayton Street', '100 West Johnson Street '
                ],
                'totalSpots': 850,
                'openSpots': None,
                'webUrl': 'http://www.cityofmadison.com/parkingUtility/garagesLots/facilities/stateStCapitol.cfm'
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
                'coordinates': {
                    'lat': 43.073397,
                    'lng': -89.4088843
                },
                'entrances': [],
                'totalSpots': 220,
                'openSpots': None,
                'webUrl': 'https://fpm-www1.fpm.wisc.edu/smomap/lot.aspx?lot=20'
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
                'coordinates': {
                    'lat': 43.0751477,
                    'lng': -89.4097714
                },
                'entrances': [],
                'totalSpots': 48,
                'openSpots': None,
                'webUrl': 'https://fpm-www1.fpm.wisc.edu/smomap/lot.aspx?lot=27'
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
                'coordinates': {
                    'lat': 43.0764412,
                    'lng': -89.4138189
                },
                'entrances': [],
                'totalSpots': 463,
                'openSpots': None,
                'webUrl': 'https://fpm-www1.fpm.wisc.edu/smomap/lot.aspx?lot=36'
            },
            {
                'shortName': '6U',
                'name': 'Helen C. White Garage Upper Level',
                'operatedBy': 'uw',
                'address': {
                    'street': '600 North Park Street',
                    'city': 'Madison',
                    'state': 'WI',
                    'postalCode': '53706'
                },
                'coordinates': {
                    'lat': 43.0763396,
                    'lng': -89.4007865
                },
                'entrances': [],
                'totalSpots': 95,
                'openSpots': None,
                'webUrl': 'https://fpm-www1.fpm.wisc.edu/smomap/lot.aspx?lot=06'
            },

            {
                'shortName': '6L',
                'name': 'Helen C. White Garage Lower Level',
                'operatedBy': 'uw',
                'address': {
                    'street': '600 North Park Street',
                    'city': 'Madison',
                    'state': 'WI',
                    'postalCode': '53706'
                },
                'coordinates': {
                    'lat': 43.0767906197085,
                    'lng': -89.4007865
                },
                'entrances': [],
                'totalSpots': 95,
                'openSpots': None,
                'webUrl': 'https://fpm-www1.fpm.wisc.edu/smomap/lot.aspx?lot=06'
            },
            {
                'shortName': '7',
                'name': 'Grainger Hall Garage',
                'operatedBy': 'uw',
                'address': {
                    'street': '325 North Brooks Street',
                    'city': 'Madison',
                    'state': 'WI',
                    'postalCode': '53715'
                },
                'coordinates': {
                    'lat': 43.07277759999999,
                    'lng': -89.40241119999999
                },
                'entrances': [],
                'totalSpots': 412,
                'openSpots': None,
                'webUrl': 'https://fpm-www1.fpm.wisc.edu/smomap/lot.aspx?lot=07'
            },
            {
                'shortName': '29',
                'name': 'North Park Street Ramp',
                'operatedBy': 'uw',
                'address': {
                    'street': '21 North Park Street',
                    'city': 'Madison',
                    'state': 'WI',
                    'postalCode': '53715'
                },
                'coordinates': {
                    'lat': 43.0682501,
                    'lng': -89.4000363
                },
                'entrances': [],
                'totalSpots': 340,
                'openSpots': None,
                'webUrl': 'https://fpm-www1.fpm.wisc.edu/smomap/lot.aspx?lot=029'
            },
            {
                'shortName': '46',
                'name': 'Lake & Johnson Ramp',
                'operatedBy': 'uw',
                'address': {
                    'street': '301 North Lake Street',
                    'city': 'Madison',
                    'state': 'WI',
                    'postalCode': '53715'
                },
                'coordinates': {
                    'lat': 43.0723259,
                    'lng': -89.396855
                },
                'entrances': [],
                'totalSpots': 733,
                'openSpots': None,
                'webUrl': 'https://fpm-www1.fpm.wisc.edu/smomap/lot.aspx?lot=046'
            },
            {
                'shortName': '83',
                'name': 'Fluno Center Garage',
                'operatedBy': 'uw',
                'address': {
                    'street': '314 North Frances Street',
                    'city': 'Madison',
                    'state': 'WI',
                    'postalCode': '53703'
                },
                'coordinates': {
                    'lat': 43.0725931,
                    'lng': -89.3958675
                },
                'entrances': [],
                'totalSpots': 296,
                'openSpots': None,
                'webUrl': 'https://fpm-www1.fpm.wisc.edu/smomap/lot.aspx?lot=83'
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
                'coordinates': {
                    'lat': 43.07213400000001,
                    'lng': -89.4122016
                },
                'entrances': [],
                'totalSpots': 822,
                'openSpots': None,
                'webUrl': 'https://fpm-www1.fpm.wisc.edu/smomap/lot.aspx?lot=17'
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
                'coordinates': {
                    'lat': 43.0712481,
                    'lng': -89.40804949999999
                },
                'entrances': [],
                'totalSpots': 168,
                'openSpots': None,
                'webUrl': 'https://fpm-www1.fpm.wisc.edu/smomap/lot.aspx?lot=80'
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
                'coordinates': {
                    'lat': 43.0813065,
                    'lng': -89.4282504
                },
                'entrances': [],
                'totalSpots': 1290,
                'openSpots': None,
                'webUrl': 'https://fpm-www1.fpm.wisc.edu/smomap/lot.aspx?lot=76'
            }
        ]