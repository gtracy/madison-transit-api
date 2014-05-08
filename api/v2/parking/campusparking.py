from api.v2.parking.parkingdata import ParkingData


# Handles fetch, parse and combine of cityparking data
class CampusParkingService():
    def __init__(self, campusparking=None):  # allow injection of parking data
        if campusparking:
            self.lots = campusparking
        else:
            self.lots = ParkingData()

    def get_data(self):
        parking_availability_html = self.fetch_availability_html()
        parking_availabilities = self.parse_availability_html(parking_availability_html)

        special_events_html = self.fetch_special_events_html()
        special_events = self.parse_special_events_html(special_events_html)

        self.fill_campusparking_data_obj(parking_availabilities, special_events)
        return self.lots

    def fetch_availability_html(self):
        availability_url = 'http://transportation.wisc.edu/parking/lotinfo_occupancy.aspx'

        return None

    def parse_availability_html(self, cityparking_avail_html):
        return None

    def fetch_special_events_html(self):
        return None

    def parse_special_events_html(self, special_events_html):
        return None

    def fill_campusparking_data_obj(self, parking_availabilities, special_events):
        return None

