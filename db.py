import os
from supabase import create_client

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def save_movie(key, source_chat_id, source_message_id, title, overview, poster_url):
    return (
        supabase.table("movies")
        .insert(
            {
                "key": key,
                "source_chat_id": str(source_chat_id),
                "source_message_id": source_message_id,
                "title": title,
                "overview": overview,
                "poster_url": poster_url,
            }
        )
        .execute()
    )


def get_movie_by_key(key: str):
    res = supabase.table("movies").select("*").eq("key", key).limit(1).execute()
    data = res.data
    return data[0] if data else None


def key_exists(key: str) -> bool:
    res = supabase.table("movies").select("id").eq("key", key).limit(1).execute()
    return len(res.data) > 0
