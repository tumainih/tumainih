# app.py
import streamlit as st
import pandas as pd
import os
from datetime import datetime
from email.mime.text import MIMEText
import smtplib

# -------------------------
# CONFIG
# -------------------------
DATA_CSV = "VYAKULA.csv"
USERS_CSV = "users.csv"
HISTORY_FOLDER = "goal_history"
os.makedirs(HISTORY_FOLDER, exist_ok=True)

# Prefer environment variables for credentials; fallback to hardcoded for compatibility
EMAIL_SENDER = os.environ.get("FR_ADMIN_EMAIL", "hoseatumaini12@gmail.com")
EMAIL_PASSWORD = os.environ.get("FR_ADMIN_PASSWORD", "3232Lhf$")

# -------------------------
# HELPER FUNCTIONS
# -------------------------
def ensure_csv(path, columns):
    if os.path.exists(path):
        df = pd.read_csv(path)
        for c in columns:
            if c not in df.columns:
                df[c] = pd.NA
        return df
    else:
        df = pd.DataFrame(columns=columns)
        df.to_csv(path, index=False)
        return df

def save_csv(df, path):
    df.to_csv(path, index=False)

def get_nutrient_value(row, col):
    if col in row and pd.notna(row[col]):
        try:
            return float(row[col])
        except:
            s = str(row[col])
            digits = ''.join(ch for ch in s if (ch.isdigit() or ch=='.' or ch=='-'))
            try:
                return float(digits) if digits else 0.0
            except:
                return 0.0
    return 0.0

def calculate_bmi(weight_kg, height_m):
    """Calculate BMI: weight(kg) / height(m)^2"""
    if height_m > 0:
        return round(weight_kg / (height_m ** 2), 2)
    return 0.0

def calculate_bmr(weight_kg, height_cm, age, sex):
    """Calculate Basal Metabolic Rate using Mifflin-St Jeor equation"""
    if sex.upper() == 'M':
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    else:  # Female
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161
    return round(bmr, 2)

def calculate_tdee(bmr, activity_level):
    """Calculate Total Daily Energy Expenditure based on activity level"""
    activity_factors = {
        "Sedentary": 1.2,
        "Light": 1.375,
        "Moderate": 1.55,
        "Very Active": 1.725,
        "Extra Active": 1.9
    }
    factor = activity_factors.get(activity_level, 1.55)
    return round(bmr * factor, 2)

def send_email(to, subject, body):
    try:
        msg = MIMEText(body)
        msg['Subject'] = subject
        # Use admin email as the visible sender
        msg['From'] = f"Admin <{EMAIL_SENDER}>"
        msg['Reply-To'] = EMAIL_SENDER
        msg['To'] = to
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        # allow `to` to be a list or a single email
        recipients = to if isinstance(to, (list, tuple)) else [to]
        server.sendmail(EMAIL_SENDER, recipients, msg.as_string())
        server.quit()
        return True
    except:
        return False

# -------------------------
# LOAD USERS
# -------------------------
user_cols = ["email", "name", "password"]
users_df = ensure_csv(USERS_CSV, user_cols)

# Ensure admin exists
admin_email = "hoseatumaini12@gmail.com"
admin_password = "3232Lhf$"
if admin_email not in users_df['email'].values:
    users_df = pd.concat([users_df, pd.DataFrame([{"email":admin_email,"name":"Admin","password":admin_password}])], ignore_index=True)
    save_csv(users_df, USERS_CSV)

# -------------------------
# LOAD FOOD DATASET
# -------------------------
try:
    food_df = pd.read_csv(DATA_CSV)
except Exception as e:
    st.error(f"Could not load dataset '{DATA_CSV}': {e}")
    st.stop()

if "code" not in food_df.columns or "Chakula" not in food_df.columns:
    st.error("Dataset MUST contain columns: 'code' and 'Chakula'.")
    st.stop()

# -------------------------
# FOOD GROUPS
# -------------------------
food_groups_sw = {
    "A1": "Nafaka na bidhaa za nafaka",
    "A2": "Vyakula vyenye asili ya nafaka",
    "B1": "Mizizi, Viazi na Ndizi",
    "B2": "Asili ya Mizizi, Viazi na Ndizi",
    "C1": "Mahabage, Njugu, Mbegu",
    "C2": "Asili ya maharage na mbegu",
    "D1": "Nyama, Kuku, Samaki",
    "D2": "Asili ya wanyama/ndege",
    "D3": "Maziwa na Bidhaa",
    "E": "Mafuta",
    "F1": "Matunda & Juisi",
    "F2": "Juisi za Matunda",
    "F3": "Mboga",
    "F4": "Asili ya mboga"
}
sw_to_key = {v:k for k,v in food_groups_sw.items()}

