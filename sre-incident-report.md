Redis failure causes 9.8 seconds latency spike

Date: Today
Duration: 10 minutes
Severity: High

Timeline: 
3:42 PM - Redis was stopped deliberately
3:43 PM - p95 latency spike began increasing to 8.75
3:46 PM to 3:48 PM - p95 latency was at it's peak between 9.63 and 9.88

Root cause:
Redis connection failure led to data being fetched from the database

Fix: 
Need to setup alerting when Redis goes down

Follow-up Actions:
Add an alert when Cache Hit Ratio drops below 0.05
Add alert when p95 latency exceeds 2 seconds

