import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import warnings
import io

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
    """Update pack size state directly in Google Sheets"""
    try:
        credentials = load_credentials()
        if not credentials:
            return False
        
        gc = gspread.authorize(credentials)
        sh = gc.open_by_key("17jeWWOaREFg6QMqDpQX-T3LYsETR7F4iZvWS5lC0I3w")
        worksheet = sh.get_worksheet(2)
        
        # Find the pack size row within the recipe section
        section_start = recipe_row + 1
        section_end = recipe_row + 24
        
        for row_idx in range(section_start, section_end):
            try:
                row_data = worksheet.row_values(row_idx)
                if len(row_data) >= 3:
                    col_c = row_data[2] if len(row_data) > 2 else ""
                    if col_c == pack_size:
                        # Update column B (index 2 in 1-based)
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
    
    # Basic info
    internal_name = str(section.iloc[0, 1]) if pd.notna(section.iloc[0, 1]) else ""
    sku_code = str(section.iloc[1, 1]) if pd.notna(section.iloc[1, 1]) else ""
    
    # 1. Specifications DataFrame (without pack sizes)
    specs_data = []
    pack_sizes = []
    
    for idx, row in section.iterrows():
        col_a = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
        col_b = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ""
        col_c = str(row.iloc[2]).strip() if pd.notna(row.iloc[2]) else ""
        
        if col_a in ["Standard Batch Size", "Theoretical Total", "Final Net Output (yielded weight)", 
                    "Processing Loss", "Processing Loss %", "Total Production Time"]:
            specs_data.append({"SPECIFICATIONS": col_a, "Value": col_b, "UOM": col_c})
        
        # Extract pack sizes separately
        elif col_a == "Pack Size" or (col_a == "" and col_b in ["TRUE", "FALSE"] and col_c in ["500g", "1000g", "2000g", "5000g"]):
            if col_b in ["TRUE", "FALSE"] and col_c:
                pack_sizes.append({
                    "size": col_c,
                    "available": col_b == "TRUE"
                })
    
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
        "labor_productivity": labor_df,
        "pack_sizes": pack_sizes
    }

# Main app
station = st.selectbox("Station:", ["Cold Kitchen", "Fabrication Poultry", "Fabrication Meats", "Pastry", "Hot Kitchen"], key="station_selector")

if station == "Cold Kitchen":
    with st.spinner("Loading Cold Kitchen data..."):
        df = load_cold_kitchen_data()
    
    if df is not None:
        subrecipes = get_subrecipes(df)
        
        if subrecipes:
            recipe_names = [r['name'] for r in subrecipes]
            selected_recipe = st.selectbox("Select Subrecipe:", recipe_names, key="subrecipe_selector")
            
            if selected_recipe:
                selected_row = next(r['row'] for r in subrecipes if r['name'] == selected_recipe)
                bom_data = extract_bom_data(df, selected_row)
                
                # Display Basic Info
                st.markdown("### Basic Information")
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**INTERNAL NAME:** {bom_data['internal_name']}")
                with col2:
                    st.markdown(f"**SKU CODE:** {bom_data['sku_code']}")
                
                # Display Specifications
                st.markdown("### SPECIFICATIONS")
                st.dataframe(bom_data['specifications'], use_container_width=True, hide_index=True)
                
                # Pack Sizes Section that persists to Google Sheets
                if bom_data['pack_sizes']:
                    st.markdown("### PACK SIZES")
                    
                    # Create columns for pack sizes
                    pack_cols = st.columns(len(bom_data['pack_sizes']))
                    
                    for i, pack in enumerate(bom_data['pack_sizes']):
                        with pack_cols[i]:
                            # Create unique key for each checkbox
                            checkbox_key = f"pack_{selected_recipe}_{pack['size']}_checkbox"
                            
                            # Display checkbox with current state from sheet
                            new_state = st.checkbox(
                                pack['size'],
                                value=pack['available'],
                                key=checkbox_key
                            )
                            
                            # If state changed, update the Google Sheet
                            if new_state != pack['available']:
                                with st.spinner(f"Updating {pack['size']}..."):
                                    success = update_pack_size_in_sheet(selected_row, pack['size'], new_state)
                                    if success:
                                        st.success(f"{pack['size']} updated!")
                                        # Clear cache to reload fresh data
                                        st.cache_data.clear()
                                        st.rerun()
                                    else:
                                        st.error(f"Failed to update {pack['size']}")
                                        st.rerun()
                
                # Display Recipe Yield
                st.markdown("### RECIPE INFORMATION")
                st.dataframe(bom_data['recipe_yield'], use_container_width=True, hide_index=True)
                
                # Display Ingredients
                st.markdown("### INGREDIENTS")
                st.dataframe(bom_data['ingredients'], use_container_width=True, hide_index=True)
                
                # Display Labor Productivity
                st.markdown("### LABOR PRODUCTIVITY")
                st.dataframe(bom_data['labor_productivity'], use_container_width=True, hide_index=True)
        else:
            st.warning("No subrecipes found in the data")
    else:
        st.error("Failed to load Cold Kitchen data")
else:
    st.info(f"{station} not yet implemented")
