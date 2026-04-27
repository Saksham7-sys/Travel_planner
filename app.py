import os, sys, csv, subprocess, math
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SPOTS = [
    # Waterfalls
    {"name":"Nohkalikai Falls",          "lat":25.2547,"lng":91.6893,"cat":"waterfall","emoji":"🌊","desc":"Tallest plunge waterfall in India (340 m)"},
    {"name":"Elephant Falls",            "lat":25.5537,"lng":91.8460,"cat":"waterfall","emoji":"🌊","desc":"Three-tiered waterfall near Shillong"},
    {"name":"Krang Suri Falls",          "lat":25.1830,"lng":92.5780,"cat":"waterfall","emoji":"🌊","desc":"Crystal-clear turquoise waterfall, Jaintia Hills"},
    {"name":"Seven Sisters Falls",       "lat":25.2558,"lng":91.7048,"cat":"waterfall","emoji":"🌊","desc":"Nohsngithiang — seven parallel streams"},
    {"name":"Wei Sawdong Falls",         "lat":25.3030,"lng":91.7170,"cat":"waterfall","emoji":"🌊","desc":"Three-tiered hidden waterfall near Cherrapunji"},
    {"name":"Wah Kaba Falls",            "lat":25.2889,"lng":91.6933,"cat":"waterfall","emoji":"🌊","desc":"Scenic seasonal waterfall, Sohra area"},
    # Lakes & Rivers
    {"name":"Umiam Lake",                "lat":25.6527,"lng":91.9060,"cat":"lake","emoji":"🏞️","desc":"Sprawling reservoir — watersports hub"},
    {"name":"Dawki & Umngot River",      "lat":25.1858,"lng":92.0255,"cat":"lake","emoji":"🏞️","desc":"World-famous crystal-clear river"},
    {"name":"Thadlaskein Lake",          "lat":25.4340,"lng":92.2010,"cat":"lake","emoji":"🏞️","desc":"Serene lake near Jowai, Jaintia Hills"},
    # Canyons
    {"name":"Laitlum Canyon",            "lat":25.5210,"lng":91.9510,"cat":"canyon","emoji":"🏔️","desc":"End of Hills — dramatic valley panorama"},
    # Villages
    {"name":"Mawlynnong Village",        "lat":25.2022,"lng":91.9258,"cat":"village","emoji":"🏡","desc":"Asia's cleanest village"},
    {"name":"Mawsynram",                 "lat":25.2978,"lng":91.5818,"cat":"village","emoji":"🏡","desc":"Wettest place on Earth (~11,872 mm/yr)"},
    {"name":"Cherrapunji (Sohra)",       "lat":25.2800,"lng":91.7200,"cat":"village","emoji":"🏡","desc":"Second wettest place, waterfall capital"},
    {"name":"Nongjrong Village",         "lat":25.2700,"lng":91.8600,"cat":"village","emoji":"🏡","desc":"Famous bamboo sky-walk bridge"},
    # Cities
    {"name":"Shillong",                  "lat":25.5788,"lng":91.8933,"cat":"city","emoji":"🏙️","desc":"Capital — Scotland of the East"},
    {"name":"Jowai",                     "lat":25.4494,"lng":92.2029,"cat":"city","emoji":"🏙️","desc":"Capital of Jaintia Hills"},
    {"name":"Tura",                      "lat":25.5145,"lng":90.2132,"cat":"city","emoji":"🏙️","desc":"Capital of West Garo Hills"},
    {"name":"Williamnagar",              "lat":25.4967,"lng":90.6167,"cat":"city","emoji":"🏙️","desc":"Capital of East Garo Hills"},
    {"name":"Nongpoh",                   "lat":25.9044,"lng":92.0091,"cat":"city","emoji":"🏙️","desc":"Gateway town on NH 6 into Meghalaya"},
    # Living Root Bridges
    {"name":"Double Decker Root Bridge", "lat":25.2333,"lng":91.7167,"cat":"bridge","emoji":"🌉","desc":"Iconic two-storey living root bridge, Nongriat"},
    {"name":"Single Root Bridge (Riwai)","lat":25.2020,"lng":91.9255,"cat":"bridge","emoji":"🌉","desc":"Accessible living root bridge near Mawlynnong"},
    # Caves
    {"name":"Mawsmai Cave",              "lat":25.2839,"lng":91.7342,"cat":"cave","emoji":"🕳️","desc":"Popular illuminated limestone cave, Cherrapunji"},
    {"name":"Arwah Cave",                "lat":25.2833,"lng":91.7200,"cat":"cave","emoji":"🕳️","desc":"Fossil-rich cave — 5,000-yr-old marine fossils"},
    {"name":"Siju Cave",                 "lat":25.2833,"lng":90.7167,"cat":"cave","emoji":"🕳️","desc":"Bat Cave — 3rd longest in India"},
    # Forests, Rocks, Treks
    {"name":"Mawphlang Sacred Forest",   "lat":25.4667,"lng":91.7667,"cat":"forest","emoji":"🌿","desc":"Ancient sacred grove preserved 1,000+ years"},
    {"name":"Kyllang Rock",              "lat":25.6167,"lng":91.2500,"cat":"rock","emoji":"🪨","desc":"Giant 2,000-yr-old granite monolith"},
    {"name":"Mawryngkhang Bamboo Trek",  "lat":25.4833,"lng":92.0833,"cat":"trek","emoji":"🥾","desc":"Thrilling bamboo bridge and ridge trek"},
    # National Parks
    {"name":"Balpakram National Park",   "lat":25.0167,"lng":90.8833,"cat":"park","emoji":"🌳","desc":"Land of Spirits — elephants, tigers, rare orchids"},
    {"name":"Nokrek National Park",      "lat":25.4500,"lng":90.2167,"cat":"park","emoji":"🌳","desc":"UNESCO Biosphere Reserve near Tura"},
]

