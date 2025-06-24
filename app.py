import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px

@st.cache_data
def load_data():
    """
    載入化合物數據。
    在實際應用中，您應該在這裡從 Excel 或 CSV 檔案讀取數據。
    例如: df = pd.read_excel('your_data.xlsx')
    為了方便展示，我們直接在程式碼中建立 DataFrame。
    """

    df = pd.read_csv('./chem_list.csv')
    return df

def get_compound_properties(df, item_name):
    """
    根據選擇的化合物名稱，從 DataFrame 中取得其性質。
    """
    data_row = df[df['Item'] == item_name].iloc[0]
    return data_row['Vap Enthalpy (kJ/mol)'], data_row['T2 (C)'], data_row['P2 (torr)']

def calculate_new_boiling_point(P, P2, boiling_point, H_vap):
    """
    使用克勞修斯-克拉佩龍方程式計算不同壓力下的新沸點。
    """
    # 理想氣體常數，單位需匹配蒸發焓 (kJ)
    R = 8.314e-3  # kJ/(mol*K)
    
    # 將已知沸點轉換為絕對溫度 (Kelvin)
    T2_K = boiling_point + 273.15
    
    # 確保壓力值為正數，避免 log(0) 錯誤
    P_safe = np.clip(P, 1e-9, None)
    
    # 克勞修斯-克拉佩龍方程式的積分形式
    # 1/T1 = 1/T2 - (R/H_vap) * ln(P1/P2)
    T1_K = 1 / ((1 / T2_K) - (R / H_vap) * np.log(P_safe / P2))
    
    # 將計算出的絕對溫度轉換回攝氏溫度
    return T1_K - 273.15


def main():
   # --- 主應用程式介面 (UI) ---

    # 設定網頁主標題
    st.title("🧪 化合物蒸氣壓曲線產生器")
    st.write("這是一個互動工具，用來計算並繪製不同化合物在不同壓力下的沸點變化曲線。")

    # 載入數據
    df_compounds = load_data()

    # --- 側邊欄控制選項 ---
    st.sidebar.header("控制選項")

    # 在側邊欄建立下拉選單
    compound_list = df_compounds['Item'].tolist()
    selected_compound = st.sidebar.selectbox(
        "請選擇一個化合物:",
        compound_list
    )

    # 在側邊欄建立一個滑桿，讓使用者選擇壓力範圍
    pressure_range = st.sidebar.slider(
        "選擇壓力範圍 (torr):",
        min_value=0.1,
        max_value=1000.0,
        value=(1.0, 760.0), # 預設範圍
        step=0.1
    )


    # --- 核心計算與繪圖邏輯 ---

    # 1. 根據使用者選擇，取得化合物性質
    h_vap_ref,bp, p2_ref = get_compound_properties(df_compounds, selected_compound)

    # 2. 根據滑桿選擇的範圍，產生壓力數據點
    P_values = np.linspace(pressure_range[0], pressure_range[1], 1000)

    # 3. 執行計算
    T_values = calculate_new_boiling_point(P_values, p2_ref, bp, h_vap_ref)

    # 4. 將計算結果整理成 DataFrame 以便繪圖
    df_plot = pd.DataFrame({
        '壓力 (torr)': P_values,
        '計算沸點 (℃)': T_values
    })

    # --- 顯示結果 ---
    st.header(f"分析結果: {selected_compound}")
    st.write(f"在標準大氣壓 **{p2_ref:.1f} torr** 下，**{selected_compound}** 的沸點為 **{bp:.2f} ℃**，蒸發焓為 **{h_vap_ref:.3f} kJ/mol**。")


    # 建立 Plotly 圖表
    fig = px.line(
        df_plot,
        x='壓力 (torr)',
        y='計算沸點 (℃)',
        title=f'{selected_compound} 的壓力-溫度關係圖',
        labels={'壓力 (torr)': '壓力 (torr)', '計算沸點 (℃)': '溫度 (℃)'},
        template="plotly_white" # 使用簡潔的白色主題
    )
        # 讓圖表更美觀
    fig.update_traces(line=dict(color='royalblue', width=3))
    fig.update_layout(
        xaxis=dict(gridcolor='lightgrey'),
        yaxis=dict(gridcolor='lightgrey')
    )

    # 使用 st.plotly_chart 顯示圖表，use_container_width=True 讓圖表填滿寬度
    st.plotly_chart(fig, use_container_width=True)

    # 顯示計算數據的預覽表格
    with st.expander("點擊查看計算數據預覽"):
        st.dataframe(df_plot)

    # 頁尾
    st.sidebar.info("這是一個使用 Streamlit 和 Plotly 建立的互動式應用程式。")
if __name__=='__main__':
   main()
