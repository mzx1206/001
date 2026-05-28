# ==================== 心跳模拟器 ====================
class HeartbeatSim:
    def __init__(self, start):
        self.hist = []
        self.pos = start[:]
        self.path = [start[:]]
        self.idx = 0
        self.sim = False
        self.is_paused = False
        self.alt = 50
        self.spd = 50
        self.prog = 0
        self.total = 0
        self.trav = 0
        self.start_time = None
        self.elapsed = 0
        self.safety_violation = False
        self.last_update_time = None  # 新增：用于控制更新频率
    
    def set_path(self, path, alt, spd):
        self.path = path
        self.idx = 0
        self.pos = path[0][:]
        self.alt = alt
        self.spd = spd
        self.sim = True
        self.is_paused = False
        self.prog = 0
        self.trav = 0
        # 计算总路径长度（度）
        self.total = sum(dist(path[i], path[i+1]) for i in range(len(path)-1))
        self.start_time = time.time()
        self.last_update_time = time.time()  # 初始化
        self.elapsed = 0
        self.safety_violation = False
        # 清空历史记录
        self.hist = []
    
    def reset(self):
        if self.path:
            self.pos = self.path[0][:]
            self.idx = 0
            self.sim = False
            self.is_paused = False
            self.prog = 0
            self.trav = 0
            self.start_time = None
            self.last_update_time = None
            self.elapsed = 0
            self.safety_violation = False
            self.hist = []
    
    def do_pause(self):
        self.is_paused = True
    
    def do_resume(self):
        self.is_paused = False
    
    def stop(self):
        self.sim = False
        self.is_paused = False
        self.start_time = None
        self.last_update_time = None
    
    def update(self, obstacles_gcj, safe_radius):
        """更新无人机位置 - 每次调用移动固定距离"""
        if not self.sim or self.is_paused:
            return self._hb(obstacles_gcj, safe_radius)
        
        # 计算时间差（用于平滑移动）
        current_time = time.time()
        if self.last_update_time is None:
            self.last_update_time = current_time
            return self._hb(obstacles_gcj, safe_radius)
        
        dt = min(current_time - self.last_update_time, 0.5)  # 限制最大时间差
        self.last_update_time = current_time
        
        # 更新经过时间
        if self.start_time:
            self.elapsed = current_time - self.start_time
        
        # 飞行移动逻辑
        if self.idx < len(self.path) - 1:
            tar = self.path[self.idx + 1]
            dx = tar[0] - self.pos[0]
            dy = tar[1] - self.pos[1]
            distance_to_target = math.hypot(dx, dy)
            
            # 计算这一帧应该移动的距离（度）
            speed_mps = 0.5 + (self.spd / 100) * 4.5  # 速度范围 0.5-5.0 m/s
            step_m = speed_mps * dt  # 根据实际时间差移动
            step_deg = step_m / 111000.0  # 转换为度
            
            if distance_to_target <= step_deg:
                # 到达当前航点，移动到下一个
                self.trav += distance_to_target
                self.pos = tar[:]
                self.idx += 1
                
                # 打印调试信息
                print(f"到达航点 {self.idx}/{len(self.path)-1}, 位置: {self.pos}")
            else:
                # 向目标移动
                ratio = step_deg / distance_to_target
                self.pos[0] += dx * ratio
                self.pos[1] += dy * ratio
                self.trav += step_deg
            
            # 更新进度
            if self.total > 0:
                self.prog = min(1.0, self.trav / self.total)
            
            # 检查是否完成所有航点
            if self.idx >= len(self.path) - 1:
                self.sim = False
                self.prog = 1.0
                print("飞行完成！")
        else:
            self.sim = False
            self.prog = 1.0
        
        # 保存历史位置
        hb_data = self._hb(obstacles_gcj, safe_radius)
        self.hist.insert(0, hb_data)  # 最新数据放在前面
        # 限制历史记录长度
        if len(self.hist) > 1000:
            self.hist = self.hist[:1000]
        
        return hb_data
    
    def _hb(self, obstacles_gcj, safe_radius):
        """生成心跳数据"""
        # 计算当前速度
        if self.sim and not self.is_paused:
            speed = round(0.5 + (self.spd / 100) * 4.5, 1)
        else:
            speed = 0
        
        # 计算剩余距离
        if self.sim and not self.is_paused and self.idx < len(self.path) - 1:
            remaining_in_path = 0.0
            # 到当前目标点的距离
            remaining_in_path += dist(self.pos, self.path[self.idx + 1])
            # 后续航段的总距离
            for i in range(self.idx + 1, len(self.path) - 1):
                remaining_in_path += dist(self.path[i], self.path[i + 1])
            remaining_dist = remaining_in_path * 111000
        else:
            remaining_dist = max(0, self.total - self.trav) * 111000
        
        # 安全检查
        safe, min_d, danger = check_safety_radius(self.pos, obstacles_gcj, self.alt, safe_radius)
        self.safety_violation = not safe
        
        # 电池模拟
        battery = max(0, 100 - int(self.prog * 100))
        
        # 预计剩余时间
        if speed > 0 and remaining_dist > 0:
            eta_sec = remaining_dist / speed
            if eta_sec < 60:
                remain_str = f"{eta_sec:.0f}秒"
            else:
                minutes = int(eta_sec // 60)
                seconds = int(eta_sec % 60)
                remain_str = f"{minutes:02d}:{seconds:02d}"
        else:
            remain_str = "00:00"
        
        # 模拟遥测数据
        voltage = 22.2 + random.uniform(-0.5, 0.5)
        satellites = random.randint(8, 14)
        delay = round(random.uniform(10, 50), 1) if self.sim else 0
        loss = round(random.uniform(0, 0.2), 1) if self.sim else 0
        arrived = not self.sim and self.prog >= 1.0
        
        return {
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "lng": self.pos[0],
            "lat": self.pos[1],
            "altitude": self.alt + random.randint(-5, 5) if self.sim else random.randint(0, 10),
            "speed": speed,
            "progress": self.prog,
            "total": self.total,
            "traveled": self.trav,
            "current_wp": f"{self.idx + 1}/{len(self.path)}",
            "remain": remain_str,
            "battery": battery,
            "elapsed": self.elapsed,
            "delay_ms": delay,
            "loss_percent": loss,
            "simulating": self.sim,
            "paused": self.is_paused,
            "flight_time": self.elapsed,
            "voltage": voltage,
            "satellites": satellites,
            "arrived": arrived,
            "safety_violation": self.safety_violation,
            "remaining_distance": remaining_dist
        }
