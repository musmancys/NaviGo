import os
import sys
import json
import uuid
import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.app.db.sqlite_demo import get_db_connection, init_demo_db

DESTINATIONS = [
    # ── Northern Mountains ──────────────────────────────────────────
    {
        "id": str(uuid.uuid4()), "slug": "naran", "name": "Naran",
        "sub_title": "Alpine valley with lakes, rivers, and the Babusar Top gateway.",
        "about": "A breathtaking town in Kaghan Valley famous for Saif-ul-Malook Lake, river rafting on Kunhar River, and the road to Babusar Top. Best time to visit is May to September.",
        "hero_image_url": "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=1600&q=80",
        "from_price_pkr": 12000, "tags": ["Nature", "Adventure", "Lakes"], "best_season": "May – September",
        "latitude": 34.9089, "longitude": 73.6528
    },
    {
        "id": str(uuid.uuid4()), "slug": "hunza", "name": "Hunza",
        "sub_title": "Land of forts, apricot blossoms, and dramatic mountain peaks.",
        "about": "A jewel of Gilgit-Baltistan known for Baltit Fort, Altit Fort, turquoise Attabad Lake, and unforgettable mountain hospitality.",
        "hero_image_url": "https://images.unsplash.com/photo-1589308078059-be1415eab4c3?auto=format&fit=crop&w=1600&q=80",
        "from_price_pkr": 22000, "tags": ["Mountains", "Culture", "Scenic"], "best_season": "April – October",
        "latitude": 36.3167, "longitude": 74.6500
    },
    {
        "id": str(uuid.uuid4()), "slug": "skardu", "name": "Skardu",
        "sub_title": "Gateway to the Karakoram — lakes, deserts, and glaciers.",
        "about": "Gateway to K2 featuring Shangrila Resort, Upper Kachura Lake, Sarfaranga Cold Desert, and Deosai National Park.",
        "hero_image_url": "https://images.unsplash.com/photo-1509316785289-025f5b846b35?auto=format&fit=crop&w=1600&q=80",
        "from_price_pkr": 25000, "tags": ["Adventure", "Landscapes", "Trekking"], "best_season": "May – October",
        "latitude": 35.2971, "longitude": 75.6333
    },
    {
        "id": str(uuid.uuid4()), "slug": "swat", "name": "Swat",
        "sub_title": "The Switzerland of Pakistan — rivers, meadows, pine forests.",
        "about": "Lush meadows, Swat River, Malam Jabba ski resort, Kalam Valley, and ancient Buddhist archaeological sites.",
        "hero_image_url": "https://images.unsplash.com/photo-1533130061792-64b345e4a833?auto=format&fit=crop&w=1600&q=80",
        "from_price_pkr": 10000, "tags": ["Nature", "Relaxation", "Rivers"], "best_season": "March – November",
        "latitude": 35.2227, "longitude": 72.4258
    },
    {
        "id": str(uuid.uuid4()), "slug": "murree", "name": "Murree",
        "sub_title": "Classic hill station — pine trees, cool air, and Mall Road.",
        "about": "Pakistan's most historic hill station, nestled in the Pir Panjal range just an hour's drive from Islamabad.",
        "hero_image_url": "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?auto=format&fit=crop&w=1600&q=80",
        "from_price_pkr": 6000, "tags": ["Hills", "Weekend", "Family"], "best_season": "All Year",
        "latitude": 33.9070, "longitude": 73.3943
    },
    {
        "id": str(uuid.uuid4()), "slug": "kashmir", "name": "Kashmir",
        "sub_title": "Heaven on earth — Neelum Valley, houseboats, and lush meadows.",
        "about": "Azad Jammu & Kashmir offers dramatic valleys, dense pine forests, pristine streams, and alpine lakes from Neelum to Rawalakot.",
        "hero_image_url": "https://images.unsplash.com/photo-1595815771614-ade9d652a65d?auto=format&fit=crop&w=1600&q=80",
        "from_price_pkr": 18000, "tags": ["Lakes", "Paradise", "Valleys"], "best_season": "April – October",
        "latitude": 34.5959, "longitude": 73.9142
    },
    {
        "id": str(uuid.uuid4()), "slug": "gilgit", "name": "Gilgit",
        "sub_title": "Gateway to the northern valleys, rivers, and rugged peaks.",
        "about": "Gilgit is the bustling crossroads of the Karakoram Highway and entry point to Hunza, Skardu, and Ghizer.",
        "hero_image_url": "https://images.unsplash.com/photo-1519681393784-d120267933ba?auto=format&fit=crop&w=1600&q=80",
        "from_price_pkr": 20000, "tags": ["Valleys", "Rivers", "Transit"], "best_season": "May – October",
        "latitude": 35.9208, "longitude": 74.3144
    },
    {
        "id": str(uuid.uuid4()), "slug": "fairy", "name": "Fairy Meadows",
        "sub_title": "Green pastures at the foot of Nanga Parbat.",
        "about": "Fairy Meadows is a high-altitude alpine pasture offering jaw-dropping views of Nanga Parbat (8,126m). Unmatched stargazing and trekking.",
        "hero_image_url": "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=1600&q=80",
        "from_price_pkr": 8500, "tags": ["Meadows", "Nanga Parbat", "Camping"], "best_season": "June – September",
        "latitude": 35.3850, "longitude": 74.5775
    },

    # ── Major Cities ────────────────────────────────────────────────
    {
        "id": str(uuid.uuid4()), "slug": "lahore", "name": "Lahore",
        "sub_title": "The cultural capital — Mughal heritage, food streets, and vibrant arts.",
        "about": "Pakistan's heart of culture and cuisine. Home to the iconic Badshahi Mosque, Lahore Fort (UNESCO), Walled City, Data Darbar, and the legendary Gawalmandi Food Street. A must-visit city.",
        "hero_image_url": "https://images.unsplash.com/photo-1597040663342-45b6af3d91a5?auto=format&fit=crop&w=1600&q=80",
        "from_price_pkr": 5000, "tags": ["Heritage", "Food", "Culture", "History"], "best_season": "October – March",
        "latitude": 31.5497, "longitude": 74.3436
    },
    {
        "id": str(uuid.uuid4()), "slug": "karachi", "name": "Karachi",
        "sub_title": "City of lights — beaches, seafood, and Pakistan's commercial hub.",
        "about": "Pakistan's largest city and economic capital. Clifton Beach, Sea View, Do Darya seafood restaurants, Quaid's Mausoleum, Mohatta Palace Museum, and vibrant street food culture make it unmissable.",
        "hero_image_url": "https://images.unsplash.com/photo-1567168544813-cc03465b4fa8?auto=format&fit=crop&w=1600&q=80",
        "from_price_pkr": 4000, "tags": ["Coastal", "Urban", "Seafood", "Culture"], "best_season": "November – February",
        "latitude": 24.8607, "longitude": 67.0011
    },
    {
        "id": str(uuid.uuid4()), "slug": "islamabad", "name": "Islamabad",
        "sub_title": "Pakistan's green capital — Faisal Mosque, Margalla Hills, and modern living.",
        "about": "Pakistan's planned capital city. The iconic Faisal Mosque, Margalla Hills hiking trails, Daman-e-Koh viewpoint, Pakistan Monument, Centaurus Mall, and pristine parks make it the country's most organized city.",
        "hero_image_url": "https://images.unsplash.com/photo-1596422846543-75c6fc197f07?auto=format&fit=crop&w=1600&q=80",
        "from_price_pkr": 6000, "tags": ["Capital", "Nature", "Modern", "Hiking"], "best_season": "All Year",
        "latitude": 33.6844, "longitude": 73.0479
    },
    {
        "id": str(uuid.uuid4()), "slug": "peshawar", "name": "Peshawar",
        "sub_title": "Gateway to the Khyber — ancient bazaars, Pathan hospitality, and history.",
        "about": "One of the world's oldest cities. Qissa Khwani Bazaar (Storytellers' Bazaar), Mahabat Khan Mosque, Bala Hissar Fort, Peshawar Museum, and famous Namak Mandi chapli kebabs draw visitors year-round.",
        "hero_image_url": "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?auto=format&fit=crop&w=1600&q=80",
        "from_price_pkr": 5500, "tags": ["History", "Culture", "Food", "Heritage"], "best_season": "October – April",
        "latitude": 34.0150, "longitude": 71.5249
    },
    {
        "id": str(uuid.uuid4()), "slug": "quetta", "name": "Quetta",
        "sub_title": "Fruit capital of Pakistan — Hanna Lake, Ziarat, and Baloch culture.",
        "about": "The cool high-altitude capital of Balochistan. Known for Hanna Lake, Urak Valley orchards, Quaid-e-Azam Residency in Ziarat, and the vibrant Liaquat Bazaar. Famous for dried fruits, pomegranates, and apples.",
        "hero_image_url": "https://images.unsplash.com/photo-1578662996442-48f60103fc96?auto=format&fit=crop&w=1600&q=80",
        "from_price_pkr": 7000, "tags": ["Mountains", "Culture", "Fruits", "Scenic"], "best_season": "April – October",
        "latitude": 30.1798, "longitude": 66.9750
    },
    {
        "id": str(uuid.uuid4()), "slug": "multan", "name": "Multan",
        "sub_title": "City of Saints — Sufi shrines, blue pottery, and mangoes.",
        "about": "Known as the City of Saints and Pirs. Shah Rukn-e-Alam shrine, Bahauddin Zakariya tomb, Multan Fort, famous blue pottery crafts, and the world-renowned Chaunsa mangoes make Multan a unique cultural destination.",
        "hero_image_url": "https://images.unsplash.com/photo-1559827291-72ee739d0d9a?auto=format&fit=crop&w=1600&q=80",
        "from_price_pkr": 4500, "tags": ["Sufi", "Heritage", "Culture", "Crafts"], "best_season": "October – March",
        "latitude": 30.1575, "longitude": 71.5249
    },

    # ── Coastal ─────────────────────────────────────────────────────
    {
        "id": str(uuid.uuid4()), "slug": "gwadar", "name": "Gwadar",
        "sub_title": "Arabia Sea jewel — golden beaches, CPEC port, and deep-sea fishing.",
        "about": "Pakistan's emerging port city on the Arabia Sea. Hammerhead Beach, Padi Zirr Beach, CPEC deep-water port, Koh-e-Batil, and fresh seafood from local fishermen make Gwadar a rising travel destination.",
        "hero_image_url": "https://images.unsplash.com/photo-1505118380757-91f5f5632de0?auto=format&fit=crop&w=1600&q=80",
        "from_price_pkr": 8000, "tags": ["Coastal", "Beach", "CPEC", "Fishing"], "best_season": "October – April",
        "latitude": 25.1216, "longitude": 62.3254
    },

    # ── Heritage Sites ───────────────────────────────────────────────
    {
        "id": str(uuid.uuid4()), "slug": "taxila", "name": "Taxila",
        "sub_title": "UNESCO World Heritage — ancient Gandhara Buddhist civilization.",
        "about": "One of the greatest archaeological sites in South Asia. Taxila Museum, Sirkap ancient city ruins, Dharmarajika Stupa, and Jaulian Monastery showcase 5,000 years of Gandhara civilization.",
        "hero_image_url": "https://images.unsplash.com/photo-1591020547040-e8d4e6a59bd7?auto=format&fit=crop&w=1600&q=80",
        "from_price_pkr": 3000, "tags": ["Heritage", "UNESCO", "History", "Archaeology"], "best_season": "October – April",
        "latitude": 33.7463, "longitude": 72.8375
    },
]

