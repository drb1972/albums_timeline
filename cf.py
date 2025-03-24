import requests
import base64
import time
import yaml
from datetime import datetime


def timestamp():
    return datetime.now().strftime("%Y/%m/%d %H:%M:%S")

#- Function to get the Spotify access token -----------------
def spotify_api_token(client_id, client_secret):
    # Define the URL for the token request
    url = "https://accounts.spotify.com/api/token"
    # Encode the client ID and secret in base64
    auth = base64.b64encode(f"{client_id}:{client_secret}".encode('utf-8')).decode('utf-8')
    # Set the headers for the request
    headers = {
        "Authorization": f"Basic {auth}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    # Set the body for the request
    body = {
        "grant_type": "client_credentials"
    }
    # Send the POST request to get the token
    response = requests.post(url, headers=headers, data=body, verify=False)
    # Parse the JSON response and get the access token
    token_data = response.json()
    access_token = token_data.get("access_token")
    return access_token



#- Get Spotify info about All albums released by an artist --
def spotify_artists_albums(band_id, access_token):
    #- To store the full spotify response ---------------
    band_full_response = {}
    #----------------------------------------------------
    #- Loop until no more responses ---------------------
    offset_band = 0        
    loop_band = True
    while loop_band:
        url = f"https://api.spotify.com/v1/artists/{band_id}/albums?market=ES&limit=50&include_groups=album,single,compilation,appears_on&offset={offset_band}"
        # url = f"https://api.spotify.com/v1/artists/{band_id}/albums?limit=50&include_groups=album&offset={offset}"
        # print(url) # dxr
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        response = requests.get(url, headers=headers, verify=False)

        if response.status_code != 200:
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 5))  # Default to 5 seconds
                print(f"{timestamp()} - >>>>>>>> Rate limit exceeded, waiting for {retry_after} seconds...")
                time.sleep(retry_after)
                return spotify_artists_albums(band_id, access_token)
            else:
                print(f'{timestamp()} - Error: Unable to fetch albums for artist {band_id}, status code: {response.status_code}')
            return {}
        else:
            data = response.json()
            if offset_band==0:
                band_full_response["items"] = data["items"]
            else:
                # Add responses above 50 accurrences
                band_full_response["items"].extend(data["items"])
            if data["next"]==None:
                loop_band = False
            else:
                offset_band+=50
            
    return band_full_response


#- Get Spotify info about 1 album details -------------------
def spotify_tracks_info(albums_ids, access_token):
    url = f"https://api.spotify.com/v1/albums?ids={albums_ids}&market=ES"
    # print(url) # dxr
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    response = requests.get(url, headers=headers, verify=False)

    if response.status_code != 200:
        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 5))  # Default to 5 seconds
            print(f'{timestamp()} - >>>>>>>> Rate limit exceeded, waiting for {retry_after} seconds...')
            time.sleep(retry_after)
            return spotify_artists_albums(albums_ids, access_token)
        else:
            print(f'{timestamp()} - Error: Unable to fetch albums for artist {albums_ids}, status code: {response.status_code}')
        return {}
    else:
        albums_full_response = response.json()
            
    return albums_full_response
    

#- Get Spotify search a band (5 bands) ----------------------
def spotify_search_bands(band, access_token):
    url = f"https://api.spotify.com/v1/search?q={band}&type=artist&limit=5"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    response = requests.get(url, headers=headers, verify=False)

    if response.status_code != 200:
        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 5))  # Default to 5 seconds
            print(f'{timestamp()} - >>>>>>>> Rate limit exceeded, waiting for {retry_after} seconds...')
            time.sleep(retry_after)
        else:
            print(f'{timestamp()} - Error: Unable to search artist {band}, status code: {response.status_code}')
        return {}
    else:
        spotify_search_bands_result = response.json()
            
    return spotify_search_bands_result



def get_year_month(release_date_precision, release_date):
    if release_date_precision == "year":
        release_year = release_date
        release_month = 1
    elif release_date_precision == "day" or release_date_precision == "month":
        release_year = release_date.split('-')[0]
        release_month = release_date.split('-')[1]
    else:
        release_year = None
        release_month = None
    return release_year, release_month