from itsdangerous import URLSafeSerializer
from keys import secret_key,salt
def endata(data):
    serializer=URLSafeSerializer(secret_key)
    return serializer.dumps(data,salt=salt)

def dedata(data):
    serializer=URLSafeSerializer(secret_key)
    return serializer.loads(data,salt=salt)