# Food-specific color mapping (realistic food colors)
food_group_colors = {
    "A1": {"bg": "linear-gradient(135deg, #D4A574 0%, #C4915F 100%)", "emoji": "🌾", "name": "Nafaka"},  # Grains - brown
    "A2": {"bg": "linear-gradient(135deg, #E8D4B0 0%, #D4B896 100%)", "emoji": "🍞", "name": "Bidhaa za Nafaka"},  # Bread - wheat
    "B1": {"bg": "linear-gradient(135deg, #DC7633 0%, #C45F1B 100%)", "emoji": "🥔", "name": "Mizizi/Viazi"},  # Potatoes - orange-brown
    "B2": {"bg": "linear-gradient(135deg, #E59866 0%, #D4764D 100%)", "emoji": "🍠", "name": "Mizizi Asili"},  # Sweet potato - orange
    "C1": {"bg": "linear-gradient(135deg, #F39C12 0%, #E67E22 100%)", "emoji": "🌽", "name": "Mahabage"},  # Corn - yellow-orange
    "C2": {"bg": "linear-gradient(135deg, #AF601A 0%, #8B4513 100%)", "emoji": "🥜", "name": "Njugu"},  # Legumes - brown
    "D1": {"bg": "linear-gradient(135deg, #C13F34 0%, #A1332F 100%)", "emoji": "🥩", "name": "Nyama"},  # Meat - red-brown
    "D2": {"bg": "linear-gradient(135deg, #F5DEB3 0%, #D4A076 100%)", "emoji": "🍗", "name": "Kuku"},  # Chicken - light brown
    "D3": {"bg": "linear-gradient(135deg, #F0F8FF 0%, #E8F4F8 100%)", "emoji": "🥛", "name": "Maziwa"},  # Dairy - light blue-white
    "E": {"bg": "linear-gradient(135deg, #FFD700 0%, #FFA500 100%)", "emoji": "🧈", "name": "Mafuta"},  # Oils - golden-yellow
    "F1": {"bg": "linear-gradient(135deg, #FF6347 0%, #DC143C 100%)", "emoji": "🍎", "name": "Matunda Nyekundu"},  # Red fruits - red
    "F2": {"bg": "linear-gradient(135deg, #FFD700 0%, #FFA500 100%)", "emoji": "🍊", "name": "Matunda Machungwa"},  # Orange fruits
    "F3": {"bg": "linear-gradient(135deg, #228B22 0%, #008000 100%)", "emoji": "🥬", "name": "Mboga Zaidi"},  # Vegetables - green
    "F4": {"bg": "linear-gradient(135deg, #9370DB 0%, #8A2BE2 100%)", "emoji": "🍆", "name": "Mboga Nyingi"}  # Purple veggies
}

food_groups_ranges = {
    "A1": [(1,100)], "A2": [(501,550)], "B1": [(351,400)], "B2": [(951,1000)],
    "C1": [(151,200)], "C2": [(651,700)], "D1": [(201,250),(301,350)],
    "D2": [(551,600)], "D3": [(251,300)], "E": [(1101,1150)], "F1": [(101,150)],
    "F2": [(601,650)], "F3": [(401,450)], "F4": [(751,800)]
}

# -------------------------
# HEALTH GOALS
# -------------------------
goal_to_columns = {
    "Kudhibiti Kolesteroli": ["FASAT","FAMS","FAPU","CHOLE","FAT"],
    "Kudhibiti Sukari": ["CHOCDF","SUCS","FIB"],
    "Kupunguza Uzito": ["ENERGY_KC","PROCNT","FAT","CHOCDF","FIB"],
    "Kuongeza Misuli": ["PROCNT","A_PROTEI","MFP_PROT","LEU","ILE","LYS","VAL","ARG"],
    "Kuongeza Stamina": ["ENERGY_KC","PROCNT","FAT","CHOCDF","VIT B6","MG","K"],
    "Usagaji Bora": ["FIB","PHYTAC","NA","K","MG"],
    "Kuongeza Kinga": ["VITC","VITA","A_VITA","VITD","ZN","CU","FE","MFP_FE"],
    "Afya ya Mifupa": ["CA","P","MG","VITD"],
    "Afya ya Moyo": ["FASAT","FAMS","FAPU","NA","K","CHOLE","PROCNT"],
    "Afya ya Ubongo": ["FE","VIT B12","FOL","VIT B6","ILE","LEU","LYS","TYR","PHE","ENERGY_KC"]
}
health_goals = list(goal_to_columns.keys())

