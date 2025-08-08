import asyncio  
import random  
import ssl  
import json  
import time  
import uuid  
import base64  
import aiohttp  
import socket  
from datetime import datetime, timedelta  
from colorama import init, Fore, Style  
from websockets_proxy import Proxy, proxy_connect  
from urllib.parse import urlparse  
  
# Initialize colorama  
init(autoreset=True)  
  
class AndroidGrassFarmer:  
    def __init__(self):  
        self.device_db = self.load_device_db()  
        self.current_fingerprint = None  
        self.session_stats = {  
            'total': 0,  
            'success': 0,  
            'failures': 0,  
            'rotations': 0  
        }  
          
        # Zona waktu per negara  
        self.timezones = {  
            "KR": 9, "VN": 7, "ID": 7, "BR": -3, "US": -8,  
            "CN": 8, "IN": 5.5, "ES": 2, "RU": 3, "PL": 2,  
            "TH": 7, "PH": 8, "MY": 8, "BD": 6, "MX": -6, "PK": 5  
        }  
          
        # Profil jaringan  
        self.network_profiles = {  
            '4g': {'latency': (100, 300), 'jitter': (10, 50)},  
            '5g': {'latency': (30, 100), 'jitter': (5, 20)},  
            'wifi': {'latency': (5, 30), 'jitter': (1, 10)}  
        }  
          
        # Banner  
        self.banner = f"""{Fore.CYAN}  
   _____ _____ _____ _____   _____ _____ _____ _____ _____   
  / ____|  __ \_   _/ ____| |  __ \_   _/ ____|_   _|  __ \\  
 | |  __| |__) || || |      | |__) || || |  __  | | | |__) |  
 | | |_ |  _  / | || |      |  ___/ | || | |_ | | | |  _  /   
 | |__| | | \ \_| || |____  | |    _| || |__| |_| |_| | \ \\  
  \_____|_|  \_\_____\_____| |_|   |_____\_____|_____|_|  \_\\  
        {Style.RESET_ALL}"""  
  
    def load_device_db(self):  
        """Muat database perangkat dari file"""  
        try:  
            with open('device_database.json', 'r') as f:  
                return json.load(f)  
        except Exception as e:  
            print(f"{Fore.RED}Error loading device database: {str(e)}")  
            print(f"Using fallback device database{Style.RESET_ALL}")  
              
            # Fallback minimal jika file tidak ada  
            return {  
                "samsung": {  
                    "midrange": [  
                        {  
                            "model": "SM-A546E",  
                            "name": "Galaxy A54 5G",  
                            "res": "1080x2400",  
                            "dpi": 400,  
                            "cpu": "arm64-v8a",  
                            "countries": ["ID", "VN", "TH"]  
                        }  
                    ]  
                }  
            }  
  
    def generate_fingerprint(self):  
        """Buat identitas perangkat Android yang unik"""  
        brand = random.choice(list(self.device_db.keys()))  
        device_type = random.choice(list(self.device_db[brand].keys()))  
        device = random.choice(self.device_db[brand][device_type])  
          
        android_ver = random.choice([  
            {"os": "Android 14", "build": "UP1A.231005.007", "sdk": 34},  
            {"os": "Android 13", "build": "TP1A.220624.014", "sdk": 33},  
            {"os": "Android 12", "build": "SP2A.220405.004", "sdk": 32}  
        ])  
          
        country = random.choice(device["countries"])  
        network_type = random.choice(list(self.network_profiles.keys()))  
        network_profile = self.network_profiles[network_type]  
          
        self.current_fingerprint = {  
            "device": {  
                "brand": brand,  
                "model": device['model'],  
                "name": device['name'],  
                "resolution": device['res'],  
                "dpi": device['dpi'],  
                "cpu": device['cpu'],  
                "android": android_ver,  
                "country": country,  
                "unique_ids": {  
                    "android_id": base64.b64encode(uuid.uuid4().bytes).decode()[:16],  
                    "ad_id": str(uuid.uuid4())  
                }  
            },  
            "network": {  
                "type": network_type,  
                "latency_ms": random.randint(*network_profile['latency']),  
                "jitter_ms": random.randint(*network_profile['jitter'])  
            },  
            "user_agent": (  
                f"Mozilla/5.0 (Linux; Android {android_ver['os']}; "  
                f"{device['model']} Build/{android_ver['build']}) "  
                "AppleWebKit/537.36 (KHTML, like Gecko) "  
                "Chrome/122.0.6261.90 Mobile Safari/537.36"  
            )  
        }  
        self.session_stats['rotations'] += 1  
  
    def get_local_time(self):  
        """Dapatkan waktu lokal berdasarkan negara perangkat"""  
        country = self.current_fingerprint['device']['country']  
        utc_offset = self.timezones.get(country, 0)  
        return datetime.utcnow() + timedelta(hours=utc_offset)  
  
    def get_activity_level(self):  
        """Tentukan tingkat aktivitas berdasarkan waktu lokal"""  
        local_time = self.get_local_time()  
        hour = local_time.hour  
          
        if 8 <= hour <= 20:  # Waktu aktif  
            return random.choices(  
                ["high", "medium", "low"],  
                weights=[0.6, 0.3, 0.1]  
            )[0]  
        else:  # Waktu tidur  
            return random.choices(  
                ["medium", "low", "idle"],  
                weights=[0.3, 0.5, 0.2]  
            )[0]  
  
    async def human_like_delay(self, activity_level):  
        """Generate delay seperti manusia"""  
        if activity_level == "high":  
            return random.uniform(0.5, 2.0)  
        elif activity_level == "medium":  
            return random.uniform(2.0, 5.0)  
        elif activity_level == "low":  
            return random.uniform(5.0, 15.0)  
        else:  # idle  
            return random.uniform(15.0, 60.0)  
  
    def get_network_delay(self):  
        """Hitung delay jaringan yang realistis"""  
        base_latency = self.current_fingerprint['network']['latency_ms'] / 1000  
        jitter = (random.random() * 0.1) - 0.05  # Jitter ±5%  
        return base_latency * (1 + jitter)  
  
    def get_mobile_headers(self):  
        """Generate header khusus perangkat mobile"""  
        return {  
            "User-Agent": self.current_fingerprint['user_agent'],  
            "X-Requested-With": "com.android.chrome",  
            "Sec-CH-UA-Mobile": "?1",  
            "Sec-CH-UA-Platform": "\"Android\"",  
            "Accept-Language": "en-US,en;q=0.9",  
            "X-Device-Id": self.current_fingerprint['device']['unique_ids']['android_id'],  
            "X-Country": self.current_fingerprint['device']['country']  
        }  
  
    async def mobile_session(self, proxy_url, user_id):  
        """Sesi utama untuk koneksi perangkat Android"""  
        self.generate_fingerprint()  
        device_id = f"{self.current_fingerprint['device']['brand']}:{self.current_fingerprint['device']['unique_ids']['android_id']}"  
        country = self.current_fingerprint['device']['country']  
        model = self.current_fingerprint['device']['model']  
          
        try:  
            # Delay awal seperti pengguna membuka aplikasi  
            await asyncio.sleep(random.uniform(1.0, 3.0))  
              
            # Konfigurasi SSL untuk perangkat Android  
            ssl_context = ssl.create_default_context()  
            ssl_context.set_ciphers('ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256')  
            ssl_context.options |= ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1  
              
            # Siapkan header  
            headers = self.get_mobile_headers()  
            headers.update({  
                "Origin": "android-app://com.getgrass.app",  
                "Grass-Device-Info": base64.b64encode(json.dumps({  
                    "brand": self.current_fingerprint['device']['brand'],  
                    "model": model,  
                    "os_version": self.current_fingerprint['device']['android']['os'],  
                    "country": country  
                }).encode()).decode()  
            })  
              
            # Koneksi WebSocket  
            async with proxy_connect(  
                "wss://proxy.wynd.network:4444",  
                proxy=Proxy.from_url(proxy_url),  
                ssl=ssl_context,  
                extra_headers=headers,  
                ping_interval=None,  
                socket=socket.socket(socket.AF_INET6 if random.random() > 0.5 else socket.AF_INET, socket.SOCK_STREAM)  
            ) as ws:  
                self.session_stats['total'] += 1  
                self.log(f"Session started in {country} ({model})", "INFO", proxy_url)  
                  
                # Otentikasi  
                auth_payload = {  
                    "id": str(uuid.uuid4()),  
                    "action": "AUTH",  
                    "data": {  
                        "browser_id": device_id,  
                        "user_id": user_id,  
                        "user_agent": self.current_fingerprint['user_agent'],  
                        "timestamp": int(time.time()) - random.randint(0, 3600),  
                        "device_type": "mobile",  
                        "platform": "android",  
                        "device_model": model,  
                        "country": country,  
                        "version": f"4.{random.randint(20,30)}.0"  
                    }  
                }  
                await ws.send(json.dumps(auth_payload))  
                  
                # Tentukan tingkat aktivitas  
                activity_level = self.get_activity_level()  
                await asyncio.sleep(await self.human_like_delay(activity_level))  
                  
                # Loop interaksi utama  
                while True:  
                    try:  
                        # Kirim ping  
                        ping_data = {  
                            "id": str(uuid.uuid4()),  
                            "action": "PING",  
                            "data": {  
                                "battery_level": random.randint(20, 95),  
                                "network": self.current_fingerprint['network']['type']  
                            }  
                        }  
                        await ws.send(json.dumps(ping_data))  
                          
                        # Tunggu respons  
                        response = await asyncio.wait_for(ws.recv(), timeout=30)  
                        msg = json.loads(response)  
                          
                        if msg.get("action") == "PONG":  
                            await asyncio.sleep(random.uniform(0.1, 0.5))  # Delay manusia  
                            await ws.send(json.dumps({  
                                "id": msg["id"],  
                                "action": "PONG_ACK"  
                            }))  
                          
                        # Perbarui aktivitas secara periodik  
                        if random.random() < 0.1:  
                            activity_level = self.get_activity_level()  
                          
                        # Delay antar aksi  
                        await asyncio.sleep(await self.human_like_delay(activity_level))  
                              
                    except asyncio.TimeoutError:  
                        self.log(f"Timeout in {country}, reconnecting...", "WARNING", proxy_url)  
                        break  
                          
        except Exception as e:  
            self.session_stats['failures'] += 1  
            self.log(f"Session error: {str(e)}", "ERROR", proxy_url)  
        else:  
            self.session_stats['success'] += 1  
            self.log("Session completed successfully", "INFO", proxy_url)  
        finally:  
            # Delay sebelum sesi berikutnya  
            await asyncio.sleep(random.uniform(10, 30))  
  
    def log(self, message, level, proxy=None):  
        """Logging yang dioptimalkan"""  
        colors = {  
            "INFO": Fore.GREEN,  
            "WARNING": Fore.YELLOW,  
            "ERROR": Fore.RED,  
            "DEBUG": Fore.BLUE  
        }  
        timestamp = datetime.now().strftime("%H:%M:%S")  
        device_model = self.current_fingerprint['device']['model'] if self.current_fingerprint else "UNKNOWN"  
        country = self.current_fingerprint['device']['country'] if self.current_fingerprint else "??"  
          
        # Sembunyikan detail proxy di log  
        proxy_display = urlparse(proxy).hostname if proxy else "No Proxy"  
          
        print(f"{Fore.WHITE}[{timestamp}] {colors.get(level, Fore.WHITE)}[{level}] {Fore.CYAN}[{country}] {Fore.MAGENTA}[{device_model}] {message} {Fore.LIGHTBLACK_EX}({proxy_display})")  
  
