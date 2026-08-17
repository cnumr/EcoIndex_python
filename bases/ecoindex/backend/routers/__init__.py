from ecoindex.backend.routers.bff import router as router_bff
from ecoindex.backend.routers.compute import router as router_compute
from ecoindex.backend.routers.ecoindex import router as router_ecoindex
from ecoindex.backend.routers.health import router as router_health
from ecoindex.backend.routers.host import router as router_host
from ecoindex.backend.routers.tasks import router as router_task
from fastapi import APIRouter

router = APIRouter()

router.include_router(router=router_bff, include_in_schema=False)
router.include_router(router=router_ecoindex)
router.include_router(router=router_compute)
router.include_router(router=router_host)
router.include_router(router=router_task)
router.include_router(router=router_health)