# -------------------------
# RECOMMENDATION FUNCTION
# -------------------------
def recommend(goal, selected_group_keys, top_n):
    cols_needed = goal_to_columns.get(goal,[])
    cols_exist = [c for c in cols_needed if c in food_df.columns]
    results={}
    for grp_key in selected_group_keys:
        temp_df=pd.DataFrame()
        for start,end in food_groups_ranges.get(grp_key,[]):
            temp_df=pd.concat([temp_df, food_df[(food_df["code"]>=start) & (food_df["code"]<=end)]], ignore_index=True)
        if temp_df.empty:
            results[grp_key]=pd.DataFrame(columns=["Chakula","score"])
            continue
        if cols_exist:
            temp_df[cols_exist] = temp_df[cols_exist].apply(pd.to_numeric, errors="coerce").fillna(0)
            temp_df["score"] = temp_df[cols_exist].sum(axis=1)
        else:
            temp_df["score"]=0
        ranked = temp_df.sort_values("score",ascending=False)["Chakula"].head(top_n)
        results[grp_key] = ranked.reset_index(drop=True)
    return results

# -------------------------
# STREAMLIT CONFIG
# -------------------------
st.set_page_config(page_title="Food Recommender System", page_icon="🍽️", layout="wide")
if "user" not in st.session_state:
    st.session_state["user"] = None
if "admin" not in st.session_state:
    st.session_state["admin"] = False
if "confirm_logout" not in st.session_state:
    st.session_state["confirm_logout"] = False

# -------------------------
# CSS STYLING - Food Themed with Greenish Colors
# -------------------------
st.markdown(
    """
    <style>
    body {background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);}
    .stApp {background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);}
    .stButton>button {
        background: linear-gradient(135deg, #2e7d32 0%, #43a047 100%);
        color: white;
        height: 3em;
        width: 100%;
        border-radius: 15px;
        border: none;
        font-weight: bold;
        box-shadow: 0 4px 12px rgba(46, 125, 50, 0.3);
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(46, 125, 50, 0.5);
    }
    .stTextInput>div>div>input, .stNumberInput>div>div>input {
        height: 2.5em;
        border-radius: 10px;
        border: 2px solid #2e7d32 !important;
        background-color: #f1f8e9 !important;
        padding: 8px !important;
    }
    .stSelectbox>div>div>div>select {
        height: 2.5em;
        border-radius: 10px;
        border: 2px solid #2e7d32 !important;
        background-color: #f1f8e9 !important;
    }
    .stTabs [data-baseweb="tab-list"] {
        background: linear-gradient(90deg, #2e7d32 0%, #43a047 100%);
        border-radius: 12px;
        padding: 5px;
    }
    .stTabs [data-baseweb="tab"] {
        color: white;
        font-weight: bold;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background: #e8f5e9;
        color: #2e7d32;
    }
    .stExpander {
        background: linear-gradient(135deg, #f1f8e9 0%, #e8f5e9 100%);
        border: 2px solid #43a047;
        border-radius: 10px;
    }
    .stWarning {
        background: linear-gradient(135deg, #fff8dc 0%, #ffeaa7 100%) !important;
        border-left: 5px solid #ff6f61;
    }
    .stSuccess {
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%) !important;
        border-left: 5px solid #28a745;
    }
    .stInfo {
        background: linear-gradient(135deg, #d1ecf1 0%, #bee5eb 100%) !important;
        border-left: 5px solid #17a2b8;
    }
    .stError {
        background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%) !important;
        border-left: 5px solid #dc3545;
    }
    .stCheckbox>label {color: #2e7d32; font-weight: bold;}
    h1, h2, h3 {color: #1b5e20 !important; font-weight: bold;}
    .food-card{box-shadow:0 6px 16px rgba(46,125,50,0.25);border-radius:15px;padding:30px 10px;text-align:center;margin-bottom:10px;color:white;font-weight:bold;transition:opacity 0.6s ease, transform 0.6s ease;opacity:0;transform:translateY(12px);animation:fadeIn 0.6s forwards;}
    @keyframes fadeIn{from{opacity:0;transform:translateY(12px);}to{opacity:1;transform:translateY(0);}}
    .food-emoji{font-size:32px;margin-bottom:8px;display:block}
    </style>
    """, unsafe_allow_html=True
)

