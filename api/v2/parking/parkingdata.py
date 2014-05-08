# CityParkingData.lots pre-populates static props and later fills dynamic props
class ParkingData:
    def __init__(self):

        self.city_lots = [
            {
                'name': 'State Street Campus Garage',
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
                'operatedBy':'city',  # city|uw|private
                'webUrl': None,
                'specialEvents': []
            },
            {
                'name': 'Brayton Lot',
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
                'operatedBy': 'city',  # city|uw|private
                'webUrl': None,
                'specialEvents': []
            },
            {
                'name': 'Capitol Square North Garage',
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
                'operatedBy':'city',  # city|uw|private
                'webUrl': None,
                'specialEvents': []
            },
            {
                'name': 'Government East Garage',
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
                'operatedBy':'city',  # city|uw|private
                'webUrl': None,
                'specialEvents': []
            },
            {
                'name': 'Overture Center Garage',
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
                'operatedBy':'city',  # city|uw|private
                'webUrl': None,
                'specialEvents': []
            },
            {
                'name': 'State Street Capitol Garage',
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
                'operatedBy':'city',  # city|uw|private
                'webUrl': None,
                'specialEvents': []
            }
        ]

        # define lots with mostly initial data to minimize potential for breakage.
        self.campus_lots = [
            {
               'id': 1,
               'shortName': '020',
               'name': 'University Avenue Ramp',
               'address': {
                 'street': '1390 University Avenue',
                 'city': 'Madison',
                 'state': 'WI',
                 'postalCode': '53706'
               },
               'entrances': [],
               'totalSpots': 220,
               'openSpots': None,
               'operatedBy':'uw',  # city|uw|private
               'webUrl': None,
               'specialEvents': []
            },
            {
               'id': 2,
               'shortName': '027',
               'name': 'Nancy Nicholas Hall Garage',
               'address': {
                 'street': '1330 Linden Drive',
                 'city': 'Madison',
                 'state': 'WI',
                 'postalCode': '53706'
               },
               'entrances': [],
               'totalSpots': 48,
               'openSpots': None,
               'operatedBy':'uw',  # city|uw|private
               'webUrl': None,
               'specialEvents': []
            },
            {
               'id': 3,
               'shortName': '036',
               'name': 'Observatory Drive Ramp',
               'address': {
                 'street': '1645 Observatory Drive',
                 'city': 'Madison',
                 'state': 'WI',
                 'postalCode': '53706'
               },
               'entrances': [],
               'totalSpots': 463,
               'openSpots': None,
               'operatedBy':'uw',  # city|uw|private
               'webUrl': None,
               'specialEvents': []
            },
            {
               'id': 4,
               'shortName': '06U',
               'name': 'Helen C. White Garage Upper Level',
               'address': {
                 'street': '600 N. Park Street',
                 'city': 'Madison',
                 'state': 'WI',
                 'postalCode': '53706'
               },
               'entrances': [],
               'totalSpots': 95,
               'openSpots': None,
               'operatedBy':'uw',  # city|uw|private
               'webUrl': 'https://fpm-www1.fpm.wisc.edu/smomap/lot.aspx?lot=06',
               'specialEvents': []
            },
            {
               'id': 5,
               'shortName': '06L',
               'name': 'Helen C. White Garage Lower Level',
               'address': {
                 'street': '600 N. Park Street',
                 'city': 'Madison',
                 'state': 'WI',
                 'postalCode': '53706'
               },
               'entrances': [],
               'totalSpots': 95,
               'openSpots': None,
               'operatedBy':'uw',  # city|uw|private
               'webUrl': 'https://fpm-www1.fpm.wisc.edu/smomap/lot.aspx?lot=06',
               'specialEvents': []
            },
            {
               'id': 6,
               'shortName': '007',
               'name': 'Grainger Hall Garage',
               'address': {
                 'street': '325 N. Brooks Street',
                 'city': 'Madison',
                 'state': 'WI',
                 'postalCode': '53715'
               },
               'entrances': [],
               'totalSpots': 412,
               'openSpots': None,
               'operatedBy':'uw',  # city|uw|private
               'webUrl': 'https://fpm-www1.fpm.wisc.edu/smomap/lot.aspx?lot=07',
               'specialEvents': []
            },
            {
               'id': 7,
               'shortName': '029',
               'name': 'North Park Street Ramp',
               'address': {
                 'street': '21 N. Park Street',
                 'city': 'Madison',
                 'state': 'WI',
                 'postalCode': '53715'
               },
               'entrances': [],
               'totalSpots': 340,
               'openSpots': None,
               'operatedBy':'uw',  # city|uw|private
               'webUrl': 'https://fpm-www1.fpm.wisc.edu/smomap/lot.aspx?lot=029',
               'specialEvents': []
            },
            {
               'id': 8,
               'shortName': '046',
               'name': 'Lake & Johnson Ramp',
               'address': {
                 'street': '301 N. Lake Street',
                 'city': 'Madison',
                 'state': 'WI',
                 'postalCode': '53715'
               },
               'entrances': [],
               'totalSpots': 733,
               'openSpots': None,
               'operatedBy':'uw',  # city|uw|private
               'webUrl': 'https://fpm-www1.fpm.wisc.edu/smomap/lot.aspx?lot=046',
               'specialEvents': []
            },
            {
               'id': 9,
               'shortName': '083',
               'name': 'Fluno Center Garage',
               'address': {
                 'street': '314 N. Frances Street',
                 'city': 'Madison',
                 'state': 'WI',
                 'postalCode': '53703'
               },
               'entrances': [],
               'totalSpots': 296,
               'openSpots': None,
               'operatedBy':'uw',  # city|uw|private
               'webUrl': 'https://fpm-www1.fpm.wisc.edu/smomap/lot.aspx?lot=083',
               'specialEvents': []
            },
            {
               'id': 10,
               'shortName': '017',
               'name': 'Engineering Drive Ramp',
               'address': {
                 'street': '1525 Engineering Drive',
                 'city': 'Madison',
                 'state': 'WI',
                 'postalCode': '53706'
               },
               'entrances': [],
               'totalSpots': 822,
               'openSpots': None,
               'operatedBy':'uw',  # city|uw|private
               'webUrl': 'https://fpm-www1.fpm.wisc.edu/smomap/lot.aspx?lot=017',
               'specialEvents': []
            },
            {
               'id': 11,
               'shortName': '080',
               'name': 'Union South Garage',
               'address': {
                 'street': '1308 West Dayton Street',
                 'city': 'Madison',
                 'state': 'WI',
                 'postalCode': '53715'
               },
               'entrances': [],
               'totalSpots': 168,
               'openSpots': None,
               'operatedBy':'uw',  # city|uw|private
               'webUrl': 'https://fpm-www1.fpm.wisc.edu/smomap/lot.aspx?lot=080',
               'specialEvents': []
            },
            {
               'id': 12,
               'shortName': '076',
               'name': 'University Bay Drive Ramp',
               'address': {
                 'street': '2501 University Bay Drive',
                 'city': 'Madison',
                 'state': 'WI',
                 'postalCode': '53705'
               },
               'entrances': [],
               'totalSpots': 1290,
               'openSpots': None,
               'operatedBy':'uw',  # city|uw|private
               'webUrl': 'https://fpm-www1.fpm.wisc.edu/smomap/lot.aspx?lot=076',
               'specialEvents': []
            }
        ]