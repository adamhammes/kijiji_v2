import typing


class ScrapeOrigin(typing.NamedTuple):
    short_code: str
    full_name: str
    kijiji_id: str
    kijiji_name: str
    latitude: float
    longitude: float
    radius: float


quebec = ScrapeOrigin(
    short_code="quebec",
    full_name="Quebec City",
    kijiji_id="l1700124",
    kijiji_name="ville-de-quebec",
    latitude=46.834872,
    longitude=-71.264868,
    radius=30,
)

montreal = ScrapeOrigin(
    short_code="montreal",
    full_name="Montréal",
    kijiji_id="l80002",
    kijiji_name="grand-montreal",
    latitude=45.5017,
    longitude=-73.5673,
    radius=30,
)

sherbrooke = ScrapeOrigin(
    short_code="sherbrooke",
    full_name="Sherbrooke",
    kijiji_id="l1700156",
    kijiji_name="sherbrooke-qc",
    latitude=45.4042,
    longitude=-71.8929,
    radius=30,
)

enabled_origins = [quebec]
