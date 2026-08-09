from typing import List
from fastapi import APIRouter, Depends, HTTPException
from ai.pipeline import ArkanaPipeline
from ai.backend.api.schemas import SiteResponse
from ai.backend.api.dependencies import get_pipeline

router = APIRouter()

@router.get("/sites", response_model=List[SiteResponse])
async def list_sites(
    limit: int = 50,
    offset: int = 0,
    pipeline: ArkanaPipeline = Depends(get_pipeline)
):
    """
    List canonical heritage sites.
    """
    if not pipeline.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
        
    query = """
        SELECT site_id, name, state, category, short_summary, 
               ST_Y(coordinates::geometry) as latitude, 
               ST_X(coordinates::geometry) as longitude 
        FROM heritage_sites 
        ORDER BY data_quality_score DESC
        LIMIT $1 OFFSET $2
    """
    async with pipeline.db_pool.acquire() as conn:
        rows = await conn.fetch(query, limit, offset)
        
    return [
        {
            "site_id": str(row["site_id"]),
            "name": row["name"],
            "state": row["state"],
            "category": row["category"],
            "short_summary": row["short_summary"],
            "coordinates": {"lat": row["latitude"], "lng": row["longitude"]}
        }
        for row in rows
    ]

@router.get("/sites/{site_id}", response_model=SiteResponse)
async def get_site(
    site_id: str,
    pipeline: ArkanaPipeline = Depends(get_pipeline)
):
    """
    Get a single heritage site by ID.
    """
    if not pipeline.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
        
    query = """
        SELECT site_id, name, state, category, short_summary, 
               ST_Y(coordinates::geometry) as latitude, 
               ST_X(coordinates::geometry) as longitude 
        FROM heritage_sites 
        WHERE site_id = $1::uuid
    """
    async with pipeline.db_pool.acquire() as conn:
        row = await conn.fetchrow(query, site_id)
        
    if not row:
        raise HTTPException(status_code=404, detail="Site not found")
        
    return {
        "site_id": str(row["site_id"]),
        "name": row["name"],
        "state": row["state"],
        "category": row["category"],
        "short_summary": row["short_summary"],
        "coordinates": {"lat": row["latitude"], "lng": row["longitude"]}
    }