# -------------------------
# MENU
# -------------------------
menu_options = ["📊 Dasibodi","📜 Historia Yangu","📝 Maoni","🚪 Ondoka"]
menu_choice = st.sidebar.selectbox("📋 Menyu", menu_options)

# Logout confirmation UI (triggered from sidebar or menu)
if st.session_state.get("confirm_logout"):
    st.warning("⚠️ Una uhakika unataka kuondoka?")
    col_yes, col_no = st.columns(2)
    if col_yes.button("✅ Ndiyo, Ondoka", key="confirm_yes"):
        st.session_state['user'] = None
        st.session_state['confirm_logout'] = False
        st.success("✅ Umeonekana vizuri!")
        try:
            st.experimental_rerun()
        except Exception:
            pass
    if col_no.button("❌ Ghairi", key="confirm_no"):
        st.session_state['confirm_logout'] = False
        try:
            st.experimental_rerun()
        except Exception:
            pass

# If logged in, show basic account panel with logout
if st.session_state.get("user"):
    user_email = st.session_state.get("user")
    user_row = users_df[users_df['email'].str.strip().str.lower()==user_email.strip().lower()]
    user_name = user_row.iloc[0]['name'] if not user_row.empty else user_email
    with st.sidebar.expander("👤 Akaunti", expanded=True):
        st.markdown(f"👤 **{user_name}**\n\n📧 {user_email}")
        if st.button("🚪 Ondoka", key="sidebar_logout"):
            st.session_state['confirm_logout'] = True
            try:
                st.experimental_rerun()
            except Exception:
                pass

# Show login/register controls in the sidebar when no user is logged in
if not st.session_state["user"]:
    with st.sidebar.expander("🔑 Ingia / ✍️ Jisajili", expanded=True):
        tabs = st.tabs(["🔑 Ingia", "✍️ Jisajili"])
        # --- Login tab ---
        with tabs[0]:
            login_email = st.text_input("📧 Barua Pepe", key="login_email")
            login_password = st.text_input("🔐 Nenosiri", type="password", key="login_password")
            if st.button("🔑 Ingia", use_container_width=True, key="btn_login"):
                if not login_email or not login_password:
                    st.error("❌ Tafadhali ingiza barua pepe na nenosiri")
                else:
                    matched = users_df[(users_df['email'].str.strip().str.lower()==login_email.strip().lower()) & (users_df['password']==login_password)]
                    if not matched.empty:
                        st.session_state['user'] = login_email.strip().lower()
                        st.success("✅ Umeingia vizuri")
                        try:
                            st.experimental_rerun()
                        except Exception:
                            pass
                    else:
                        st.error("❌ Jina mtumiaji au nenosiri sio sahihi")

        # --- Register tab ---
        with tabs[1]:
            reg_name = st.text_input("👤 Jina", key="reg_name")
            reg_email = st.text_input("📧 Barua Pepe", key="reg_email")
            reg_password = st.text_input("🔐 Nenosiri", type="password", key="reg_password")
            if st.button("✍️ Jisajili", use_container_width=True, key="btn_register"):
                if not (reg_name and reg_email and reg_password):
                    st.error("❌ Tafadhali jaza sehemu zote")
                elif reg_email.strip().lower() in users_df['email'].str.lower().values:
                    st.warning("⚠️ Barua pepe hii tayari imesajiliwa")
                else:
                    new_row = pd.DataFrame([{"email": reg_email.strip().lower(), "name": reg_name.strip(), "password": reg_password}])
                    users_df = pd.concat([users_df, new_row], ignore_index=True)
                    save_csv(users_df, USERS_CSV)
                    # Auto-login after registration
                    st.session_state['user'] = reg_email.strip().lower()
                    st.success("✅ Umesajiliwa na kuingia vizuri")
                    try:
                        st.experimental_rerun()
                    except Exception:
                        pass

