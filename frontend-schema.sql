CREATE TABLE ScrapeOrigin (
  short_code TEXT PRIMARY KEY,
  full_name TEXT NOT NULL,
  kijiji_id TEXT NOT NULL,
  kijiji_name TEXT NOT NULL,
  latitude FLOAT NOT NULL,
  longitude FLOAT NOT NULL,
  radius FLOAT NOT NULL
);

CREATE TABLE Apartment (
  id INT PRIMARY KEY,
  url TEXT NOT NULL,
  headline TEXT NOT NULL,
  description TEXT NOT NULL,
  date_posted TEXT NOT NULL,
  price INTEGER,
  num_rooms INTEGER,
  num_bathrooms INTEGER,
  latitude REAL NOT NULL,
  longitude REAL NOT NULL,
  formatted_address REAL NOT NULL,
  origin TEXT NOT NULL REFERENCES ScrapeOrigin(short_code)
);
