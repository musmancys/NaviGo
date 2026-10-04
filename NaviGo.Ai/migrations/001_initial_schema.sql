-- ==============================================================================
-- NaviGo Schema Migration 001: Core Architecture, Spatial & Vector Setup
-- ==============================================================================

-- Enable Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "postgis";
CREATE EXTENSION IF NOT EXISTS "vector";

-- 1. Destinations Table
CREATE TABLE IF NOT EXISTS destinations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug VARCHAR(64) UNIQUE NOT NULL,
    name VARCHAR(128) NOT NULL,
    sub_title VARCHAR(256),
    about TEXT,
    hero_image_url TEXT,
    from_price_pkr INTEGER DEFAULT 0,
    tags TEXT[] DEFAULT '{}',
    best_season VARCHAR(64),
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    geom GEOMETRY(Point, 4326),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_destinations_slug ON destinations(slug);
CREATE INDEX IF NOT EXISTS idx_destinations_geom ON destinations USING GIST(geom);

-- 2. Places Table (Attractions, Hotels, Fuel, Hospitals, etc.)
CREATE TABLE IF NOT EXISTS places (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    destination_id UUID REFERENCES destinations(id) ON DELETE CASCADE,
    destination_slug VARCHAR(64) NOT NULL,
    name VARCHAR(128) NOT NULL,
    place_type VARCHAR(32) NOT NULL, -- attraction, hotel, restaurant, fuel, hospital, atm, guide
    icon VARCHAR(16) DEFAULT '📍',
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    map_x DOUBLE PRECISION,
    map_y DOUBLE PRECISION,
    description TEXT,
    price_level VARCHAR(16),
    rating NUMERIC(2,1) DEFAULT 4.5,
    address TEXT,
    contact_phone VARCHAR(32),
    is_verified BOOLEAN DEFAULT FALSE,
    geom GEOMETRY(Point, 4326),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_places_type ON places(place_type);
CREATE INDEX IF NOT EXISTS idx_places_dest_slug ON places(destination_slug);
CREATE INDEX IF NOT EXISTS idx_places_geom ON places USING GIST(geom);

-- 3. Trips Table
CREATE TABLE IF NOT EXISTS trips (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,
    destination_slug VARCHAR(64) NOT NULL,
    title VARCHAR(128) NOT NULL,
    duration_days INTEGER NOT NULL DEFAULT 3,
    travelers_count INTEGER NOT NULL DEFAULT 4,
    budget_pkr INTEGER NOT NULL DEFAULT 35000,
    transport_type VARCHAR(32) DEFAULT 'car',
    interests TEXT[] DEFAULT '{}',
    itinerary_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    budget_breakdown_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    status VARCHAR(32) DEFAULT 'draft', -- draft, upcoming, completed
    share_slug VARCHAR(64) UNIQUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_trips_user ON trips(user_id);
CREATE INDEX IF NOT EXISTS idx_trips_share_slug ON trips(share_slug);

-- 4. Road Reports Table (Live Community Updates)
CREATE TABLE IF NOT EXISTS road_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,
    destination_slug VARCHAR(64) NOT NULL,
    road_name VARCHAR(128) NOT NULL,
    status VARCHAR(32) NOT NULL, -- open, caution, closed
    issue_tags TEXT[] DEFAULT '{}',
    severity VARCHAR(16) DEFAULT 'medium', -- low, medium, high, severe
    confidence NUMERIC(3,2) DEFAULT 0.85,
    ai_analysis_json JSONB DEFAULT '{}'::jsonb,
    photo_url TEXT,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    confirmations_count INTEGER DEFAULT 0,
    cleared_votes_count INTEGER DEFAULT 0,
    is_authority_override BOOLEAN DEFAULT FALSE,
    geom GEOMETRY(Point, 4326),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '24 hours')
);

CREATE INDEX IF NOT EXISTS idx_reports_status ON road_reports(status);
CREATE INDEX IF NOT EXISTS idx_reports_dest ON road_reports(destination_slug);
CREATE INDEX IF NOT EXISTS idx_reports_geom ON road_reports USING GIST(geom);