PLACES = [
    # ── Naran ────────────────────────────────────────────────────────
    {"id": "p-nar-1", "dest": "naran", "name": "Saif-ul-Malook Lake", "type": "attraction", "icon": "🏔️", "lat": 34.8786, "lng": 73.6931, "x": 32, "y": 38, "desc": "Legendary alpine lake with fairytale folklore and boat rides.", "price": "Rs. 500 Entry", "rating": 4.8},
    {"id": "p-nar-2", "dest": "naran", "name": "Lulusar Lake", "type": "attraction", "icon": "🏔️", "lat": 35.0833, "lng": 73.9167, "x": 58, "y": 28, "desc": "W-shaped pristine lake reflecting snow-capped peaks en route Babusar.", "price": "Free", "rating": 4.7},
    {"id": "p-nar-3", "dest": "naran", "name": "Babusar Top", "type": "attraction", "icon": "🏔️", "lat": 35.1500, "lng": 74.0500, "x": 78, "y": 22, "desc": "Panoramic mountain pass at 4,173m elevation connecting Kaghan to Chilas.", "price": "Free", "rating": 4.9},
    {"id": "p-nar-4", "dest": "naran", "name": "Pine Park Hotel Naran", "type": "hotel", "icon": "🏨", "lat": 34.9080, "lng": 73.6510, "x": 44, "y": 55, "desc": "Comfortable family hotel with mountain views and hot water.", "price": "Rs. 8,500/night", "rating": 4.6},
    {"id": "p-nar-5", "dest": "naran", "name": "Kunhar Trout Fish Restaurant", "type": "restaurant", "icon": "🍽️", "lat": 34.9095, "lng": 73.6540, "x": 66, "y": 62, "desc": "Fresh river trout fried to perfection, karahi, and chapli kebabs.", "price": "Rs. 1,500/meal", "rating": 4.5},
    {"id": "p-nar-6", "dest": "naran", "name": "PSO Fuel Station Naran", "type": "fuel", "icon": "⛽", "lat": 34.9050, "lng": 73.6480, "x": 22, "y": 70, "desc": "Reliable petrol & diesel fueling point on main Naran Road.", "price": "Govt Rate", "rating": 4.3},
    {"id": "p-nar-7", "dest": "naran", "name": "THQ Hospital Naran", "type": "hospital", "icon": "🏥", "lat": 34.9110, "lng": 73.6560, "x": 74, "y": 44, "desc": "24/7 emergency medical facility, oxygen cylinders, and trauma room.", "price": "Emergency", "rating": 4.2},
    {"id": "p-nar-8", "dest": "naran", "name": "HBL ATM Naran Bazaar", "type": "atm", "icon": "🏧", "lat": 34.9090, "lng": 73.6520, "x": 50, "y": 50, "desc": "24/7 cash withdrawal machine on main bazaar strip.", "price": "Standard", "rating": 4.1},

    # ── Hunza ────────────────────────────────────────────────────────
    {"id": "p-hun-1", "dest": "hunza", "name": "Baltit Fort", "type": "attraction", "icon": "🏰", "lat": 36.3260, "lng": 74.6698, "x": 45, "y": 30, "desc": "700-year-old UNESCO-restored royal fortress in Karimabad.", "price": "Rs. 600", "rating": 4.9},
    {"id": "p-hun-2", "dest": "hunza", "name": "Attabad Lake", "type": "attraction", "icon": "🚤", "lat": 36.3350, "lng": 74.8680, "x": 65, "y": 40, "desc": "Turquoise glacial lake famous for jet skiing and boat rides.", "price": "Rs. 1,000 Boat", "rating": 4.8},
    {"id": "p-hun-3", "dest": "hunza", "name": "Passu Cones (Cathedral)", "type": "attraction", "icon": "🏔️", "lat": 36.4780, "lng": 74.8820, "x": 80, "y": 20, "desc": "Iconic serrated jagged mountain peaks towering over the KKH.", "price": "Free", "rating": 4.9},
    {"id": "p-hun-4", "dest": "hunza", "name": "Serena Hunza Baltit Inn", "type": "hotel", "icon": "🏨", "lat": 36.3210, "lng": 74.6650, "x": 40, "y": 50, "desc": "Heritage luxury resort with views of Ultar Sar and Ladyfinger.", "price": "Rs. 24,000/night", "rating": 4.9},
    {"id": "p-hun-5", "dest": "hunza", "name": "Cafe de Hunza", "type": "restaurant", "icon": "☕", "lat": 36.3250, "lng": 74.6680, "x": 48, "y": 55, "desc": "World famous walnut cake and freshly brewed espresso.", "price": "Rs. 800", "rating": 4.8},
    {"id": "p-hun-6", "dest": "hunza", "name": "Aga Khan Health Centre Aliabad", "type": "hospital", "icon": "🏥", "lat": 36.3090, "lng": 74.6180, "x": 30, "y": 60, "desc": "Equipped healthcare center serving Central Hunza.", "price": "Emergency", "rating": 4.7},

    # ── Swat ─────────────────────────────────────────────────────────
    {"id": "p-swt-1", "dest": "swat", "name": "Malam Jabba Ski Resort", "type": "attraction", "icon": "⛷️", "lat": 34.7989, "lng": 72.5714, "x": 55, "y": 35, "desc": "Premier skiing hub with chairlift, zipline, and snowy slopes.", "price": "Rs. 1,200 Lift", "rating": 4.7},
    {"id": "p-swt-2", "dest": "swat", "name": "Mahodand Lake", "type": "attraction", "icon": "🏔️", "lat": 35.7144, "lng": 72.6483, "x": 70, "y": 25, "desc": "Glacial lake encircled by meadows and pinewood forests in upper Ushu.", "price": "Free", "rating": 4.8},
    {"id": "p-swt-3", "dest": "swat", "name": "Walnut Heights Hotel Kalam", "type": "hotel", "icon": "🏨", "lat": 35.4910, "lng": 72.5850, "x": 60, "y": 50, "desc": "Rustic alpine wood chalet with scenic river valley views.", "price": "Rs. 9,500/night", "rating": 4.6},

    # ── Lahore ───────────────────────────────────────────────────────
    {"id": "p-lhr-1", "dest": "lahore", "name": "Badshahi Mosque", "type": "attraction", "icon": "🕌", "lat": 31.5881, "lng": 74.3106, "x": 30, "y": 35, "desc": "Mughal-era grand mosque, one of the largest in the world. Free entry.", "price": "Free", "rating": 4.9},
    {"id": "p-lhr-2", "dest": "lahore", "name": "Lahore Fort (Shahi Qila)", "type": "attraction", "icon": "🏰", "lat": 31.5882, "lng": 74.3154, "x": 35, "y": 30, "desc": "UNESCO World Heritage Mughal fort with Sheesh Mahal, Naulakha Pavilion, and Alamgiri Gate.", "price": "Rs. 500", "rating": 4.8},
    {"id": "p-lhr-3", "dest": "lahore", "name": "Data Darbar", "type": "attraction", "icon": "⭐", "lat": 31.5786, "lng": 74.3097, "x": 28, "y": 45, "desc": "Shrine of Hazrat Data Ganj Bakhsh — spiritual landmark visited by thousands daily.", "price": "Free", "rating": 4.8},
    {"id": "p-lhr-4", "dest": "lahore", "name": "Gawalmandi Food Street", "type": "restaurant", "icon": "🍢", "lat": 31.5679, "lng": 74.3099, "x": 40, "y": 55, "desc": "Legendary street food hub — phajja siri paye, halwa puri, nihari, and dahi bhalle.", "price": "Rs. 500–1,500/meal", "rating": 4.9},
    {"id": "p-lhr-5", "dest": "lahore", "name": "Pearl Continental Lahore", "type": "hotel", "icon": "🏨", "lat": 31.5204, "lng": 74.3587, "x": 60, "y": 65, "desc": "Pakistan's most iconic 5-star hotel with international dining and pool.", "price": "Rs. 35,000/night", "rating": 4.8},
    {"id": "p-lhr-6", "dest": "lahore", "name": "Avari Towers Lahore", "type": "hotel", "icon": "🏨", "lat": 31.5153, "lng": 74.3425, "x": 55, "y": 60, "desc": "Upscale business hotel near Gulberg with excellent service and multiple restaurants.", "price": "Rs. 18,000/night", "rating": 4.7},
    {"id": "p-lhr-7", "dest": "lahore", "name": "Lahore Museum", "type": "attraction", "icon": "🏛️", "lat": 31.5701, "lng": 74.3148, "x": 45, "y": 40, "desc": "Largest museum in Pakistan — Gandhara art, Mughal manuscripts, and the Zaman Shah cannon.", "price": "Rs. 200", "rating": 4.7},
    {"id": "p-lhr-8", "dest": "lahore", "name": "Services Hospital Lahore", "type": "hospital", "icon": "🏥", "lat": 31.5497, "lng": 74.3150, "x": 50, "y": 70, "desc": "Major government teaching hospital with 24/7 emergency services.", "price": "Emergency", "rating": 4.3},

    # ── Karachi ──────────────────────────────────────────────────────
    {"id": "p-khi-1", "dest": "karachi", "name": "Clifton Beach (Sea View)", "type": "attraction", "icon": "🏖️", "lat": 24.8019, "lng": 67.0138, "x": 30, "y": 70, "desc": "Karachi's most popular beach — camel rides, beach food stalls, and Arabian Sea sunsets.", "price": "Free", "rating": 4.5},
    {"id": "p-khi-2", "dest": "karachi", "name": "Quaid-e-Azam Mausoleum", "type": "attraction", "icon": "⭐", "lat": 24.8742, "lng": 67.0483, "x": 50, "y": 45, "desc": "The magnificent white marble mausoleum of Pakistan's founding father Muhammad Ali Jinnah.", "price": "Free", "rating": 4.9},
    {"id": "p-khi-3", "dest": "karachi", "name": "Do Darya Restaurant Row", "type": "restaurant", "icon": "🦐", "lat": 24.8191, "lng": 67.0128, "x": 35, "y": 65, "desc": "Premium seafood district — grilled fish, jumbo prawns, and fresh crab by the sea.", "price": "Rs. 2,000–5,000/meal", "rating": 4.8},
    {"id": "p-khi-4", "dest": "karachi", "name": "Marriott Hotel Karachi", "type": "hotel", "icon": "🏨", "lat": 24.8614, "lng": 67.0104, "x": 55, "y": 40, "desc": "5-star luxury hotel in the heart of Karachi business district.", "price": "Rs. 40,000/night", "rating": 4.8},
    {"id": "p-khi-5", "dest": "karachi", "name": "Mohatta Palace Museum", "type": "attraction", "icon": "🏛️", "lat": 24.8031, "lng": 67.0298, "x": 45, "y": 60, "desc": "Stunning pink Jodhpur stone palace turned museum — Sindhi art and heritage.", "price": "Rs. 100", "rating": 4.6},
    {"id": "p-khi-6", "dest": "karachi", "name": "Agha Khan University Hospital", "type": "hospital", "icon": "🏥", "lat": 24.8607, "lng": 67.0743, "x": 70, "y": 45, "desc": "Pakistan's leading private hospital — 24/7 emergency, internationally accredited.", "price": "Emergency", "rating": 4.9},

    # ── Islamabad ────────────────────────────────────────────────────
    {"id": "p-isb-1", "dest": "islamabad", "name": "Faisal Mosque", "type": "attraction", "icon": "🕌", "lat": 33.7295, "lng": 73.0372, "x": 35, "y": 30, "desc": "South Asia's largest mosque — iconic tent-shaped design by Turkish architect Vedat Dalokay.", "price": "Free", "rating": 4.9},
    {"id": "p-isb-2", "dest": "islamabad", "name": "Margalla Hills Trail 3", "type": "attraction", "icon": "🥾", "lat": 33.7479, "lng": 73.0479, "x": 45, "y": 25, "desc": "Most popular hiking trail in Islamabad with panoramic city views and wildlife.", "price": "Free", "rating": 4.7},
    {"id": "p-isb-3", "dest": "islamabad", "name": "Pakistan Monument", "type": "attraction", "icon": "🏛️", "lat": 33.6942, "lng": 73.0697, "x": 50, "y": 50, "desc": "Four-petal flower shaped monument representing the four provinces and territories of Pakistan.", "price": "Rs. 100", "rating": 4.8},
    {"id": "p-isb-4", "dest": "islamabad", "name": "Serena Hotel Islamabad", "type": "hotel", "icon": "🏨", "lat": 33.7215, "lng": 73.0674, "x": 55, "y": 55, "desc": "Pakistan's premier luxury hotel — diplomatic quarter location with world-class facilities.", "price": "Rs. 45,000/night", "rating": 4.9},
    {"id": "p-isb-5", "dest": "islamabad", "name": "Daman-e-Koh Viewpoint", "type": "attraction", "icon": "🌄", "lat": 33.7508, "lng": 73.0649, "x": 60, "y": 28, "desc": "Garden viewpoint in Margalla Hills offering panoramic views of Islamabad city.", "price": "Free", "rating": 4.8},
    {"id": "p-isb-6", "dest": "islamabad", "name": "Monal Restaurant", "type": "restaurant", "icon": "🍽️", "lat": 33.7486, "lng": 73.0600, "x": 55, "y": 32, "desc": "Iconic hilltop restaurant with spectacular city views — Pakistani cuisine at its best.", "price": "Rs. 2,500/person", "rating": 4.7},

    # ── Peshawar ─────────────────────────────────────────────────────
    {"id": "p-pew-1", "dest": "peshawar", "name": "Qissa Khwani Bazaar", "type": "attraction", "icon": "🏪", "lat": 34.0059, "lng": 71.5607, "x": 40, "y": 45, "desc": "Legendary Storytellers' Bazaar — spice markets, dried fruit stalls, and centuries-old teahouses.", "price": "Free", "rating": 4.7},
    {"id": "p-pew-2", "dest": "peshawar", "name": "Peshawar Museum", "type": "attraction", "icon": "🏛️", "lat": 34.0081, "lng": 71.5734, "x": 50, "y": 40, "desc": "One of South Asia's finest museums — world-class Gandhara Buddhist sculpture collection.", "price": "Rs. 100", "rating": 4.8},
    {"id": "p-pew-3", "dest": "peshawar", "name": "Mahabat Khan Mosque", "type": "attraction", "icon": "🕌", "lat": 34.0050, "lng": 71.5579, "x": 35, "y": 50, "desc": "17th century Mughal mosque in Walled City with ornate frescoes and minarets.", "price": "Free", "rating": 4.8},
    {"id": "p-pew-4", "dest": "peshawar", "name": "Namak Mandi Chapli Kebab", "type": "restaurant", "icon": "🍖", "lat": 34.0095, "lng": 71.5648, "x": 45, "y": 55, "desc": "Pakistan's most famous chapli kebab street — freshly minced beef patties with local spices.", "price": "Rs. 300–600/meal", "rating": 4.9},
    {"id": "p-pew-5", "dest": "peshawar", "name": "Pearl Continental Peshawar", "type": "hotel", "icon": "🏨", "lat": 33.9935, "lng": 71.5345, "x": 60, "y": 60, "desc": "Premium 5-star hotel with full amenities in Peshawar's diplomatic enclave.", "price": "Rs. 22,000/night", "rating": 4.7},

    # ── Quetta ───────────────────────────────────────────────────────
    {"id": "p-qta-1", "dest": "quetta", "name": "Hanna Lake", "type": "attraction", "icon": "🏞️", "lat": 30.1965, "lng": 67.0843, "x": 55, "y": 35, "desc": "Scenic reservoir surrounded by rocky mountains — boating and picnics are popular.", "price": "Rs. 100 Entry", "rating": 4.5},
    {"id": "p-qta-2", "dest": "quetta", "name": "Quetta Fruit Market", "type": "attraction", "icon": "🍎", "lat": 30.1833, "lng": 66.9908, "x": 40, "y": 50, "desc": "World-famous market for Balochistan's pomegranates, apples, apricots, and dried fruits.", "price": "Free", "rating": 4.7},
    {"id": "p-qta-3", "dest": "quetta", "name": "Lourdes Hotel Quetta", "type": "hotel", "icon": "🏨", "lat": 30.1860, "lng": 66.9909, "x": 50, "y": 55, "desc": "Comfortable mid-range hotel in Quetta city center with restaurant and parking.", "price": "Rs. 8,000/night", "rating": 4.4},

    # ── Multan ───────────────────────────────────────────────────────
    {"id": "p-mtn-1", "dest": "multan", "name": "Shah Rukn-e-Alam Shrine", "type": "attraction", "icon": "⭐", "lat": 30.1958, "lng": 71.4726, "x": 40, "y": 35, "desc": "Pakistan's most spectacular Sufi shrine — blue and white tilework, 13th century masterpiece.", "price": "Free", "rating": 4.9},
    {"id": "p-mtn-2", "dest": "multan", "name": "Multan Fort (Qasim Bagh)", "type": "attraction", "icon": "🏰", "lat": 30.1996, "lng": 71.4662, "x": 45, "y": 30, "desc": "Ancient fort with panoramic views of Multan city — houses a cricket stadium inside.", "price": "Free", "rating": 4.5},
    {"id": "p-mtn-3", "dest": "multan", "name": "Multani Blue Pottery Workshop", "type": "attraction", "icon": "🏺", "lat": 30.1920, "lng": 71.4740, "x": 50, "y": 55, "desc": "Traditional craftsmen creating the iconic blue-glazed pottery unique to Multan.", "price": "Free Visit", "rating": 4.7},

    # ── Gwadar ───────────────────────────────────────────────────────
    {"id": "p-gwd-1", "dest": "gwadar", "name": "Hammerhead Beach", "type": "attraction", "icon": "🏖️", "lat": 25.1135, "lng": 62.3245, "x": 35, "y": 65, "desc": "Pristine golden sand beach on the Makran Coast — excellent for swimming and photography.", "price": "Free", "rating": 4.6},
    {"id": "p-gwd-2", "dest": "gwadar", "name": "Koh-e-Batil Viewpoint", "type": "attraction", "icon": "🌄", "lat": 25.1204, "lng": 62.3198, "x": 40, "y": 30, "desc": "Scenic hilltop viewpoint overlooking the CPEC port, city, and Arabia Sea.", "price": "Free", "rating": 4.7},
    {"id": "p-gwd-3", "dest": "gwadar", "name": "PC Gwadar Hotel", "type": "hotel", "icon": "🏨", "lat": 25.1187, "lng": 62.3271, "x": 55, "y": 50, "desc": "Premier hotel in Gwadar with sea views, restaurant, and modern facilities.", "price": "Rs. 18,000/night", "rating": 4.6},
    {"id": "p-gwd-4", "dest": "gwadar", "name": "Gwadar Fish Harbour", "type": "restaurant", "icon": "🐟", "lat": 25.1238, "lng": 62.3312, "x": 60, "y": 60, "desc": "Freshest catch directly from fishermen — grilled kingfish, lobster, and prawns.", "price": "Rs. 800–2,000", "rating": 4.8},

    # ── Taxila ───────────────────────────────────────────────────────
    {"id": "p-tax-1", "dest": "taxila", "name": "Taxila Museum", "type": "attraction", "icon": "🏛️", "lat": 33.7463, "lng": 72.8375, "x": 40, "y": 40, "desc": "World-class Gandhara Buddhist sculpture collection — 2nd century BCE to 5th century CE artifacts.", "price": "Rs. 200", "rating": 4.8},
    {"id": "p-tax-2", "dest": "taxila", "name": "Sirkap Ruins", "type": "attraction", "icon": "🗿", "lat": 33.7534, "lng": 72.8433, "x": 55, "y": 35, "desc": "Indo-Greek city ruins from 2nd century BCE — streets, temples, and wells still visible.", "price": "Rs. 100", "rating": 4.7},
    {"id": "p-tax-3", "dest": "taxila", "name": "Dharmarajika Stupa", "type": "attraction", "icon": "☸️", "lat": 33.7376, "lng": 72.8296, "x": 35, "y": 50, "desc": "One of the oldest Buddhist stupas in the world, built by Emperor Ashoka.", "price": "Rs. 100", "rating": 4.8},
]

