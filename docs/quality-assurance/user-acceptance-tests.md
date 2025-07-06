# User Acceptance Tests

This document defines the user acceptance tests for the WorkshopsAPI project based on the core user stories and requirements.

## Test Overview

The user acceptance tests are designed to validate that the WorkshopsAPI meets the core functional requirements from the user's perspective. These tests ensure that the system behaves as expected for both regular users and administrators.

## Test Environment

- **API Base URL**: `http://localhost:8000` (development)
- **Database**: PostgreSQL with test data
- **Authentication**: JWT tokens for admin and user access
- **Test Tools**: Manual testing via API clients (Postman, curl, etc.)

## Test Cases

### TC-001: User Views Existing Workshops

**User Story**: Пользователь может зайти на сайт и видеть существующие воркшопы

**Objective**: Verify that users can view a list of all available workshops

**Preconditions**:
- System is running and accessible
- At least one workshop exists in the database
- User has valid authentication token (optional for public endpoints)

**Test Steps**:
1. Send GET request to `/workshops/`
2. Verify response status code is 200
3. Verify response contains JSON array of workshops
4. Verify each workshop object contains required fields:
   - `id`
   - `name`
   - `description`
   - `capacity`
   - `remain_places`
   - `dtstart`
   - `dtend`
   - `is_active`

**Expected Results**:
- Status code: 200 OK
- Response format: JSON array
- All active workshops are returned
- Workshop data is accurate and complete

**Acceptance Criteria**:
- ✅ User can access the workshops list without authentication
- ✅ All active workshops are displayed
- ✅ Workshop information is complete and accurate
- ✅ Response time is under 2 seconds

---

### TC-002: Admin Adds New Workshop

**User Story**: Админ может добавить воркшоп, после чего он становится виден в списке воркшопов

**Objective**: Verify that administrators can create new workshops that become visible to users

**Preconditions**:
- System is running and accessible
- Admin user has valid authentication token
- Admin user has appropriate permissions

**Test Steps**:
1. Authenticate as admin user and obtain JWT token
2. Send POST request to `/workshops/` with workshop data:
   ```json
   {
     "name": "Test Workshop",
     "description": "A test workshop for UAT",
     "capacity": 20,
     "dtstart": "2024-12-01T10:00:00Z",
     "dtend": "2024-12-01T12:00:00Z",
     "is_active": true
   }
   ```
3. Verify response status code is 201
4. Verify response contains created workshop data
5. Send GET request to `/workshops/` to verify workshop appears in list
6. Verify the new workshop is visible and active

**Expected Results**:
- Status code: 201 Created
- Response contains complete workshop data with generated ID
- Workshop appears in the workshops list
- Workshop is marked as active

**Acceptance Criteria**:
- ✅ Admin can create workshop with valid data
- ✅ Created workshop has unique ID
- ✅ Workshop becomes immediately visible in list
- ✅ Workshop is active by default
- ✅ All required fields are properly saved

**Negative Test Cases**:
- **TC-002-N1**: Non-admin user attempts to create workshop
  - Expected: 403 Forbidden
- **TC-002-N2**: Admin creates workshop with invalid data
  - Expected: 400 Bad Request with validation errors
- **TC-002-N3**: Admin creates workshop with overlapping time
  - Expected: 400 Bad Request with conflict message

---

### TC-003: User Registers for Workshop

**User Story**: Пользователь может записаться на воркшоп, после чего он отображается в списке записанных

**Objective**: Verify that users can register for workshops and see their registrations

**Preconditions**:
- System is running and accessible
- User has valid authentication token
- At least one active workshop exists with available capacity
- User is not already registered for the workshop

**Test Steps**:
1. Authenticate as regular user and obtain JWT token
2. Send GET request to `/workshops/` to identify available workshop
3. Send POST request to `/workshops/{workshop_id}/checkin` with user ID
4. Verify response status code is 200
5. Verify workshop capacity is reduced by 1
6. Send GET request to `/workshops/my-workshops` to view user's workshops
7. Verify the workshop appears in user's registered workshops list

**Expected Results**:
- Status code: 200 OK
- Workshop capacity decreases by 1
- Workshop appears in user's registered workshops
- Check-in timestamp is recorded

