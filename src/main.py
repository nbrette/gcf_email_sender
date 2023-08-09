import base64
import json
import logging
import os
from http import HTTPStatus

import functions_framework
from functions_framework import flask
from jinja2 import Environment, FileSystemLoader
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

SENDGRID_API_KEY = os.environ["SENDGRID_API_KEY"]
FROM = os.environ["FROM"]
TO = os.environ["TO"]
TEMPLATE_FILE = "email_template.html"

logger = logging.getLogger("GCF_EMAIL_SENDER")
logging.basicConfig(level=logging.INFO)


@functions_framework.cloud_event
def send_email(cloud_event):
    """Function to handle new pubsub message published"""

    # Decode pubsub message and convert it
    decoded_bytes = base64.b64decode(cloud_event.data["message"]["data"])
    decoded_string = decoded_bytes.decode("utf-8")
    result = json.loads(decoded_string)

    template_dir = os.path.join(os.path.dirname(__file__), "templates")
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template(TEMPLATE_FILE)

    content = template.render(items=result["listings"])

    sg = SendGridAPIClient()
    message = Mail(
        from_email=FROM,
        to_emails=TO,
        subject=f"New {result['set']} listings",
        html_content=content,
    )
    response = sg.send(message)

    if response.status_code not in [200, 201, 202]:
        logger.error(
            f"Error when sending email, ended with code {response.status_code}"
        )
        flask.abort(HTTPStatus.INTERNAL_SERVER_ERROR)

    logger.info(
        f"Email sent for {result['set']} with {len(result['listings'])} new listings"
    )

    return HTTPStatus.OK
