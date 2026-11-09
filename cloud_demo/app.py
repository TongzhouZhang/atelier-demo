import streamlit as st
import os
import json
import base64
import time
import streamlit.components.v1 as components

st.set_page_config(page_title="ATELIER AI", page_icon="🕊️", layout="wide", initial_sidebar_state="collapsed")

# ================= CSS =================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,600&family=Montserrat:wght@300;400;500&display=swap');
    [data-testid="collapsedControl"], [data-testid="stSidebar"], header, #MainMenu, footer { visibility: hidden !important; }
    .stApp { background-color: #FFFFFF; font-family: 'Montserrat', sans-serif; }
    h1 { font-family: 'Playfair Display', serif !important; font-size: 54px !important; text-align: center; letter-spacing: 6px; margin-top: 20px; }
    .subtitle { text-align: center; font-size: 13px; color: #666; letter-spacing: 8px; margin-bottom: 40px; text-transform: uppercase; }
    .caption { font-size: 11px; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 15px; font-weight: 500; }
    .stButton>button { background-color: #000000 !important; color: #FFFFFF !important; border-radius: 0px !important; height: 50px !important; font-size: 13px !important; letter-spacing: 3px; border: 1px solid #000000 !important; transition: all 0.3s ease; }
    .stButton>button:hover { background-color: #FFFFFF !important; color: #000000 !important; }
    .stAlert { border-radius: 0px !important; border-left: 2px solid #000 !important; background-color: #FAFAFA !important; color: #000 !important; }
</style>
""", unsafe_allow_html=True)

st.markdown("<h1>VIRTUAL ATELIER</h1>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>专属 3D 虚拟试衣体验</div>", unsafe_allow_html=True)

# 读取数据
DB_PATH = os.path.join(os.getcwd(), "merchants.json")
try:
    with open(DB_PATH, "r", encoding="utf-8") as f:
        PLATFORM_DB = json.load(f)
        current_merchant = list(PLATFORM_DB.values())[0]
except Exception as e:
    st.error("数据读取失败，请检查 merchants.json")
    st.stop()

PRODUCTS = current_merchant.get('products', {})

# 纯数学计算15项数据（去除 open3d 依赖）
def process_body_model(user_height, user_weight, is_male=True):
    standard_chest = user_height * 0.53 if is_male else user_height * 0.50
    standard_waist = user_height * 0.45 if is_male else user_height * 0.38
    standard_hip = user_height * 0.55 if is_male else user_height * 0.56
    bmi = user_weight / ((user_height / 100) ** 2)
    weight_mod = (bmi - 21.0) * 1.5
    return {
        "身高": round(user_height, 1), "胸围": round(standard_chest + weight_mod * 0.5, 1), "肩宽": round(user_height * 0.26, 1),
        "颈围": round(standard_chest * 0.38, 1), "下胸围": round(standard_chest * 0.88, 1), "腰围": round(standard_waist + weight_mod * 1.2, 1),
        "上臀围": round(standard_hip * 0.9, 1), "下臀围": round(standard_hip + weight_mod * 0.8, 1), "臂围": round(standard_chest * 0.30, 1),
        "前臂围": round(standard_chest * 0.22, 1), "手腕围": round(standard_chest * 0.17, 1), "大腿围": round(standard_hip * 0.55, 1),
        "膝围": round(standard_hip * 0.35, 1), "小腿围": round(standard_hip * 0.34, 1), "踝围": round(standard_chest * 0.22, 1)
    }

def get_recommended_size(user_data, size_chart, category='top'):
    best_size = list(size_chart.keys())[0]
    min_diff = float('inf')
    for size_name, size_info in size_chart.items():
        if category == 'pants':
            diff = abs(size_info.get('waist', 0) - user_data['腰围'])
        else:
            diff = abs(size_info.get('chest', 0) - user_data['胸围'])
        if diff < min_diff:
            min_diff = diff
            best_size = size_name
    return best_size

def evaluate_garment_fit(user_data, size_info, category='top', prod_info=None):
    warnings = []
    is_fit = True
    if category == 'pants':
        waist_diff = size_info.get('waist', 0) - user_data['腰围']
        if waist_diff < 0:
            warnings.append(f"腰围偏紧 ({waist_diff:.1f}cm)")
            is_fit = False
        elif waist_diff > 6:
            warnings.append(f"腰围偏松 ({waist_diff:+.1f}cm)")
        hip_val = size_info.get('hip', size_info.get('下臀围', 0))
        if hip_val > 0:
            hip_diff = hip_val - user_data['下臀围']
            if hip_diff < 2:
                warnings.append("胯部可能卡裆/紧绷")
                is_fit = False
    else:
        chest_diff = size_info.get('chest', 0) - user_data['胸围']
        if chest_diff < 2:
            warnings.append(f"胸围偏紧 ({chest_diff:.1f}cm)")
            is_fit = False
        elif chest_diff > 10:
            warnings.append(f"胸围宽松 ({chest_diff:+.1f}cm)")
    return is_fit, warnings

spacer1, main_col, spacer2 = st.columns([1, 3, 1])

with main_col:
    # 01 衣橱
    st.markdown("<div class='caption'>01 / 臻选衣橱</div>", unsafe_allow_html=True)
    prod_cols = st.columns(min(len(PRODUCTS), 3), gap="medium")
    for idx, (pid, prod) in enumerate(PRODUCTS.items()):
        with prod_cols[idx % len(prod_cols)]:
            with st.container(border=True):
                cat_cn = "上衣" if prod.get('category') == 'top' else "裤子"
                st.markdown(f"<div style='font-size:10px;color:#888;'>{current_merchant.get('merchant_name', '')}</div>", unsafe_allow_html=True)
                st.markdown(f"<div style='font-size:9px;border:1px solid #CCC;display:inline-block;padding:2px 6px;'>{cat_cn}</div>", unsafe_allow_html=True)
                st.markdown(f"<div style='font-size:14px;font-weight:600;margin:6px 0;'>{prod['name']}</div>", unsafe_allow_html=True)

                size_options = list(prod['sizes'].keys())
                picked_size = st.selectbox("尺码", size_options, key=f"pick_{pid}", label_visibility="collapsed")

                if st.button(f"一键试穿 {picked_size} 码", key=f"try_{pid}", use_container_width=True):
                    st.session_state['selected_pid'] = pid
                    st.session_state['selected_size'] = picked_size
                    st.rerun()

    # 02 量体
    st.write(""); st.write("---")
    st.markdown("<div class='caption'>02 / 快速量体，生成专属画像</div>", unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1: user_height = st.number_input("身高 (CM)", min_value=130.0, max_value=220.0, value=165.0)
    with c2: user_weight = st.number_input("体重 (KG)", min_value=30.0, max_value=150.0, value=55.0)
    
    gender = st.radio("性别", ["男性", "女性"], horizontal=True, label_visibility="collapsed")
    is_male = (gender == "男性")

    if st.button("生成 15 项身体数据", use_container_width=True):
        st.session_state['body_data'] = process_body_model(user_height, user_weight, is_male)
        st.rerun()

    if 'body_data' in st.session_state:
        st.write("")
        m1, m2, m3 = st.columns(3)
        m1.metric("胸围", f"{st.session_state['body_data']['胸围']}")
        m2.metric("腰围", f"{st.session_state['body_data']['腰围']}")
        m3.metric("臀围", f"{st.session_state['body_data']['下臀围']}")

    # 03 试穿
    if 'body_data' in st.session_state and 'selected_pid' in st.session_state:
        st.write(""); st.write("---")
        st.markdown("<div class='caption'>03 / 试穿报告</div>", unsafe_allow_html=True)

        prod = PRODUCTS[st.session_state['selected_pid']]
        size_chart = prod['sizes']
        category = prod.get('category', 'top')
        selected_size = st.session_state['selected_size']

        rec_size = get_recommended_size(st.session_state['body_data'], size_chart, category)
        st.success(f"✅ 综合计算，我们推荐您选择：**{rec_size} 码**")

        item_info = size_chart[selected_size]
        is_fit, warnings = evaluate_garment_fit(st.session_state['body_data'], item_info, category, prod)
        
        if is_fit and not warnings: st.success("✅ 完美合身：各维度数据契合。")
        elif is_fit and warnings: st.warning(f"⚠️ 版型提示：{', '.join(warnings)}")
        else: st.error(f"🚨 极度不适：{', '.join(warnings)}")

        st.write("---")
        st.markdown("<p style='font-size:12px; font-weight:600;'>👉 姿态仿真与细节渲染</p>", unsafe_allow_html=True)
        
        if category == 'pants':
            posture_options = ["站立", "坐姿", "抬腿"]
        else:
            posture_options = ["自然站立", "抬臂/弯腰 (动态)"]

        posture = st.radio("姿态测试", posture_options, horizontal=True, label_visibility="collapsed")

        if st.button(f"渲染 3D 效果", use_container_width=True):
            with st.spinner("加载高精度云资产..."):
                time.sleep(1)
                st.session_state['current_posture'] = posture
                st.success("✅ 3D 渲染完成！")

# ================= 底部 3D 展示 =================
if 'body_data' in st.session_state:
    current_posture = st.session_state.get('current_posture', '站立')
    
    # 读取本地(云端)的文件
    if current_posture == "坐姿":
        glb_path = "final_sit.glb"
    elif current_posture == "抬腿":
        glb_path = "final_up.glb"
    else:
        glb_path = "final_stand.glb"

    if os.path.exists(glb_path):
        with open(glb_path, "rb") as f:
            glb_data = base64.b64encode(f.read()).decode("utf-8")
        st.write(""); st.write("")
        st.markdown("<h2 style='text-align:center; font-family: \"Playfair Display\", serif; font-size: 32px;'>THE SILHOUETTE</h2>", unsafe_allow_html=True)
        
        html_3d = f'''
        <script type="module" src="https://ajax.googleapis.com/ajax/libs/model-viewer/3.4.0/model-viewer.min.js"></script>
        <model-viewer 
            src="data:model/gltf-binary;base64,{glb_data}" 
            auto-rotate camera-controls shadow-intensity="1.5" 
            environment-image="neutral" exposure="1.2"
            camera-orbit="0deg 75deg 2.5m"
            style="width: 100%; height: 500px; background-color: #FAFAFA;">
        </model-viewer>
        '''
        components.html(html_3d, height=520)
    else:
        st.warning(f"⚠️ 找不到模型文件：{glb_path}")