# -------------------------
# DASHBOARD
# -------------------------
if menu_choice=="📊 Dasibodi":
    if not st.session_state["user"]:
        st.markdown("""
        <div style='background: linear-gradient(135deg, rgba(46, 125, 50, 0.8), rgba(67, 160, 71, 0.8)), url("https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=800"); background-size: cover; background-position: center; padding: 40px; border-radius: 15px; text-align: center; margin-bottom: 20px; box-shadow: 0 8px 20px rgba(46, 125, 50, 0.3);'>
            <h1 style='color: white; margin: 0; text-shadow: 2px 2px 4px rgba(0,0,0,0.5);'>🥗 Karibu — Mgeni</h1>
            <p style='color: white; font-size: 18px; text-shadow: 1px 1px 3px rgba(0,0,0,0.5);'>Jaribu kama mgeni au jiandikishe ili uhifadhi mwanzo</p>
        </div>
        """, unsafe_allow_html=True)
        with st.expander("🥘 Jaribu kama Mgeni — Pata Mapendekezo", expanded=True):
            gw_weight = st.number_input("⚖️ Uzani (kg)",20.0,200.0,60.0, key="gw_weight")
            gw_height_m = st.number_input("📏 Urefu (m)",1.0,2.5,1.7, key="gw_height")
            gw_age = st.number_input("🎂 Umri",5,120,25, key="gw_age")
            gw_sex_sw = st.selectbox("🚻 Jinsia",["M - Mume","F - Mwanamke"], key="gw_sex")
            gw_sex = gw_sex_sw[0]
            gw_activity_sw = st.selectbox("🏃 Kiwango cha Shughuli",["Bila Harakati","Kidogo","Kwa Kawaida","Wengi","Wengi Sana"], key="gw_activity")
            activity_map = {"Bila Harakati": "Sedentary", "Kidogo": "Light", "Kwa Kawaida": "Moderate", "Wengi": "Very Active", "Wengi Sana": "Extra Active"}
            gw_activity = activity_map.get(gw_activity_sw, "Moderate")
            gw_goal = st.selectbox("🎯 Lengo la Afya", health_goals, key="gw_goal")
            gw_groups = st.multiselect("🥬 Vikundi vya Vyakula", list(food_groups_sw.values()), key="gw_groups")
            gw_top_n = st.number_input("🍽️ Idadi ya Vyakula",1,50,5, key="gw_topn")
            guest_email = st.text_input("📧 Barua Pepe (kwa maandishi ya matokeo - kosa kwa skip)", key="guest_email")
            send_by_email = st.checkbox("💌 Tuma matokeo kwa barua pepe", key="guest_send_email")
            if st.button("🥑 Pata Mapendekezo (Mgeni)", use_container_width=True):
                if not gw_groups:
                    st.warning("⚠️ Chagua angalau vikundi vya vyakula moja!")
                else:
                    selected_keys = [sw_to_key[s] for s in gw_groups if s in sw_to_key]
                    results = recommend(gw_goal, selected_keys, int(gw_top_n))
                    # Calculate metabolic metrics
                    bmi = calculate_bmi(gw_weight, gw_height_m)
                    bmr = calculate_bmr(gw_weight, round(gw_height_m*100), gw_age, gw_sex)
                    tdee = calculate_tdee(bmr, gw_activity)
                    new_rows=[]
                    for grp_key, table in results.items():
                        color_info = food_group_colors.get(grp_key, {"bg": "linear-gradient(135deg, #81c784 0%, #66bb6a 100%)", "emoji": "🥘"})
                        st.markdown(f"### {color_info['emoji']} {grp_key} - {food_groups_sw.get(grp_key,'')}")
                        col1,col2,col3 = st.columns(3)
                        for i, food_name in enumerate(table.tolist()):
                            col = [col1,col2,col3][i%3]
                            img_path = f"images/{food_name}.jpg"
                            delay = round((i % 9) * 0.12, 2)
                            if os.path.exists(img_path):
                                col.markdown(
                                    f"""
                                    <div class='food-card' style="background-image: url('{img_path}'); background-size: cover; background-position: center; animation-delay: {delay}s;">
                                        <div style='background:rgba(0,0,0,0.25);padding:18px;border-radius:12px;'>✨ {food_name} ✨</div>
                                    </div>
                                    """, unsafe_allow_html=True
                                )
                            else:
                                bg_gradient = color_info["bg"]
                                emoji = color_info["emoji"]
                                col.markdown(
                                    f"<div class='food-card' style='background: {bg_gradient}; animation-delay: {delay}s;'><span class=\"food-emoji\">{emoji}</span><div style=\"font-size:14px;margin-top:6px\">{food_name}</div></div>", unsafe_allow_html=True
                                )
                            row = food_df[food_df["Chakula"]==food_name].iloc[0]
                            protein = get_nutrient_value(row,"PROCNT")
                            fiber = get_nutrient_value(row,"FIB")
                            omega3 = get_nutrient_value(row,"FAPU") if "FAPU" in row else 0
                            vitc = get_nutrient_value(row,"VITC") if "VITC" in row else 0
                            calories = get_nutrient_value(row,"ENERGY_KC") if "ENERGY_KC" in row else 0
                            new_rows.append({
                                "email": guest_email if guest_email else "guest",
                                "age": gw_age,
                                "sex": gw_sex,
                                "bmi": bmi,
                                "bmr": bmr,
                                "tdee": tdee,
                                "food": food_name,
                                "rating": pd.NA,
                                "protein_g": protein,
                                "fiber_g": fiber,
                                "omega3_g": omega3,
                                "vitC_mg": vitc,
                                "calories_kc": calories,
                                "date": str(datetime.now())
                            })
                    if new_rows:
                        goal_file = os.path.join(HISTORY_FOLDER,f"{gw_goal.replace(' ','_')}.csv")
                        goal_df = ensure_csv(goal_file, new_rows[0].keys())
                        goal_df = pd.concat([goal_df,pd.DataFrame(new_rows)],ignore_index=True)
                        save_csv(goal_df,goal_file)
                        st.success(f"✅ Pendekezo la mgeni limesave kwa lengo: {gw_goal}")
                        if send_by_email and guest_email:
                            foods_text = "\n".join([r["food"] for r in new_rows])
                            if send_email(guest_email,f"Mapendekezo ya Vyakula ({gw_goal})",foods_text):
                                st.success("📧 Barua pepe imetumwa vizuri!")
                            else:
                                st.error("❌ Barua pepe haijatumwa. Jaribu tena.")
        st.info("💡 Ili kuokoa mapendekezo yako, tafadhali jisajili au ingia akaunti yako.")
    else:
        user_email = st.session_state["user"]
        user_row = users_df[users_df['email'].str.strip().str.lower()==user_email.strip().lower()]
        user_name = user_row.iloc[0]['name'] if not user_row.empty else user_email
        st.markdown(
            f"""
            <div style='background: linear-gradient(135deg, rgba(46, 125, 50, 0.85), rgba(67, 160, 71, 0.85)), url("https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=800"); background-size: cover; background-position: center; padding: 40px; border-radius: 15px; text-align: center; margin-bottom: 20px; box-shadow: 0 8px 20px rgba(46, 125, 50, 0.4);'>
                <h1 style='color: white; margin: 0; text-shadow: 2px 2px 4px rgba(0,0,0,0.5);'>🍽️ Karibu, {user_name}!</h1>
                <p style='color: white; font-size: 16px; margin: 10px 0 0 0; text-shadow: 1px 1px 3px rgba(0,0,0,0.5);'>Tafuta vyakula vya kuogopesha kwa ajili yako</p>
            </div>
            """, unsafe_allow_html=True
        )
        st.markdown("<h3>📋 Kujaza Taarifa Zako</h3>", unsafe_allow_html=True)
        weight = st.number_input("⚖️ Uzani (kg)",20.0,200.0,60.0)
        height_m = st.number_input("📏 Urefu (m)",1.0,2.5,1.7)
        age = st.number_input("🎂 Umri",5,120,25)
        sex = st.selectbox("🚻 Jinsia",["M - Mume","F - Mwanamke"])
        activity = st.selectbox("🏃 Kiwango cha Shughuli",["Bila Harakati","Kidogo","Kwa Kawaida","Wengi","Wengi Sana"])
        goal = st.selectbox("🎯 Lengo la Afya",health_goals)
        groups_sw = st.multiselect("🥬 Vikundi vya Vyakula", list(food_groups_sw.values()))
        top_n = st.number_input("🍽️ Idadi ya Vyakula",1,50,5)

        if st.button("🥑 Pata Mapendekezo", use_container_width=True):
            if not groups_sw:
                st.warning("⚠️ Chagua angalau vikundi vya vyakula moja!")
            else:
                selected_keys = [sw_to_key[s] for s in groups_sw if s in sw_to_key]
                results = recommend(goal, selected_keys, int(top_n))
                sex_code = sex[0]
                activity_map = {"Bila Harakati": "Sedentary", "Kidogo": "Light", "Kwa Kawaida": "Moderate", "Wengi": "Very Active", "Wengi Sana": "Extra Active"}
                activity_eng = activity_map.get(activity, "Moderate")
                bmi = calculate_bmi(weight, height_m)
                bmr = calculate_bmr(weight, round(height_m*100), age, sex_code)
                tdee = calculate_tdee(bmr, activity_eng)
                new_rows=[]
                
                for grp_key, table in results.items():
                    color_info = food_group_colors.get(grp_key, {"bg": "linear-gradient(135deg, #81c784 0%, #66bb6a 100%)", "emoji": "🥘"})
                    st.markdown(f"### {color_info['emoji']} {grp_key} - {food_groups_sw.get(grp_key,'')}")
                    col1,col2,col3 = st.columns(3)
                    for i, food_name in enumerate(table.tolist()):
                        col = [col1,col2,col3][i%3]
                        img_path = f"images/{food_name}.jpg"
                        delay = round((i % 9) * 0.12, 2)
                        if os.path.exists(img_path):
                            col.markdown(
                                f"""
                                <div class='food-card' style="background-image: url('{img_path}'); background-size: cover; background-position: center; animation-delay: {delay}s;">
                                    <div style='background:rgba(0,0,0,0.25);padding:18px;border-radius:12px;'>✨ {food_name} ✨</div>
                                </div>
                                """, unsafe_allow_html=True
                            )
                        else:
                            bg_gradient = color_info["bg"]
                            emoji = color_info["emoji"]
                            col.markdown(
                                f"<div class='food-card' style='background: {bg_gradient}; animation-delay: {delay}s;'><span class=\"food-emoji\">{emoji}</span><div style=\"font-size:14px;margin-top:6px\">{food_name}</div></div>", unsafe_allow_html=True
                            )
                        row = food_df[food_df["Chakula"]==food_name].iloc[0]
                        protein = get_nutrient_value(row,"PROCNT")
                        fiber = get_nutrient_value(row,"FIB")
                        omega3 = get_nutrient_value(row,"FAPU") if "FAPU" in row else 0
                        vitc = get_nutrient_value(row,"VITC") if "VITC" in row else 0
                        calories = get_nutrient_value(row,"ENERGY_KC") if "ENERGY_KC" in row else 0
                        new_rows.append({
                            "email":user_email,"age":age,"sex":sex_code,"bmi":bmi,"bmr":bmr,
                            "tdee":tdee,"food":food_name,"rating":pd.NA,
                            "protein_g":protein,"fiber_g":fiber,"omega3_g":omega3,
                            "vitC_mg":vitc,"calories_kc":calories,"date":str(datetime.now())
                        })
                
                if new_rows:
                    goal_file = os.path.join(HISTORY_FOLDER,f"{goal.replace(' ','_')}.csv")
                    goal_df = ensure_csv(goal_file, new_rows[0].keys())
                    goal_df = pd.concat([goal_df,pd.DataFrame(new_rows)],ignore_index=True)
                    save_csv(goal_df,goal_file)
                    st.success(f"✅ Pendekezo limesave kwa lengo: {goal}")

                    foods_text = "\n".join([r["food"] for r in new_rows])
                    if st.button("📤 Tuma Sasa kwa Barua Pepe", key=f"send_now_{goal}"):
                        if send_email(user_email,f"Mapendekezo ya Vyakula ({goal})",foods_text):
                            st.success("📧 Barua pepe imetumwa vizuri!")
                        else:
                            st.error("❌ Barua pepe haijatumwa. Jaribu tena.")

