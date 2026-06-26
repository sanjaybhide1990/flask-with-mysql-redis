Mock chaos between 8:25 AM and 8:29 AM by initiaing 30 requests

Date: Today
Duration: 4 minutes
Severity: High

Timeline: 
8:25 AM - Started a python script to start hitting the endpoint
8:25 AM - After 10 iterations, Redis was stopped deliberately
8:26 AM - p95 latency spike began increasing to 6.01
8:26 AM - After 3 counts of not connecting to Redis, circuit breaker triggered and data was fetched from MySQL database
8:27 AM - Redis was brought up and latency subsided to 5.63 ms 

Impact:
- After redis was not accessible, if the data is not fetched from cache for 3 consecutive times, the subsequent data is directly fetched from the database
- This resulted in increasing the p95 latency to 6.01
- After redis was down, the next 3 requests experienced a latency of 8 seconds. 
As circuit breaker was triggered, during 30 seconds cooldown period, the subsequent requests from directly fetched from database instead of waiting for redis cache
- The circuit breaker is configured to check every 30 seconds, whether Redis was up

Fix: 
- Have added the redis status to the '/health' endpoint 
- Added the alert on Prometheus if p95 latency is greater than 2 seconds
- Added the alert on Prometheus if cache hit ratio is less than 0.1 for more than 30 seconds
- For Redis configuration, have set socket_connect_time_out and socket_timeout at 0.1 



