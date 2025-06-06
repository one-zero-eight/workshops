from src.modules.users.routes import router as router_users
from src.modules.workshops.routes import router as router_workshops

routers = [router_users, router_workshops]

__all__ = ["routers"]