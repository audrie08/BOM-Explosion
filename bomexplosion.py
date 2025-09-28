import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from oauth2client.service_account import ServiceAccountCredentials
from streamlit_gsheets import GSheetsConnection
from streamlit_option_menu import option_menu
from google.oauth2.service_account import Credentials
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from streamlit_option_menu import option_menu
import base64
from io import BytesIO
from PIL import Image
import warnings
import json
import pytz
import numpy as np
import time
from google.oauth2 import service_account
from googleapiclient.discovery import build
warnings.filterwarnings('ignore')

st.set_page_config(page_title="BOM Explosion", page_icon="🧪", layout="wide")
st.title("🧪 BOM Explosion")

@st.cache_resource
def load_credentials():
    credentials_dict = {
        "type": st.secrets["google_credentials"]["type"],
        "project_id": st.secrets["google_credentials"]["project_id"],
        "private_key_id": st.secrets["google_credentials"]["private_key_id"],
        "private_key": st.secrets["google_credentials"]["private_key"].replace('\\n', '\n'),
        "client_email": st.secrets["google_credentials"]["client_email"],
        "client_id": st.secrets["google_credentials"]["client_id"],
        "auth_uri": st.secrets["google_credentials"]["auth_uri"],
        "token_uri": st.secrets["google_credentials"]["token_uri"],
        "auth_provider_x509_cert_url": st.secrets["google_credentials"]["auth_provider_x509_cert_url"],
        "client_x509_cert_url": st.secrets["google_credentials"]["client_x509_cert_url"]
    }
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    return Credentials.from_service_account_info(credentials_dict, scopes=scopes)

@st.cache_data(ttl=60)
def load_cold_kitchen_data():
    gc = gspread.authorize(load_credentials())
    sh = gc.open_by_key("1K7PTd9Y3X5j-5N_knPyZm8yxDEgxXFkVZOwnfQf98hQ")
    worksheet = sh.get_worksheet(2)  # Sheet index 2 for Cold Kitchen
    data = worksheet.get_all_values()
    return pd.DataFrame(data)

def get_subrecipes(df):
    subrecipes = []
    for idx, row in df.iterrows():
        if str(row.iloc[0]).strip().upper() == "INTERNAL NAME":
            name = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else f"Recipe_{idx}"
            subrecipes.append({'name': name, 'row': idx})
    return subrecipes

def extract_bom_data(df, start_row):
    section = df.iloc[start_row:start_row+24]
    
    # Basic info
    internal_name = str(section.iloc[0, 1]) if pd.notna(section.iloc[0, 1]) else ""
    sku_code = str(section.iloc[1, 1]) if pd.notna(section.iloc[1, 1]) else ""
    
    # Get ingredients from columns H, I, J
    ingredients = []
    for idx, row in section.iterrows():
        if len(row) > 9:
            qty = str(row.iloc[7]).strip() if pd.notna(row.iloc[7]) else ""
            batch_qty = str(row.iloc[8]).strip() if pd.notna(row.iloc[8]) else ""
            ingredient_name = str(row.iloc[9]).strip() if pd.notna(row.iloc[9]) else ""
            
            if qty and batch_qty and ingredient_name and ingredient_name != "INTERNAL NAME":
                try:
                    float(qty)
                    ingredients.append(f"{qty}\t{batch_qty}\t{ingredient_name}")
                except:
                    pass
    
    # Format output
    output = f"""INTERNAL NAME: {internal_name}
SKU CODE: {sku_code}

INGREDIENTS:
QTY\tBATCH QTY\tINTERNAL NAME
{chr(10).join(ingredients)}"""
    
    return output

# Main app
station = st.selectbox("Station:", ["Cold Kitchen", "Fabrication Poultry", "Fabrication Meats", "Pastry", "Hot Kitchen"])

if station == "Cold Kitchen":
    df = load_cold_kitchen_data()
    subrecipes = get_subrecipes(df)
    
    if subrecipes:
        recipe_names = [r['name'] for r in subrecipes]
        selected_recipe = st.selectbox("Select Subrecipe:", recipe_names)
        
        if selected_recipe:
            selected_row = next(r['row'] for r in subrecipes if r['name'] == selected_recipe)
            bom_output = extract_bom_data(df, selected_row)
            
            st.text_area("BOM Output:", bom_output, height=400)
            
            st.download_button(
                "Download BOM",
                bom_output,
                f"{selected_recipe}_BOM.txt"
            )
else:
    st.info(f"{station} not yet implemented")
