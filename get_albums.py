import cf
import json
import yaml
import os
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

print(f'{cf.timestamp()} - Starting process')

# Read input.yaml
with open('input.yaml', 'r') as f:
   input = yaml.safe_load(f)

#- GLOBAL VARIABLES -----------------------------------------
refresh_api_calls = 'No'
#- Get bands from the ./bands/ directory
bands_in_dir =  [os.path.splitext(file)[0] for file in os.listdir('./spotify_bands/')  if file.endswith('.json')]

client_id = input['client_id']
client_secret = input['client_secret']
#- END OF GLOBAL VARIABLES ----------------------------------


#- Get Spotify info about All albums released by all artist -
def get_albums(access_token):
    # Loop through each band in the 'bands' dictionary ------
    for short_name, band_info in input['bands'].items():
        band_name = band_info['band_name']
        band_id = band_info['band_id']
        print(f'{cf.timestamp()} - Processing: {band_name} - Band_id: {band_id} - Retrieving Albums')
        #- Do not refresh band if already in the bands dir --
        if refresh_api_calls == 'No' and band_id in bands_in_dir: 
            print(f'{cf.timestamp()} - Band {band_name} - {band_id} skipped - Already stored')
            continue
        #----------------------------------------------------

        #- Retrieve all albums for a band -------------------
        band_full_response = cf.spotify_artists_albums(band_id, access_token)
        #----------------------------------------------------

        #- Store the original apotify response in a file named {band}.json
        print(f'{cf.timestamp()} - Creating: ./spotify_bands/{band_id}.json') 
        with open(f'./spotify_bands/{band_id}.json', 'w') as json_file: 
            json.dump(band_full_response, json_file, indent=4)
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
            print(f'{cf.timestamp()} - Removing: {band_name} - {band_id} - {album["name"]}') 

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
            release_year, release_month = cf.get_year_month(album["release_date_precision"], album["release_date"])
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
                    print(f'{cf.timestamp()} - No artists found in album: {album["name"]}')
        else:
            print(f'{cf.timestamp()} - No albums found in the response.')

        # If no valid URL was found, set band_spotify_url to ''
        if not band_spotify_url:
            band_spotify_url = ''
        # band_spotify_url = band_full_response['items'][0]['artists'][0]['external_urls']['spotify']

        band_dict = {
            "band": band_name,
            "band_spotify_url": band_spotify_url,
            "band_link_text": f'Open Album in Spotify {band_name}',
            "albums": albums_list
            }
        #----------------------------------------------------

    #--------------------------------------------------------

        #- Get all songs from albums ------------------------
        get_record_tracks(band_dict, band_id, access_token)
        #----------------------------------------------------

    return


def get_record_tracks(band_dict, band_id, access_token):
    band_name = band_dict["band"]
    print(f'{cf.timestamp()} - Retrieving tracks for {band_name}')
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
            albums_temp_response = cf.spotify_tracks_info(albums_ids, access_token)
            albums_full_response["albums"].extend(albums_temp_response["albums"])
            #- store the desired fields in a list of dicts
            albums_ids = ""  # Reset for the next batch
    #--------------------------------------------------------

    #- Store the original spotify response in a file named {band}.json
    print(f'{cf.timestamp()} - Creating: ./spotify_albums/{band_id}.json') 
    with open(f'./spotify_albums/{band_id}.json', 'w') as json_file: 
        json.dump(albums_full_response, json_file, indent=4)
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

    # Save the band's album list as a JSON file -------------
    print(f'{cf.timestamp()} - Creating: ./bands/{band_id}.json')
    with open(f'./bands/{band_id}.json', 'w') as json_file:
        json.dump(band_dict, json_file, indent=4)
    #--------------------------------------------------------
    return


# Main function to run the script ---------------------------
def main():
    #- Get the access token --------------------------------
    access_token = cf.spotify_api_token(client_id, client_secret)
    if not access_token:
        print(f'{cf.timestamp()} - Error: Unable to get access token')
        return
    print(f'{cf.timestamp()} - Accss token: ', access_token)

    #- Get the artist's albums ------------------------------
    get_albums(access_token)

if __name__ == "__main__":
    main()