BUSINESSES = [
    {
        "id": "b-nar-1",
        "dest": "naran",
        "type": "hotel",
        "name": "Pine Park Hotel Naran",
        "contact_name": "Shahid Khan",
        "phone": "+92 300 9876543",
        "email": "pinepark.naran@gmail.com",
        "desc": "Family-run hotel with 35 heated rooms, generators, high-speed Wi-Fi, and in-house restaurant.",
        "price_range": "Rs. 7,000 – 14,000",
        "photos": ["https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=800&q=80"],
        "facilities": ["Free Wi-Fi", "Hot Water", "Generator", "Parking", "Restaurant"],
        "is_verified": 1,
        "verified_at": "September 2026",
        "verified_by": "KPK Tourism Department",
        "rating": 4.7
    },
    {
        "id": "b-nar-2",
        "dest": "naran",
        "type": "guide",
        "name": "Tariq Mehmood (Certified Alpine Guide)",
        "contact_name": "Tariq Mehmood",
        "phone": "+92 345 1122334",
        "email": "tariq.guide@navigo.app",
        "desc": "Licensed Kaghan & Babusar trek leader with 8 years wilderness first-aid experience.",
        "price_range": "Rs. 3,500/day",
        "photos": ["https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=600&q=80"],
        "facilities": ["Urdu", "English", "Hindko", "First-Aid Certified", "High-Altitude Trekking"],
        "is_verified": 1,
        "verified_at": "September 2026",
        "verified_by": "Pakistan Alpine Club",
        "rating": 4.9
    },
    {
        "id": "b-swt-1",
        "dest": "swat",
        "type": "guide",
        "name": "Ali Khan",
        "contact_name": "Ali Khan",
        "phone": "+92 333 4455667",
        "email": "ali.kalam@navigo.app",
        "desc": "Expert Swat Valley and Mahodand 4x4 guide with 5 years local touring experience.",
        "price_range": "Rs. 3,000/day",
        "photos": ["https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&w=600&q=80"],
        "facilities": ["Urdu", "English", "Pashto", "Hiking", "Photography", "Jeep Safari"],
        "is_verified": 1,
        "verified_at": "September 2026",
        "verified_by": "Swat Tourism Directorate",
        "rating": 4.8
    }
]

