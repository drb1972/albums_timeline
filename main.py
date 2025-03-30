# streamlit run main.py --server.port 8085
import streamlit as st
from streamlit_timeline import timeline
import os
import json
import yaml
import cf
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

st.set_page_config(page_title="Bands Timeline", layout="wide")

#------------------- SESSION STATE ------------------------------------------
if 'selected_bands_list' not in st.session_state:
    st.session_state.selected_bands_list = []
if 'token' not in st.session_state:
    st.session_state.access_token = False
if 'all_bands_dict' not in st.session_state:
    st.session_state.all_bands_dict = {"items": []}


def get_token():
    spotify_client_id = st.secrets['spotify_client_id']
    spotify_client_secret = st.secrets['spotify_client_secret']
    st.session_state.access_token = cf.spotify_api_token(spotify_client_id, spotify_client_secret)
    if not st.session_state.access_token:
        print(f'{cf.timestamp()} - Error: Unable to get access token')


#------------------- SIDEBAR ------------------------------------------------
with st.sidebar:

    if not st.session_state.access_token: get_token()
    
    five_artists = []
    
    st.text('Search Band')
    search = st.text_input("Search Band",placeholder='Type here', label_visibility="collapsed",key="search")
    if search!='':
        print(f'{cf.timestamp()} -Searching {search}')
        band_to_search = search.strip().replace(' ', '+')
        spotify_search_bands_result = cf.spotify_search_bands(band_to_search, st.session_state.access_token)
        for artist in spotify_search_bands_result['artists']['items']:
            five_artists.append(artist["name"])


    if five_artists != []:
        selected_band = st.selectbox("Select from this list", five_artists, index=None)
        if selected_band:
            # five_artists = []
            artist_id = None
            for artist in spotify_search_bands_result['artists']['items']:
                if artist['name'] == selected_band:
                    artist_id = artist['id'] 
                    break
            # Check if selected_band and artist_id are provided
            if selected_band not in st.session_state.selected_bands_list:
                print(f'{cf.timestamp()} -Removing {selected_band}')
                st.session_state.selected_bands_list.append(selected_band)
                with st.spinner(text="Building Timeline"):
                    albums_data = cf.get_albums(st.session_state.access_token, selected_band, artist_id)
                st.session_state.all_bands_dict["items"].append(albums_data)


    album_types_options = ["album", "single", "compilation"]
    album_type_filter = st.segmented_control(
                "Album Type Filter", 
                album_types_options, selection_mode="multi",
                default="album"
                )

    def clear_text():
        st.session_state["search"] = ""

    st.caption("Remove from Timeline")
    with st.container(border=True):
        if st.session_state.selected_bands_list!= []:
            for band in st.session_state.selected_bands_list:
                remove_button = st.button(band, type="tertiary", key=f'{band}_remove', on_click=clear_text)
                if remove_button:
                    st.write('Remove band', band)
                    st.session_state.selected_bands_list.remove(band)
                    for item in st.session_state.all_bands_dict["items"]:
                        if item["band"] == band:
                            st.session_state.all_bands_dict["items"].remove(item)
                            print(f'{cf.timestamp()} -Removing {band}')
                            break
                    st.rerun()
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

elif st.session_state.all_bands_dict["items"]:
    
    events = []

    for band in st.session_state.all_bands_dict["items"]:

        band_name = band["band"]
        band_spotify_url = band["band_spotify_url"]
        band_link_text = f'Open Band: "{band_name}" in Spotify'

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
            album_link_text = f'Open Album: "{album_name}" in Spotify'
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