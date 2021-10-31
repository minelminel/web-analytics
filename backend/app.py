import os
import re
import sys
import json
import time
import random
import hashlib
import logging
from urllib.parse import urlparse

from dotenv import load_dotenv
from flask import Flask, request, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_marshmallow import Marshmallow

# from celery import Celery
from marshmallow import (
    fields,
    validate,
    pre_load,
    EXCLUDE,
)
from passlib.apps import custom_app_context as password_context

log = logging.getLogger(__name__)
load_dotenv()


class Config:
    def __init__(self, **overrides):
        for key, value in overrides.items():
            log.debug(f"Config override: {key} = {value}")
            setattr(self, key, value)

    LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG")
    LOG_FILE = os.getenv("LOG_FILE", None)
    # CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379")
    # CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379")
    SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI", "sqlite:///:memory:")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    def to_dict(self):
        pattern = r"\b[A-Z]+(_[A-Z]+)*\b"
        return {
            attr: getattr(self, attr) for attr in dir(self) if re.match(pattern, attr)
        }


def configure_logging(app):
    """
    Global logging configuration. Access in other modules using
    >>> import logging
    >>> log = logging.getLogger(__name__)
    """
    log_file = app.config.get("LOG_FILE", None)
    log_level = app.config.get("LOG_LEVEL", "INFO")

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(funcName)s:%(lineno)s - %(levelname)s - %(message)s"
    )
    handlers = []
    if log_file:
        file_handler = logging.FileHandler(filename=log_file, mode="a")
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)
    stream_handler = logging.StreamHandler(stream=sys.stdout)
    stream_handler.setFormatter(formatter)
    handlers.append(stream_handler)
    logging.basicConfig(
        datefmt="%m/%d/%Y %I:%M:%S %p", level=log_level, handlers=handlers
    )
    for _module, _level in app.config.get("LOGGING_OVERRIDES", {}).items():
        log.debug(f"Overriding module logging: {_module} --> {_level}")
        logging.getLogger(_module).setLevel(_level)
    return app


def create_app(**overrides):
    app = Flask(__name__)
    config = Config(**overrides)
    app.config.from_object(config)
    configure_logging(app)
    log.debug(config.to_dict())
    CORS(app)
    return app


app = create_app()
# celery = Celery(app.name, broker=app.config["CELERY_BROKER_URL"])
# celery.conf.update(app.config)
db = SQLAlchemy(app)
ma = Marshmallow()


def current_time():
    return int(time.time())


def sha256(string):
    return hashlib.sha256(string.encode("utf-8")).hexdigest()


class BaseSchema(ma.SQLAlchemyAutoSchema):
    """
    missing     used for deserialization (dump)
    default     used for serialization (load)
    https://github.com/marshmallow-code/marshmallow/issues/588#issuecomment-283544372
    """

    class Meta:
        """Alternate method of configuration which eliminates the need to
        subclass BaseSchema.Meta
        https://marshmallow-sqlalchemy.readthedocs.io/en/latest/recipes.html#base-schema-ii
        """

        sqla_session = db.session
        load_instance = True
        transient = True
        unknown = EXCLUDE

    @pre_load
    def set_nested_session(self, data, **kwargs):
        """Allow nested schemas to use the parent schema's session. This is a
        longstanding bug with marshmallow-sqlalchemy.
        https://github.com/marshmallow-code/marshmallow-sqlalchemy/issues/67
        https://github.com/marshmallow-code/marshmallow/issues/658#issuecomment-328369199
        """
        nested_fields = {
            k: v for k, v in self.fields.items() if type(v) == fields.Nested
        }
        for field in nested_fields.values():
            field.schema.session = self.session
        return data


class BaseModel(db.Model):
    __abstract__ = True
    id = db.Column(db.Integer(), primary_key=True)
    time = db.Column(db.Integer(), unique=False, nullable=False, default=current_time)


class UserModel(BaseModel):
    __tablename__ = "users"

    username = db.Column(db.String(32), unique=True, nullable=False)
    password = db.Column(db.String(128), unique=False, nullable=False)

    def hash_password(self, password):
        log.info("Hashing password")
        self.password = password_context.encrypt(password)


class CampaignModel(BaseModel):
    __tablename__ = "campaigns"

    user_id = db.Column(db.Integer(), unique=False, nullable=False)
    host = db.Column(db.String(), unique=False, nullable=True)
    name = db.Column(db.String(), unique=False, nullable=True)
    description = db.Column(db.String(), unique=False, nullable=True)


class VisitModel(BaseModel):
    __tablename__ = "visits"

    campaign_id = db.Column(db.Integer(), unique=False, nullable=False)
    ip = db.Column(db.String(), unique=False, nullable=False)
    url = db.Column(db.String(), unique=False, nullable=False)
    agent = db.Column(db.String(), unique=False, nullable=False)
    zone = db.Column(db.String(), unique=False, nullable=False)
    screen = db.Column(db.String(), unique=False, nullable=False)


