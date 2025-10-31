from langchain_community.utilities import SQLDatabase 

uri = "postgresql://blog-assignment_owner:npg_QGj8zmUExCu4@ep-red-truth-a4blfydv-pooler.us-east-1.aws.neon.tech/blog-assignment?sslmode=require&channel_binding=require"
db = SQLDatabase.from_uri(uri)
print(db)