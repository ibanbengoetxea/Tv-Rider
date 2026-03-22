import os
import json
import gzip
import lxml.etree as ET
from datetime import datetime, timedelta, timezone
import requests
from dateutil import parser as date_parser

EPG_URL = "https://www.tdtchannels.com/epg/TV.xml.gz"
# Ensure the output stays inside the repository folder
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), "output")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "programacion.json")

# TARGET CHANNELS to extract
TARGET_CHANNELS = {
    "La 1": ["la 1", "la1", "tve 1"],
    "La 2": ["la 2", "la2", "tve 2"],
    "Antena 3": ["antena 3", "antena3"],
    "Cuatro": ["cuatro"],
    "Telecinco": ["telecinco"],
    "La Sexta": ["la sexta", "lasexta"],
    "24h": ["24h", "24 horas", "canal 24h"],
    "Teledeporte": ["teledeporte", "tdp"],
    "Clan": ["clan"]
}

def get_channel_id_mapping(root):
    """Maps XML channel IDs to our target channel names and extracts logos."""
    mapping = {}
    
    for channel in root.findall('channel'):
        channel_id = channel.get('id')
        display_names = [dn.text.lower() for dn in channel.findall('display-name') if dn.text]
        icon = channel.find('icon')
        logo_url = icon.get('src') if icon is not None else ""
        
        for target_name, aliases in TARGET_CHANNELS.items():
            # Avoid adding multiple versions (like CAT or CAN) if we already have the main one
            if target_name in [m['channel_name'] for m in mapping.values()]:
                continue
                
            is_match = False
            for alias in aliases:
                for dn in display_names:
                    # Looser matching to catch "La 1", "La 1 HD", etc.
                    if alias in dn:
                        is_match = True
                        break
                if is_match: break
            
            if is_match:
                mapping[channel_id] = {
                    "channel_name": target_name,
                    "logo_url": logo_url
                }
    
    return mapping

def parse_xmltv_date(date_str):
    """Parses XMLTV date format '20260322150000 +0100' or similar."""
    try:
        return date_parser.parse(date_str)
    except Exception:
        return None

def main():
    print(f"Downloading EPG from {EPG_URL}...")
    response = requests.get(EPG_URL, stream=True)
    response.raise_for_status()
    
    print("Decompressing and parsing XML...")
    xml_content = gzip.decompress(response.content)
    root = ET.fromstring(xml_content)
    
    channel_mapping = get_channel_id_mapping(root)
    print(f"Found {len(channel_mapping)} matching channel IDs.")
    
    # Define time window (UTC)
    now = datetime.now(timezone.utc)
    start_window = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_window = start_window + timedelta(days=1, hours=6)
    
    print(f"Time window: {start_window} to {end_window} (UTC)")
    
    results = {
        name: {
            "channel_name": name,
            "logo_url": meta['logo_url'],
            "programs": []
        }
        for ch_id, meta in channel_mapping.items()
        for name in [meta['channel_name']]
    }
    
    # Pre-populate empty channels just in case
    for name in TARGET_CHANNELS.keys():
        if name not in results:
            results[name] = {"channel_name": name, "logo_url": "", "programs": []}

    print("Processing programs...")
    for prog in root.findall('programme'):
        channel_id = prog.get('channel')
        if channel_id not in channel_mapping:
            continue
            
        start_str = prog.get('start')
        end_str = prog.get('stop')
        if not start_str or not end_str: continue
            
        start_dt = parse_xmltv_date(start_str)
        end_dt = parse_xmltv_date(end_str)
        if not start_dt or not end_dt: continue
            
        if start_dt.tzinfo is None:
            start_dt = start_dt.replace(tzinfo=timezone.utc)
        if end_dt.tzinfo is None:
            end_dt = end_dt.replace(tzinfo=timezone.utc)
            
        if end_dt <= start_window or start_dt >= end_window:
            continue
            
        title_element = prog.find('title')
        desc_element = prog.find('desc')
        title = title_element.text if title_element is not None and title_element.text else "Programación"
        desc = desc_element.text if desc_element is not None and desc_element.text else ""
        
        target_name = channel_mapping[channel_id]['channel_name']
        results[target_name]["programs"].append({
            "title": title,
            "desc": desc,
            "start": start_dt.isoformat(),
            "end": end_dt.isoformat()
        })
        
    for ch_name in results:
        results[ch_name]["programs"].sort(key=lambda x: x["start"])
        
    final_output = list(results.values())
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Writing output to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(final_output, f, ensure_ascii=False, separators=(',', ':'))
        
    print(f"Done! Processed {len(final_output)} channels.")

if __name__ == "__main__":
    main()