class UserSchema(BaseSchema):
    class Meta(BaseSchema.Meta):
        model = UserModel

    id = fields.Int(dump_only=True)
    time = fields.Int()
    username = fields.Str(
        required=True, allow_none=False, validate=validate.Length(max=32)
    )
    password = fields.Str(
        load_only=True,
        required=True,
        allow_none=False,
        validate=validate.Length(max=128),
    )


class CampaignSchema(BaseSchema):
    class Meta(BaseSchema.Meta):
        model = CampaignModel

    id = fields.Int(dump_only=True)
    time = fields.Int()
    user_id = fields.Int(required=True, allow_none=False)
    homepage = fields.Str(required=False, allow_none=True)
    name = fields.Str(required=False, allow_none=True)
    description = fields.Str(required=False, allow_none=True)


class VisitSchema(BaseSchema):
    class Meta(BaseSchema.Meta):
        model = VisitModel

    id = fields.Int(dump_only=True)
    time = fields.Int()
    ip = fields.Str()
    url = fields.Str()
    agent = fields.Str()
    zone = fields.Str()
    time = fields.Int()
    screen = fields.Str()


# @celery.task
def process_request(campaign_id, visit):
    # Null guard clauses
    if campaign_id is None:
        log.debug(f"Skipping write, null campaign_id")
        return False
    campaign = CampaignSchema().dump(
        db.session.query(CampaignModel).filter_by(id=campaign_id).first()
    )
    if not campaign:
        log.debug(f"Skipping write, invalid campaign_id")
        return False
    # Hostname validation
    host = campaign.get("host")
    if host:
        o = urlparse(visit["url"])
        if host.lower() != o.hostname.lower():
            log.debug(f"Skipping write, failed hostname validation")
            return False
    # Write record
    row = VisitSchema().load(dict(**visit, campaign_id=campaign_id))
    db.session.add(row)
    db.session.commit()
    return True


@app.route("/api/campaign/<int:campaign_id>", methods=["POST"])
def campaign_view(campaign_id=None):
    visit = dict(**request.args, ip=request.remote_addr)
    result = process_request(campaign_id=campaign_id, visit=visit)
    return jsonify(result=result)


# @app.route("/task/<string:task_id>")
# def task_view(task_id=None):
#     if task_id is None:
#         return {"error": f"invalid task: {task_id}"}, 400
#     task = process_request.AsyncResult(task_id)
#     response = dict(
#         id=task_id,
#         status=task.status,
#         successful=task.successful(),
#         result=task.result if task.successful() else None,
#     )
#     return jsonify(response)


@app.route("/api/campaigns/<int:campaign_id>")
def campaigns_view(campaign_id=None):
    abort(403)
    if (
        campaign_id is None
        or not db.session.query(CampaignModel).filter_by(id=campaign_id).first()
    ):
        return {"error": f"invalid campaign: {campaign_id}"}, 400
    return jsonify(
        CampaignSchema().dump(
            db.session.query(CampaignModel).filter_by(id=campaign_id).first()
        )
    )


@app.route("/api/visits/<int:campaign_id>")
def visits_view(campaign_id=None):
    abort(403)
    if (
        campaign_id is None
        or not db.session.query(CampaignModel).filter_by(id=campaign_id).first()
    ):
        return {"error": f"invalid campaign: {campaign_id}"}, 400
    return jsonify(
        VisitSchema(many=True).dump(
            db.session.query(VisitModel).filter_by(campaign_id=campaign_id).all()
        )
    )


def startup():
    log.debug("Creating database")
    db.create_all()
    filepath = os.path.join("data", "db.json")
    log.debug(f"Reading file: {filepath}")
    with open(filepath, "r") as file:
        data = json.load(file)
    models = {m.__tablename__: m for m in (UserModel, CampaignModel, VisitModel)}
    for table, rows in data.items():
        log.debug(f"Hydrating: {table} ({len(rows)})")
        model = models[table]
        for row in rows:
            try:
                obj = model(**row)
                db.session.add(obj)
                db.session.commit()
            except Exception as err:
                log.error(err)
    log.debug("Finished startup function, good luck!")
    return data


if __name__ == "__main__":
    # This block only run in development
    db.drop_all()
    data = startup()

    # spoof some site visits (makes assumptions regarding db.json)
    schema = VisitSchema()
    kwargs = dict(
        campaign_id=data["campaigns"][0]["id"],
        ip="127.0.0.1",
        url="https://neetchy.com",
        agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.54 Safari/537.36",
        zone="America/New_York",
        screen="1920x1080",
    )
    now = current_time()
    records = 0
    days_ago = 3
    timestamp = now - (60 * 60 * 24 * days_ago)
    # increment from anywhere betweem 1s to 1h
    random_increment = lambda: random.randint(1, 3600)
    while timestamp <= now:
        timestamp += random_increment()
        obj = schema.load({**kwargs, "time": timestamp})
        db.session.add(obj)
        db.session.commit()
        records += 1
    log.debug(f"Added {records} mocked visit records in {current_time() - now} sec")

    if "shell" not in sys.argv:
        app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=True)
