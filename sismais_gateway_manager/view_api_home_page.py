from django.http import HttpResponse


def index(request):
    status_api = '<b><span style="color: green;"> Online! </span></b>'
    return HttpResponse(
        f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset='utf-8'>
            <meta http-equiv='X-UA-Compatible' content='IE=edge'>
            <title>API / Sismais Gateway Manager</title>
            <meta name='viewport' content='width=device-width, initial-scale=1'>
        </head>
        <body>
            <h1>API Sismais Gateway Manager!</h1>
            Status: {status_api}
            <p>
                Documentação:
                <a href="api-auth/login/">api-auth/login/</a>
            </p>
        </body>
        </html>
        """,
    )
