from firebase_admin import auth

class FirebaseTokenMiddleware:
    def __init__(self, get_response):
            self.get_response = get_response

        def __call__(self, request):
            # Get the Firebase access token from the request headers
            firebase_token = request.headers.get('Authorization')

            if firebase_token:
                try:
                    # Verify the Firebase token
                    decoded_token = auth.verify_id_token(firebase_token)
                    
                    # Extract the user's UID from the token and store it in the request object
                    request.user_uid = decoded_token['uid']
                except auth.ExpiredIdTokenError:a
                    # Handle token expiration or invalid token as needed
                    pass
                except auth.InvalidIdTokenError:
                    # Handle invalid token as needed
                    pass

            response = self.get_response(request)
            return response