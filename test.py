from redis import Redis
from rq import Queue, get_current_job

redis_conn = Redis()




current_job = get_current_job(connection=redis_conn)

if current_job:
    print("Currently executing job ID:", current_job.id)
else:
    print("No job is currently being executed.")
