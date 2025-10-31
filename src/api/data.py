    "message": {
        "messages": [
            {
                "content": "give me top 6 rows of dataset",
                "additional_kwargs": {},
                "response_metadata": {},
                "type": "human",
                "name": null,
                "id": "2b7d990a-3e57-4e4c-8cb7-89771c0dcd27",
                "example": false
            },
            {
                "content": "all the relevant metadata about the csv file has been generated and stored in the state",
                "additional_kwargs": {},
                "response_metadata": {},
                "type": "ai",
                "name": null,
                "id": "92b4bfba-b7c5-46a4-a160-f097bc72fb9b",
                "example": false,
                "tool_calls": [],
                "invalid_tool_calls": [],
                "usage_metadata": null
            },
            {
                "content": "Generated SQL query: SELECT * FROM read_csv_auto('https://twypdtqllbeaaxkbduju.supabase.co/storage/v1/object/public/data_csv/20251010_213653_442975.csv') ORDER BY \"Index\" ASC LIMIT 6;",
                "additional_kwargs": {},
                "response_metadata": {},
                "type": "ai",
                "name": null,
                "id": "03b54278-1b5b-4a0c-9283-598741e9e6b0",
                "example": false,
                "tool_calls": [],
                "invalid_tool_calls": [],
                "usage_metadata": null
            },
            {
                "content": "the query is checked",
                "additional_kwargs": {},
                "response_metadata": {},
                "type": "ai",
                "name": null,
                "id": "275224d6-401d-467b-bfd2-ef8d0b6feca5",
                "example": false,
                "tool_calls": [],
                "invalid_tool_calls": [],
                "usage_metadata": null
            }
        ],
        "schema_context": {
            "n_rows": 1000,
            "n_cols": 12,
            "columns": [
                "Index",
                "Customer Id",
                "First Name",
                "Last Name",
                "Company",
                "City",
                "Country",
                "Phone 1",
                "Phone 2",
                "Email",
                "Subscription Date",
                "Website"
            ],
            "dtypes": {
                "Index": "int64",
                "Customer Id": "object",
                "First Name": "object",
                "Last Name": "object",
                "Company": "object",
                "City": "object",
                "Country": "object",
                "Phone 1": "object",
                "Phone 2": "object",
                "Email": "object",
                "Subscription Date": "object",
                "Website": "object"
            },
            "null_counts": {
                "Index": 0,
                "Customer Id": 0,
                "First Name": 0,
                "Last Name": 0,
                "Company": 0,
                "City": 0,
                "Country": 0,
                "Phone 1": 0,
                "Phone 2": 0,
                "Email": 0,
                "Subscription Date": 0,
                "Website": 0
            },
            "head": [
                {
                    "Index": 1,
                    "Customer Id": "dE014d010c7ab0c",
                    "First Name": "Andrew",
                    "Last Name": "Goodman",
                    "Company": "Stewart-Flynn",
                    "City": "Rowlandberg",
                    "Country": "Macao",
                    "Phone 1": "846-790-4623x4715",
                    "Phone 2": "(422)787-2331x71127",
                    "Email": "marieyates@gomez-spencer.info",
                    "Subscription Date": "2021-07-26",
                    "Website": "http://www.shea.biz/"
                },
                {
                    "Index": 2,
                    "Customer Id": "2B54172c8b65eC3",
                    "First Name": "Alvin",
                    "Last Name": "Lane",
                    "Company": "Terry, Proctor and Lawrence",
                    "City": "Bethside",
                    "Country": "Papua New Guinea",
                    "Phone 1": "124-597-8652x05682",
                    "Phone 2": "321.441.0588x6218",
                    "Email": "alexandra86@mccoy.com",
                    "Subscription Date": "2021-06-24",
                    "Website": "http://www.pena-cole.com/"
                },
                {
                    "Index": 3,
                    "Customer Id": "d794Dd48988d2ac",
                    "First Name": "Jenna",
                    "Last Name": "Harding",
                    "Company": "Bailey Group",
                    "City": "Moniquemouth",
                    "Country": "China",
                    "Phone 1": "(335)987-3085x3780",
                    "Phone 2": "001-680-204-8312",
                    "Email": "justincurtis@pierce.org",
                    "Subscription Date": "2020-04-05",
                    "Website": "http://www.booth-reese.biz/"
                },
                {
                    "Index": 4,
                    "Customer Id": "3b3Aa4aCc68f3Be",
                    "First Name": "Fernando",
                    "Last Name": "Ford",
                    "Company": "Moss-Maxwell",
                    "City": "Leeborough",
                    "Country": "Macao",
                    "Phone 1": "(047)752-3122",
                    "Phone 2": "048.779.5035x9122",
                    "Email": "adeleon@hubbard.org",
                    "Subscription Date": "2020-11-29",
                    "Website": "http://www.hebert.com/"
                },
                {
                    "Index": 5,
                    "Customer Id": "D60df62ad2ae41E",
                    "First Name": "Kara",
                    "Last Name": "Woods",
                    "Company": "Mccarthy-Kelley",
                    "City": "Port Jacksonland",
                    "Country": "Nepal",
                    "Phone 1": "+1-360-693-4419x19272",
                    "Phone 2": "163-627-2565",
                    "Email": "jesus90@roberson.info",
                    "Subscription Date": "2022-04-22",
                    "Website": "http://merritt.com/"
                }
            ]
        },
        "csv_url": "https://twypdtqllbeaaxkbduju.supabase.co/storage/v1/object/public/data_csv/20251010_213653_442975.csv",
        "dialect": "sqlite",
        "query": "SELECT * FROM read_csv_auto('https://twypdtqllbeaaxkbduju.supabase.co/storage/v1/object/public/data_csv/20251010_213653_442975.csv') ORDER BY \"Index\" ASC LIMIT 6;",
        "sql_query_output": null,
        "result": null,
        "decision": "sql"
    }

print(type(run))