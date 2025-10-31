client = get_client(url="http://localhost:2024")
assistant = await client.assistants.get("assistant_id_123")