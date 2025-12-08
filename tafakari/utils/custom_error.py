from rest_framework.response import Response

def error_response(message, errors=None, status_code=400):
    return Response(
        {
            "status": "error",
            "message": message,
            "stack": errors or {},
            "error": {
                "statusCode": status_code,
                "status": "error"
            }
        },
        status=status_code
    )