async def main():  
    farmer = AndroidGrassFarmer()  
      
    print(farmer.banner)  
    print(f"{Fore.YELLOW}Android Grass Farmer - Advanced Anti-Detection System")  
    print(f"Version 2.0 | Designed for Stability{Style.RESET_ALL}\n")  
      
    # Dapatkan User ID  
    user_id = input(f"{Fore.GREEN}Enter your Grass User ID: {Style.RESET_ALL}").strip()  
      
    # Muat proxy  
    try:  
        with open('proxy_list.txt', 'r') as f:  
            proxies = [line.strip() for line in f.readlines() if line.strip() and not line.startswith('#')]  
    except Exception as e:  
        print(f"{Fore.RED}Error loading proxies: {str(e)}{Style.RESET_ALL}")  
        return  
      
    if not proxies:  
        print(f"{Fore.RED}No proxies found! Add proxies to proxy_list.txt{Style.RESET_ALL}")  
        return  
      
    print(f"{Fore.GREEN}Loaded {len(proxies)} proxies{Style.RESET_ALL}")  
    print(f"{Fore.YELLOW}Starting farming sessions...{Style.RESET_ALL}\n")  
      
    # Mulai sesi  
    tasks = []  
    for proxy in proxies:  
        task = asyncio.create_task(farmer.mobile_session(proxy, user_id))  
        tasks.append(task)  
        await asyncio.sleep(0.5)  # Stagger connections  
      
    await asyncio.gather(*tasks)  
  
if __name__ == "__main__":  
    try:  
        asyncio.run(main())  
    except KeyboardInterrupt:  
        print(f"\n{Fore.RED}Stopped by user{Style.RESET_ALL}")  
        print("\nSession Report:")  
        print(f"Total sessions: {Fore.CYAN}{farmer.session_stats['total']}")  
        print(f"Successful: {Fore.GREEN}{farmer.session_stats['success']}")  
        print(f"Failures: {Fore.RED}{farmer.session_stats['failures']}")  
        print(f"Device rotations: {Fore.YELLOW}{farmer.session_stats['rotations']}")