import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import warnings
import io

warnings.filterwarnings('ignore')

st.set_page_config(page_title="BOM Explosion", layout="wide")

# Custom CSS for Option 2 design
st.markdown("""
<style>
    /* Hide Streamlit default elements */
    .main > div {
        padding-top: 0rem;
    }
    
    /* Custom navigation bar */
    .nav-bar {
        background-color: #2C2C2C;
        padding: 20px 30px;
        display: flex;
        align-items: center;
        gap: 30px;
        margin: -1rem -1rem 0 -1rem;
        border-bottom: 3px solid #F4C430;
    }
    
    .nav-brand {
        color: #F4C430;
        font-size: 1.8rem;
        font-weight: 700;
        margin: 0;
    }
    
    .nav-controls {
        display: flex;
        gap: 20px;
        align-items: center;
        margin-left: auto;
    }
    
    /* Custom breadcrumb */
    .breadcrumb {
        background-color: #F5F5F5;
        padding: 15px 30px;
        margin: 0 -1rem 20px -1rem;
        font-size: 14px;
        color: #666;
        border-bottom: 1px solid #E0E0E0;
    }
    
    .breadcrumb a {
        color: #F4C430;
        text-decoration: none;
        font-weight: 500;
    }
    
    .breadcrumb a:hover {
        text-decoration: underline;
    }
    
    /* Content header */
    .content-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 30px;
        padding-bottom: 15px;
        border-bottom: 3px solid #F4C430;
    }
    
    .content-title {
        font-size: 2.5rem;
        color: #2C2C2C;
        font-weight: 700;
        margin: 0;
    }
    
    .sku-badge {
        background: #F4C430;
        color: #2C2C2C;
        padding: 12px 24px;
        border-radius: 25px;
        font-weight: 700;
        font-size: 16px;
        border: none;
    }
    
    /* Section styling */
    .bom-section {
        background: white;
        border-radius: 8px;
        margin-bottom: 25px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        overflow: hidden;
    }
    
    .section-header {
        background: #F4C430;
        color: #2C2C2C;
        padding: 18px 25px;
        font-weight: 700;
        font-size: 1.2rem;
        margin: 0;
        letter-spacing: 0.5px;
    }
    
    .section-content {
        padding: 25px;
    }
    
    /* Custom table styling */
    .dataframe {
        border: none !important;
        font-family: 'Inter', sans-serif !important;
    }
    
    .dataframe thead th {
        background-color: #F5F5F5 !important;
        color: #2C2C2C !important;
        font-weight: 600 !important;
        padding: 15px 12px !important;
        border-bottom: 2px solid #E0E0E0 !important;
        border-top: none !important;
        border-left: none !important;
        border-right: none !important;
        font-size: 14px !important;
        letter-spacing: 0.3px !important;
    }
    
    .dataframe tbody td {
        padding: 15px 12px !important;
        border-bottom: 1px solid #E0E0E0 !important;
        border-top: none !important;
        border-left: none !important;
        border-right: none !important;
        font-size: 14px !important;
        color: #333 !important;
    }
    
    .dataframe tbody tr:nth-child(even) {
        background-color: #FAFAFA !important;
    }
    
    .dataframe tbody tr:hover {
        background-color: #FFF9E6 !important;
    }
    
    /* Pack sizes styling */
    .pack-sizes {
        display: flex;
        gap: 15px;
        flex-wrap: wrap;
        padding: 20px 0;
    }
    
    .pack-size-item {
        display: flex;
        align-items: center;
        gap: 10px;
        background: #F5F5F5;
        padding: 12px 18px;
        border-radius: 8px;
        border: 2px solid #E0E0E0;
        transition: all 0.3s ease;
        font-weight: 500;
    }
    
    .pack-size-item:hover {
        border-color: #F4C430;
        background: #FFFDF5;
    }
    
    /* Hide Streamlit selectbox styling */
    .stSelectbox > div > div {
        background-color: #3A3A3A;
        border: 2px solid #F4C430;
        border-radius: 8px;
        color: white;
    }
    
    .stSelectbox > div > div > div {
        color: white;
        font-weight: 500;
    }
    
    /* Hide default title */
    h1 {
        display: none;
    }
    
    /* Custom spacing */
    .block-container {
        padding-top: 0rem;
        padding-bottom: 2rem;
    }
    
    /* Checkbox styling */
    .stCheckbox > label {
        font-weight: 500;
        color: #2C2C2C;
    }
    
    .stCheckbox > label > div {
        border-color: #F4C430 !important;
    }
    
    .stCheckbox > label > div[data-checked="true"] {
        background-color: #F4C430 !important;
        border-color: #F4C430 !important;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def load_credentials():
    try:
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
    except Exception as e:
        st.error(f"Error loading credentials: {e}")
        return None

@st.cache_data(ttl=60)
def load_cold_kitchen_data():
    try:
        credentials = load_credentials()
        if not credentials:
            return None
        
        gc = gspread.authorize(credentials)
        sh = gc.open_by_key("17jeWWOaREFg6QMqDpQX-T3LYsETR7F4iZvWS5lC0I3w")
        worksheet = sh.get_worksheet(2)
        data = worksheet.get_all_values()
        df = pd.DataFrame(data)
        return df
    except Exception as e:
        st.error(f"Error loading Cold Kitchen data: {e}")
        return None

def get_subrecipes(df):
    subrecipes = []
    for idx, row in df.iterrows():
        col_a_value = str(row.iloc[0]).strip().upper()
        if "INTERNAL NAME" in col_a_value:
            name = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else f"Recipe_{idx}"
            subrecipes.append({'name': name, 'row': idx})
    return subrecipes

def update_pack_size_in_sheet(recipe_row, pack_size, new_state):
    try:
        credentials = load_credentials()
        if not credentials:
            return False
        
        gc = gspread.authorize(credentials)
        sh = gc.open_by_key("17jeWWOaREFg6QMqDpQX-T3LYsETR7F4iZvWS5lC0I3w")
        worksheet = sh.get_worksheet(2)
        
        section_start = recipe_row + 1
        section_end = recipe_row + 24
        
        for row_idx in range(section_start, section_end):
            try:
                row_data = worksheet.row_values(row_idx)
                if len(row_data) >= 3:
                    col_c = row_data[2] if len(row_data) > 2 else ""
                    if col_c == pack_size:
                        worksheet.update_cell(row_idx, 2, "TRUE" if new_state else "FALSE")
                        return True
            except:
                continue
        
        return False
    except Exception as e:
        st.error(f"Error updating sheet: {e}")
        return False

def extract_bom_data(df, start_row):
    section = df.iloc[start_row:start_row+24]
    
    internal_name = str(section.iloc[0, 1]) if pd.notna(section.iloc[0, 1]) else ""
    sku_code = str(section.iloc[1, 1]) if pd.notna(section.iloc[1, 1]) else ""
    
    specs_data = []
    pack_sizes = []
    
    for idx, row in section.iterrows():
        col_a = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
        col_b = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ""
        col_c = str(row.iloc[2]).strip() if pd.notna(row.iloc[2]) else ""
        
        if col_a in ["Standard Batch Size", "Theoretical Total", "Final Net Output (yielded weight)", 
                    "Processing Loss", "Processing Loss %", "Total Production Time"]:
            specs_data.append({"SPECIFICATIONS": col_a, "Value": col_b, "UOM": col_c})
        
        elif col_a == "Pack Size" or (col_a == "" and col_b in ["TRUE", "FALSE"] and col_c in ["500g", "1000g", "2000g", "5000g"]):
            if col_b in ["TRUE", "FALSE"] and col_c:
                pack_sizes.append({
                    "size": col_c,
                    "available": col_b == "TRUE"
                })
    
    specs_df = pd.DataFrame(specs_data)
    
    recipe_yield = ""
    recipe_batches = ""
    for idx, row in section.iterrows():
        if len(row) > 6:
            col_f = str(row.iloc[5]).strip() if pd.notna(row.iloc[5]) else ""
            col_g = str(row.iloc[6]).strip() if pd.notna(row.iloc[6]) else ""
            if col_f and col_g and col_f != "RECIPE YIELD (Unportioned)":
                try:
                    float(col_f)
                    recipe_yield = col_f
                    recipe_batches = col_g
                    break
                except:
                    pass
    
    recipe_df = pd.DataFrame([{
        "RECIPE YIELD (Unportioned)": recipe_yield,
        "RECIPE (# of Batches)": recipe_batches
    }])
    
    ingredients_data = []
    for idx, row in section.iterrows():
        if len(row) > 9:
            qty = str(row.iloc[7]).strip() if pd.notna(row.iloc[7]) else ""
            batch_qty = str(row.iloc[8]).strip() if pd.notna(row.iloc[8]) else ""
            ingredient_name = str(row.iloc[9]).strip() if pd.notna(row.iloc[9]) else ""
            
            if qty and batch_qty and ingredient_name and ingredient_name != "INTERNAL NAME":
                try:
                    float(qty)
                    ingredients_data.append({
                        "QTY": qty,
                        "BATCH QTY": batch_qty,
                        "INTERNAL NAME": ingredient_name
                    })
                except:
                    pass
    
    ingredients_df = pd.DataFrame(ingredients_data)
    
    labor_data = []
    labor_departments = ["Dry Product Scaling", "Vegetable Production", "Butchery", 
                        "Cold Kitchen", "Hot Kitchen", "Pastry Kitchen", "Packaging", "TOTAL"]
    
    for idx, row in section.iterrows():
        col_a = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
        if col_a in labor_departments:
            notes = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ""
            batch_production = str(row.iloc[2]).strip() if pd.notna(row.iloc[2]) else ""
            cost = str(row.iloc[3]).strip() if pd.notna(row.iloc[3]) else ""
            labor_data.append({
                "LABOR PRODUCTIVITY (minutes)": col_a,
                "Procedure Notes": notes,
                "Batch Production": batch_production,
                "Cost per 1 batch": cost
            })
    
    labor_df = pd.DataFrame(labor_data)
    
    return {
        "internal_name": internal_name,
        "sku_code": sku_code,
        "specifications": specs_df,
        "recipe_yield": recipe_df,
        "ingredients": ingredients_df,
        "labor_productivity": labor_df,
        "pack_sizes": pack_sizes
    }

# Create navigation bar
nav_col1, nav_col2, nav_col3 = st.columns([2, 1, 1])

with nav_col1:
    st.markdown('<div class="nav-bar"><h1 class="nav-brand">BOM Explosion</h1></div>', unsafe_allow_html=True)

with nav_col2:
    station = st.selectbox("", ["Cold Kitchen", "Fabrication Poultry", "Fabrication Meats", "Pastry", "Hot Kitchen"], key="station_selector")

# Load data and create subrecipe selector
if station == "Cold Kitchen":
    df = load_cold_kitchen_data()
    if df is not None:
        subrecipes = get_subrecipes(df)
        if subrecipes:
            recipe_names = [r['name'] for r in subrecipes]
            with nav_col3:
                selected_recipe = st.selectbox("", recipe_names, key="subrecipe_selector")
        else:
            selected_recipe = None
    else:
        selected_recipe = None
else:
    selected_recipe = None

# Breadcrumb navigation
if selected_recipe:
    st.markdown(f'''
    <div class="breadcrumb">
        <a href="#">Home</a> / <a href="#">{station}</a> / {selected_recipe}
    </div>
    ''', unsafe_allow_html=True)

# Main content
if station == "Cold Kitchen" and selected_recipe and df is not None:
    selected_row = next(r['row'] for r in subrecipes if r['name'] == selected_recipe)
    bom_data = extract_bom_data(df, selected_row)
    
    # Content header
    st.markdown(f'''
    <div class="content-header">
        <h1 class="content-title">{bom_data['internal_name']}</h1>
        <div class="sku-badge">{bom_data['sku_code']}</div>
    </div>
    ''', unsafe_allow_html=True)
    
    # Specifications section
    st.markdown('<div class="bom-section">', unsafe_allow_html=True)
    st.markdown('<h2 class="section-header">SPECIFICATIONS</h2>', unsafe_allow_html=True)
    st.markdown('<div class="section-content">', unsafe_allow_html=True)
    st.dataframe(bom_data['specifications'], use_container_width=True, hide_index=True)
    st.markdown('</div></div>', unsafe_allow_html=True)
    
    # Pack sizes section
    if bom_data['pack_sizes']:
        st.markdown('<div class="bom-section">', unsafe_allow_html=True)
        st.markdown('<h2 class="section-header">PACK SIZES</h2>', unsafe_allow_html=True)
        st.markdown('<div class="section-content">', unsafe_allow_html=True)
        
        pack_cols = st.columns(len(bom_data['pack_sizes']))
        for i, pack in enumerate(bom_data['pack_sizes']):
            with pack_cols[i]:
                checkbox_key = f"pack_{selected_recipe}_{pack['size']}_checkbox"
                new_state = st.checkbox(pack['size'], value=pack['available'], key=checkbox_key)
                
                if new_state != pack['available']:
                    with st.spinner(f"Updating {pack['size']}..."):
                        success = update_pack_size_in_sheet(selected_row, pack['size'], new_state)
                        if success:
                            st.success(f"{pack['size']} updated!")
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error(f"Failed to update {pack['size']}")
                            st.rerun()
        
        st.markdown('</div></div>', unsafe_allow_html=True)
    
    # Recipe information section
    st.markdown('<div class="bom-section">', unsafe_allow_html=True)
    st.markdown('<h2 class="section-header">RECIPE INFORMATION</h2>', unsafe_allow_html=True)
    st.markdown('<div class="section-content">', unsafe_allow_html=True)
    st.dataframe(bom_data['recipe_yield'], use_container_width=True, hide_index=True)
    st.markdown('</div></div>', unsafe_allow_html=True)
    
    # Ingredients section
    st.markdown('<div class="bom-section">', unsafe_allow_html=True)
    st.markdown('<h2 class="section-header">INGREDIENTS</h2>', unsafe_allow_html=True)
    st.markdown('<div class="section-content">', unsafe_allow_html=True)
    st.dataframe(bom_data['ingredients'], use_container_width=True, hide_index=True)
    st.markdown('</div></div>', unsafe_allow_html=True)
    
    # Labor productivity section
    st.markdown('<div class="bom-section">', unsafe_allow_html=True)
    st.markdown('<h2 class="section-header">LABOR PRODUCTIVITY</h2>', unsafe_allow_html=True)
    st.markdown('<div class="section-content">', unsafe_allow_html=True)
    st.dataframe(bom_data['labor_productivity'], use_container_width=True, hide_index=True)
    st.markdown('</div></div>', unsafe_allow_html=True)

elif station != "Cold Kitchen":
    st.info(f"{station} not yet implemented")
elif not selected_recipe:
    st.warning("No subrecipes found in the data")
