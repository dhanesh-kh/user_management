from builtins import range
from datetime import datetime, timedelta
import pytest
from sqlalchemy import select
from app.dependencies import get_settings
from app.models.user_model import User, UserRole
from app.schemas.user_schemas import UserFilter
from app.services.user_service import UserService
from app.utils.nickname_gen import generate_nickname

pytestmark = pytest.mark.asyncio

# Test creating a user with valid data
async def test_create_user_with_valid_data(db_session, email_service):
    user_data = {
        "nickname": generate_nickname(),
        "email": "valid_user@example.com",
        "password": "ValidPassword123!",
        "role": UserRole.ADMIN.name
    }
    user = await UserService.create(db_session, user_data, email_service)
    assert user is not None
    assert user.email == user_data["email"]

# Test creating a user with invalid data
async def test_create_user_with_invalid_data(db_session, email_service):
    user_data = {
        "nickname": "",  # Invalid nickname
        "email": "invalidemail",  # Invalid email
        "password": "short",  # Invalid password
    }
    user = await UserService.create(db_session, user_data, email_service)
    assert user is None

# Test fetching a user by ID when the user exists
async def test_get_by_id_user_exists(db_session, user):
    retrieved_user = await UserService.get_by_id(db_session, user.id)
    assert retrieved_user.id == user.id

# Test fetching a user by ID when the user does not exist
async def test_get_by_id_user_does_not_exist(db_session):
    non_existent_user_id = "non-existent-id"
    retrieved_user = await UserService.get_by_id(db_session, non_existent_user_id)
    assert retrieved_user is None

# Test fetching a user by nickname when the user exists
async def test_get_by_nickname_user_exists(db_session, user):
    retrieved_user = await UserService.get_by_nickname(db_session, user.nickname)
    assert retrieved_user.nickname == user.nickname

# Test fetching a user by nickname when the user does not exist
async def test_get_by_nickname_user_does_not_exist(db_session):
    retrieved_user = await UserService.get_by_nickname(db_session, "non_existent_nickname")
    assert retrieved_user is None

# Test fetching a user by email when the user exists
async def test_get_by_email_user_exists(db_session, user):
    retrieved_user = await UserService.get_by_email(db_session, user.email)
    assert retrieved_user.email == user.email

# Test fetching a user by email when the user does not exist
async def test_get_by_email_user_does_not_exist(db_session):
    retrieved_user = await UserService.get_by_email(db_session, "non_existent_email@example.com")
    assert retrieved_user is None

# Test updating a user with valid data
async def test_update_user_valid_data(db_session, user):
    new_email = "updated_email@example.com"
    updated_user = await UserService.update(db_session, user.id, {"email": new_email})
    assert updated_user is not None
    assert updated_user.email == new_email

# Test updating a user with invalid data
async def test_update_user_invalid_data(db_session, user):
    updated_user = await UserService.update(db_session, user.id, {"email": "invalidemail"})
    assert updated_user is None

# Test deleting a user who exists
async def test_delete_user_exists(db_session, user):
    deletion_success = await UserService.delete(db_session, user.id)
    assert deletion_success is True

# Test attempting to delete a user who does not exist
async def test_delete_user_does_not_exist(db_session):
    non_existent_user_id = "non-existent-id"
    deletion_success = await UserService.delete(db_session, non_existent_user_id)
    assert deletion_success is False

# Test listing users with pagination
async def test_list_users_with_pagination(db_session, users_with_same_role_50_users):
    users_page_1 = await UserService.list_users(db_session, skip=0, limit=10)
    users_page_2 = await UserService.list_users(db_session, skip=10, limit=10)
    assert len(users_page_1) == 10
    assert len(users_page_2) == 10
    assert users_page_1[0].id != users_page_2[0].id

# Test registering a user with valid data
async def test_register_user_with_valid_data(db_session, email_service):
    user_data = {
        "nickname": generate_nickname(),
        "email": "register_valid_user@example.com",
        "password": "RegisterValid123!",
        "role": UserRole.ADMIN
    }
    user = await UserService.register_user(db_session, user_data, email_service)
    assert user is not None
    assert user.email == user_data["email"]

# Test attempting to register a user with invalid data
async def test_register_user_with_invalid_data(db_session, email_service):
    user_data = {
        "email": "registerinvalidemail",  # Invalid email
        "password": "short",  # Invalid password
    }
    user = await UserService.register_user(db_session, user_data, email_service)
    assert user is None

# Test successful user login
async def test_login_user_successful(db_session, verified_user):
    user_data = {
        "email": verified_user.email,
        "password": "MySuperPassword$1234",
    }
    logged_in_user = await UserService.login_user(db_session, user_data["email"], user_data["password"])
    assert logged_in_user is not None

# Test user login with incorrect email
async def test_login_user_incorrect_email(db_session):
    user = await UserService.login_user(db_session, "nonexistentuser@noway.com", "Password123!")
    assert user is None

# Test user login with incorrect password
async def test_login_user_incorrect_password(db_session, user):
    user = await UserService.login_user(db_session, user.email, "IncorrectPassword!")
    assert user is None

# Test account lock after maximum failed login attempts
async def test_account_lock_after_failed_logins(db_session, verified_user):
    max_login_attempts = get_settings().max_login_attempts
    for _ in range(max_login_attempts):
        await UserService.login_user(db_session, verified_user.email, "wrongpassword")
    
    is_locked = await UserService.is_account_locked(db_session, verified_user.email)
    assert is_locked, "The account should be locked after the maximum number of failed login attempts."

