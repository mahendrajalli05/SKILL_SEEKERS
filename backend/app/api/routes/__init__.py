from fastapi import APIRouter

from app.api.routes import (
    citizen,
    compliance,
    copilot,
    cost,
    demo,
    documents,
    evidence,
    forensics,
    geo,
    graph,
    health,
    images,
    milestone,
    need,
    overlap,
    pce,
    projects,
    review,
    risk,
    satellite,
    time,
)

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(projects.router, tags=["projects"])
api_router.include_router(review.router, tags=["officer-review"])
api_router.include_router(cost.router, tags=["cost-intelligence"])
api_router.include_router(time.router, tags=["time-intelligence"])
api_router.include_router(overlap.router, tags=["overlap-intelligence"])
api_router.include_router(compliance.router, tags=["compliance"])
api_router.include_router(evidence.router, tags=["evidence"])
api_router.include_router(pce.router, tags=["plan-claim-evidence"])
api_router.include_router(documents.router, tags=["documents"])
api_router.include_router(images.router, tags=["image-evidence"])
api_router.include_router(forensics.router, tags=["image-forensics"])
api_router.include_router(geo.router, tags=["geospatial"])
api_router.include_router(need.router, tags=["need-impact"])
api_router.include_router(milestone.router, tags=["milestone-advisor"])
api_router.include_router(citizen.router, tags=["jan-sakshi"])
api_router.include_router(satellite.router, tags=["satellite-remote-sensing"])
api_router.include_router(copilot.router, tags=["investigation-copilot"])
api_router.include_router(demo.router, tags=["demo-cases"])
api_router.include_router(risk.router, tags=["risk-fusion"])
api_router.include_router(graph.router, tags=["relationship-graph"])
