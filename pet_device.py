import json
import random
import time
import ssl
import paho.mqtt.client as mqtt
from config import *

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("[MQTT] Successfully connected to EMQX Cloud Broker!")
        # 订阅控制指令主题
        client.subscribe(TOPIC_COMMAND, qos=1)
        print(f"[MQTT] Subscribed to topic: {TOPIC_COMMAND}")
    else:
        print(f"[MQTT] Connection failed with code {rc}")

def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode('utf-8')
        print(f"\n[Received Command] Topic: {msg.topic} | Payload: {payload}")
        data = json.loads(payload)
        # 示例：处理云端下发的喂食指令
        if data.get("action") == "feed":
            amount = data.get("amount", 50)
            print(f">>> [Action Executed] Feeding pet {amount}g of food now! 🍖")
    except Exception as e:
        print(f"[Error] Failed to parse incoming message: {e}")

def main():
    # 初始化 MQTT 客户端（使用 paho-mqtt v2.x 推荐的 CallbackAPIVersion）
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=CLIENT_ID)
    
    if USERNAME and PASSWORD:
        client.username_pw_set(USERNAME, PASSWORD)

    client.on_connect = on_connect
    client.on_message = on_message

    # 配置 TLS/SSL 安全连接（使用同目录下的 CA 证书）
    try:
        client.tls_set(
            ca_certs="emqxsl-ca.crt",
            tls_version=ssl.PROTOCOL_TLS_CLIENT
        )
        print("[TLS] CA certificate loaded successfully.")
    except Exception as e:
        print(f"[Warning] Failed to load 'emqxsl-ca.crt': {e}")
        print("[Warning] Ensure 'emqxsl-ca.crt' is in the current directory before connecting.")

    print(f"[Connecting] Connecting to {BROKER_HOST}:{BROKER_PORT}...")
    try:
        client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
    except Exception as e:
        print(f"[Connection Error]: {e}")
        print("请检查网络、Broker 地址及 CA 证书文件是否正确。")
        return

    # 启动后台网络循环
    client.loop_start()

    print("\n==============================================")
    print(" Smart Pet Feeder Device Simulator Started")
    print(" Reporting telemetry data every 5 seconds...")
    print(" Press Ctrl+C to exit.")
    print("==============================================\n")

    try:
        while True:
            # 1. 模拟动态数据生成
            temperature = round(random.uniform(20.0, 32.0), 1)       # 环境温度 (°C)
            food_percentage = max(0, round(random.uniform(10.0, 100.0), 1))  # 剩余粮量 (%)
            
            # 设备状态判断
            if food_percentage < 20.0:
                status = "low_food_warning"
            else:
                status = "normal"

            payload_data = {
                "device_id": CLIENT_ID,
                "timestamp": int(time.time()),
                "temperature": temperature,
                "food_percentage": food_percentage,
                "status": status
            }

            payload_str = json.dumps(payload_data)

            # 2. 发布数据到 MQTT Broker
            result = client.publish(TOPIC_TELEMETRY, payload_str, qos=1)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"[Publish] Sent -> Temp: {temperature}°C | Food: {food_percentage}% | Status: {status}")
            else:
                print(f"[Publish Error] Code: {result.rc}")

            # 3. 每 5 秒上报一次
            time.sleep(5)

    except KeyboardInterrupt:
        print("\n[Disconnecting] Stopping device simulator...")
        client.loop_stop()
        client.disconnect()
        print("[Exit] Device stopped safely.")

if __name__ == "__main__":
    main()
