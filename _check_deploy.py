import urllib.request, json

API_KEY = "rnd_ugtJqzOI3Q7s6CYoBGJhkw07wb2S"
SVC_ID = "srv-d7n07s0sfn5c73dpbv8g"

# List deploys
req = urllib.request.Request(
    "https://api.render.com/v1/services/" + SVC_ID + "/deploys?limit=5",
    headers={"Accept": "application/json", "Authorization": "Bearer " + API_KEY}
)
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read())
    for d in data:
        dep = d.get("deploy", d)
        did = dep.get("id", "?")
        status = dep.get("status", "?")
        commit = dep.get("commit", {})
        msg = commit.get("message", "n/a")[:60] if isinstance(commit, dict) else "n/a"
        print(did, "|", status, "|", msg)

# Trigger a new deploy
print("\nTriggering new deploy...")
req2 = urllib.request.Request(
    "https://api.render.com/v1/services/" + SVC_ID + "/deploys",
    data=b"{}",
    headers={"Accept": "application/json", "Content-Type": "application/json", "Authorization": "Bearer " + API_KEY},
    method="POST"
)
try:
    with urllib.request.urlopen(req2) as resp2:
        d2 = json.loads(resp2.read())
        print("New deploy ID:", d2.get("id"))
        print("Status:", d2.get("status"))
except urllib.error.HTTPError as e:
    print("Error:", e.code, e.read().decode())
