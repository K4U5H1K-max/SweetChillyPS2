import httpx
import asyncio
import time
from pprint import pprint

async def test_upload_and_status():
    async with httpx.AsyncClient(timeout=60.0) as client:
        print("Uploading document...")
        with open("fake_bad.pdf", "rb") as f:
            files = {"file": ("fake_bad.pdf", f, "application/pdf")}
            response = await client.post("http://localhost:8000/documents", files=files)
        
        print("Upload response:", response.status_code)
        print(response.json())
        data = response.json()
        
        doc_id = data.get("document_id")
        if not doc_id:
            print("No document_id returned!")
            return
            
        print("\nChecking status...")
        for _ in range(10):
            res = await client.get(f"http://localhost:8000/documents/{doc_id}/status")
            status_data = res.json()
            print("Status:", status_data["status"], "Stage:", status_data["processing_stage"])
            if status_data["status"] in ["PROCESSED", "FAILED"]:
                break
            time.sleep(2)
            
        print("\nChecking pages...")
        res = await client.get(f"http://localhost:8000/documents/{doc_id}/pages")
        pprint(res.json())
        
        print("\nChecking chunks...")
        res = await client.get(f"http://localhost:8000/documents/{doc_id}/chunks")
        pprint(res.json())

if __name__ == "__main__":
    asyncio.run(test_upload_and_status())
