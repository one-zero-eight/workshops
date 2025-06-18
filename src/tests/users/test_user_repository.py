import pytest

from src.storages.sql.models.users import UserRole


class TestUser:
    @pytest.mark.asyncio
    async def test_create(self, add_user_and_clean, create_user_data):
        user = add_user_and_clean

        assert user.innohassle_id == create_user_data.innohassle_id
        assert user.id != ""
        assert user.role == UserRole.user

    @pytest.mark.asyncio
    async def test_read_by_id(self, getUserRepository, add_user_and_clean):        
        user = add_user_and_clean
        user_found = await getUserRepository.read_by_id(user.id)
        assert user_found is not None
        assert user_found == user

    @pytest.mark.asyncio
    async def test_read_by_innohassle_id(self, getUserRepository, add_user_and_clean):
        user = add_user_and_clean
        print(user.id)
        user_id_found = await getUserRepository.read_id_by_innohassle_id(user.innohassle_id)
        assert user_id_found == user.id

    @pytest.mark.asyncio
    async def test_change_role_of_user(self, getUserRepository, add_user_and_clean):
        user = add_user_and_clean
        user_found = await getUserRepository.change_role_of_user(user.id, UserRole.user)
        assert user_found.role == UserRole.user
        assert user_found.innohassle_id == user.innohassle_id

    @pytest.mark.asyncio
    async def test_delete(self, getUserRepository, add_user_and_clean):
        user = add_user_and_clean
        await getUserRepository.delete(user)
        
        user_found = await getUserRepository.read_by_id(user.id)
        assert user_found is None

        

