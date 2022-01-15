from setuptools import setup

setup(
    name="logger-docker",
    version="0.1.0",
    author="Ramon Darwich de Menezes",
    description="Logs optional communication between anything and provides a visual interface",
    license="GNU",
    install_requires=["flask", "flask-sqlalchemy", "flask-login", "flask-sslify", "requests",
                      "psycopg2", "werkzeug", "sqlalchemy", "psutil", "gunicorn"],
    entry_points={
        "console_scripts": [
            # <Nome do Comando>=<Modulo (Arquivo)>:<Funcao>
            "run_log_server=startup:main"
        ]
    }
)
