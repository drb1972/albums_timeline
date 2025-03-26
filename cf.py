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



#- Get Spotify info about All albums released by all artist -
def get_albums(access_token, band_name, band_id):
    #- Retrieve all albums for a band -------------------
    band_full_response = spotify_artists_albums(band_id, access_token)
    #----------------------------------------------------

    #- Clean Up - Loop through the albums and remove those with "Deluxe" in the name
    albums_to_remove = []
    for album in band_full_response.get('items', []):
        #- Check if 'Remastered' or 'Deluxe' is in the album name
        album.pop('available_markets', None)
        if "Deluxe" in album['name']:
            albums_to_remove.append(album)

        #- Check if the band_name appears in the artists list
        album['artists'] = [artist for artist in album['artists'] if artist['name'] == band_name]

        #- If no artist matches the band_name, mark the album for removal
        if not album['artists']:
            albums_to_remove.append(album)
    #----------------------------------------------------

    # Remove the unwanted albums ------------------------
    for album in albums_to_remove:
        print(f'{timestamp()} - Removing: {band_name} - {band_id} - {album["name"]}') 

        if album in band_full_response['items']:
            band_full_response['items'].remove(album)
    #----------------------------------------------------

    #- Create band dictionary ---------------------------
    albums_list = []
    for album in band_full_response.get('items', []):
        # minutes, seconds = divmod(song["duration_ms"] // 1000, 60)
        album_name = album["name"]
        album_name = album_name.replace("(Remastered)", "").strip()
        album_name = album_name.replace("(Remaster)", "").strip()
        release_year, release_month = get_year_month(album["release_date_precision"], album["release_date"])
        #- Check "artists" is not empty
        if not album["artists"]:
            album_spotify_url = ''
        else:
            album_spotify_url = f'{album["external_urls"]["spotify"]}'
        album_dict = {
            "id": album["id"],
            "name": album_name,
            "type": album["album_type"],
            "album_cover": album["images"][0]["url"],
            "thumbnail": album["images"][2]["url"],
            "total_tracks": album["total_tracks"],
            "album_group": album["album_group"],
            "album_type": album["album_type"],
            "release_date": album["release_date"],
            "release_date_precision": album["release_date_precision"],
            "release_year": release_year,
            "release_month": release_month,
            "album_spotify_url": album_spotify_url
        }

        albums_list.append(album_dict)

    # Safely access the external_urls of the first artist in the artists list

    # Initialize the band_spotify_url as an empty string
    band_spotify_url = ''

    # Check if there are items (albums) in the response
    if 'items' in band_full_response and band_full_response['items']:
        # Loop through all albums
        for album in band_full_response['items']:
            # Check if the 'artists' list is not empty
            if album.get('artists') and len(album['artists']) > 0:
                # Loop through all artists in the 'artists' list
                for artist in album['artists']:
                    # Get another URL (e.g., 'href') for the artist
                    artist_url = artist.get('external_urls', {}).get('spotify', '')
                    
                    if artist_url:
                        # If a URL is found, set it to band_spotify_url and break the loop
                        band_spotify_url = artist_url
                        break  # Exit the loop when the first valid URL is found
                if band_spotify_url:  # If a URL was found, break out of the outer loop as well
                    break
            else:
                print(f'{timestamp()} - No artists found in album: {album["name"]}')
    else:
        print(f'{timestamp()} - No albums found in the response.')

    # If no valid URL was found, set band_spotify_url to ''
    if not band_spotify_url:
        band_spotify_url = ''
    # band_spotify_url = band_full_response['items'][0]['artists'][0]['external_urls']['spotify']

    band_dict = {
        "band": band_name,
        "band_id": band_id,
        "band_spotify_url": band_spotify_url,
        "band_link_text": f'Open Album in Spotify {band_name}',
        "albums": albums_list
        }
    #----------------------------------------------------

#--------------------------------------------------------

    #- Get all songs from albums ------------------------
    band_dict = get_record_tracks(band_dict, band_id, access_token)
    #----------------------------------------------------

    return band_dict


def get_record_tracks(band_dict, band_id, access_token):
    band_name = band_dict["band"]
    print(f'{timestamp()} - Retrieving tracks for {band_name}')
    #- Call Spotify to retrieve up to 20 albums info --------
    albums_ids = ""
    albums_full_response = {"albums": []}
    #- Loop through band_dict albums to collect the IDs -----
    for i, album in enumerate(band_dict['albums']):
        #- Add the album ID to the string -------------------
        if i > 0:
            albums_ids += ","  # Add comma between IDs
        albums_ids += album["id"]
        
        #- If there are 20 IDs, call the function and reset the string
        if (i + 1) % 20 == 0 or i == len(band_dict['albums']) - 1:
            #- Remove leading or trailing commas from the albums_ids string
            albums_ids = albums_ids.strip(',')
            #- Call the function with the current batch of IDs
            albums_temp_response = spotify_tracks_info(albums_ids, access_token)
            albums_full_response["albums"].extend(albums_temp_response["albums"])
            #- store the desired fields in a list of dicts
            albums_ids = ""  # Reset for the next batch
    #--------------------------------------------------------

    #- Loop through band_dict albums and add tracks info ----
    
    for album in albums_full_response['albums']:
        tracks_list = []
        for track in album["tracks"]["items"]:
            minutes, seconds = divmod(track["duration_ms"] // 1000, 60)
            track = {
                "name": track["name"],
                "track_number": track["track_number"],
                "duration": f"{minutes}:{seconds:02d}",
                "track_spotify_url": track["external_urls"]["spotify"]
            }
            tracks_list.append(track)

        #- Add tracks list to each album in band_dict -------
        for albums_items in band_dict['albums']:
            if albums_items["id"]==album["id"]:
                albums_items["tracks"] = tracks_list

    return band_dict





