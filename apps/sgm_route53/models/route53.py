import route53
from sismais_gateway_manager.settings import env

class Route53():

    def __init__(self):
        self.conn = route53.connect(
            aws_access_key_id=env('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=env('AWS_SECRET_ACCESS_KEY'),
        )
