import os
from smtp_web import create_app

app = create_app()

if __name__ == '__main__':
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 5000))

    app.run(host=host, port=port, use_reloader=False)
