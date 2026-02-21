
import urllib

def get_location(location):
    
   
    
    # Taking the location and getting map link
    #if location and location.get('latitude') and location.get('longitude'):
    latitude=location.get('latitude')#17.4356266#
    longitude=location.get('longitude')#78.4395346#
    search_query='neary by pharmacies'
    encoded_query=urllib.parse.quote(search_query)
    map_link = f"https://www.google.com/maps/search/{encoded_query}/@{latitude},{longitude},15z"
    return map_link
    #return 'Location not provided or permission denied'

