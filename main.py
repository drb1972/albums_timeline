# streamlit run main.py --server.port 8083
import streamlit as st
from streamlit_timeline import timeline
import os
import json
import yaml
import cf
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


st.set_page_config(page_title="Bands Timeline", layout="wide")
# st.logo("images/Gafas-Turkas-6.png",size="large")
# st.title("Bands Timeline")

#------------------- SESSION STATE ------------------------------------------
if 'selected_bands_list' not in st.session_state:
    st.session_state.selected_bands_list = []
if 'selected_ids_list' not in st.session_state:
    st.session_state.selected_ids_list = []
if 'token' not in st.session_state:
    st.session_state.token = False


if not st.session_state.token:
    # Read input.yaml
    with open('input.yaml', 'r') as f:
        input = yaml.safe_load(f)
    client_id = input['client_id']
    client_secret = input['client_secret']
    st.session_state.access_token = cf.spotify_api_token(client_id, client_secret)
    if not st.session_state.access_token:
        print(f'{cf.timestamp()} - Error: Unable to get access token')

#------------------- SIDEBAR ------------------------------------------------
with st.sidebar:

    col1, col2 = st.columns(2, vertical_alignment="top", border=True)
# with st.container(border=True):
   
    with col1:

        st.text('Search Band')
        search = st.text_input("Search Band",placeholder='Type here', label_visibility="collapsed")

        if search!='':
                band_to_search = search.strip().replace(' ', '+')
                spotify_search_bands_result = cf.spotify_search_bands(band_to_search, st.session_state.access_token)
                
                artists_info = []
                for artist in spotify_search_bands_result['artists']['items']:
                    artist_info = {
                        "name": artist['name'],
                        "id": artist['id']
                    }
                    artists_info.append(artist_info)
                artist_names = [artist["name"] for artist in artists_info]
                selected_band = st.selectbox("Select from this list", artist_names, index=None)
                artist_id = None
                for artist in spotify_search_bands_result['artists']['items']:
                    if artist['name'] == selected_band:
                        artist_id = artist['id']
                        break

                # Check if selected_band and artist_id are provided
                if selected_band and artist_id:
                    # Load the current content of 'input.yaml' into a variable
                    with open('input.yaml', 'r') as f:
                        input_data = yaml.safe_load(f)

                    # Sanitize selected_band value for use as a key
                    band_key = selected_band.lower().replace(' ', '_')

                    # Check if the band is already in the dictionary
                    if band_key not in input_data["bands"]:
                        input_data["bands"][band_key] = {
                            "band_name": selected_band,
                            "band_id": artist_id
                        }

                        # Write the updated data back to 'input.yaml' only once all changes are done
                        with open('input.yaml', 'w') as f:
                            yaml.safe_dump(input_data, f)

                        # Notify the user and trigger external script
                        with st.spinner(text="Building Timeline"):
                            os.system("python get_albums.py")

                    if selected_band not in st.session_state.selected_bands_list:
                        st.session_state.selected_bands_list.append(selected_band)
                        st.session_state.selected_ids_list.append(artist_id)


    
    with st.container(border=True):
        with col2:
            st.caption("Remove from Timeline")
            with st.container(border=True):
                for band in st.session_state.selected_bands_list:
                    st.button(band, type="tertiary", key=f'{band}_remove')
                    if st.session_state[f'{band}_remove']:
                        if band in st.session_state.selected_bands_list:
                            st.session_state.selected_bands_list.remove(band)
                            st.session_state.selected_ids_list.remove(artist_id)
                            st.rerun()


    album_types_options = ["album", "single", "compilation"]
    album_type_filter = st.segmented_control(
                "Album Type Filter", 
                album_types_options, selection_mode="multi",
                default="album"
                )
#------------------- END OF SIDEBAR -----------------------------------------



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

if album_type_filter==[]:
    st.write('Select at least 1 Album Type Filter')

if st.session_state.selected_bands_list!=[]:
    events = []
    #- Read each band json file
    for item in st.session_state.selected_ids_list: 
        with open(f'./bands/{item}.json', 'r') as f:
            band = json.load(f)

        band_name = band["band"]
        band_spotify_url = band["band_spotify_url"]
        band_link_text = f'Open "{band_name}" in Spotify'

        for album in band["albums"]:
            #- Filter album type ----------------------------
            if album_type_filter==[]:
                break
            
            if album["album_group"] not in album_type_filter:
                continue

            album_name = album["name"]
            album_name = album_name.replace("(Remastered)", "").strip()
            album_name = album_name.replace("(Remaster)", "").strip()
            album_cover = album["album_cover"]
            thumbnail = album["thumbnail"]
            album_spotify_url = album["album_spotify_url"]
            album_link_text = f'Open "{album_name}" in Spotify'
            total_tracks = album["total_tracks"]
            album_type = album["album_type"]
            release_date = album["release_date"]
            release_date_precision = album["release_date_precision"]
            release_year, release_month = get_year_month(release_date_precision, release_date)
            
            info_text = f'''
            </p><a href="{band_spotify_url}" target="_blank">{band_link_text}</a>
            </p><a href="{album_spotify_url}" target="_blank">{album_link_text}</a>
            </p>Total Tracks: {total_tracks}
            </p>Songs'''
            for track in album["tracks"]:
                info_text += f'''</p><a href="{track['track_spotify_url']}" target="_blank">{track["track_number"]}. {track["name"]}</a>'''
                

            event = {
                "media": {
                    "url": f'{album_cover}',
                    "caption": f'{album_name}',
                    "thumbnail": f'<img src="{thumbnail}>'
                },
                "start_date": {
                    "year": f'{release_year}',
                    "month": f'{release_month}' 
                },
                "text": {
                    "headline": f'{album_name}',
                    "text": f'{info_text}'
                },
                "group": f'{band_name}'
            }

            events.append(event)
    
    #- Create timeline header - dict: timeline_dict
    if album_type_filter!=[]:
        if events == []:
            st.write(f"No albums found for type {album_type_filter}")
        else:
            timeline_dict = {
                "title": {
                    "text": {
                        "headline": "Album Release Timeline",
                        "text": '<p>🎸 <a href="mailto:drb1972@gmail.com" style="color:blue;">drb1972@gmail.com</a></p>'
                    },
                }
            }
            timeline_dict["events"] = events
            with st.spinner(text="Building line"):
                timeline(timeline_dict, height=750)