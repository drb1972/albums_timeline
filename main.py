# streamlit run main.py --server.port 8085
import streamlit as st
from streamlit_timeline import timeline
import os
import json
import yaml
import cf
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import logging

st.set_page_config(page_title="Bands Timeline", layout="wide")


#------------------- SESSION STATE ------------------------------------------
if 'selected_bands_list' not in st.session_state:
    st.session_state.selected_bands_list = []

if 'action' not in st.session_state:
    st.session_state.action = 'search_band'
if 'five_artists' not in st.session_state:
    st.session_state.five_artists=[]

st.write('st.session_state.action:', st.session_state.action )


# Remove from bands_list y timeline_dict
if st.session_state.selected_bands_list!=[]:
    st.caption("Remove from Timeline")
    with st.container(border=True):
        for band in st.session_state.selected_bands_list:
            st.button(band, type="tertiary", key=f'{band}_remove')
            if st.session_state[f'{band}_remove']:
                st.session_state.selected_bands_list.remove(band)
                st.session_state.action=='search_band'
                st.rerun()

# Buscar bandas
st.write('Entro en buscar bandas')
if st.session_state.action=='search_band':
    st.text('Search Band')
    search = st.text_input("Search Band",placeholder='Type here', label_visibility="collapsed")
    if search:
        st.write('Entro en search')
        if search == 'a': st.session_state.five_artists = ['a1','a2','a3','a4','a5']
        if search == 'b': st.session_state.five_artists = ['b1','b2','b3','b4','b5']
        st.session_state.action=='select_band'
        st.rerun()

# Seleccionar banda y obtener discos
if st.session_state.action=='select_band':
    selected_band = st.selectbox("Select from this list", st.session_state.five_artists, index=None)
    if selected_band!='':
        st.session_state.selected_bands_list.append(selected_band)
        st.write(f'Busco info de todos los discos de {selected_band}')
        st.write(f'y la añado al diccionario de timeline')
        st.rerun()   
    
st.write(f'Lista de bandas: {st.session_state.selected_bands_list}')