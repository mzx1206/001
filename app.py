# 在监控页面开头添加自动刷新控制
# 找到 "elif page == '监控':" 这一行，将整个监控页面的代码替换为以下内容：

elif page == "监控":
    st.header("📡 飞行实时画面 - 任务执行监控")
    
    # 添加自动刷新控制
    auto_refresh = st.checkbox("自动刷新 (实时飞行)", value=True, key="auto_refresh_monitor")
    
    # 控制按钮行
    col_btn = st.columns(5)  # 增加一列用于手动刷新
    
    with col_btn[0]:
        if st.button("▶️ 开始/继续", use_container_width=True):
            if not st.session_state.running:
                if st.session_state.full_path is None or len(st.session_state.full_path) < 2:
                    st.warning("请先在规划页面刷新规划路径")
                else:
                    st.session_state.hb.set_path(st.session_state.full_path, st.session_state.alt, st.session_state.drone_spd)
                    st.session_state.running = True
                    st.success("飞行开始！")
                    st.rerun()
            else:
                st.session_state.hb.do_resume()
                st.rerun()
    
    with col_btn[1]:
        if st.button("⏸️ 暂停", use_container_width=True):
            if st.session_state.running:
                st.session_state.hb.do_pause()
                st.rerun()
            else:
                st.warning("当前没有飞行任务")
    
    with col_btn[2]:
        if st.button("⏹️ 停止", use_container_width=True):
            st.session_state.running = False
            st.session_state.hb.stop()
            st.rerun()
    
    with col_btn[3]:
        if st.button("🔄 重置", use_container_width=True):
            st.session_state.running = False
            st.session_state.hb.reset()
            st.session_state.hist = []
            st.rerun()
    
    with col_btn[4]:
        if st.button("📡 手动刷新", use_container_width=True):
            if st.session_state.running:
                new_hb = st.session_state.hb.update(st.session_state.obs, st.session_state.safe_rad)
                st.session_state.hist.append([new_hb['lng'], new_hb['lat']])
                if len(st.session_state.hist) > 200:
                    st.session_state.hist.pop(0)
                if new_hb['arrived']:
                    st.session_state.running = False
                    st.success("🏁 无人机已安全到达目的地！")
            st.rerun()
    
    st.markdown("---")
    
    # 自动更新飞行数据（使用 JavaScript 定时刷新）
    if st.session_state.running and auto_refresh:
        # 使用 meta refresh 实现自动刷新
        st.markdown(
            '<meta http-equiv="refresh" content="0.2">',
            unsafe_allow_html=True
        )
        
        # 每次刷新时更新位置
        current_time = time.time()
        if current_time - st.session_state.last_time >= HEARTBEAT_INTERVAL:
            new_hb = st.session_state.hb.update(st.session_state.obs, st.session_state.safe_rad)
            st.session_state.last_time = current_time
            st.session_state.hist.append([new_hb['lng'], new_hb['lat']])
            if len(st.session_state.hist) > 200:
                st.session_state.hist.pop(0)
            if new_hb['arrived']:
                st.session_state.running = False
                st.success("🏁 无人机已安全到达目的地！")
    
    # 如果不在自动刷新模式，但飞行中，显示提示
    if st.session_state.running and not auto_refresh:
        st.info("💡 提示：请勾选「自动刷新」以实时查看飞行进度，或点击「手动刷新」按钮")
    
    # 获取最新心跳数据
    if st.session_state.hb.hist:
        d = st.session_state.hb.hist[0]
    else:
        d = {"current_wp":"0/0","speed":0,"elapsed":0,"total":0,"traveled":0,"remain":"00:00","battery":0,"progress":0,"delay_ms":0,"loss_percent":0,
             "flight_time":0,"voltage":22.2,"satellites":0,"arrived":False,"safety_violation":False,"remaining_distance":0}
    
    total_waypoints = len(st.session_state.waypoints)
    if total_waypoints > 0 and 'progress' in d:
        segment_index = int(d['progress'] * (total_waypoints - 1))
        current_wp_num = segment_index + 1
        current_wp_num = min(current_wp_num, total_waypoints)
    else:
        current_wp_num = 0
    
    # 显示飞行状态
    status_color = "🟢" if st.session_state.running and not d.get('paused', False) else ("🟡" if d.get('paused', False) else "🔴")
    st.markdown(f"### 飞行状态: {status_color} {'飞行中' if st.session_state.running and not d.get('paused', False) else ('已暂停' if d.get('paused', False) else '已停止')}")
    
    st.markdown("### ✈️ 飞行进度")
    st.progress(d.get('progress',0), text=f"任务进度: {d.get('progress',0)*100:.1f}%")
    
    # 显示当前位置信息
    st.info(f"📍 当前位置: 经度 {d.get('lng', 0):.6f}, 纬度 {d.get('lat', 0):.6f}")
    
    st.markdown("### 📊 实时飞行数据")
    row1 = st.columns(4)
    row1[0].metric("🎯 当前航点", f"{current_wp_num}/{total_waypoints}" if total_waypoints>0 else "0/0")
    row1[1].metric("💨 飞行速度", f"{d.get('speed',0)} m/s")
    elapsed = d.get('elapsed',0)
    row1[2].metric("⏰ 已用时间", f"{int(elapsed//60):02d}:{int(elapsed%60):02d}")
    remaining = d.get('remaining_distance',0)
    row1[3].metric("📏 剩余距离", f"{remaining:.0f} m" if remaining>=0 else "0 m")
    
    row2 = st.columns(2)
    row2[0].metric("🕐 预计到达", d.get('remain','00:00'))
    battery = d.get('battery',0)
    row2[1].metric("🔋 电量模拟", f"{battery}%")
    
    st.markdown("---")
    
    # 设备状态与通信拓扑
    col_status, col_top = st.columns(2)
    
    with col_status:
        st.subheader("📡 设备状态")
        online = st.session_state.running
        st.markdown(f"- **GCS**：{'✅ 在线' if online else '❌ 离线'}")
        st.markdown(f"- **OBC**：{'✅ 在线' if online else '❌ 离线'}")
        st.markdown(f"- **FCU**：{'✅ 在线' if online else '❌ 离线'}")
    
    with col_top:
        st.subheader("🔗 通信链路拓扑与数据流")
        delay = d.get('delay_ms',0)
        loss = d.get('loss_percent',0)
        st.markdown(f"""
        - **GCS** ↔ **OBC**：延迟 {delay} ms
        - **GCS** ↔ **FCU**：延迟 {delay+5} ms
        - **OBC** ↔ **FCU**：延迟 ~{max(0,delay-2)} ms
        - **丢包率**：{loss}%
        """)
        st.code("GCS → OBC → FCU → UAV")
        st.caption("数据流：遥控指令 → 飞控 → 执行器 | 遥测数据 ← 飞控 ← 传感器")
    
    st.markdown("---")
    
    # 实时飞行地图
    st.subheader("🗺️ 实时飞行地图")
    
    if st.session_state.hb.hist:
        latest = st.session_state.hb.hist[0]
        center = [latest['lat'], latest['lng']]
    elif st.session_state.waypoints:
        center = [st.session_state.waypoints[0][1], st.session_state.waypoints[0][0]]
    else:
        center = [SCHOOL_CENTER[1], SCHOOL_CENTER[0]]
    
    tiles = SAT_URL if map_type=="satellite" else VEC_URL
    m = folium.Map(location=center, zoom_start=17, tiles=tiles, attr=ATTR)
    add_safety(m, st.session_state.obs, st.session_state.safe_rad, st.session_state.alt)
    
    for o in st.session_state.obs:
        coords = o.get('polygon',[])
        if len(coords)>=3:
            folium.Polygon([[c[1],c[0]] for c in coords], color='red', fill=True, fill_opacity=0.3).add_to(m)
    
    if st.session_state.full_path:
        folium.PolyLine([[p[1],p[0]] for p in st.session_state.full_path], color='green', weight=3).add_to(m)
    
    if st.session_state.hb.hist:
        trail = [[h['lat'],h['lng']] for h in st.session_state.hb.hist[:30] if 'lat' in h]
        if len(trail)>1:
            folium.PolyLine(trail, color='orange', weight=2).add_to(m)
        latest = st.session_state.hb.hist[0]
        folium.Marker([latest['lat'], latest['lng']], popup=f"📍 当前位置\n高度:{latest['altitude']}m",
                     icon=folium.Icon(color='red', icon='plane', prefix='fa')).add_to(m)
    
    for i,wp in enumerate(st.session_state.waypoints):
        color = 'green' if i==0 else ('red' if i==len(st.session_state.waypoints)-1 else 'blue')
        folium.Marker([wp[1], wp[0]], popup=f"航点{i+1}", icon=folium.Icon(color=color)).add_to(m)
    
    folium_static(m, width=1000, height=500)
    
    st.markdown("---")
    
    # 数据图表
    st.subheader("📈 实时数据图表")
    
    if len(st.session_state.hb.hist) > 1:
        col_ch1, col_ch2 = st.columns(2)
        with col_ch1:
            # 反转历史记录，让时间从左到右递增
            hist_reversed = list(reversed(st.session_state.hb.hist[:50]))
            speed_data = [{"时间(s)": i*HEARTBEAT_INTERVAL, "速度(m/s)": h['speed']} for i,h in enumerate(hist_reversed)]
            st.line_chart(pd.DataFrame(speed_data), x="时间(s)", y="速度(m/s)")
            st.caption("速度变化趋势")
        with col_ch2:
            hist_reversed = list(reversed(st.session_state.hb.hist[:50]))
            remain_data = [{"时间(s)": i*HEARTBEAT_INTERVAL, "剩余距离(m)": max(0,h['remaining_distance'])} for i,h in enumerate(hist_reversed)]
            st.line_chart(pd.DataFrame(remain_data), x="时间(s)", y="剩余距离(m)")
            st.caption("剩余距离变化趋势")
    else:
        st.info("等待飞行数据...")
    
    st.markdown("---")
    
    # 飞行日志记录
    st.subheader("📋 飞行日志记录")
    
    if st.session_state.hb.hist:
        log_df = pd.DataFrame([{
            "时间": h['timestamp'],
            "飞行时间(s)": f"{h['elapsed']:.1f}",
            "纬度": h['lat'],
            "经度": h['lng'],
            "高度(m)": h['altitude'],
            "速度(m/s)": h['speed'],
            "电压(V)": h['voltage'],
            "卫星数": h['satellites'],
            "剩余距离(m)": f"{h['remaining_distance']:.0f}",
            "进度": f"{h['progress']*100:.1f}%"
        } for h in st.session_state.hb.hist[:20]])
        st.dataframe(log_df, use_container_width=True)
        
        if st.button("📊 导出完整飞行数据", use_container_width=True):
            full_df = pd.DataFrame([{
                "timestamp": h['timestamp'],
                "flight_time_s": h['elapsed'],
                "lat": h['lat'],
                "lng": h['lng'],
                "altitude_m": h['altitude'],
                "speed_mps": h['speed'],
                "voltage_v": h['voltage'],
                "satellites": h['satellites'],
                "remaining_distance_m": h['remaining_distance'],
                "progress_pct": h['progress']*100,
                "safety_violation": h['safety_violation']
            } for h in st.session_state.hb.hist])
            csv = full_df.to_csv(index=False)
            st.download_button("📥 下载CSV", csv, f"flight_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", "text/csv", use_container_width=True)
    else:
        st.info("暂无飞行数据")
