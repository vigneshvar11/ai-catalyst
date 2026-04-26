import urllib.request, json

API_KEY = "rnd_ugtJqzOI3Q7s6CYoBGJhkw07wb2S"
SVC_ID = "srv-d7n07s0sfn5c73dpbv8g"

# Check events
req = urllib.request.Request(
    "https://api.render.com/v1/services/" + SVC_ID + "/events?limit=20",
    headers={"Accept": "application/json", "Authorization": "Bearer " + API_KEY}
)
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read())
    for e in data:
        evt = e.get("event", e)
        print(json.dumps(evt, indent=2, default=str)[:300])
        print("---")