**Acceptance Criteria**:
- ✅ User can successfully register for available workshop
- ✅ Workshop capacity is properly updated
- ✅ Registration appears in user's workshop list
- ✅ User cannot register for same workshop twice
- ✅ Registration is recorded with timestamp

**Negative Test Cases**:
- **TC-003-N1**: User attempts to register for full workshop
  - Expected: 400 Bad Request with "No places available" message
- **TC-003-N2**: User attempts to register for inactive workshop
  - Expected: 400 Bad Request with "Workshop not active" message
- **TC-003-N3**: User attempts to register for non-existent workshop
  - Expected: 404 Not Found
- **TC-003-N4**: User attempts to register for overlapping workshop
  - Expected: 400 Bad Request with "Overlapping workshops" message

---

### TC-004: User Views Registered Workshops

**Objective**: Verify that users can view their registered workshops

**Preconditions**:
- System is running and accessible
- User has valid authentication token
- User has registered for at least one workshop

**Test Steps**:
1. Authenticate as regular user and obtain JWT token
2. Send GET request to `/workshops/my-workshops`
3. Verify response status code is 200
4. Verify response contains array of user's registered workshops
5. Verify each workshop contains complete information

**Expected Results**:
- Status code: 200 OK
- Response contains only workshops user is registered for
- Workshop data is complete and accurate

**Acceptance Criteria**:
- ✅ User can view their registered workshops
- ✅ Only user's workshops are returned
- ✅ Workshop information is complete
- ✅ Empty list returned if no registrations

---

### TC-005: User Cancels Workshop Registration

**Objective**: Verify that users can cancel their workshop registrations

**Preconditions**:
- System is running and accessible
- User has valid authentication token
- User is registered for at least one workshop

**Test Steps**:
1. Authenticate as regular user and obtain JWT token
2. Send DELETE request to `/workshops/{workshop_id}/checkout`
3. Verify response status code is 200
4. Verify workshop capacity increases by 1
5. Send GET request to `/workshops/my-workshops`
6. Verify workshop no longer appears in user's list

**Expected Results**:
- Status code: 200 OK
- Workshop capacity increases by 1
- Workshop removed from user's registered workshops

**Acceptance Criteria**:
- ✅ User can successfully cancel registration
- ✅ Workshop capacity is properly restored
- ✅ Workshop removed from user's list
- ✅ Cancellation timestamp is recorded

**Negative Test Cases**:
- **TC-005-N1**: User attempts to cancel non-existent registration
  - Expected: 404 Not Found
- **TC-005-N2**: User attempts to cancel another user's registration
  - Expected: 403 Forbidden

## Test Data Requirements

### Workshop Test Data
```json
{
  "workshops": [
    {
      "name": "Python Basics",
      "description": "Introduction to Python programming",
      "capacity": 15,
      "dtstart": "2024-12-01T10:00:00Z",
      "dtend": "2024-12-01T12:00:00Z",
      "is_active": true
    },
    {
      "name": "Web Development",
      "description": "Building web applications",
      "capacity": 20,
      "dtstart": "2024-12-02T14:00:00Z",
      "dtend": "2024-12-02T16:00:00Z",
      "is_active": true
    }
  ]
}
```

### User Test Data
```json
{
  "admin_user": {
    "innohassle_id": "admin_123",
    "email": "admin@example.com",
    "role": "admin"
  },
  "regular_user": {
    "innohassle_id": "user_456",
    "email": "user@example.com",
    "role": "user"
  }
}
```

## Test Execution

### Manual Testing
1. Use API testing tools (Postman, Insomnia, curl)
2. Follow test steps in order
3. Document results and any issues found
4. Verify all acceptance criteria are met

### Automated Testing
- Tests can be automated using pytest with requests library
- Use test fixtures for data setup and cleanup
- Mock external dependencies where appropriate

## Success Criteria

All test cases must pass with the following criteria:
- ✅ All positive test cases return expected status codes
- ✅ All negative test cases return appropriate error responses
- ✅ Data integrity is maintained throughout operations
- ✅ Response times are within acceptable limits (< 2 seconds)
- ✅ Authentication and authorization work correctly
- ✅ Error messages are clear and actionable

## Test Reporting

After test execution, document:
- Test execution date and time
- Environment details
- Pass/fail status for each test case
- Any issues or bugs discovered
- Performance metrics
- Recommendations for improvements
