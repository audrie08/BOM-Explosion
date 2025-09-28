import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import warnings
import io

warnings.filterwarnings('ignore')

st.set_page_config(page_title="BOM Explosion", layout="wide")

# Custom CSS for exact UI design
st.markdown("""
<style>
    /* Hide Streamlit default elements */
    .main > div {
        padding-top: 0rem;
    }
    
    .block-container {
        padding-top: 0rem;
        padding-bottom: 2rem;
        margin-top: 0rem;
    }
    
    /* Hide default title */
    h1[data-testid="stHeader"] {
        display: none;
    }
    
    .stApp > header {
        display: none;
    }
    
    /* Custom navigation bar styling */
    .top-nav {
        padding: 15px 30px !important;
        margin: -10px -1rem 0 -1rem !important;
        position: sticky !important;
        top: 0 !important;
        z-index: 999 !important;
    }
    
    /* BOM Explosion title styling */
    .nav-title {
        color: #2C2C2C !important;
        font-size: 2.5rem !important;
        font-weight: 700 !important;
        margin: 0 !important;
        letter-spacing: 0.5px !important;
        display: flex !important;
        align-items: center !important;
        height: 10px !important;
        padding-top: 55px !important;
    }
    
    /* Force dark background on nav columns */
    .top-nav .stColumn {
        background-color: #2C2C2C !important;
        display: flex !important;
        align-items: center !important;
    }
    
    .top-nav .stColumn > div {
        background-color: #2C2C2C !important;
        display: flex !important;
        align-items: center !important;
        width: 100% !important;
    }
    
    /* Style selectboxes in nav */
    .nav-selectors .stSelectbox {
        margin-bottom: 0 !important;
        display: flex !important;
        align-items: center !important;
        height: 10px !important;
        padding-top: 55px !important;
    }
    
    .nav-selectors .stSelectbox > label {
        display: none !important;
    }
    
    .nav-selectors .stSelectbox > div {
        margin-bottom: 0 !important;
        display: flex !important;
        align-items: center !important;
        height: 10px !important;
        padding-top: 55px !important;
    }
    
    .nav-selectors .stSelectbox > div > div {
        background-color: #3A3A3A !important;
        border: 2px solid #F4C430 !important;
        border-radius: 8px !important;
        color: white !important;
        min-width: 200px !important;
        font-weight: 500 !important;
        height: 75px !important;
        display: flex !important;
        align-items: center !important;
        height: 10px !important;
        padding-top: 55px !important;
    }
    
    .nav-selectors .stSelectbox > div > div > div {
        color: white !important;
        display: flex !important;
        align-items: center !important;
        height: 10px !important;
        padding-top: 55px !important;
    }
    
    /* Custom breadcrumb */
    .breadcrumb {
        background-color: #F5F5F5;
        padding: 15px 30px;
        margin: 0 -1rem 30px -1rem;
        font-size: 20px;
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
    
    /* Page title styling - override Streamlit hiding */
    .page-title {
        font-size: 2.5rem !important;
        color: #2C2C2C !important;
        font-weight: 700 !important;
        margin: 0 !important;
        display: block !important;
        visibility: visible !important;
        height: 10px !important;
        padding-top: 10px !important;
    }
    
    .sku-badge {
        background: #F4C430;
        color: #2C2C2C;
        padding: 12px 24px;
        border-radius: 25px;
        font-weight: 700;
        font-size: 20px;
    }
    
    /* Section containers */
    .section-container {
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
        text-transform: uppercase;
    }
    
    .section-content {
        padding: 0;
    }
    
    /* Custom dataframe styling */
    .stDataFrame {
        border: none !important;
    }
    
    .stDataFrame > div {
        border: none !important;
    }
    
    .stDataFrame table {
        border: none !important;
        font-family: 'Inter', sans-serif !important;
        width: 100% !important;
    }
    
    .stDataFrame thead th {
        background-color: #F5F5F5 !important;
        color: #2C2C2C !important;
        font-weight: 600 !important;
        padding: 15px 20px !important;
        border: none !important;
        border-bottom: 2px solid #E0E0E0 !important;
        font-size: 14px !important;
        letter-spacing: 0.3px !important;
        text-transform: uppercase !important;
    }
    
    .stDataFrame tbody td {
        padding: 15px 20px !important;
        border: none !important;
        border-bottom: 1px solid #E0E0E0 !important;
        font-size: 14px !important;
        color: #333 !important;
    }
    
    /* Left align QTY column */
    .stDataFrame tbody td:first-child {
        text-align: left !important;
    }
    
    .stDataFrame tbody tr:nth-child(even) {
        background-color: #FAFAFA !important;
    }
    
    .stDataFrame tbody tr:hover {
        background-color: #FFF9E6 !important;
    }
    
    /* Pack sizes styling */
    .pack-sizes-container {
        padding: 20px 25px;
        display: flex;
        gap: 15px;
        flex-wrap: wrap;
    }
    
    /* Simple checkbox styling - remove containers */
    .stCheckbox {
        margin-bottom: 0 !important;
    }
    
    .stCheckbox > label {
        font-weight: 500 !important;
        color: #2C2C2C !important;
        font-size: 14px !important;
        display: flex !important;
        align-items: center !important;
        gap: 8px !important;
        background: transparent !important;
        padding: 8px 0 !important;
        border: none !important;
        border-radius: 0 !important;
        transition: none !important;
        margin-bottom: 0 !important;
    }
    
    .stCheckbox > label:hover {
        background: transparent !important;
        border: none !important;
    }
    
    .stCheckbox > label > div[data-testid="stCheckbox"] {
        margin-right: 8px !important;
    }
    
    .stCheckbox > label > div[data-testid="stCheckbox"] > div {
        border-color: #D0D0D0 !important;
        border-width: 2px !important;
    }
    
    .stCheckbox > label > div[data-testid="stCheckbox"] > div[data-checked="true"] {
        background-color: #F4C430 !important;
        border-color: #F4C430 !important;
    }
    
    /* Hide all default streamlit titles and headers */
    h1, h2, h3 {
        display: none !important;
    }
    
    /* Pack sizes section title */
    .pack-sizes-title {
        color: #2C2C2C !important;
        font-weight: 700 !important;
        font-size: 1.2rem !important;
        margin: 0px 0 15px 0 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
        display: block !important;
        visibility: visible !important;
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
    final_net_output = ""
    
    for idx, row in section.iterrows():
        col_a = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
        col_b = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ""
        col_c = str(row.iloc[2]).strip() if pd.notna(row.iloc[2]) else ""
        
        if col_a in ["Standard Batch Size", "Total Production Time"]:
            specs_data.append({"SPECIFICATIONS": col_a, "Value": col_b, "UOM": col_c})
        elif col_a == "Final Net Output (yielded weight)":
            final_net_output = col_b
        
        elif col_a == "Pack Size" or (col_a == "" and col_b in ["TRUE", "FALSE"] and col_c in ["500g", "1000g", "2000g", "5000g"]):
            if col_b in ["TRUE", "FALSE"] and col_c:
                pack_sizes.append({
                    "size": col_c,
                    "available": col_b == "TRUE"
                })
    
    # Get base recipe yield and batches
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
    
    # Get ingredients data
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
        "base_specs": specs_data,
        "recipe_yield": recipe_yield,
        "recipe_batches": recipe_batches,
        "final_net_output": final_net_output,
        "ingredients": ingredients_df,
        "labor_productivity": labor_df,
        "pack_sizes": pack_sizes
    }

def calculate_specifications(recipe_yield, final_net_output):
    """Calculate dynamic specifications based on recipe yield and final net output from sheet"""
    try:
        theoretical_total = float(recipe_yield) if recipe_yield else 0
        final_output = float(final_net_output) if final_net_output else 0
        
        processing_loss = theoretical_total - final_output
        processing_loss_pct = (processing_loss / theoretical_total * 100) if theoretical_total > 0 else 0
        
        return theoretical_total, final_output, processing_loss, processing_loss_pct
    except:
        return 0, 0, 0, 0

def calculate_ingredients_with_batches(ingredients_df, num_batches):
    """Multiply ingredient quantities by number of batches"""
    if ingredients_df.empty:
        return ingredients_df
    
    try:
        batches = float(num_batches) if num_batches else 1
        updated_df = ingredients_df.copy()
        
        # Multiply QTY column by number of batches and rename to QTY
        updated_df['QTY'] = updated_df['QTY'].astype(float) * batches
        updated_df['QTY'] = updated_df['QTY'].round(3)
        
        # Keep original column order
        updated_df = updated_df[['QTY', 'BATCH QTY', 'INTERNAL NAME']]
        
        return updated_df
    except:
        return ingredients_df

# Load data first to get recipe names
station = "Cold Kitchen"  # Set default
selected_recipe = None

if station == "Cold Kitchen":
    df = load_cold_kitchen_data()
    if df is not None:
        subrecipes = get_subrecipes(df)
        recipe_names = [r['name'] for r in subrecipes] if subrecipes else []
    else:
        recipe_names = []
else:
    recipe_names = []

st.divider()

# Create navigation bar using columns
st.markdown('<div class="top-nav">', unsafe_allow_html=True)

# Navigation row: Title + Filters
nav_col1, nav_col2, nav_col3 = st.columns([3, 2, 2])

with nav_col1:
    st.markdown('<div class="nav-title">BOM Explosion</div>', unsafe_allow_html=True)

with nav_col2:
    st.markdown('<div class="nav-selectors">', unsafe_allow_html=True)
    station = st.selectbox("Station", ["Cold Kitchen", "Fabrication Poultry", "Fabrication Meats", "Pastry", "Hot Kitchen"], key="station_selector")
    st.markdown('</div>', unsafe_allow_html=True)

with nav_col3:
    st.markdown('<div class="nav-selectors">', unsafe_allow_html=True)
    if recipe_names:
        selected_recipe = st.selectbox("Recipe", recipe_names, key="subrecipe_selector")
    else:
        selected_recipe = st.selectbox("Recipe", ["No recipes available"], key="subrecipe_selector_empty")
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# Breadcrumb navigation
if selected_recipe and selected_recipe != "No recipes available":
    st.markdown(f'''
    <div class="breadcrumb">
        <a href="#">Home</a> / <a href="#">{station}</a> / {selected_recipe}
    </div>
    ''', unsafe_allow_html=True)

# Main content
if station == "Cold Kitchen" and selected_recipe and selected_recipe != "No recipes available" and df is not None:
    selected_row = next(r['row'] for r in subrecipes if r['name'] == selected_recipe)
    bom_data = extract_bom_data(df, selected_row)
    
    # Page header using columns: Recipe Name + SKU
    st.markdown('<div style="margin: 30px 0 20px 0;">', unsafe_allow_html=True)
    
    header_col1, header_col2 = st.columns([3, 1])
    
    with header_col1:
        st.markdown(f'<h1 class="page-title">{selected_recipe}</h1>', unsafe_allow_html=True)
    
    with header_col2:
        st.markdown(f'<div style="display: flex; justify-content: flex-end; align-items: center; height: 80px;"><div class="sku-badge">{bom_data["sku_code"]}</div></div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Add the yellow line separator
    st.markdown('<div style="border-bottom: 3px solid #F4C430; margin: 0 0 30px 0;"></div>', unsafe_allow_html=True)
    
    # Specifications section
    st.markdown('''
    <div class="section-container">
        <div class="section-header">SPECIFICATIONS</div>
        <div class="section-content">
    ''', unsafe_allow_html=True)
    
    # Show specifications first (will be updated later with calculated values)
    specs_placeholder = st.empty()
    
    st.markdown('</div></div>', unsafe_allow_html=True)
    
    # Recipe Information section (now interactive and below specifications)
    st.markdown('''
    <div class="section-container">
        <div class="section-header">RECIPE INFORMATION</div>
        <div class="section-content" style="padding: 20px;">
    ''', unsafe_allow_html=True)
    
    # Interactive recipe inputs
    recipe_col1, recipe_col2 = st.columns([2, 2])
    
    with recipe_col1:
        st.markdown("**Recipe Yield (Unportioned):**")
        st.text(f"{bom_data['recipe_yield']} L")
    
    with recipe_col2:
        st.markdown("**Recipe (# of Batches):**")
        num_batches = st.number_input("", min_value=1, value=int(float(bom_data['recipe_batches'])) if bom_data['recipe_batches'] else 1, step=1, key="batches_input")
    
    st.markdown('</div></div>', unsafe_allow_html=True)
    
    # Calculate dynamic specifications
    theoretical_total, final_net_output, processing_loss, processing_loss_pct = calculate_specifications(
        bom_data['recipe_yield'], bom_data['final_net_output']
    )
    
    # Build dynamic specifications dataframe
    dynamic_specs = []
    for spec in bom_data['base_specs']:
        dynamic_specs.append(spec)
    
    # Add calculated specifications
    dynamic_specs.extend([
        {"SPECIFICATIONS": "Theoretical Total", "Value": f"{theoretical_total:.2f}", "UOM": "L"},
        {"SPECIFICATIONS": "Final Net Output (yielded weight)", "Value": f"{final_net_output:.2f}", "UOM": "L"},
        {"SPECIFICATIONS": "Processing Loss", "Value": f"{processing_loss:.2f}", "UOM": "L"},
        {"SPECIFICATIONS": "Processing Loss %", "Value": f"{processing_loss_pct:.2f}", "UOM": "%"}
    ])
    
    specs_df = pd.DataFrame(dynamic_specs)
    
    # Update specifications with calculated values
    with specs_placeholder:
        st.dataframe(specs_df, use_container_width=True, hide_index=True)
    
    # Pack sizes section (without container - simple title and checkboxes)
    if bom_data['pack_sizes']:
        st.markdown('<h3 class="pack-sizes-title">PACK SIZES</h3>', unsafe_allow_html=True)
        
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
    
    # Ingredients section (with calculated quantities)
    calculated_ingredients = calculate_ingredients_with_batches(bom_data['ingredients'], num_batches)
    
    st.markdown('''
    <div class="section-container">
        <div class="section-header">INGREDIENTS</div>
        <div class="section-content">
    ''', unsafe_allow_html=True)
    
    st.dataframe(calculated_ingredients, use_container_width=True, hide_index=True)
    
    st.markdown('</div></div>', unsafe_allow_html=True)
    
    # Labor productivity section
    st.markdown('''
    <div class="section-container">
        <div class="section-header">LABOR PRODUCTIVITY</div>
        <div class="section-content">
    ''', unsafe_allow_html=True)
    
    st.dataframe(bom_data['labor_productivity'], use_container_width=True, hide_index=True)
    
    st.markdown('</div></div>', unsafe_allow_html=True)

elif station != "Cold Kitchen":
    st.info(f"{station} not yet implemented")
elif not selected_recipe or selected_recipe == "No recipes available":
    st.warning("No subrecipes found in the data")