ROAD_REPORTS = [
    {
        "id": "rep-1",
        "dest": "naran",
        "road_name": "Naran Road (Near Kaghan)",
        "status": "caution",
        "issue_tags": ["Mud", "Standing Water"],
        "severity": "medium",
        "confidence": 0.88,
        "photo_url": "https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?auto=format&fit=crop&w=800&q=80",
        "lat": 34.8500,
        "lng": 73.6100,
        "confirmations": 6,
        "cleared": 0,
        "is_auth": 0,
        "created_at": datetime.datetime.now().isoformat()
    },
    {
        "id": "rep-2",
        "dest": "naran",
        "road_name": "Babusar Top Pass",
        "status": "open",
        "issue_tags": ["Clear", "Dry Road"],
        "severity": "low",
        "confidence": 0.95,
        "photo_url": "",
        "lat": 35.1500,
        "lng": 74.0500,
        "confirmations": 14,
        "cleared": 0,
        "is_auth": 1,
        "created_at": datetime.datetime.now().isoformat()
    },
    {
        "id": "rep-3",
        "dest": "naran",
        "road_name": "Jalkhad – Chilas Road",
        "status": "closed",
        "issue_tags": ["Landslide", "Boulder Fall"],
        "severity": "severe",
        "confidence": 0.92,
        "photo_url": "",
        "lat": 35.0300,
        "lng": 73.9800,
        "confirmations": 11,
        "cleared": 1,
        "is_auth": 0,
        "created_at": datetime.datetime.now().isoformat()
    }
]

