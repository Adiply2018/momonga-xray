import tkinter as tk
from tkinter import ttk, messagebox
import requests
import json
import base64
import subprocess
import webbrowser
import urllib3
import urllib.parse
from typing import Optional, Dict, List
import re
from PIL import Image, ImageTk
import traceback
import io

class LobbyRevealer:
    def __init__(self):
        self.client_port = None
        self.client_token = None
        self.riot_port = None
        self.riot_token = None
        self.current_summoner = None
        self.region = None
        self.game_phase = None
        self.summoner_names = []
        self.opgg_names = []
        self.riot_ids = []
        self.photo = None
        
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        self.setup_gui()
        self.update_client_status()

    def setup_gui(self):
        self.root = tk.Tk()
        self.root.title("MomongaXray")
        self.root.geometry("360x160")
        self.root.resizable(False, False)

        try:
            response = requests.get("https://ddragon.leagueoflegends.com/cdn/img/champion/splash/Teemo_0.jpg")
            img_data = response.content
            background_image = Image.open(io.BytesIO(img_data))
            
            background_image = background_image.resize((380, 200), Image.Resampling.LANCZOS)
            self.bg_photo = ImageTk.PhotoImage(background_image)
            
            background_label = tk.Label(self.root, image=self.bg_photo)
            background_label.place(x=0, y=0, relwidth=1, relheight=1)
            
        except Exception as e:
            print(f"Error loading background image: {e}")
        
        self.client_status_label = ttk.Label(self.root, text="Client: Not Connected", foreground="black", background="white")
        self.client_status_label.place(x=10, y=8)
        
        self.phase_label = ttk.Label(self.root, text="Status: ", foreground="black", background="white")
        self.phase_label.place(x=10, y=30)
        
        ttk.Button(self.root, text="Get Summoners", command=self.update_client_status).place(x=250, y=10)
        ttk.Button(self.root, text="OP.GG", command=lambda: self.open_site("opgg")).place(x=250, y=40)
        ttk.Button(self.root, text="DEEPLOL", command=lambda: self.open_site("deeplol")).place(x=250, y=70)
        
        style = ttk.Style()
        style.configure("Danger.TButton", foreground="red", font=("Segoe UI", 9, "bold"))
        self.dodge_button = ttk.Button(
            self.root, 
            text="DODGE", 
            style="Danger.TButton",
            command=self.confirm_dodge
        )
        self.dodge_button.place(x=250, y=120)
        
        self.output_text = tk.Text(self.root, width=28, height=7, bg='white', fg='black')
        self.output_text.place(x=10, y=60)

    def get_client_info(self) -> bool:
        try:
            cmd = 'wmic process where name="LeagueClientUx.exe" get commandline'
            output = subprocess.check_output(cmd, shell=True).decode()
            
            app_port_match = re.search('--app-port=([0-9]*)', output)
            auth_token_match = re.search('--remoting-auth-token=([\w-]*)', output)
            riot_port_match = re.search('--riotclient-app-port=([0-9]*)', output)
            riot_token_match = re.search('--riotclient-auth-token=([\w-]*)', output)
            
            if all([app_port_match, auth_token_match, riot_port_match, riot_token_match]):
                self.client_port = app_port_match.group(1)
                self.client_token = auth_token_match.group(1)
                self.riot_port = riot_port_match.group(1)
                self.riot_token = riot_token_match.group(1)
                return True
        except:
            return False
        return False

    def get_auth_headers(self) -> tuple:
        client_basic = base64.b64encode(f"riot:{self.client_token}".encode()).decode()
        client_headers = {
            "Authorization": f"Basic {client_basic}"
        }
        
        riot_basic = base64.b64encode(f"riot:{self.riot_token}".encode()).decode()
        riot_headers = {
            "Authorization": f"Basic {riot_basic}"
        }
        
        return client_headers, riot_headers

    def get_current_summoner(self, client_headers: Dict, riot_headers: Dict) -> bool:
        try:
            response = requests.get(
                f"https://127.0.0.1:{self.client_port}/lol-summoner/v1/current-summoner",
                headers=client_headers,
                verify=False
            )
            self.current_summoner = response.json()["displayName"]
            
            response = requests.get(
                f"https://127.0.0.1:{self.riot_port}/riotclient/region-locale",
                headers=riot_headers,
                verify=False
            )
            self.region = response.json()["region"]
            
            response = requests.get(
                f"https://127.0.0.1:{self.client_port}/lol-gameflow/v1/gameflow-phase",
                headers=client_headers,
                verify=False
            )
            self.game_phase = response.json()
            
            return True
        except Exception as e:
            print(f"Error in get_current_summoner: {e}")
            print(f"Full error details: {traceback.format_exc()}")
            return False

    def get_summoner_names(self, riot_headers: Dict):
        try:
            response = requests.get(
                f"https://127.0.0.1:{self.riot_port}/chat/v5/participants",
                headers=riot_headers,
                verify=False
            )
            
            participants = [p for p in response.json()["participants"] 
                          if p["activePlatform"] == "windows" and 
                          f"{p['game_name']}#{p['game_tag']}" != self.current_summoner]
            
            self.summoner_names.clear()
            self.opgg_names.clear()
            self.riot_ids.clear()
            
            for p in participants:
                display_name = f"{p['game_name']}#{p['game_tag']}"
                self.summoner_names.append(display_name)
                self.opgg_names.append(f"{p['game_name']}%23{p['game_tag']}")
                self.riot_ids.append(f"{p['game_name']}-{p['game_tag']}")
            
            self.output_text.delete(1.0, tk.END)
            self.output_text.insert(tk.END, "\n".join(self.summoner_names))
            
        except Exception as e:
            print(f"Error getting summoner names: {e}")
            print(f"Full error details: {traceback.format_exc()}")

    def update_client_status(self):
        if self.get_client_info():
            client_headers, riot_headers = self.get_auth_headers()
            if self.get_current_summoner(client_headers, riot_headers):
                self.client_status_label.config(text="Client: Connected", foreground="lime")
                self.phase_label.config(text=f"Status: {self.game_phase}")
                
                if self.game_phase == "ChampSelect":
                    self.get_summoner_names(riot_headers)
            else:
                self.client_status_label.config(text="Client: Failed", foreground="red")
        else:
            self.client_status_label.config(text="Client: Not Found", foreground="red")
            self.phase_label.config(text="Status: ")
            self.output_text.delete(1.0, tk.END)

    def open_site(self, site: str):
        if not self.region or not self.summoner_names:
            return
            
        region_codes = {
            "NA": "na1", "EUNE": "eun1", "EUW": "euw1", "KR": "kr",
            "BR": "br1", "JP": "jp1", "RU": "ru", "OCE": "oc1",
            "TR": "tr1", "LAN": "la1", "LAS": "la2"
        }
        
        if site == "opgg":
            if self.game_phase == "InProgress":
                url = f"https://www.op.gg/summoners/{self.region.lower()}/{self.current_summoner}/ingame"
            else:
                names = ",".join(self.opgg_names)
                url = f"https://www.op.gg/multisearch/{self.region.lower()}?summoners={names}"
                
        elif site == "deeplol":
            encoded_names = []
            for name in self.summoner_names:
                name_parts = name.split('#')
                if len(name_parts) == 2:
                    encoded_name = urllib.parse.quote(name_parts[0]) + '%23' + urllib.parse.quote(name_parts[1])
                    encoded_names.append(encoded_name)
            
            names = ",".join(encoded_names)
            url = f"https://www.deeplol.gg/multi/{self.region}/{names}"
        
        webbrowser.open(url)

    def confirm_dodge(self):
        if messagebox.askyesno(
            "Dodge確認", 
            "本当にDodgeしますか？\nクライアントが強制終了されます。",
            icon='warning'
        ):
            subprocess.run(['taskkill', '/f', '/im', 'LeagueClientUx.exe'])

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = LobbyRevealer()
    app.run()