-- 5. Travel Alerts Table
CREATE TABLE IF NOT EXISTS alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    destination_slug VARCHAR(64),
    title VARCHAR(128) NOT NULL,
    description TEXT NOT NULL,
    alert_type VARCHAR(32) NOT NULL, -- road_closure, weather_warning, landslide, flooding, traffic, security
    severity VARCHAR(16) NOT NULL DEFAULT 'warning', -- info, warning, emergency
    source VARCHAR(32) DEFAULT 'authority', -- authority, ai_weather_cron, high_confidence_report
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '48 hours')
);

CREATE INDEX IF NOT EXISTS idx_alerts_active ON alerts(is_active);

-- 6. Local Marketplace Businesses (Hotels, Guides, Jeeps, etc.)
CREATE TABLE IF NOT EXISTS businesses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,
    destination_slug VARCHAR(64) NOT NULL,
    business_type VARCHAR(32) NOT NULL, -- hotel, guide, jeep, restaurant, camping, adventure, handicrafts
    name VARCHAR(128) NOT NULL,
    contact_name VARCHAR(128),
    phone VARCHAR(32),
    email VARCHAR(128),
    description TEXT,
    price_range VARCHAR(64),
    photos TEXT[] DEFAULT '{}',
    facilities TEXT[] DEFAULT '{}',
    is_verified BOOLEAN DEFAULT FALSE,
    verified_at VARCHAR(64),
    verified_by VARCHAR(64),
    rating NUMERIC(2,1) DEFAULT 4.8,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_businesses_dest ON businesses(destination_slug);
CREATE INDEX IF NOT EXISTS idx_businesses_type ON businesses(business_type);

-- 7. Reviews Table
CREATE TABLE IF NOT EXISTS reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID REFERENCES businesses(id) ON DELETE CASCADE,
    destination_slug VARCHAR(64) NOT NULL,
    user_id UUID,
    user_name VARCHAR(128) NOT NULL,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    comment TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 8. Price Catalog Table (Deterministic Budget Benchmarks)
CREATE TABLE IF NOT EXISTS price_catalog (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    item_key VARCHAR(64) UNIQUE NOT NULL,
    category VARCHAR(32) NOT NULL,
    base_price_pkr INTEGER NOT NULL,
    unit VARCHAR(32) NOT NULL,
    notes TEXT
);

-- 9. Profiles Table
CREATE TABLE IF NOT EXISTS profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE,
    full_name VARCHAR(128) NOT NULL,
    email VARCHAR(128),
    role VARCHAR(32) DEFAULT 'tourist', -- tourist, business, authority, admin
    preferred_language VARCHAR(8) DEFAULT 'en',
    saved_destinations TEXT[] DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Row Level Security (RLS) Policies
ALTER TABLE destinations ENABLE ROW LEVEL SECURITY;
ALTER TABLE places ENABLE ROW LEVEL SECURITY;
ALTER TABLE trips ENABLE ROW LEVEL SECURITY;
ALTER TABLE road_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE businesses ENABLE ROW LEVEL SECURITY;
ALTER TABLE reviews ENABLE ROW LEVEL SECURITY;
ALTER TABLE price_catalog ENABLE ROW LEVEL SECURITY;
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Public destinations viewable by all" ON destinations FOR SELECT USING (true);
CREATE POLICY "Public places viewable by all" ON places FOR SELECT USING (true);
CREATE POLICY "Public road reports viewable by all" ON road_reports FOR SELECT USING (true);
CREATE POLICY "Public alerts viewable by all" ON alerts FOR SELECT USING (true);
CREATE POLICY "Public businesses viewable by all" ON businesses FOR SELECT USING (true);
CREATE POLICY "Public reviews viewable by all" ON reviews FOR SELECT USING (true);
CREATE POLICY "Public price catalog viewable by all" ON price_catalog FOR SELECT USING (true);

CREATE POLICY "Users can manage their own trips" ON trips FOR ALL USING (auth.uid() = user_id OR user_id IS NULL);
CREATE POLICY "Authenticated users can submit road reports" ON road_reports FOR INSERT WITH CHECK (true);
CREATE POLICY "Authenticated users can write reviews" ON reviews FOR INSERT WITH CHECK (true);
