from fastapi import FastAPI

from app.routers import backup, clusters, governance, health, jobs, kubevirt, nodepools, observability, storagepools, workflows

app = FastAPI(
    title="K8s Platform API",
    version="0.2.0",
    description="L16 Workflow-enabled Platform API for Kubernetes, CSI, KubeVirt, governance, observability and backup workflows.",
)

app.include_router(health.router)
app.include_router(jobs.router, prefix="/api/v1")
app.include_router(workflows.router, prefix="/api/v1")
app.include_router(clusters.router, prefix="/api/v1")
app.include_router(nodepools.router, prefix="/api/v1")
app.include_router(storagepools.router, prefix="/api/v1")
app.include_router(kubevirt.router, prefix="/api/v1")
app.include_router(backup.router, prefix="/api/v1")
app.include_router(governance.router, prefix="/api/v1")
app.include_router(observability.router, prefix="/api/v1")
