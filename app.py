# app.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time

# 设置页面配置
st.set_page_config(
    page_title="心跳包监控系统",
    page_icon="❤️",
    layout="wide"
)

# 页面标题
st.title("❤️ 心跳包监控仪表板")
st.markdown("---")

# 侧边栏配置
with st.sidebar:
    st.header("⚙️ 配置选项")
    
    # 数据源选择
    data_source = st.radio(
        "数据源选择",
        ["模拟数据", "上传CSV文件", "API实时数据"]
    )
    
    st.markdown("---")
    
    # 可视化参数
    st.subheader("📊 图表设置")
    show_grid = st.checkbox("显示网格", value=True)
    show_trend = st.checkbox("显示趋势线", value=True)
    points_per_page = st.slider("每页显示点数", 50, 500, 200)
    
    st.markdown("---")
    st.caption("💡 提示：心跳包序号应该连续递增，异常跳变表示连接问题")

# 模拟数据生成函数
def generate_mock_data(n_points=200):
    """生成模拟的心跳包数据"""
    end_time = datetime.now()
    start_time = end_time - timedelta(seconds=n_points)
    
    timestamps = [start_time + timedelta(seconds=i) for i in range(n_points)]
    seq_numbers = list(range(1000, 1000 + n_points))
    
    # 随机添加一些数据包丢失和延迟
    seq_numbers_with_loss = []
    for i, seq in enumerate(seq_numbers):
        # 模拟0.5%的丢包率
        if np.random.random() > 0.005:
            seq_numbers_with_loss.append(seq)
        else:
            seq_numbers_with_loss.append(None)
    
    return timestamps, seq_numbers_with_loss

# CSV文件处理函数
def load_csv_data(uploaded_file):
    """处理上传的CSV文件"""
    try:
        df = pd.read_csv(uploaded_file)
        # 假设CSV包含'timestamp'和'seq_number'列
        required_cols = ['timestamp', 'seq_number']
        if all(col in df.columns for col in required_cols):
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            return df['timestamp'].tolist(), df['seq_number'].tolist()
        else:
            st.error(f"CSV文件需要包含列: {required_cols}")
            return None, None
    except Exception as e:
        st.error(f"读取CSV文件失败: {e}")
        return None, None

# API实时数据获取函数（示例）
def fetch_realtime_data():
    """模拟实时API数据获取"""
    current_time = datetime.now()
    current_seq = int(time.time() * 100) % 10000  # 模拟序号
    
    return current_time, current_seq

# 创建折线图
def create_line_chart(timestamps, seq_numbers, show_grid=True, show_trend=False):
    """使用Plotly创建交互式折线图"""
    
    # 创建DataFrame
    df = pd.DataFrame({
        '时间': timestamps,
        '心跳包序号': seq_numbers
    })
    
    # 移除NaN值用于趋势线
    df_clean = df.dropna()
    
    fig = go.Figure()
    
    # 添加主要折线图
    fig.add_trace(go.Scatter(
        x=df['时间'],
        y=df['心跳包序号'],
        mode='lines+markers',
        name='心跳包序号',
        line=dict(color='red', width=2),
        marker=dict(size=4, color='red', symbol='circle'),
        connectgaps=False,  # 不连接缺失点
        hovertemplate='<b>时间</b>: %{x}<br>' +
                      '<b>序号</b>: %{y}<br>' +
                      '<extra></extra>'
    ))
    
    # 添加丢失的数据点标记
    missing_data = df[df['心跳包序号'].isna()]
    if len(missing_data) > 0:
        fig.add_trace(go.Scatter(
            x=missing_data['时间'],
            y=[df['心跳包序号'].min()] * len(missing_data),
            mode='markers',
            name='丢失数据包',
            marker=dict(size=10, color='gray', symbol='x'),
            hovertemplate='<b>时间</b>: %{x}<br>' +
                          '<b>状态</b>: 数据包丢失<br>' +
                          '<extra></extra>'
        ))
    
    # 添加趋势线
    if show_trend and len(df_clean) > 1:
        z = np.polyfit(range(len(df_clean)), df_clean['心跳包序号'], 1)
        p = np.poly1d(z)
        trend_values = p(range(len(df_clean)))
        
        fig.add_trace(go.Scatter(
            x=df_clean['时间'],
            y=trend_values,
            mode='lines',
            name='趋势线',
            line=dict(color='blue', width=1, dash='dash'),
            opacity=0.7
        ))
    
    # 更新布局
    fig.update_layout(
        title='心跳包序号随时间变化',
        xaxis_title='时间',
        yaxis_title='心跳包序号',
        hovermode='closest',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        height=600,
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        )
    )
    
    # 配置网格
    if show_grid:
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
    else:
        fig.update_xaxes(showgrid=False)
        fig.update_yaxes(showgrid=False)
    
    return fig

