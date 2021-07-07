CREATE TABLE ScrapeMetadata (
  timestamp TEXT PRIMARY KEY
);

CREATE TABLE ScrapeOrigin (
  short_code TEXT PRIMARY KEY,
  full_name TEXT NOT NULL,
  kijiji_id TEXT NOT NULL,
  kijiji_name TEXT NOT NULL,
  latitude FLOAT NOT NULL,
  longitude FLOAT NOT NULL,
  radius FLOAT NOT NULL
);

CREATE TABLE ApartmentScrape (
  id INTEGER PRIMARY KEY,
  scrape_origin_short_code INTEGER NOT NULL REFERENCES ScrapeOrigin(short_code),
  url TEXT NOT NULL,
  content TEXT NOT NULL,
  scraped_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE ApartmentDetails (
  apartment_scrape_id INTEGER PRIMARY KEY REFERENCES ApartmentScrape(id),
  headline TEXT NOT NULL,
  description TEXT NOT NULL,
  date_posted TEXT NOT NULL,
  price INTEGER,
  raw_address TEXT NOT NULL,
  num_rooms INTEGER,
  num_bathrooms INTEGER
);

CREATE TABLE ApartmentAddress (
  apartment_scrape_id INTEGER PRIMARY KEY REFERENCES ApartmentScrape(id),
  latitude REAL NOT NULL,
  longitude REAL NOT NULL,
  formatted_address REAL NOT NULL
);
