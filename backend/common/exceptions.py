from rest_framework.views import exception_handler

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        errors = []
        if isinstance(response.data, dict):
            for field, messages in response.data.items():
                if isinstance(messages, list):
                    for msg in messages:
                        errors.append({'field': field, 'detail': str(msg)})
                else:
                    errors.append({'field': field, 'detail': str(messages)})
        elif isinstance(response.data, list):
            errors = [{'detail': str(msg)} for msg in response.data]
        response.data = {'errors': errors}
    return response
