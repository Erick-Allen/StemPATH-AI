import json
import sys

from src.arango_client import get_app_db


def main() -> None:
    db = get_app_db()

    occupation_key = sys.argv[1] if len(sys.argv) > 1 else "software_developer"
    occupation_id = f"occupations/{occupation_key}"

    query = """
    LET occupation = DOCUMENT(@occupation_id)

    RETURN {
        occupation: occupation.title,
        description: occupation.description,

        domains: (
            FOR v IN OUTBOUND @occupation_id occupation_belongs_to_domain
                RETURN v.name
        ),

        skills: (
            FOR v IN OUTBOUND @occupation_id occupation_requires_skill
                RETURN v.name
        ),

        technologies: (
            FOR v IN OUTBOUND @occupation_id occupation_uses_technology
                RETURN v.name
        ),

        tasks: (
            FOR v IN OUTBOUND @occupation_id occupation_performs_task
                RETURN v.description
        )
    }
    """

    result = list(
        db.aql.execute(
            query,
            bind_vars={"occupation_id": occupation_id},
        )
    )

    if not result or result[0]["occupation"] is None:
        print(f"No occupation found for key: {occupation_key}")
        return

    print(json.dumps(result[0], indent=2))


if __name__ == "__main__":
    main()