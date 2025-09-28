import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import warnings

warnings.filterwarnings('ignore')

st.set_page_config(page_title="BOM Explosion", page_icon="🧪", layout="wide")
st.title("🧪 BOM Explosion")

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
        worksheet = sh.get_worksheet(2)  # Sheet index 2 for Cold Kitchen
        data = worksheet.get_all_values()
        df = pd.DataFrame(data)
        st.success(f"Loaded {len(df)} rows from Cold Kitchen sheet")
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

def extract_bom_data(df, start_row):
    section = df.iloc[start_row:start_row+24]
    
    # Basic info
    internal_name = str(section.iloc[0, 1]) if pd.notna(section.iloc[0, 1]) else ""
    sku_code = str(section.iloc[1, 1]) if pd.notna(section.iloc[1, 1]) else ""
    
    # 1. Specifications DataFrame
    specs_data = []
    for idx, row in section.iterrows():
        col_a = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
        col_b = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ""
        col_c = str(row.iloc[2]).strip() if pd.notna(row.iloc[2]) else ""
        
        if col_a in ["Standard Batch Size", "Theoretical Total", "Final Net Output (yielded weight)", 
                    "Processing Loss", "Processing Loss %", "Total Production Time"]:
            specs_data.append({"SPECIFICATIONS": col_a, "Value": col_b, "UOM": col_c})
    
    specs_df = pd.DataFrame(specs_data)
    
    # 2. Recipe Yield DataFrame
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
    
    # 3. Ingredients DataFrame
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
    
    # 4. Labor Productivity DataFrame
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
        "labor_productivity": labor_df
    }

# Main app
station = st.selectbox("Station:", ["Cold Kitchen", "Fabrication Poultry", "Fabrication Meats", "Pastry", "Hot Kitchen"])

if station == "Cold Kitchen":
    with st.spinner("Loading Cold Kitchen data..."):
        df = load_cold_kitchen_data()
    
    if df is not None:
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
            st.warning("No subrecipes found in the data")
    else:
        st.error("Failed to load Cold Kitchen data")
else:
    st.info(f"{station} not yet implemented")
