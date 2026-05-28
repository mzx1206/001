elif page == "监控":
    st.header("📡 飞行实时画面 - 任务执行监控")
    
    # 控制按钮
    col_btn = st.columns(5)
    with col_btn[0]:
        if st.button("▶️ 开始/继续", use_container_width=True):
            if not st.session_state.running:
                if st.session_state.full_path is None:
                    st.warning("请先在规划页面刷新规划路径")
                else:
                    st.session_state.hb.set_path(st.session_state.full_path, st.session_state.alt, st.session_state.drone_spd)
                    st.session_state.running = True
                    st.rerun()
            else:
                st.session_state.hb.do_resume()
                st.rerun()
    
    with col_btn[1]:
        if st.button("⏸️ 暂停", use_container_width=True):
            if st.session_state.running:
                st.session_state.hb.do_pause()
                st.rerun()
    
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
        if st.button("📡 刷新数据", use_container_width=True):
            if st.session_state.running:
                st.session_state.hb.update(st.session_state.obs, st.session_state.safe_rad)
            st.rerun()
    
    st.markdown("---")
    
    # 自动更新飞行数据（不使用 meta refresh，改用用户手动刷新）
    if st.session_state.running:
        # 每次页面加载时更新一次位置
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
        
        # 显示自动刷新提示和手动刷新按钮
        st.info("🔄 飞行中 - 点击「刷新数据」按钮更新位置，或勾选下方自动刷新")
        
        # 自动刷新选项（使用 checkbox 让用户选择是否自动刷新）
        auto_refresh = st.checkbox("自动刷新页面", value=False, key="auto_refresh")
        if auto_refresh:
            st.markdown('<meta http-equiv="refresh" content="0.5">', unsafe_allow_html=True)
            st.warning("⚠️ 自动刷新已开启，页面将每0.5秒自动刷新。如需停止，请取消勾选或点击停止飞行")
    
    # 获取最新心跳数据
    if st.session_state.hb.hist:
        d = st.session_state.hb.hist[0]
    else:
        d = {"speed": 0, "progress": 0, "elapsed": 0, "remaining_distance": 0,
             "remain": "00:00", "battery": 0, "lng": 0, "lat": 0, "paused": False,
             "altitude": 50, "current_wp": "0/0"}
    
    total_waypoints = len(st.session_state.waypoints)
    current_wp_num = int(d.get('progress', 0) * total_waypoints) + 1 if total_waypoints > 0 else 0
    current_wp_num = min(current_wp_num, total_waypoints)
    
    # 显示状态
    if st.session_state.running:
        status_text = "✈️ 飞行中" if not d.get('paused', False) else "⏸️ 已暂停"
        status_color = "green" if not d.get('paused', False) else "orange"
    else:
        status_text = "⏹️ 已停止"
        status_color = "red"
    
    st.markdown(f"### 状态: <span style='color:{status_color}'>{status_text}</span>", unsafe_allow_html=True)
    
    # 飞行进度
    st.markdown("### ✈️ 飞行进度")
    st.progress(d.get('progress', 0), text=f"进度: {d.get('progress', 0)*100:.1f}%")
    
    # 飞行数据
    st.markdown("### 📊 实时飞行数据")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🎯 当前航点", f"{current_wp_num}/{total_waypoints}" if total_waypoints > 0 else "0/0")
    col2.metric("💨 飞行速度", f"{d.get('speed', 0)} m/s")
    elapsed = d.get('elapsed', 0)
    col3.metric("⏰ 已用时间", f"{int(elapsed//60):02d}:{int(elapsed%60):02d}")
    remaining = d.get('remaining_distance', 0)
    col4.metric("📏 剩余距离", f"{remaining:.0f} m" if remaining >= 0 else "0 m")
    
    col5, col6 = st.columns(2)
    col5.metric("🕐 预计到达", d.get('remain', '00:00'))
    col6.metric("🔋 电量模拟", f"{d.get('battery', 0)}%")
    
    st.markdown("---")
    
    # 当前位置
    st.info(f"📍 当前位置: 经度 {d.get('lng', 0):.6f}, 纬度 {d.get('lat', 0):.6f} | 高度: {d.get('altitude', 50)}m")
    
    st.markdown("---")
    
    # 实时飞行地图
    st.markdown("### 🗺️ 实时飞行地图")
    
    # 确定地图中心
    if d.get('lat', 0) != 0:
        center = [d['lat'], d['lng']]
    elif st.session_state.waypoints:
        center = [st.session_state.waypoints[0][1], st.session_state.waypoints[0][0]]
    else:
        center = [SCHOOL_CENTER[1], SCHOOL_CENTER[0]]
    
    # 创建地图
    m = folium.Map(location=center, zoom_start=17, tiles=VEC_URL, attr=ATTR)
    
    # 添加障碍物
    for o in st.session_state.obs:
        coords = o.get('polygon', [])
        if len(coords) >= 3:
            folium.Polygon([[c[1], c[0]] for c in coords], color='red', fill=True, fill_opacity=0.3,
                          popup=f"{o.get('name', '障碍物')}\n高度:{o.get('height', 20)}m").add_to(m)
    
    # 添加完整航线
    if st.session_state.full_path and len(st.session_state.full_path) > 1:
        folium.PolyLine([[p[1], p[0]] for p in st.session_state.full_path], color='green', weight=3, opacity=0.8, 
                       popup="规划航线").add_to(m)
    
    # 添加航点
    for i, wp in enumerate(st.session_state.waypoints):
        color = 'green' if i == 0 else ('red' if i == len(st.session_state.waypoints)-1 else 'blue')
        folium.Marker([wp[1], wp[0]], popup=f"航点{i+1}", icon=folium.Icon(color=color)).add_to(m)
    
    # 添加历史轨迹
    if st.session_state.hist and len(st.session_state.hist) > 1:
        trail = [[p[1], p[0]] for p in st.session_state.hist[-50:] if len(p) == 2]
        if len(trail) > 1:
            folium.PolyLine(trail, color='orange', weight=2, opacity=0.7, popup="历史轨迹").add_to(m)
    
    # 添加无人机当前位置
    if d.get('lat', 0) != 0:
        folium.Marker([d['lat'], d['lng']], 
                     popup=f"📍 无人机\n高度:{d.get('altitude', 50)}m\n速度:{d.get('speed', 0)}m/s",
                     icon=folium.Icon(color='red', icon='plane', prefix='fa')).add_to(m)
        
        # 添加安全半径圆圈
        folium.Circle([d['lat'], d['lng']], radius=st.session_state.safe_rad,
                     color='blue', fill=True, fill_opacity=0.2, popup=f"安全区 {st.session_state.safe_rad}m").add_to(m)
    
    # 显示地图
    st_folium(m, width=1000, height=500, returned_objects=[])
    
    st.markdown("---")
    
    # 飞行日志
    st.markdown("### 📋 飞行日志")
    if st.session_state.hb.hist:
        log_df = pd.DataFrame([{
            "时间": h['timestamp'],
            "飞行时间": f"{h['elapsed']:.1f}s",
            "纬度": f"{h['lat']:.6f}",
            "经度": f"{h['lng']:.6f}",
            "高度": f"{h['altitude']}m",
            "速度": f"{h['speed']}m/s",
            "进度": f"{h['progress']*100:.1f}%"
        } for h in st.session_state.hb.hist[:10]])
        st.dataframe(log_df, use_container_width=True)
    else:
        st.info("暂无飞行数据，请开始飞行任务")
    
    # 提示信息
    if st.session_state.running:
        st.info("💡 提示：点击「刷新数据」按钮更新位置，或勾选「自动刷新页面」让页面自动更新")
    else:
        st.info("💡 提示：请先在「规划」页面设置航点并点击「刷新规划」，然后点击「开始/继续」启动飞行任务")