ALERTS = [
    {
        "id": "alt-1",
        "dest": "naran",
        "title": "Babusar Pass Evening Wind & Frost Advisory",
        "description": "Temperature dropping below freezing past 5:00 PM. High clearance vehicles advised. Cross before dusk.",
        "alert_type": "weather_warning",
        "severity": "warning",
        "source": "authority",
        "is_active": 1,
        "created_at": datetime.datetime.now().isoformat()
    },
    {
        "id": "alt-2",
        "dest": "swat",
        "title": "Kalam – Mahodand 4x4 Jeep Requirement",
        "description": "Heavy stream runoff near Ushu Forest requires 4x4 vehicles only. Low clearance sedans prohibited.",
        "alert_type": "road_closure",
        "severity": "warning",
        "source": "authority",
        "is_active": 1,
        "created_at": datetime.datetime.now().isoformat()
    }
]

PRICE_CATALOG = [
    {"id": "pc-1", "key": "transport_car_daily", "category": "transport", "price": 7000, "unit": "per_day", "notes": "Private sedan with driver & fuel allowance"},
    {"id": "pc-2", "key": "transport_van_daily", "category": "transport", "price": 12000, "unit": "per_day", "notes": "Toyota Grand Cabin / HiAce for groups"},
    {"id": "pc-3", "key": "transport_bus_seat", "category": "transport", "price": 2800, "unit": "per_person", "notes": "Intercity luxury bus ticket"},
    {"id": "pc-4", "key": "hotel_budget_night", "category": "hotel", "price": 4500, "unit": "per_night", "notes": "Clean standard guest house room"},
    {"id": "pc-5", "key": "hotel_standard_night", "category": "hotel", "price": 8500, "unit": "per_night", "notes": "3-star hotel with heating and breakfast"},
    {"id": "pc-6", "key": "hotel_luxury_night", "category": "hotel", "price": 18000, "unit": "per_night", "notes": "4-5 star luxury resort"},
    {"id": "pc-7", "key": "food_standard_daily", "category": "food", "price": 1600, "unit": "per_person_per_day", "notes": "Breakfast, lunch, tea, and dinner"},
    {"id": "pc-8", "key": "jeep_local_safari", "category": "activities", "price": 6000, "unit": "fixed", "notes": "Saif-ul-Malook or Mahodand return jeep hire"},
    {"id": "pc-9", "key": "guide_certified_daily", "category": "activities", "price": 3500, "unit": "per_day", "notes": "Local verified mountain guide"}
]

