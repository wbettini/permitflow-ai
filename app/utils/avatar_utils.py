from app.prompts.flowbot_prompts import AVATAR_MAP, PERSONAS

def get_alternate_avatars(exclude: str | None = None) -> list[dict]:
    """
    Build a list of alternate avatars from avatars.json and personas.json.

    Args:
        exclude: Optional avatar name to exclude from the list.

    Returns:
        [
            {
                "avatar": "FlowBot",
                "demeanor": "Happy",
                "icon": "/static/flowbot-avatar.png",
                "default": True
            },
            ...
        ]
    """
    alternates = []
    for avatar_name, data in AVATAR_MAP.items():
        if exclude and avatar_name == exclude:
            continue

        persona_key = data.get("persona", "default")
        demeanor = PERSONAS.get(persona_key, {}).get("demeanor", "")

        alternates.append({
            "avatar": avatar_name,
            "demeanor": demeanor.title(),
            "icon": data.get("icon"),
            "default": data.get("default", False)  # ✅ include default flag
        })

    return alternates