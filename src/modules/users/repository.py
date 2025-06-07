from sqlmodel import select


from src.modules.users.schemes import UserRole, Users


from sqlmodel import select

from src.modules.users.schemes import Users
from src.modules.users.enums import UsersEnum

from sqlalchemy.ext.asyncio import AsyncSession


class UsersRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, user_create: Users) -> tuple[Users, UsersEnum]:
        self.session.add(user_create)
        await self.session.commit()
        await self.session.refresh(user_create)

        return user_create, UsersEnum.CREATED
        
         
    async def read_by_email(self, user_email: str) -> Users | None:
        query = select(Users).where(Users.email == user_email)
        user = await self.session.execute(query)
        return user.scalars().first()
    
    
    async def change_role_of_user(self, user_id: str, role: str) -> Users | None:
        query = select(Users).where(Users.id == user_id)
        result = await self.session.execute(query)
        user = result.scalars().first()
        
        if not user:
            return None
        
        if role == "admin":
            user.role = UserRole.admin
        else: 
            user.role = UserRole.user
                
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        
        return user
        
    