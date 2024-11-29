import httpx
import msgspec
from .structs import EventStudent, OrganizationRef, EventTeamRef


def clean_none_params(**kwargs: str | None) -> dict[str, str]:
    """Constructs a dictionary of parameters from keyword arguments. Any
    None values are removed.
    """
    return {k: v for k, v in kwargs.items() if v is not None}


class Client:
    def __init__(self, api_token: str) -> None:
        """Creates a new ContestDojo API Client with the given API token.

        Args:
            api_token (str): The API token to use for authentication.
        """

        self.client = httpx.AsyncClient(
            base_url="https://api.contestdojo.com/",
            headers={"Authorization": f"Bearer {api_token}"},
            follow_redirects=True,
        )

    async def list_event_students(
        self,
        event_id: str,
        *,
        org_id: str | None = None,
        team_id: str | None = None,
        number: str | None = None,
        email: str | None = None,
    ) -> list[EventStudent]:
        """Lists the students for a given event.

        Args:
            event_id (str): The ID of the event to list students for.
            org_id (str, optional): The ID of the organization to filter by.
            team_id (str, optional): The ID of the team to filter by.
            number (str, optional): The student number to filter by.
            email (str, optional): The student email to filter by.

        Returns:
            list[EventStudent]: A list of EventStudent objects.
        """
        params = clean_none_params(
            org_id=org_id,
            team_id=team_id,
            number=number,
            email=email,
        )

        r = await self.client.get(f"/events/{event_id}/students/", params=params)
        r.raise_for_status()
        return msgspec.json.decode(r.content, type=list[EventStudent])

    async def update_event_student(
        self,
        event_id: str,
        student_id: str,
        *,
        grade: str | None = None,
        org: OrganizationRef | None = None,
        team: EventTeamRef | None = None,
        number: str | None = None,
        waiver: bool | str | None = None,
        notes: str | None = None,
        custom_fields: dict[str, str] | None = None,
    ) -> EventStudent:
        """Updates a given student.

        Positional Args:
            event_id (str): The ID of the event to update the student for.
            student_id (str): The ID of the student to update.

        Keyword Args:
            grade (str, optional): The new grade for the student.
            org (OrganizationRef, optional): The new organization for the
                student.
            team (EventTeamRef, optional): The new team for the student.
            number (str, optional): The new student number for the student.
            waiver (bool | str, optional): The new waiver status for the
                student.
            notes (str, optional): The new notes for the student.
            custom_fields (dict[str, str], optional): The new custom fields
                for the student.

        Returns:
            EventStudent: The updated EventStudent object.
        """
        body = clean_none_params(
            grade=grade,
            org=org,
            team=team,
            number=number,
            waiver=waiver,
            notes=notes,
            customFields=custom_fields,
        )

        r = await self.client.patch(
            f"/events/{event_id}/students/{student_id}",
            json=body,
        )
        r.raise_for_status()
        return msgspec.json.decode(r.content, type=EventStudent)