# -------------------------
# MY HISTORY
# -------------------------
elif menu_choice=="📜 Historia Yangu":
    if not st.session_state["user"]:
        st.warning("🔒 Tafadhali ingia kwanza!")
    else:
        user_email = st.session_state["user"]
        st.markdown(
            """
            <div style='background: linear-gradient(135deg, rgba(46, 125, 50, 0.85), rgba(67, 160, 71, 0.85)), url("https://images.unsplash.com/photo-1495521821757-a1efb6729352?w=800"); background-size: cover; background-position: center; padding: 40px; border-radius: 15px; text-align: center; margin-bottom: 20px; box-shadow: 0 8px 20px rgba(46, 125, 50, 0.4);'>
                <h1 style='color: white; margin: 0; text-shadow: 2px 2px 4px rgba(0,0,0,0.5);'>📜 Historia Yangu</h1>
                <p style='color: white; font-size: 16px; margin: 10px 0 0 0; text-shadow: 1px 1px 3px rgba(0,0,0,0.5);'>Tazama mapendekezo yako ya awali</p>
            </div>
            """, unsafe_allow_html=True
        )
        all_files = [os.path.join(HISTORY_FOLDER,f) for f in os.listdir(HISTORY_FOLDER) if f.endswith(".csv")]
        if all_files:
            combined = pd.concat([pd.read_csv(f) for f in all_files],ignore_index=True)
            user_history = combined[combined["email"]==user_email]
            if not user_history.empty:
                st.markdown("<h3>🍽️ Vyakula Vya Hapo Awali</h3>", unsafe_allow_html=True)
                st.dataframe(user_history, use_container_width=True)
            else:
                st.info("💡 Bado hakuna historia. Tafadhali pata mapendekezo kwanza!")
        else:
            st.info("📊 Hakuna historia inayopatikana.")