def seed_all():
    init_demo_db()
    conn = get_db_connection()
    cursor = conn.cursor()

    # Seed Destinations
    for d in DESTINATIONS:
        cursor.execute("""
        INSERT OR REPLACE INTO destinations (id, slug, name, sub_title, about, hero_image_url, from_price_pkr, tags, best_season, latitude, longitude, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            d["id"], d["slug"], d["name"], d["sub_title"], d["about"],
            d["hero_image_url"], d["from_price_pkr"], json.dumps(d["tags"]),
            d["best_season"], d["latitude"], d["longitude"], datetime.datetime.now().isoformat()
        ))

    # Seed Places
    for p in PLACES:
        cursor.execute("""
        INSERT OR REPLACE INTO places (id, destination_slug, name, place_type, icon, latitude, longitude, map_x, map_y, description, price_level, rating, address, contact_phone, is_verified, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            p["id"], p["dest"], p["name"], p["type"], p["icon"],
            p["lat"], p["lng"], p.get("x", 50), p.get("y", 50),
            p["desc"], p.get("price", ""), p.get("rating", 4.5),
            f"{p['name']}, {p['dest'].title()}", "+92 300 0000000", 1, datetime.datetime.now().isoformat()
        ))

    # Seed Businesses
    for b in BUSINESSES:
        cursor.execute("""
        INSERT OR REPLACE INTO businesses (id, user_id, destination_slug, business_type, name, contact_name, phone, email, description, price_range, photos, facilities, is_verified, verified_at, verified_by, rating, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            b["id"], "user-owner-1", b["dest"], b["type"], b["name"],
            b["contact_name"], b["phone"], b["email"], b["desc"],
            b["price_range"], json.dumps(b["photos"]), json.dumps(b["facilities"]),
            b["is_verified"], b["verified_at"], b["verified_by"], b["rating"], datetime.datetime.now().isoformat()
        ))

    # Seed Road Reports
    for r in ROAD_REPORTS:
        cursor.execute("""
        INSERT OR REPLACE INTO road_reports (id, user_id, destination_slug, road_name, status, issue_tags, severity, confidence, ai_analysis_json, photo_url, latitude, longitude, confirmations_count, cleared_votes_count, is_authority_override, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            r["id"], "user-reporter-1", r["dest"], r["road_name"], r["status"],
            json.dumps(r["issue_tags"]), r["severity"], r["confidence"],
            json.dumps({"summary": r["road_name"], "disclaimer": "Possible issue detected — AI suggestion, please confirm"}),
            r["photo_url"], r["lat"], r["lng"], r["confirmations"], r["cleared"], r["is_auth"], r["created_at"]
        ))

    # Seed Alerts
    for a in ALERTS:
        cursor.execute("""
        INSERT OR REPLACE INTO alerts (id, destination_slug, title, description, alert_type, severity, source, is_active, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            a["id"], a["dest"], a["title"], a["description"], a["alert_type"],
            a["severity"], a["source"], a["is_active"], a["created_at"]
        ))

    # Seed Price Catalog
    for pc in PRICE_CATALOG:
        cursor.execute("""
        INSERT OR REPLACE INTO price_catalog (id, item_key, category, base_price_pkr, unit, notes)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (
            pc["id"], pc["key"], pc["category"], pc["price"], pc["unit"], pc["notes"]
        ))

    # Seed Profiles
    cursor.execute("""
    INSERT OR REPLACE INTO profiles (id, user_id, full_name, email, role, preferred_language, saved_destinations, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "prof-1", "demo-user-1", "Traveler", "traveler@navigo.pk", "tourist", "en",
        json.dumps(["naran", "hunza"]), datetime.datetime.now().isoformat()
    ))

    conn.commit()
    conn.close()
    
    try:
        from scripts.seed_showcase_trips import seed_showcase
        seed_showcase()
    except Exception as e:
        print("Note: seed_showcase error:", e)

    print("Seeded all demo data cleanly into SQLite database!")

if __name__ == "__main__":
    seed_all()
