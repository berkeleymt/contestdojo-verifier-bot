import msgspec
from typing import NewType

type UserRef = NewType("UserRef", str)
type OrganizationRef = NewType("OrganizationRef", str)
type EventTeamRef = NewType("EventTeamRef", str)


class EventStudent(msgspec.Struct):
    id: str
    email: str
    fname: str
    lname: str
    grade: int | str
    user: UserRef
    team: EventTeamRef | None = None
    org: OrganizationRef | None = None
    number: str | None = None
    waiver: bool | str | None = None
    notes: str | None = None
    customFields: dict[str, str] | None = None
    checkInPool: dict[str, str] | None = None
    roomAssignments: dict[str, str] | None = None