# Test resetting a user's password
async def test_reset_password(db_session, user):
    new_password = "NewPassword123!"
    reset_success = await UserService.reset_password(db_session, user.id, new_password)
    assert reset_success is True

# Test verifying a user's email
async def test_verify_email_with_token(db_session, user):
    token = "valid_token_example"  # This should be set in your user setup if it depends on a real token
    user.verification_token = token  # Simulating setting the token in the database
    await db_session.commit()
    result = await UserService.verify_email_with_token(db_session, user.id, token)
    assert result is True

# Test unlocking a user's account
async def test_unlock_user_account(db_session, locked_user):
    unlocked = await UserService.unlock_user_account(db_session, locked_user.id)
    assert unlocked, "The account should be unlocked"
    refreshed_user = await UserService.get_by_id(db_session, locked_user.id)
    assert not refreshed_user.is_locked, "The user should no longer be locked"

# Test search users by username
async def test_search_users_by_username(db_session, specific_nickname_user: User):
    search_params = UserFilter(username="specific_nickname")
    result_users = await UserService.search_users(db_session, search_params=search_params)
    print("Result Users:", [user.nickname for user in result_users])  # Debug output
    assert any(user.nickname == "specific_nickname" for user in result_users), "No user found with the nickname 'specific_nickname'"


# Test search users by email
async def test_search_users_by_username(db_session, specific_nickname_user: User):
    search_params = UserFilter(username="specific_nickname")
    result_users = await UserService.search_users(db_session, search_params=search_params)
    print("Result Users:", [user.nickname for user in result_users])  # Debug output
    assert any(user.nickname == "specific_nickname" for user in result_users), "No user found with the nickname 'specific_nickname'"

# Test search users by role
async def test_search_users_by_role(db_session, role_user: User):
    search_params = UserFilter(role="MANAGER")
    result_users = await UserService.search_users(db_session, search_params=search_params)
    print("Result Users:", [user.role.name for user in result_users])  # Debug output
    assert any(user.role == UserRole.MANAGER for user in result_users), "No user found with the role 'MANAGER'"

# Test search users by locked account
async def test_search_users_by_account_status_locked(db_session, locked_and_unlocked_users):
    search_params = UserFilter(account_status="locked")
    result_users = await UserService.search_users(db_session, search_params=search_params)
    print("Result Users:", [user.nickname for user in result_users])  # Debug output
    assert any(user.is_locked for user in result_users), "No user found with 'locked' account status"

# Test search users by unlocked account
async def test_search_users_by_account_status_unlocked(db_session, locked_and_unlocked_users):
    search_params = UserFilter(account_status="unlocked")
    result_users = await UserService.search_users(db_session, search_params=search_params)
    print("Result Users:", [user.nickname for user in result_users])  # Debug output
    assert any(not user.is_locked for user in result_users), "No user found with 'unlocked' account status"

# Test search with given date range
async def test_search_users_by_date_range(db_session, users_with_dates):
    now = datetime.utcnow().date()
    start_date = now - timedelta(days=5)
    end_date = now
    search_params = UserFilter(start_date=start_date, end_date=end_date)
    result_users = await UserService.search_users(db_session, search_params=search_params)
    assert all(start_date <= user.created_at.date() <= end_date for user in result_users)

# Test search with no results
async def test_search_users_with_no_results(db_session):
    search_params = UserFilter(username="non_existent_nickname")
    result_users = await UserService.search_users(db_session, search_params=search_params)
    assert len(result_users) == 0

# Test when email already exists
async def test_create_user_with_duplicate_email(db_session, email_service):
    user_data = {
        "nickname": generate_nickname(),
        "email": "duplicate_email@example.com",
        "password": "UniquePassword123!",
        "role": UserRole.AUTHENTICATED.name
    }
    await UserService.create(db_session, user_data, email_service)
    user = await UserService.create(db_session, user_data, email_service)
    assert user is None  # or assert an appropriate error is raised

# Test partial username search
async def test_search_users_by_partial_username_match(db_session, specific_nickname_user: User):
    search_params = UserFilter(username="specific")
    result_users = await UserService.search_users(db_session, search_params=search_params)
    print("Result Users:", [user.nickname for user in result_users])  # Debug output
    assert any(user.nickname == "specific_nickname" for user in result_users), "No user found with a partial username match"

# Test partial email search
async def test_search_users_by_partial_email_match(db_session, specific_email_user: User):
    search_params = UserFilter(email="specific_email")
    result_users = await UserService.search_users(db_session, search_params=search_params)
    print("Result Users:", [user.email for user in result_users])  # Debug output
    assert any(user.email == "specific_email@example.com" for user in result_users), "No user found with a partial email match"

# Test no results with date range search
async def test_search_users_by_date_range_no_results(db_session):
    now = datetime.utcnow().date()
    start_date = now + timedelta(days=10)
    end_date = now + timedelta(days=20)
    search_params = UserFilter(start_date=start_date, end_date=end_date)
    result_users = await UserService.search_users(db_session, search_params=search_params)
    assert len(result_users) == 0

# Test case insensitive username search
async def test_search_users_by_username_case_insensitivity(db_session, specific_nickname_user: User):
    search_params = UserFilter(username="SPECIFIC_NICKNAME")
    result_users = await UserService.search_users(db_session, search_params=search_params)
    print("Result Users:", [user.nickname for user in result_users])  # Debug output
    assert any(user.nickname == "specific_nickname" for user in result_users), "No user found with the username matching case-insensitive search"