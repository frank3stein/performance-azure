from flask import Flask, request, render_template
import os
import random
import redis
import socket
import sys
import logging
from applicationinsights import TelemetryClient
from datetime import datetime
import logging

from opencensus.ext.azure.log_exporter import AzureLogHandler
from opencensus.ext.azure import metrics_exporter
from opencensus.stats import aggregation as aggregation_module
from opencensus.stats import measure as measure_module
from opencensus.stats import stats as stats_module
from opencensus.stats import view as view_module
from opencensus.tags import tag_map as tag_map_module
from opencensus.ext.azure.trace_exporter import AzureExporter
from opencensus.trace.samplers import ProbabilitySampler
from opencensus.trace.tracer import Tracer
from opencensus.ext.flask.flask_middleware import FlaskMiddleware
from opencensus.trace.samplers import ProbabilitySampler
from applicationinsights.flask.ext import AppInsights


# App Insights
# TODO: Import required libraries for App Insights

# tc = TelemetryClient("InstrumentationKey=264396b1-b060-4052-ad86-5e2f0e0c842b;IngestionEndpoint=https://westeurope-1.in.applicationinsights.azure.com/")
# tc.track_event("Test event", {"foo": "bar"}, {"baz": 42})
# tc.flush()


# Logging
# logger = # TODO: Setup logger

# Metrics
# exporter = # TODO: Setup exporter

# Tracing
# tracer = # TODO: Setup tracer

# app = Flask(__name__)

# Requests
# middleware = # TODO: Setup flask middleware


instrumentation_key = "264396b1-b060-4052-ad86-5e2f0e0c842b"
print(instrumentation_key)
tc = TelemetryClient(instrumentation_key)
# logging
logger = logging.getLogger(__name__)
logger.addHandler(
    AzureLogHandler(
        connection_string="InstrumentationKey=264396b1-b060-4052-ad86-5e2f0e0c842b"
    )
)


# Metrics
exporter = metrics_exporter.new_metrics_exporter(
    enable_standard_metrics=True,
    connection_string="InstrumentationKey=264396b1-b060-4052-ad86-5e2f0e0c842b",
)

# Tracing
tracer = Tracer(
    exporter=AzureExporter(
        connection_string="InstrumentationKey=264396b1-b060-4052-ad86-5e2f0e0c842b"
    ),
    sampler=ProbabilitySampler(1.0),
)
app = Flask(__name__)

# Requests
# Flask middleware
middleware = FlaskMiddleware(
    app,
    exporter=AzureExporter(
        connection_string="InstrumentationKey=264396b1-b060-4052-ad86-5e2f0e0c842b"
    ),
    sampler=ProbabilitySampler(rate=1.0),
)


# Load configurations from environment or config file
app.config.from_pyfile("config_file.cfg")

if "VOTE1VALUE" in os.environ and os.environ["VOTE1VALUE"]:
    button1 = os.environ["VOTE1VALUE"]
else:
    button1 = app.config["VOTE1VALUE"]

if "VOTE2VALUE" in os.environ and os.environ["VOTE2VALUE"]:
    button2 = os.environ["VOTE2VALUE"]
else:
    button2 = app.config["VOTE2VALUE"]

if "TITLE" in os.environ and os.environ["TITLE"]:
    title = os.environ["TITLE"]
else:
    title = app.config["TITLE"]

# Redis Connection
r = redis.Redis()

# Change title to host name to demo NLB
if app.config["SHOWHOST"] == "true":
    title = socket.gethostname()

# Init Redis
if not r.get(button1):
    r.set(button1, 0)
if not r.get(button2):
    r.set(button2, 0)


@app.route("/", methods=["GET", "POST"])
def index():

    if request.method == "GET":

        # Get current values
        vote1 = r.get(button1).decode("utf-8")
        # Tracer for azure appinsights
        tracer.span(name="Button 1 cat vote is clicked")
        logger.warning(f"Cat button is clicked {vote1} times")
        tc.track_event("Cat button is clicked", {"clickcount": r.get(button1)})
        vote2 = r.get(button2).decode("utf-8")
        tc.track_event("Dog button is clicked", {"clickcount": r.get(button2)})
        tracer.span(name="Button 2 dog vote is clicked")
        logger.warning(f"Dog button is clicked {vote2} time")

        # Return index with values
        return render_template(
            "index.html",
            value1=int(vote1),
            value2=int(vote2),
            button1=button1,
            button2=button2,
            title=title,
        )

    elif request.method == "POST":

        if request.form["vote"] == "reset":

            vote1 = r.get(button1).decode("utf-8")
            properties = {"custom_dimensions": {"Cats Vote": r.get(button1)}}
            print(f"Cat button is clicked {vote1} times")
            logger.warning(f"Cat button is clicked {vote1} times in total.")
            # logger for appinsights
            print(f"Cat button has been clicked {r.get(button1)} times.")
            logger.warning("Cat Votes at Form Submit", extra=properties)
            vote2 = r.get(button2).decode("utf-8")
            properties = {"DogsVote": r.get(button2)}
            logger.warning("Dog Votes at Form Submit", extra=properties)

            # Empty table and return results
            r.set(button1, 0)
            r.set(button2, 0)

            return render_template(
                "index.html",
                value1=int(vote1),
                value2=int(vote2),
                button1=button1,
                button2=button2,
                title=title,
            )

        else:

            # Insert vote result into DB
            vote = request.form["vote"]
            r.incr(vote, 1)
            # Get current values
            vote1 = r.get(button1).decode("utf-8")

            vote2 = r.get(button2).decode("utf-8")
            if vote == "Cats":
                print("running")
                logger.warning(
                    f"%s have been clicked %s times" % (vote, vote1),
                    extra={"custom_dimensions": {"Cats Vote": vote1}},
                )
            else:
                logger.warning(
                    f"{vote} have been clicked {vote2} times",
                    extra={"custom_dimensions": {"Dogs Vote": r.get(button2)}},
                )

            # Return results
            return render_template(
                "index.html",
                value1=int(vote1),
                value2=int(vote2),
                button1=button1,
                button2=button2,
                title=title,
            )


if __name__ == "__main__":
    # comment line below when deploying to VMSS
    app.run()  # local
    # uncomment the line below before deployment to VMSS
    # app.run(host="0.0.0.0", threaded=True, debug=True)  # remote
