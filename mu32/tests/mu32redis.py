
import redis

r = redis.Redis(host='dbwelfare.beameo.fr', port=4379, decode_responses=True)
print( r.ping() )