# -------------------------
# FEEDBACK
# -------------------------
elif menu_choice=="📝 Maoni":
    st.markdown(
        """
        <div style='background: linear-gradient(135deg, rgba(46, 125, 50, 0.85), rgba(67, 160, 71, 0.85)), url("https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=800"); background-size: cover; background-position: center; padding: 40px; border-radius: 15px; text-align: center; margin-bottom: 20px; box-shadow: 0 8px 20px rgba(46, 125, 50, 0.4);'>
            <h1 style='color: white; margin: 0; text-shadow: 2px 2px 4px rgba(0,0,0,0.5);'>📝 Toa Maoni</h1>
            <p style='color: white; font-size: 16px; margin: 10px 0 0 0; text-shadow: 1px 1px 3px rgba(0,0,0,0.5);'>Saidia tuwe nzuri — kamatia maoni yako</p>
        </div>
        """, unsafe_allow_html=True
    )
    if not st.session_state["user"]:
        st.warning("🔒 Tafadhali ingia kwanza!")
    else:
        user_email = st.session_state["user"]
        goal_fb = st.selectbox("🎯 Chagua Lengo", health_goals)
        rating = st.selectbox("⭐ Kamatia Vyakula (0=Sio Sahihi ... 4=Nzuri Sana)", [0,1,2,3,4])
        comment = st.text_area("💬 Maoni (Inaweza Kuwa Hiari)")
        if st.button("✅ Tuma Maoni", use_container_width=True):
            goal_file = os.path.join(HISTORY_FOLDER,f"{goal_fb.replace(' ','_')}.csv")
            df_hist = ensure_csv(goal_file, ["email","age","sex","bmi","bmr","tdee",
                                             "food","rating","protein_g","fiber_g","omega3_g","vitC_mg",
                                             "calories_kc","date"])
            delay_days = st.number_input("🔁 Inashauriwa kusubiri siku ngapi kabla ya kukamata maoni?", 0, 30, 1, help="Chagua idadi ya siku baada ya mapendekezo kabla ya kumwomba mtumiaji kukadiria mchango wa chakula.")
            try:
                dates = pd.to_datetime(df_hist["date"], errors='coerce')
            except Exception:
                dates = pd.Series([pd.NaT]*len(df_hist))
            now = pd.Timestamp.now()
            eligible = dates.notna() & ((now - dates).dt.total_seconds() >= (int(delay_days) * 86400))
            mask = (df_hist["email"]==user_email) & (df_hist["rating"].isna()) & (eligible)
            eligible_count = mask.sum()
            if eligible_count > 0:
                df_hist.loc[mask,"rating"] = rating
                save_csv(df_hist,goal_file)
                st.success(f"✅ Maoni yako yamesave vizuri kwa rekodi {eligible_count}!")
            else:
                st.warning("⚠️ Hakuna rekodi zilizo tayari kukamatwa kwa maoni kwa sasa (hakikisha mapendekezo yamepitwa hadi siku uliyochagua).")

# -------------------------
# LOGOUT
# -------------------------
elif menu_choice=="🚪 Ondoka":
    if not st.session_state.get("user"):
        st.info("ℹ️ Hujaingia kwa sasa.")
    else:
        st.session_state['confirm_logout'] = True
        try:
            st.experimental_rerun()
        except Exception:
            pass

# -------------------------
# ADMIN SECTION
# -------------------------
if st.session_state["user"]==admin_email:
    st.sidebar.markdown("<h3 style='color: #ff6f61;'>👨‍💼 Admin Panel</h3>", unsafe_allow_html=True)
    with st.sidebar.expander("📊 Download Data", expanded=False):
        st.markdown("<h4>ML Datasets</h4>", unsafe_allow_html=True)
        all_files = [os.path.join(HISTORY_FOLDER,f) for f in os.listdir(HISTORY_FOLDER) if f.endswith(".csv")]
        if all_files:
            for f in all_files:
                st.download_button(f"📥 {os.path.basename(f)}", pd.read_csv(f).to_csv(index=False), file_name=os.path.basename(f))
        else:
            st.info("📊 Hakuna datasets inayopatikana.")
