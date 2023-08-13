import redis

from config_data.conf import conf

r = redis.StrictRedis(host=conf.redis_db.redis_host,
                      port=conf.redis_db.redis_port,
                      password=conf.redis_db.redis_password,
                      db=conf.redis_db.redis_db_num)


