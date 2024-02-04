import logging
from channels.middleware import BaseMiddleware
from firebase_admin import auth
from asgiref.sync import sync_to_async

from user.models import User


class AuthMiddleware(BaseMiddleware):
     async def __call__(self, scope, receive, send):
          token = None

          authorization_header = dict(scope.get("headers", {})).get(b'authorization', b'').decode("utf-8")
          if authorization_header.startswith('Bearer '):
               token = authorization_header[len('Bearer '):]
          else:
               await send({"type": "websocket.close", "code": 401, "reason": "unauthorized: authentication token not provided or invalid"})
               return
          
          # Verify Firebase token 
          try:
               uid = auth.verify_id_token(token).get('uid')
     
               # Fetch user based on the UID
               user = await get_user_by_uid(uid)
               if user is None:
                    await send({"type": "websocket.close", "code": 404, "reason": "not_found: user not found with provided auth token"})
                    return 
          except auth.ExpiredIdTokenError:
               logging.error("forbidden: expired token")
               await send({"type": "websocket.close", "code": 403, "reason": "forbidden: expired token"})
               return 
          except auth.InvalidIdTokenError:
               logging.error("unauthorized: invalide token")
               await send({"type": "websocket.close", "code": 401, "reason": "unauthorized: invalide token"})
               return 
          except Exception:
               logging.error("user provided with the auth token is not a valid Firebase user, it has no Firebase UID")
               await send({"type": "websocket.close", "code": 500, "reason": "user provided with the auth token is not a valid Firebase user, it has no Firebase UID"})
               return 
          
          scope["user"] = user
          return await super().__call__(scope, receive, send)

@sync_to_async
def get_user_by_uid(uid):
     try:
          return User.objects.get(uid=uid)
     except User.DoesNotExist:
          logging.error("not_found: user not found with provided auth token")
          return None
     except Exception as e:
          logging.error(f"Error while querying the user: {str(e)}")
          return None