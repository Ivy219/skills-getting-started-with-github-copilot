"""pytest suite for the FastAPI backend application.

Tests follow the AAA (Arrange-Act-Assert) pattern and use a fresh
in-memory activities state before each test.
"""

from copy import deepcopy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src.app import app, activities

original_activities = deepcopy(activities)


@pytest.fixture(autouse=True)
def reset_activities_state():
    """Reset the in-memory activities state before each test."""
    activities.clear()
    activities.update(deepcopy(original_activities))
    yield
    activities.clear()
    activities.update(deepcopy(original_activities))


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


def activity_url(activity_name: str, action: str) -> str:
    return f"/activities/{quote(activity_name, safe='')}/{action}"


class TestGetActivities:
    def test_get_activities_returns_all_activities(self, client):
        # Arrange
        expected_activity_count = len(original_activities)

        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        assert len(response.json()) == expected_activity_count
        assert "Chess Club" in response.json()
        assert "Programming Class" in response.json()

    def test_get_activities_contains_required_fields(self, client):
        # Arrange
        required_fields = {"description", "schedule", "max_participants", "participants"}

        # Act
        response = client.get("/activities")
        activities_data = response.json()

        # Assert
        for activity_data in activities_data.values():
            assert required_fields.issubset(activity_data.keys())
            assert isinstance(activity_data["participants"], list)
            assert isinstance(activity_data["max_participants"], int)


class TestSignupForActivity:
    def test_signup_for_activity_success(self, client):
        # Arrange
        activity_name = "Chess Club"
        email = "newstudent@mergington.edu"

        # Act
        response = client.post(activity_url(activity_name, "signup"), params={"email": email})

        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Signed up {email} for {activity_name}"

        get_response = client.get("/activities")
        assert email in get_response.json()[activity_name]["participants"]

    def test_signup_for_nonexistent_activity_returns_404(self, client):
        # Arrange
        activity_name = "Nonexistent Activity"
        email = "student@mergington.edu"

        # Act
        response = client.post(activity_url(activity_name, "signup"), params={"email": email})

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_signup_duplicate_student_returns_400(self, client):
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"

        # Act
        response = client.post(activity_url(activity_name, "signup"), params={"email": email})

        # Assert
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"].lower()


class TestUnregisterFromActivity:
    def test_unregister_from_activity_success(self, client):
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"

        # Act
        response = client.delete(activity_url(activity_name, "unregister"), params={"email": email})

        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Unregistered {email} from {activity_name}"

        get_response = client.get("/activities")
        assert email not in get_response.json()[activity_name]["participants"]

    def test_unregister_nonexistent_student_returns_400(self, client):
        # Arrange
        activity_name = "Chess Club"
        email = "unknown@mergington.edu"

        # Act
        response = client.delete(activity_url(activity_name, "unregister"), params={"email": email})

        # Assert
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"].lower()
