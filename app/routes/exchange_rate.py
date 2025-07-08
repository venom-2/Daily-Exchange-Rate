from fastapi import APIRouter, Query, HTTPException
import httpx
import redis
from dotenv import load_dotenv
import os
import json

load_dotenv()
router = APIRouter()

# Redis connection
redis_client = redis.Redis.from_url(os.getenv("REDIS_URL"), decode_responses=True)

@router.get("/exchange-rate")
async def rate(currency: str = Query(..., min_length=3, max_length=3, description="Currency code (e.g., INR, EUR, JPY)")):
    currency = currency.upper()
    cache_key = "exchange_rate:quotes"

    cached_quotes = redis_client.get(cache_key)
    
    if cached_quotes:
        quotes = json.loads(cached_quotes)
    else:
        api_key = os.getenv("API_KEY")
        api_url = os.getenv("API_ENDPOINT")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(api_url, params={"access_key": api_key})
                data = response.json()

            if not data.get("success", False):
                raise HTTPException(status_code=500, detail="Failed to fetch exchange rates")

            quotes = data.get("quotes", {})

            redis_client.setex(cache_key, 86400, json.dumps(quotes))

        except httpx.RequestError:
            raise HTTPException(status_code=500, detail="Failed to connect to exchange rate provider")

    key = f"USD{currency}"
    if key not in quotes:
        raise HTTPException(status_code=404, detail=f"Exchange rate for '{currency}' not found")

    return {
        "base": "USD",
        "currency": currency,
        "rate": quotes[key]
    }