def road_dist(s1, s2):
    R = 6371
    lat1,lng1 = math.radians(s1['lat']),math.radians(s1['lng'])
    lat2,lng2 = math.radians(s2['lat']),math.radians(s2['lng'])
    a = math.sin((lat2-lat1)/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin((lng2-lng1)/2)**2
    return max(1, round(2*R*math.asin(math.sqrt(a)) * 1.5))

@app.route('/')
def index():
    return send_from_directory(BASE_DIR, 'index.html')

@app.route('/api/spots')
def api_spots():
    return jsonify(SPOTS)

@app.route('/api/run-tsp', methods=['POST'])
def api_run_tsp():
    selected = request.get_json(force=True).get('spots', [])
    if len(selected) < 2:
        return jsonify({'error': 'Select at least 2 spots.'}), 400
    if len(selected) > 12:
        return jsonify({'error': 'Select at most 12 spots for exact TSP.'}), 400

    n     = len(selected)
    names = [s['name'] for s in selected]
    adj   = [[road_dist(selected[i],selected[j]) if i!=j else 0 for j in range(n)] for i in range(n)]

    with open(os.path.join(BASE_DIR, 'input.csv'), 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['']+names)
        for i in range(n):
            w.writerow([names[i]]+adj[i])
    print("  input.csv written.")

    exe = os.path.join(BASE_DIR, 'tsp_csv.exe' if sys.platform == 'win32' else 'tsp_csv')
    if not os.path.isfile(exe):
        return jsonify({'error': f'TSP exe not found. Compile with: g++ -O2 -o tsp_csv tsp_csv.cpp'}), 500

    try:
        proc = subprocess.run([exe], capture_output=True, text=True, timeout=120, cwd=BASE_DIR)
    except FileNotFoundError:
        return jsonify({'error': f'Cannot execute {exe}.'}), 500
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'TSP timed out. Try fewer spots.'}), 500

    if proc.returncode != 0:
        return jsonify({'error': f'TSP failed:\n{proc.stderr or proc.stdout}'}), 500

    name_map    = {s['name']:s for s in selected}
    route_steps = []
    total_km    = None

    with open(os.path.join(BASE_DIR, 'output.csv'), 'r', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            step    = row.get('Step','').strip()
            name    = row.get('District','').strip().strip('"')
            cum_str = row.get('Cumulative Distance (km)','').strip().strip('"')
            if step.upper()=='TOTAL':
                try:    total_km = int(cum_str.replace(' km',''))
                except: total_km = cum_str
                continue
            spot = name_map.get(name,{})
            route_steps.append({
                'step':step,'name':name,'cumulative_km':cum_str,
                'lat':spot.get('lat'),'lng':spot.get('lng'),
                'cat':spot.get('cat',''),'emoji':spot.get('emoji','📍'),
                'desc':spot.get('desc',''),
            })

    return jsonify({'route':route_steps,'total_km':total_km})

if __name__=='__main__':
    exe = os.path.join(BASE_DIR, 'tsp_csv.exe' if sys.platform=='win32' else 'tsp_csv')
    print("\n"+"="*54)
    print("   TripTrekker  ·  Meghalaya Route Planner")
    print("="*54)
    print(f"   TSP exe : {'OK' if os.path.isfile(exe) else 'MISSING  → g++ -O2 -o '+exe+' tsp_csv.cpp'}")
    print(f"   Spots   : {len(SPOTS)} Meghalaya locations (no API)")
    print("   URL     : http://localhost:5000")
    print("="*54+"\n")
    app.run(debug=True, port=5000)
    