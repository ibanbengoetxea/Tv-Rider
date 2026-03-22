import os
import json
import gzip
import lxml.etree as ET
from datetime import datetime, timedelta, timezone
import requests
from dateutil import parser as date_parser

EPG_URL = "https://www.tdtchannels.com/epg/TV.xml.gz"
OUTPUT_DIR = "../output"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "programacion.json")

# TARGET CHANNELS to extract
TARGET_CHANNELS = [
    "La 1", "La 2", "Antena 3", "Cuatro", "Telecinco", 
    "La Sexta", "24h", "Teledeporte", "Clan"
]

def get_channel_id_mapping(root):
    """Maps XML channel IDs to our target channel names and extracts logos."""
    mapping = {}
    
    for channel in root.findall('channel'):
        channel_id = channel.get('id')
        display_names = [dn.text for dn in channel.findall('display-name') if dn.text]
        icon = channel.find('icon')
        logo_url = icon.get('src') if icon is not None else ""
        
        for name in display_names:
            # We check if the name matches one of our targets (case insensitive partial match)
            for target in TARGET_CHANNELS:
                if target.lower() in name.lower() or name.lower() in target.lower():
                    # More strict exact matches for some channels to avoid false positives 
                    # like 'Antena 3 Internacional' or 'La 1 UHD' if we only want 'La 1'.
                    if target == "La 1" and "La 1" not in name: continue
                    if target == "La 2" and "La 2" not in name: continue
                    if target == "24h" and not any(x in name.lower() for x in ["24h", "24 horas", "canal 24 hor"]): continue
                    
                    mapping[channel_id] = {
                        "channel_name": target,
                        "logo_url": logo_url
                    }
                    break
    
    return mapping

def parse_xmltv_date(date_str):
    """Parses XMLTV date format '20260322150000 +0100' or similar."""
    try:
        # e.g., 20260322150000 +0100
        return date_parser.parse(date_str)
    except Exception:
        return None

def main():
    print(f"Downloading EPG from {EPG_URL}...")
    response = requests.get(EPG_URL, stream=True)
    response.raise_for_status()
    
    print("Decompressing and parsing XML...")
    # Read gzipped content
    xml_content = gzip.decompress(response.content)
    root = ET.fromstring(xml_content)
    
    channel_mapping = get_channel_id_mapping(root)
    # Need to group mapping by target name to avoid having multiple channel IDs for the same target
    final_mapping = {}
    for ch_id, ch_meta in channel_mapping.items():
        # Keep the first matching ID for each target channel
        if ch_meta['channel_name'] not in [x['channel_name'] for x in final_mapping.values()]:
            final_mapping[ch_id] = ch_meta
            
    channel_mapping = final_mapping
    
    print(f"Found {len(channel_mapping)} matching channel IDs.")
    
    # Define time window (UTC)
    now = datetime.now(timezone.utc)
    # Start of today (00:00:00)
    start_window = now.replace(hour=0, minute=0, second=0, microsecond=0)
    # Tomorrow 06:00:00
    end_window = start_window + timedelta(days=1, hours=6)
    
    print(f"Time window: {start_window} to {end_window} (UTC)")
    
    # Initialize the structure
    results = {
        meta['channel_name']: {
            "channel_name": meta['channel_name'],
            "logo_url": meta['logo_url'],
            "programs": []
        }
        for meta in channel_mapping.values()
    }
    
    print("Processing programs...")
    for prog in root.findall('programme'):
        channel_id = prog.get('channel')
        
        # Only process if it's one of our target channels
        if channel_id not in channel_mapping:
            continue
            
        start_str = prog.get('start')
        end_str = prog.get('stop')
        
        if not start_str or not end_str:
            continue
            
        start_dt = parse_xmltv_date(start_str)
        end_dt = parse_xmltv_date(end_str)
        
        if not start_dt or not end_dt:
            continue
            
        # Ensure they are timezone aware in UTC for comparison
        if start_dt.tzinfo is None:
            start_dt = start_dt.replace(tzinfo=timezone.utc)
        if end_dt.tzinfo is None:
            end_dt = end_dt.replace(tzinfo=timezone.utc)
            
        # Check if the program overlaps with our time window
        if end_dt <= start_window or start_dt >= end_window:
            continue
            
        # Extract title and description
        title_element = prog.find('title')
        desc_element = prog.find('desc')
        
        title = title_element.text if title_element is not None and title_element.text else "Programación sin título"
        desc = desc_element.text if desc_element is not None and desc_element.text else ""
        
        target_name = channel_mapping[channel_id]['channel_name']
        
        results[target_name]["programs"].append({
            "title": title,
            "desc": desc,
            "start": start_dt.isoformat(),
            "end": end_dt.isoformat()
        })
        
    # Sort programs for each channel by start time
    for ch_name in results:
        results[ch_name]["programs"].sort(key=lambda x: x["start"])
        
    # Convert dict to list
    final_output = list(results.values())
    
    # Output to file
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Writing output to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(final_output, f, ensure_ascii=False, separators=(',', ':'))
        
    print("Done! Validated output.")

if __name__ == "__main__":
    main()
