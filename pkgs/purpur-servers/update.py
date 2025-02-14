#!/usr/bin/env nix-shell
#!nix-shell -i python3 -p python3Packages.requests python3Packages.aiohttp


import json
import asyncio
import hashlib
from pathlib import Path
import aiohttp

# API Endpoint
ENDPOINT = "https://api.purpurmc.org/v2/purpur"

# Configuration
TIMEOUT = 60 # Increased timeout for slow requests
RETRIES = 1  # Number of retry attempts
MAX_CONCURRENT_REQUESTS = 5 # Controls API load 

async def fetch_json(session, url):
    """Fetch JSON data from a URL with retries and timeout handling."""
    for attempt in range(RETRIES):
        try:
            async with session.get(url, timeout=TIMEOUT) as response:
                response.raise_for_status()
                return await response.json()
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            print(f"⚠️ Attempt {attempt + 1}: Failed to fetch {url}: {e}")
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
    print(f"❌ Giving up on {url}")
    return None

async def get_game_versions(session):
    """Fetch all available game versions."""
    print("📥 Fetching game versions...")
    data = await fetch_json(session, ENDPOINT)
    return data["versions"] if data else []

async def get_builds(version, session):
    """Fetch all builds for a given version."""
    print(f"📥 Fetching builds for {version}...")
    data = await fetch_json(session, f"{ENDPOINT}/{version}")
    return data["builds"]["all"] if data else []

async def get_build_info(version, build, session):
    """Fetch detailed info about a specific build."""
    print(f"📥 Fetching build info for {version} - Build {build}...")
    return await fetch_json(session, f"{ENDPOINT}/{version}/{build}")

async def get_build_sha256(build_url, session):
    """Download a file and compute its SHA-256 hash asynchronously."""
    print(f"🔍 Getting SHA-256 for {build_url}...")

    for attempt in range(RETRIES):
        try:
            async with session.get(build_url, timeout=TIMEOUT) as response:
                response.raise_for_status()
                sha256 = hashlib.sha256()
                async for chunk in response.content.iter_chunked(8192):
                    sha256.update(chunk)
                return sha256.hexdigest()
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            print(f"⚠️ Attempt {attempt + 1}: Failed to fetch {build_url}: {e}")
            await asyncio.sleep(2 ** attempt)

    print(f"❌ Giving up on {build_url}")
    return None

async def update_build(build_number, version, data, session, semaphore):
    """Update the build hash if it's missing, ensuring controlled concurrency."""
    async with semaphore:  # Limit concurrent API calls
        if build_number in data.get(version, {}):
            print(f"✅ Skipping build {build_number} (already exists)")
            return

        build_info = await get_build_info(version, build_number, session)
        if not build_info or build_info.get("result") == "FAILURE":
            print(f"❌ Skipping build {build_number} (invalid)")
            return

        build_url = f"{ENDPOINT}/{version}/{build_number}/download"
        build_sha256 = await get_build_sha256(build_url, session)

        if build_sha256:
            data.setdefault(version, {})[build_number] = {
                "url": build_url,
                "sha256": build_sha256,
            }

async def main(lock_path):
    """Main function to orchestrate fetching and updating builds."""
    print("🔓 Loading lock file...")
    lock_path = Path(lock_path)
    data = json.loads(lock_path.read_text()) if lock_path.exists() else {}

    print("🚀 Starting fetch process...")
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)  # Limits concurrent requests

    async with aiohttp.ClientSession() as session:
        versions = await get_game_versions(session)
        print(f"📌 Found {len(versions)} versions")

        tasks = []
        for version in versions:
            builds = await get_builds(version, session)
            for build_number in builds:
                tasks.append(update_build(build_number, version, data, session, semaphore))

        await asyncio.gather(*tasks)  # Process builds with concurrency control

    lock_path.write_text(json.dumps(data, indent=2) + "\n")

if __name__ == "__main__":
    folder = Path(__file__).parent
    lock_path = folder / "lock.json"
    asyncio.run(main(lock_path))
