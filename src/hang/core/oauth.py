from authlib.integrations.starlette_client import OAuth
from hang.schemas.config import conf

oauth_serv = OAuth()

oauth_serv.register(
    name="google",
    client_id=conf.GOOGLE_CLIENT_ID,
    client_secret=conf.GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)