# 主程序
def main():
    # 数据加载部分
    timestamps = []
    seq_numbers = []
    
    if data_source == "模拟数据":
        if st.button("🔄 生成新数据", key="generate_mock"):
            timestamps, seq_numbers = generate_mock_data(points_per_page)
            st.session_state['timestamps'] = timestamps
            st.session_state['seq_numbers'] = seq_numbers
        
        if 'timestamps' in st.session_state:
            timestamps = st.session_state['timestamps']
            seq_numbers = st.session_state['seq_numbers']
        else:
            # 初始数据
            timestamps, seq_numbers = generate_mock_data(points_per_page)
            st.session_state['timestamps'] = timestamps
            st.session_state['seq_numbers'] = seq_numbers
    
    elif data_source == "上传CSV文件":
        uploaded_file = st.file_uploader("选择CSV文件", type=['csv'])
        if uploaded_file:
            timestamps, seq_numbers = load_csv_data(uploaded_file)
            if timestamps:
                st.success("✅ 数据加载成功!")
    
    elif data_source == "API实时数据":
        st.warning("⚠️ 实时数据模式 - 数据会自动刷新")
        
        if st.button("开始实时监控"):
            placeholder = st.empty()
            for i in range(50):  # 显示50个实时数据点
                current_time, current_seq = fetch_realtime_data()
                if 'realtime_timestamps' not in st.session_state:
                    st.session_state['realtime_timestamps'] = []
                    st.session_state['realtime_seq_numbers'] = []
                
                st.session_state['realtime_timestamps'].append(current_time)
                st.session_state['realtime_seq_numbers'].append(current_seq)
                
                # 限制显示最近100个点
                if len(st.session_state['realtime_timestamps']) > 100:
                    st.session_state['realtime_timestamps'] = st.session_state['realtime_timestamps'][-100:]
                    st.session_state['realtime_seq_numbers'] = st.session_state['realtime_seq_numbers'][-100:]
                
                timestamps = st.session_state['realtime_timestamps']
                seq_numbers = st.session_state['realtime_seq_numbers']
                
                # 更新图表
                fig = create_line_chart(timestamps, seq_numbers, show_grid, show_trend)
                placeholder.plotly_chart(fig, use_container_width=True)
                time.sleep(1)
            
            st.info("实时监控结束")
            return
    
    # 显示图表
    if timestamps and seq_numbers:
        # 创建图表
        fig = create_line_chart(timestamps, seq_numbers, show_grid, show_trend)
        
        # 显示图表
        st.plotly_chart(fig, use_container_width=True)
        
        # 显示统计信息
        col1, col2, col3, col4 = st.columns(4)
        
        # 清理数据用于统计
        clean_seq = [s for s in seq_numbers if s is not None]
        missing_count = seq_numbers.count(None)
        
        with col1:
            st.metric("总数据包数", len(seq_numbers))
        with col2:
            st.metric("成功接收", len(clean_seq))
        with col3:
            loss_rate = (missing_count / len(seq_numbers)) * 100
            st.metric("丢包率", f"{loss_rate:.2f}%")
        with col4:
            if len(clean_seq) > 1:
                st.metric("序号范围", f"{clean_seq[0]} → {clean_seq[-1]}")
        
        # 显示原始数据表
        with st.expander("📋 查看原始数据"):
            df_display = pd.DataFrame({
                '时间': timestamps,
                '心跳包序号': seq_numbers
            })
            st.dataframe(df_display, use_container_width=True)
        
        # 下载数据按钮
        csv = df_display.to_csv(index=False)
        st.download_button(
            label="💾 下载数据为CSV",
            data=csv,
            file_name="heartbeat_data.csv",
            mime="text/csv"
        )
    
    else:
        st.info("👈 请从侧边栏选择数据源并加载数据")

# 运行主程序
if __name__ == "__main__":
    main()
