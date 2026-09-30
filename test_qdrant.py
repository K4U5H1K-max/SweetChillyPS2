import json
import urllib.request

req = urllib.request.Request("http://localhost:6333/collections")
with urllib.request.urlopen(req) as res:
    print(json.loads(res.read()))

req2 = urllib.request.Request(
    "http://localhost:6333/collections/documents/points/scroll",
    data=json.dumps({"limit": 1, "with_payload": True, "with_vector": False}).encode("utf-8"),
    headers={"Content-Type": "application/json"},
    method="POST"
)
with urllib.request.urlopen(req2) as res:
    data = json.loads(res.read())
    print("\nPayload:")
    import pprint
    pprint.pprint(data["result"]["points"][0]["payload"])
